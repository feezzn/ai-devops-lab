# Adaptacao para AWS Bedrock

Este documento marca o inicio da fase AWS do laboratorio.

## Objetivo

Permitir que o analisador funcione com dois providers:

- Azure OpenAI
- Amazon Bedrock

## Direcao tecnica

O desenho mais saudavel e separar o projeto em camadas:

1. leitura e sanitizacao do log
2. classificacao local
3. cliente do provider LLM
4. validacao do JSON retornado
5. renderizacao do resumo

## Variaveis esperadas para AWS

- `LLM_PROVIDER=aws`
- `AWS_REGION`
- `BEDROCK_MODEL_ID`

## Autenticacao recomendada

Usar OIDC com GitHub Actions e role temporaria na AWS.

Evitar:

- access key fixa por repositorio
- secrets de longa duracao

## Operacao recomendada

- usar modelo pequeno para laboratorio
- manter limite de custo e budget
- testar primeiro com `workflow_dispatch`
- depois integrar com cenarios reais

## Referencias oficiais consultadas

- Amazon Bedrock Converse com Boto3:
  https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started-api-ex-python.html
- Converse API examples:
  https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-examples.html
- AWS Budgets:
  https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html

## Proximo passo de implementacao

Adicionar suporte no script `scripts/analyze_logs.py` para:

- `provider=azure`
- `provider=aws`

mantendo o mesmo formato de saida JSON para nao quebrar o restante do fluxo.
