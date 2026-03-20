# Runbook: Erro de Sintaxe YAML

## Quando usar

Use este runbook quando ferramentas como Helm, kubectl, Argo CD ou CI acusarem erro de parse.

## Sinais comuns

- `mapping values are not allowed here`
- `did not find expected key`
- `error converting YAML to JSON`
- `yaml.scanner.ScannerError`

## Passos de investigacao

1. Identificar a linha reportada pelo erro.
2. Validar a indentacao perto da linha.
3. Conferir se ha:

- aspas faltando
- dois-pontos em lugar errado
- lista mal formatada
- chave repetida ou mal alinhada

4. Se for Helm, renderizar o template:

```bash
helm template <release> <chart>
```

5. Rodar um linter YAML, quando possivel.

## Acoes recomendadas

- corrigir indentacao
- revisar o bloco gerado por template
- comparar com uma versao conhecida como valida
