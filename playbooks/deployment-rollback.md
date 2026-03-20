# Playbook: Rollback de Deployment

## Objetivo

Restaurar rapidamente uma versao estavel quando um deploy recente causar falha operacional.

## Quando considerar rollback

- aumento de erro 5xx
- pods em falha apos deploy
- readiness/liveness falhando em massa
- regressao funcional evidente
- integracao critica indisponivel

## Validacoes antes do rollback

1. Confirmar que a falha comecou apos a nova versao.
2. Verificar se existe versao anterior saudavel.
3. Garantir que rollback nao vai quebrar migracoes irreversiveis.

## Acoes

1. Identificar a revisao anterior.
2. Executar rollback pela ferramenta usada pelo time.
3. Confirmar rollout saudavel.
4. Monitorar servico por alguns minutos.
5. Registrar incidente e causa provavel.

## Pos-acao

- bloquear nova promocao ate causa raiz ser entendida
- abrir correcao do pipeline, chart ou aplicacao
- atualizar knowledge e runbooks se a falha for recorrente
