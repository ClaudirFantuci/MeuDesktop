## 1. Visão do projeto

O projeto Django `MeuDesktop` possui estes apps instalados:

- Apps nativos do Django: `admin` (administração), `auth` (usuários, grupos e autenticação), `contenttypes`, `sessions`, `messages` e `staticfiles`.
- `crispy_forms` e `crispy_bootstrap5`: renderização de formulários com Django Crispy Forms e Bootstrap 5.
- `website`: domínio principal do sistema, com catálogo de componentes de computador, fabricantes, montagem de PCs, histórico de montagem, autenticação e telas web.
- `debug_toolbar`: diagnóstico durante o desenvolvimento.

A versão declarada do Django é `5.2.11`. O usuário é o modelo padrão do Django (`auth.User`), pois `AUTH_USER_MODEL` não está configurado. O fuso horário é `America/Sao_Paulo`, com `USE_TZ = True`.

O `.env` não é carregado. Não há `python-dotenv`, `load_dotenv` ou configuração equivalente. A configuração de banco está escrita diretamente em `MeuDesktop/settings.py` por meio de `DATABASE_URL`, incluindo credenciais.

Não existe um `base.html` separado. `website/templates/website/model.html` é o template base efetivamente usado pelas páginas. Ele define os blocos `title`, `breadcrumb_wrapper`, `breadcrumb` e `content`. Os templates de autenticação, catálogo e montagem usam `{% extends "website/model.html" %}`. O CSS usa Bootstrap 5.3.3 via CDN, Bootstrap Icons 1.11.3 via CDN e `static/css/style.css`, com as fontes Fira Sans e Saira Stencil.

Os models usam chaves primárias inteiras: `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"`.

Não existe entidade dona dos dados como empresa, conta, loja, clínica ou turma. O catálogo de componentes é compartilhado. A entidade `Montagem` pertence ao usuário por meio de `usuario = ForeignKey(settings.AUTH_USER_MODEL)`, e as views filtram as montagens pelo usuário autenticado. `HistoricoMontagem` pertence indiretamente ao usuário pela `Montagem`.

## 2. O que já existe de IA

- Versão do `google-genai` no `requirements.txt`: não listado.
- Models de configuração de IA: nenhum.
- Chamadas a modelos de IA: nenhuma.

A busca no projeto, ignorando ambientes virtuais, `node_modules` e migrations, por `google.genai`, `from google import genai`, `google.generativeai`, `openai`, `anthropic`, `GEMINI` e `API_KEY` não encontrou ocorrências.

## 3. Propostas

O dono da cota deve ser o usuário autenticado. O projeto não possui uma entidade organizacional dona dos dados, e as montagens já têm vínculo direto com o usuário. Isso permite aplicar o limite mensal sem criar uma entidade nova e mantém a futura troca para uma organização localizada em uma decisão explícita.

Não há chamadas existentes para classificar. Para o chatbot futuro, proponho:

- Finalidade: `app_chatbot`. O nome segue o padrão `app_acao`, identifica a funcionalidade consumidora e evita amarrar o registro a um provedor ou modelo.
- Referência: um identificador opaco da conversa, como `conversation:<uuid>`, sem depender do nome ou do ID de um model de negócio. Isso permite agrupar as chamadas de uma conversa sem misturar a referência com o provedor, o modelo ou o conteúdo do prompt.

Para chamadas futuras relacionadas a uma montagem, uma referência opcional como `montagem:<id>` pode ser usada somente quando a chamada realmente pertencer ao fluxo daquela montagem; para o chatbot geral, deve ser usado o identificador de conversa.

## 4. Riscos

- A chave do banco está escrita diretamente em `MeuDesktop/settings.py`. Uma chave de provedor de IA não deve seguir esse padrão: deve ficar no `.env`, fora do controle de versão, e ser lida pela configuração.
- Não há carregamento de `.env` hoje. Será necessário definir esse mecanismo antes de usar `GEMINI_API_KEY`, sem colocar o segredo em model, migration, template ou log.
- Prompts e respostas podem conter nomes de usuário, preferências, identificadores de montagem ou outros dados pessoais. O desenho deve decidir se o registro guarda conteúdo bruto, somente metadados ou uma forma sanitizada.
- Sem limite transacional, chamadas concorrentes podem ultrapassar a cota mensal. A reserva/contabilização de tokens precisa ser atômica e ocorrer no ponto correto em relação à chamada externa.
- Falhas do provedor, timeouts e respostas incompletas podem deixar a situação e os tokens inconsistentes. O registro deve distinguir, no mínimo, sucesso, erro e bloqueio por cota.
- O provedor pode não informar tokens de forma uniforme. É preciso definir como tratar contagens ausentes, estimadas ou separadas entre entrada e saída.
- Registrar prompts, respostas, erros ou identificadores de referência sem política de retenção pode expor dados e aumentar o custo de armazenamento.
- Modelo, cotas, limites, prazos e preços não devem ser constantes no código; precisam ser configurações editáveis conforme a regra definida.
- A ausência de testes com provedor falso pode causar chamadas reais, gasto de tokens e dependência de internet na suíte de testes.
- O projeto usa PostgreSQL configurado diretamente no settings e `DEBUG = True`; esses pontos devem ser tratados antes de disponibilizar a integração em produção.

## 5. Perguntas

1. A cota mensal será individual por usuário, ou deverá ser compartilhada por uma futura entidade dona dos dados? Sugestão: começar por usuário autenticado, pois é o único dono existente no domínio.
2. A configuração de IA será global para o sistema ou poderá variar por usuário? Sugestão: configuração global editável por administrador, com o usuário da chamada registrado separadamente.
3. A cota deve considerar a soma dos tokens de entrada e saída, e uma chamada deve ser bloqueada antes de consultar o provedor quando a cota já estiver esgotada? Sugestão: somar entrada e saída e bloquear previamente para evitar gasto acima do limite.
4. O registro de chamada deve armazenar prompt e resposta, ou somente metadados como finalidade, referência, tokens, duração e situação? Sugestão: armazenar somente metadados nesta primeira etapa, reduzindo risco de dados pessoais.
5. A referência neutra deve ser sempre um identificador de conversa, ou o chatbot também poderá receber uma referência de montagem quando fizer parte desse fluxo? Sugestão: usar `conversation:<uuid>` por padrão e aceitar `montagem:<id>` apenas em chamadas explicitamente ligadas a uma montagem.
6. Quais situações mínimas devem existir para uma chamada, incluindo falha do provedor e bloqueio por cota? Sugestão: `SUCESSO`, `ERRO` e `BLOQUEADA_COTA`, com choices estáveis no model.
