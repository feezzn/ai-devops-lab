# Taxonomia de Erros Comuns

Este documento organiza classes de erro que costumam aparecer em pipelines e ambientes de runtime.

## CI/CD

- `dependency_error`
  Exemplo: pacote nao encontrado, lockfile desatualizado, registry inacessivel.

- `version_mismatch`
  Exemplo: versao do Python, Node, imagem base ou dependencia incompatível.

- `yaml_syntax_issue`
  Exemplo: erro de indentacao, chave invalida, `mapping values are not allowed here`.

- `authentication_failure`
  Exemplo: token expirado, credencial ausente, `401 Unauthorized`, `403 Forbidden`.

## Runtime

- `kubernetes_runtime_error`
  Exemplo: `CrashLoopBackOff`, `ImagePullBackOff`, probes falhando, `OOMKilled`.

- `database_error`
  Exemplo: `no such table`, `connection refused`, migration nao aplicada.

- `container_startup_failure`
  Exemplo: entrypoint incorreto, erro de arquitetura, variavel obrigatoria ausente.

## Como usar

Quando uma nova falha aparecer:

1. verificar se ela se encaixa em alguma categoria existente
2. registrar evidencias tipicas
3. apontar validacoes recomendadas
4. linkar um runbook ou playbook correspondente
