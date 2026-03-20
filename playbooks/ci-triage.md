# Playbook: Triagem de Falhas em CI/CD

## Objetivo

Padronizar a primeira resposta a uma falha de pipeline.

## Fluxo sugerido

1. Identificar a primeira mensagem de erro relevante.
2. Classificar a falha em uma categoria conhecida.
3. Separar:

- erro da esteira
- erro de aplicacao
- erro de infraestrutura
- erro de permissao

4. Consultar o runbook correspondente.
5. Definir se cabe:

- corrigir e reexecutar
- fazer rollback
- encaminhar para outro time

## Resultado esperado

Ao final da triagem, deve existir:

- causa provavel
- evidencias
- acao imediata
- owner sugerido
