# knowledge

Esta pasta guarda conhecimento de referencia para ajudar a IA a sair do modo "generico"
e produzir analises mais uteis para o time.

## Objetivo

Aqui entram materiais que explicam como o ambiente funciona e quais erros aparecem com
mais frequencia. A ideia nao e repetir o log, e sim oferecer contexto.

## O que faz sentido guardar aqui

- taxonomia de erros comuns
- padroes de falha por tecnologia
- convencoes da plataforma
- links para documentacao interna
- ownership por servico ou componente
- boas praticas da esteira

## Como a IA usa esse material

O log mostra o sintoma.
O conteudo desta pasta ajuda a IA a entender o contexto e sugerir acoes mais especificas.

## Exemplo

Se o log mostrar `ImagePullBackOff`, a IA pode cruzar isso com o conhecimento daqui para:

- lembrar que o time usa registry privado
- sugerir validacao de permissoes no registry
- orientar a consulta do runbook certo

## Proximos passos

- adicionar conhecimento por dominio: Kubernetes, Helm, Docker, Terraform e CI/CD
- mapear erros frequentes do ambiente real
- conectar estes arquivos ao analisador como contexto adicional
