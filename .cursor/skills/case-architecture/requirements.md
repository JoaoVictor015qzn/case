# Requisitos do case (extraídos do PDF)

## Fluxo esperado

Pedido de exemplo: *"Preciso de 3 laptops para o time de vendas, até US$ 2.000 cada."*

1. **Busca e escolhe**: o agente busca no catálogo e escolhe os itens.
2. **Salva e responde**: o agente salva uma requisição de compra e responde com itens, quantidade, preço e valor total.
3. **Não inventa**: se nada atender o pedido, ele diz o que falta em vez de inventar.

## As 4 peças (sobem juntas com `docker compose up`)

| Peça | O que faz |
|---|---|
| Servidor MCP | Expõe `buscar_produtos(termo)` e `detalhar_produto(id)`, que chamam a DummyJSON (`/products/search?q=` e `/products/{id}`) |
| Backend com o agente | `POST /requisicoes` recebe o pedido, chama o LLM pela OpenRouter, usa as ferramentas do MCP e salva no Postgres. `GET /requisicoes` lista as requisições salvas. Pode ser em Python, Go ou TypeScript |
| Postgres | Guarda as requisições e seus itens |
| Chat | Tela simples em React que envia o pedido e mostra a resposta com o número da requisição criada |

- LLM: chave da OpenRouter enviada pelo processo, que **expira em 7 dias**. O modelo fica à escolha do candidato.
- Usar framework de agentes é opcional (decidimos não usar).

## Requisitos obrigatórios

- [ ] `docker compose up` sobe as quatro peças.
- [ ] As tabelas são criadas automaticamente quando o ambiente sobe.
- [ ] O modelo decide quando chamar cada ferramenta, sem fluxo fixo no código.
- [ ] Se a DummyJSON falhar ou demorar, o chat mostra uma mensagem clara.
- [ ] Há um teste para cada ferramenta do servidor MCP, rodando sem chave de LLM.
- [ ] O README explica, em poucas linhas, como rodar e as principais decisões.

## Diferenciais (só se sobrar tempo)

- [ ] **Ferramentas no chat**: mostrar no chat quais ferramentas o agente chamou.
- [ ] **Script de teste**: um script com 5 pedidos de teste que mostra quantos o agente acertou.
- [ ] **CI**: CI com lint e testes.
- [ ] **Terceira ferramenta**: salvar a requisição por uma terceira ferramenta do MCP, `criar_requisicao`, deixando o agente decidir quando gravar.

## Entrega

- Enviar um `.zip` do projeto **com a pasta `.git`**, porque eles avaliam os commits.
- Pode usar IA para programar, desde que o README diga **como** ela foi usada.
- Depois há uma conversa sobre o que foi feito.

## Critérios de avaliação

| Critério | Peso | O que olham |
|---|---|---|
| Funciona | 35% | Seguindo o README, o projeto sobe na máquina deles e responde ao pedido de exemplo |
| Agente e MCP | 25% | Ferramentas bem definidas, prompt claro e respostas sem invenção |
| Integração e ambiente | 25% | Uso das APIs e do banco, tratamento de erros, Docker e configuração |
| Comunicação | 15% | README claro e conversa sobre as decisões |

## Implicações práticas

- **"Funciona" é 35%.** O `docker compose up` precisa funcionar de primeira numa máquina limpa: sem passo manual além de copiar o `.env`, sem depender de nada instalado no host e com portas documentadas.
- **A chave é um segredo.** Ela fica no `.env`, que está no `.gitignore`, com um `.env.example` versionado. O PDF contém a chave, então não deve ser commitado.
- **O pedido de exemplo é o teste de aceitação principal.** Ele deve estar no script de avaliação e no README.
