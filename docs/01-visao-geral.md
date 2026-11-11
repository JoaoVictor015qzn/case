# Visão geral e funcionalidades

## O problema

Um comprador descreve em português o que precisa ("preciso de 2 notebooks para o time de vendas, até US$ 1.500 cada"). O sistema precisa transformar esse texto numa requisição de compra **com produtos que existem de verdade**, com preço e estoque reais, sem que o modelo de linguagem invente nada.

O catálogo é a [DummyJSON](https://dummyjson.com/docs/products): cerca de 194 produtos em 24 categorias, em inglês e em dólar.

## O que o sistema faz

| Funcionalidade | Como funciona |
|---|---|
| Chat em português | O usuário escreve o pedido em http://localhost:3000 e recebe a resposta na mesma conversa |
| Agente que decide sozinho | O modelo escolhe quais tools chamar e em que ordem; não há sequência fixa no código |
| Busca com tradução | O catálogo é em inglês: o agente traduz os termos ("notebook" → "laptop", "celular" → "smartphone") |
| Busca por categoria | Se a palavra não acha nada, o agente busca de novo numa das 24 categorias reais e vê o que existe nela |
| Requisição gravada pela tool | O agente grava com `criar_requisicao`; título, preço, estoque e pedido mínimo vêm da DummyJSON |
| Regras de compra | O backend confere estoque, quantidade mínima por pedido e orçamento por unidade antes de gravar |
| Pedido parcial | Se só parte do pedido existe, grava o que existe e lista o resto em "o que faltou", com o motivo |
| Nada inventado | Se nada do pedido existe, responde 422 explicando o que faltou e não grava nada |
| Total calculado no servidor | Subtotais e total são somados com `Decimal` no backend, nunca pelo modelo |
| Ferramentas visíveis | O chat mostra cada tool chamada, com argumentos, duração e se deu erro |
| Sem duplicidade | Reenviar o mesmo pedido com a mesma `Idempotency-Key` devolve a requisição já criada |
| Erros claros | Catálogo fora, LLM fora ou lento e chave recusada viram mensagens em português no chat |
| Histórico | `GET /requisicoes` lista as requisições mais recentes |
| Inspeção do banco | pgAdmin em http://localhost:5050, já com o servidor cadastrado |

## Exemplos

| Pedido | Resultado esperado |
|---|---|
| "Preciso de 3 laptops para o time de vendas, até US$ 2.000 cada." | 201: requisição com 3 laptops reais dentro do orçamento |
| "Preciso de 2 notebooks de até US$ 1.500 cada." | 201: o agente traduz "notebook" para "laptop" |
| "3 smartphones Samsung e 1 mouse sem fio" | 201 parcial: os Samsung entram; o mouse vai para "o que faltou" |
| "Preciso de 5 Ferraris até US$ 10 cada." | 422: não existe no catálogo, nada é gravado |
| "Quero 3 laptops por no máximo US$ 50 cada." | 422: existem laptops, mas nenhum dentro do orçamento |

## O que o sistema não faz

- Não autentica usuários; `GET /requisicoes` mostra as requisições de todos.
- Não aprova nem envia a requisição a um fornecedor: ela é só registrada.
- Não faz streaming: a resposta aparece quando o agente termina.
- Não conhece produtos fora da DummyJSON.
