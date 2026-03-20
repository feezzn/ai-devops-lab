# Modelo Operacional do Laboratorio

Este documento resume a ideia central do projeto e o que aprendemos na V1.

## Ideia principal

Uma IA consegue ler logs, resumir falhas e sugerir proximos passos.
Isso ja traz valor.

Mas para uma analise ser realmente util em ambientes reais, nao basta apenas enviar o log
para um modelo.

Uma boa estrutura combina:

- logs
- regras locais
- conhecimento de dominio
- runbooks
- playbooks

## O que a IA faz bem

- resumir o erro
- identificar padroes
- propor causa raiz provavel
- sugerir investigacoes iniciais
- produzir uma saida estruturada para CI/CD

## O que ainda depende do time e da plataforma

- contexto do ambiente
- ownership dos servicos
- politicas de seguranca
- procedimentos de rollback
- troubleshooting especifico da stack
- documentacao operacional

## Estrutura recomendada

### `knowledge/`

Base de conhecimento e contexto operacional.

Use para:

- taxonomia de erros
- convencoes da plataforma
- documentacao de referencia
- ownership e arquitetura

### `runbooks/`

Procedimentos de investigacao.

Use para:

- troubleshooting guiado
- comandos de validacao
- hipoteses comuns
- sinais que confirmam ou descartam cenarios

### `playbooks/`

Respostas operacionais padronizadas.

Use para:

- rollback
- reexecucao segura
- acao de contencao
- resposta a incidentes conhecidos

## Por que isso importa

Sem contexto adicional, a IA tende a sugerir passos genericos.

Com contexto, ela passa a gerar respostas mais proximas da realidade do time, como:

- validar permissoes no registry certo
- conferir probes do chart certo
- aplicar o rollback recomendado para aquele servico
- consultar o runbook exato para `CrashLoopBackOff`

## Frase-resumo

IA nao substitui conhecimento operacional.
Ela amplifica esse conhecimento quando o ambiente oferece contexto estruturado.

## Estado atual do projeto

### V1 pronta

- integracao com Azure OpenAI
- workflow no GitHub Actions
- logs de exemplo
- resumo em Markdown
- fallback sem IA

### Proxima etapa

Iniciar adaptacao para AWS Bedrock, mantendo a mesma ideia:

- logs como entrada
- JSON estruturado como saida
- contexto adicional via knowledge, runbooks e playbooks
