# Cenário Corporativo de Referência

Este documento aproxima o laboratorio de um ambiente corporativo parecido com o seu dia a dia:

- AWS como provider principal
- Azure Pipelines como esteira
- ArgoCD para entrega GitOps
- MongoDB como dependencia de aplicacao
- validacoes de seguranca no pipeline

## Objetivo

Usar o laboratorio nao apenas como demo de IA, mas como base para um fluxo mais realista:

1. pipeline roda validacoes
2. ferramentas de seguranca verificam codigo e dependencias
3. build e testes geram logs
4. a IA analisa a falha
5. a esteira publica artefatos
6. a entrega segue via GitOps / ArgoCD

## Fluxo sugerido

### 1. Desenvolvedor abre PR

O pipeline pode executar:

- lint
- testes
- SAST
- analise de dependencias
- policy checks

### 2. Pipeline falha

Em vez de depender apenas da leitura manual do log, o analisador:

- coleta o log
- classifica a falha
- consulta contexto do repositorio
- sugere causa raiz e acoes recomendadas

### 3. Time decide a resposta

Dependendo do tipo de erro:

- corrige e reexecuta
- faz rollback
- encaminha ao owner
- atualiza documentacao operacional

### 4. Entrega

Quando o build estiver saudavel:

- a imagem e promovida
- o repositorio GitOps e atualizado
- o ArgoCD aplica o estado desejado

## Onde entram SAST e analise de dependencias

Neste laboratorio, essas etapas ainda sao placeholders.
Mas o desenho esperado e:

- SAST antes de merge ou antes do deploy
- analise de dependencias antes da promocao
- bloqueio de release se houver risco alto

Nao importa tanto qual ferramenta sera usada no comeco.
O importante e o ponto de encaixe no pipeline.

## O que este repo ja cobre bem

- analise de logs com IA
- saida estruturada
- base inicial de contexto operacional
- exemplos de falhas comuns

## O que ainda podemos evoluir

- suporte real a Azure Pipelines como esteira principal
- provider AWS Bedrock
- mapeamento de owners
- contexto por aplicacao
- runbooks por stack real
- analise de falhas de MongoDB e conexao
- integracao com repositorio GitOps e ArgoCD

## Por que esse cenario e valioso

Porque ele aproxima o laboratorio da pergunta que interessa no trabalho:

"como transformar log + contexto + IA em algo que ajude decisao operacional?"

E isso e muito mais proximo da vida real do que apenas executar um modelo em cima de um log isolado.
