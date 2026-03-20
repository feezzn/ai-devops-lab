#!/usr/bin/env python3
"""Analisa logs de CI/CD com Azure OpenAI e gera JSON estruturado."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# Mantem o payload sob controle para reduzir custo e evitar enviar logs excessivos.
MAX_LOG_CHARS = 12_000


# O contrato de saida e enxuto para facilitar integracoes posteriores.
ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "root_cause": {"type": "string"},
        "category": {
            "type": "string",
            "enum": [
                "dependency_error",
                "version_mismatch",
                "yaml_syntax_issue",
                "authentication_failure",
                "kubernetes_runtime_error",
                "database_error",
                "container_startup_failure",
                "unknown",
            ],
        },
        "recommended_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "summary",
        "root_cause",
        "category",
        "recommended_actions",
        "confidence_score",
        "evidence",
    ],
}


# Regras locais fazem uma primeira classificacao antes da chamada ao modelo.
ISSUE_RULES = {
    "dependency_error": {
        "patterns": [
            r"No module named",
            r"ModuleNotFoundError",
            r"Could not resolve dependencies",
            r"Unable to locate package",
            r"npm ERR! code ERESOLVE",
            r"pip .* No matching distribution found",
            r"Could not find a version that satisfies the requirement",
            r"error: failed to solve:.*not found",
        ],
        "actions": [
            "Verifique se o nome e a versao da dependencia existem no registro de pacotes.",
            "Regenere o lockfile ou manifesto de dependencias se ele estiver desatualizado.",
            "Confirme se o ambiente de CI tem acesso a fonte de pacotes necessaria.",
        ],
    },
    "version_mismatch": {
        "patterns": [
            r"requires Python ['\"]?[><=].*",
            r"Unsupported engine",
            r"Expected version",
            r"version .* does not satisfy",
            r"RuntimeError: .*version",
            r"because no versions of .* match",
            r"found .* but expected",
        ],
        "actions": [
            "Alinhe a versao do runtime do CI com os requisitos declarados pela aplicacao.",
            "Fixe versoes compativeis das dependencias e atualize o lockfile.",
            "Revise mudancas recentes de versao no workflow, Dockerfile ou imagem de build.",
        ],
    },
    "yaml_syntax_issue": {
        "patterns": [
            r"yaml\.scanner\.ScannerError",
            r"mapping values are not allowed here",
            r"did not find expected key",
            r"found character that cannot start any token",
            r"while parsing a block mapping",
            r"error converting YAML to JSON",
        ],
        "actions": [
            "Valide o arquivo YAML com um linter antes de executar o pipeline.",
            "Inspecione indentacao, aspas e uso de dois-pontos perto da linha reportada.",
            "Compare o YAML alterado com uma versao conhecida como valida.",
        ],
    },
    "authentication_failure": {
        "patterns": [
            r"401 Unauthorized",
            r"403 Forbidden",
            r"AccessDenied",
            r"authentication failed",
            r"permission denied",
            r"invalid token",
            r"could not read Username",
            r"login failed",
            r"not authorized",
        ],
        "actions": [
            "Verifique se o secret ou token do CI esta presente e nao expirou.",
            "Confira a service account, role IAM ou permissoes de registry usadas pelo job.",
            "Confirme se o workflow esta expondo o secret para a etapa ou ambiente correto.",
        ],
    },
    "kubernetes_runtime_error": {
        "patterns": [
            r"CrashLoopBackOff",
            r"Back-off restarting failed container",
            r"ErrImagePull",
            r"ImagePullBackOff",
            r"Readiness probe failed",
            r"Liveness probe failed",
            r"OOMKilled",
        ],
        "actions": [
            "Verifique eventos do pod e logs do container para identificar a causa imediata da falha.",
            "Confirme probes, imagem do container, variaveis de ambiente e recursos configurados.",
            "Valide se a aplicacao sobe corretamente fora do cluster ou com configuracao minima.",
        ],
    },
    "database_error": {
        "patterns": [
            r"no such table",
            r"connection refused",
            r"could not connect to server",
            r"migration failed",
            r"database .* does not exist",
            r"sqlstate",
        ],
        "actions": [
            "Confirme se o banco esta acessivel e se as migrations foram aplicadas antes dos testes.",
            "Revise credenciais, endpoint e ordem de inicializacao dos servicos dependentes.",
            "Adicione validacoes de readiness do schema antes de executar testes ou aplicacao.",
        ],
    },
    "container_startup_failure": {
        "patterns": [
            r"exec format error",
            r"container exited with code",
            r"standard_init_linux.go",
            r"failed to start container",
            r"startup probe failed",
        ],
        "actions": [
            "Verifique o entrypoint, comando de inicializacao e arquitetura da imagem.",
            "Teste a imagem localmente para reproduzir o erro de startup antes do deploy.",
            "Revise variaveis obrigatorias e dependencias necessarias no boot do container.",
        ],
    },
}


SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[^\s]+"),
    re.compile(r"(?i)(password\s*[=:]\s*)[^\s]+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
]


def parse_args() -> argparse.Namespace:
    # Flags explicitas deixam o script simples de integrar ao GitHub Actions.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-file", required=True, help="Path to the CI/CD log file.")
    parser.add_argument(
        "--output-file",
        required=True,
        help="Where to write the JSON analysis report.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"),
        help="Azure OpenAI deployment name. Defaults to AZURE_OPENAI_DEPLOYMENT.",
    )
    parser.add_argument(
        "--max-log-chars",
        type=int,
        default=MAX_LOG_CHARS,
        help="Maximum number of sanitized log characters sent to the model.",
    )
    return parser.parse_args()


def build_client() -> Any:
    # No Azure OpenAI usamos o cliente padrao apontando para o endpoint v1 do Azure.
    from openai import OpenAI

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint or not api_key:
        raise RuntimeError(
            "Missing Azure OpenAI configuration. Set AZURE_OPENAI_ENDPOINT and "
            "AZURE_OPENAI_API_KEY."
        )

    base_url = endpoint.rstrip("/") + "/openai/v1/"
    return OpenAI(api_key=api_key, base_url=base_url)


def read_log(log_file: Path) -> str:
    if not log_file.exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")
    return log_file.read_text(encoding="utf-8")


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]" if pattern.groups else "[REDACTED]", redacted)
    return redacted


def limit_log_size(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    head_size = max_chars // 2
    tail_size = max_chars - head_size
    return (
        text[:head_size]
        + "\n\n... [TRUNCATED FOR SIZE] ...\n\n"
        + text[-tail_size:]
    )


def extract_evidence(log_text: str, patterns: list[str]) -> list[str]:
    evidence: list[str] = []
    for line in log_text.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            evidence.append(line.strip())
        if len(evidence) >= 3:
            break
    return evidence


def detect_known_issue(log_text: str) -> dict:
    for category, rule in ISSUE_RULES.items():
        evidence = extract_evidence(log_text, rule["patterns"])
        if evidence:
            return {
                "summary": f"Foi detectado um provavel caso de {category.replace('_', ' ')} no log de CI/CD.",
                "root_cause": evidence[0],
                "category": category,
                "recommended_actions": rule["actions"],
                "confidence_score": 0.88,
                "evidence": evidence,
            }

    return {
        "summary": "Nenhum padrao conhecido de erro de CI/CD combinou com o log.",
        "root_cause": "Nao foi possivel determinar um problema especifico usando apenas as regras locais.",
        "category": "unknown",
        "recommended_actions": [
            "Revise a etapa com falha e as linhas proximas ao primeiro erro explicito.",
            "Adicione mais logs por etapa ou artefatos se a falha continuar ambigua.",
            "Use a saida estruturada para encaminhar a falha ao time mais provavel.",
        ],
        "confidence_score": 0.35,
        "evidence": [],
    }


def validate_analysis(data: dict) -> dict:
    # Um validador pequeno evita dependencias extras e falha rapido em saidas invalidas.
    required_keys = set(ANALYSIS_SCHEMA["required"])
    missing = sorted(required_keys - set(data))
    if missing:
        raise ValueError(f"A resposta do modelo nao contem as chaves obrigatorias: {', '.join(missing)}")
    return data


def analyze_log(
    client: Any, model: str, log_text: str, heuristic_result: dict
) -> dict:
    prompt = f"""
You are an SRE assistant analyzing CI/CD logs.
Return only JSON that matches the provided schema.

Required behavior:
- Focus on the single most likely root cause.
- Prefer one of these categories when it fits: dependency_error, version_mismatch,
  yaml_syntax_issue, authentication_failure, kubernetes_runtime_error,
  database_error, container_startup_failure.
- The JSON values must be written in Brazilian Portuguese, except for the category field.
- Keep the summary concise and operational.
- Do not repeat or expose secrets even if they appear in the log.
- Confidence score must be between 0 and 1.

Local rule-based hint:
{json.dumps(heuristic_result, indent=2)}

Sanitized CI/CD log:
{log_text}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "cicd_debug_report",
                "strict": True,
                "schema": ANALYSIS_SCHEMA,
            }
        },
    )

    # `output_text` e a forma mais simples de obter o JSON retornado pelo modelo.
    payload = json.loads(response.output_text)
    return validate_analysis(payload)


def write_output(output_file: Path, data: dict) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        client = build_client()
        raw_log_text = read_log(Path(args.log_file))
        redacted_log_text = redact_secrets(raw_log_text)
        heuristic_result = detect_known_issue(redacted_log_text)
        safe_log_text = limit_log_size(redacted_log_text, args.max_log_chars)
        analysis = analyze_log(client, args.model, safe_log_text, heuristic_result)
        write_output(Path(args.output_file), analysis)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Analise gravada em {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
