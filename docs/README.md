# Documentação do agente de compras

Documentação técnica do projeto. O [README da raiz](../README.md) resume como rodar e as decisões principais; aqui está o detalhe de cada parte.

| Documento | O que tem |
|---|---|
| [Visão geral e funcionalidades](01-visao-geral.md) | O problema, o que o sistema faz e exemplos de pedidos |
| [Arquitetura](02-arquitetura.md) | Serviços, contextos DDD, camadas e o fluxo de um pedido de ponta a ponta |
| [Stack](03-stack.md) | Tecnologias, versões e por que cada uma foi escolhida |
| [Servidor MCP](04-servidor-mcp.md) | As três tools, o adapter da DummyJSON e o registro no backend |
| [Backend](05-backend.md) | O agente, o grounding, os casos de uso, a persistência e os erros |
| [Frontend](06-frontend.md) | O chat em Next.js e o BFF |
| [API HTTP](07-api.md) | Endpoints, corpos, respostas e códigos de status |
| [Dados](08-dados.md) | Tabelas, migrations e inspeção pelo pgAdmin |
| [Operação, testes e qualidade](09-operacao.md) | Variáveis de ambiente, testes, CI, evals e solução de problemas |

## Glossário

| Termo | Significado |
|---|---|
| Pedido | Texto livre que o usuário digita no chat ("preciso de 3 laptops até US$ 2.000") |
| Requisição | Registro de compra gravado no banco, com itens, preços reais e total |
| Tool | Ferramenta exposta pelo servidor MCP e chamada pelo modelo (`buscar_produtos`, `detalhar_produto`, `criar_requisicao`) |
| Grounding | Garantia de que produto, preço e estoque vêm do catálogo, nunca do modelo |
| Snapshot | Cópia dos dados do produto no momento da compra (o catálogo pode mudar depois) |
| Idempotency key | Chave que impede gravar a mesma requisição duas vezes |
| BFF | *Backend for Frontend*: o Route Handler do Next que repassa o chat ao backend |
