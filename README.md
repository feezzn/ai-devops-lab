# ai-devops-lab

Projeto Python minimalista para depuração de CI/CD com ajuda de IA usando a Responses API do Azure OpenAI.

## O que este projeto faz

- Lê um arquivo de log de CI/CD.
- Envia o log para um deployment do Azure OpenAI para análise.
- Salva um relatório estruturado em JSON.
- Gera um resumo em Markdown para publicar no GitHub Actions.
- Reduz o risco de exposição ao aplicar redação básica de segredos e truncamento de logs grandes.

## Estrutura do projeto

```text
ai-devops-lab/
  .github/workflows/
  knowledge/
  playbooks/
  runbooks/
  samples/
  scripts/
  README.md
  requirements.txt
```

## Variáveis de ambiente

Defina estas variáveis antes de executar a análise:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT` como `https://seu-recurso.openai.azure.com`
- `AZURE_OPENAI_DEPLOYMENT` como `gpt-4.1-mini`

## Como executar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/analyze_logs.py \
  --log-file samples/sample_ci_failure.log \
  --output-file samples/analysis.json

python scripts/render_summary.py \
  --input-file samples/analysis.json \
  --output-file samples/summary.md
```

## Como o fluxo funciona

1. O workflow simula uma falha de build.
2. O log dessa falha é salvo em arquivo.
3. O script `scripts/analyze_logs.py`:
   - lê o log
   - remove padrões comuns de segredo
   - limita o tamanho do conteúdo enviado
   - tenta classificar o erro localmente
   - chama o Azure OpenAI para gerar uma análise estruturada
4. O resultado é salvo em `samples/analysis.json`.
5. O script `scripts/render_summary.py` converte esse JSON em Markdown.
6. O GitHub Actions publica esse resumo na execução do job.

## O que é analisado

Hoje o projeto procura principalmente por estes tipos de problema:

- erro de dependência
- incompatibilidade de versão
- erro de sintaxe YAML
- falha de autenticação
- erro de runtime no Kubernetes
- erro de banco de dados
- falha de inicialização de container

Se o erro não combinar com essas regras, ele marca como `unknown`.

## Logs de exemplo incluidos

Voce pode testar manualmente diferentes cenarios usando os arquivos:

- `samples/sample_ci_failure.log`
- `samples/sample_k8s_crashloop.log`
- `samples/sample_yaml_error.log`
- `samples/sample_auth_failure.log`

No `workflow_dispatch`, basta escolher o arquivo desejado no campo `sample_log`.

## Contexto operacional

O laboratorio agora tambem inclui uma base inicial para evoluir a qualidade da analise:

- `knowledge/`
- `runbooks/`
- `playbooks/`

Essas pastas existem para registrar contexto adicional que a IA sozinha nao conhece, como:

- erros frequentes do ambiente
- formas de investigar cada falha
- acoes operacionais padronizadas
- orientacoes de rollback e triagem

Esse modelo ajuda a sair do pensamento "basta ligar a IA" e evoluir para uma abordagem
mais realista: IA + contexto + operacao.

## Observações

- O analisador usa o cliente `OpenAI` apontando para a URL base do Azure OpenAI.
- A saída estruturada é solicitada com JSON Schema pela Responses API.
- O workflow de exemplo roda em `push` para `main`, simula uma falha, salva o log e publica um resumo.
- Se os segredos do Azure OpenAI não estiverem configurados, o workflow gera um resumo de fallback explicando por que a análise por IA foi pulada.

## Próximos passos para testar de verdade

- Configurar os secrets `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` e `AZURE_OPENAI_DEPLOYMENT` no GitHub.
- Fazer um `git push` para a branch `main`.
- Abrir a execução do GitHub Actions e verificar o resumo publicado no job.
- Se quiser, você também pode rodar os scripts localmente com um log de exemplo antes de testar no GitHub.
