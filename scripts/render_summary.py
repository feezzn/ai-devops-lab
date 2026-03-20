#!/usr/bin/env python3
"""Gera um resumo em Markdown a partir da saida JSON da analise."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    # Este script trabalha com arquivos para ser encadeado facilmente no CI.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", required=True, help="Path to the JSON report.")
    parser.add_argument(
        "--output-file",
        required=True,
        help="Where to write the Markdown summary.",
    )
    return parser.parse_args()


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: dict) -> str:
    evidence_lines = "\n".join(f"- {item}" for item in report.get("evidence", []))
    action_lines = "\n".join(
        f"- {item}" for item in report.get("recommended_actions", [])
    )

    # O formato e simples para funcionar bem no resumo do job e em comentarios de PR.
    return f"""# Resumo de Depuracao de CI/CD

## Resumo
{report.get("summary", "Nenhum resumo disponivel.")}

## Causa Raiz
{report.get("root_cause", "Desconhecida")}

## Categoria
{report.get("category", "unknown")}

## Confianca
{report.get("confidence_score", "desconhecida")}

## Evidencias
{evidence_lines or "- Nenhuma evidencia capturada."}

## Acoes Recomendadas
{action_lines or "- Nenhuma recomendacao fornecida."}
"""


def main() -> int:
    args = parse_args()
    report = load_report(Path(args.input_file))

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(render_markdown(report), encoding="utf-8")

    print(f"Markdown summary written to {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
