# Runbook: CrashLoopBackOff

## Quando usar

Use este runbook quando pods entrarem em `CrashLoopBackOff`, reiniciarem continuamente
ou falharem durante o startup.

## Objetivo

Identificar se a causa esta em:

- configuracao da aplicacao
- imagem do container
- variaveis de ambiente
- conectividade com dependencias
- probes
- limite de recursos

## Passos de investigacao

1. Descrever o pod:

```bash
kubectl describe pod <pod> -n <namespace>
```

2. Ler os logs atuais e anteriores:

```bash
kubectl logs <pod> -n <namespace>
kubectl logs <pod> -n <namespace> --previous
```

3. Confirmar o motivo da ultima finalizacao:

- `Error`
- `OOMKilled`
- `Completed`
- `CrashLoopBackOff`

4. Revisar variaveis obrigatorias:

- segredos montados
- configmaps
- parametros do Helm

5. Validar probes:

- readiness
- liveness
- startup

6. Verificar se a aplicacao sobe fora do cluster ou com configuracao minima.

## Sinais comuns

- `Back-off restarting failed container`
- `Readiness probe failed`
- `Liveness probe failed`
- `RuntimeError: <variavel> is required`

## Causas frequentes

- `DATABASE_URL` ausente
- comando de startup incorreto
- imagem errada
- app demorando mais que o esperado para subir
- dependencia externa indisponivel

## Acoes recomendadas

- corrigir variaveis de ambiente
- ajustar probes
- revisar entrypoint e command
- validar imagem publicada
- revisar requests e limits
