# Assistente Virtual Inteligente (Tecnofit Case)

Este projeto implementa um agente conversacional orquestrado via LangGraph e OpenAI, capaz de classificar intenções, responder dúvidas técnicas (FAQ) e realizar a captação de leads com extração de dados estruturados.

## Arquitetura e Decisões Técnicas

Este projeto foi desenhado focando em simplicidade e manutenibilidade, evitando complexidade acidental (overengineering), conforme solicitado nos requisitos.

1. **Orquestração via Grafos (LangGraph)**
   Optou-se pelo uso de grafos de estado (StateGraph) em vez de cadeias lineares (Chains) para permitir ciclos de feedback e maior controle sobre o fluxo de conversação, facilitando a expansão futura para novos cenários de atendimento.

2. **RAG Simplificado (JSON)**
   Para a base de conhecimento, foi implementada uma estratégia de recuperação baseada em arquivo estático (JSON). Esta decisão garante latência mínima e elimina a necessidade de infraestrutura complexa de bancos vetoriais (Vector Stores) para o escopo deste teste, mantendo a precisão das respostas sobre os produtos.

3. **Extração Estruturada (Pydantic)**
   A captura de leads utiliza a funcionalidade de Structured Outputs da OpenAI combinada com validação Pydantic. Isso assegura que os dados (nome, telefone) sejam extraídos em formato estrito, eliminando erros de parsing comuns em abordagens baseadas apenas em prompt.

## Funcionalidades

1. **Roteamento Semântico:** Classifica a intenção do usuário entre Vendas, Suporte ou Conversa Geral com base no histórico.
2. **Memória de Estado:** Mantém o contexto da conversa (persistência via thread_id).
3. **Extração de Dados:** Identifica e estrutura informações de contato (Nome, Telefone, Empresa) para geração de leads qualificados.
4. **Observabilidade:** Integração com Langfuse para tracing e monitoramento de execução.

## Tecnologias

- Python 3.12
- LangGraph & LangChain
- FastAPI (Interface HTTP)
- Docker & Docker Compose
- Langfuse (Observabilidade)
- Pytest (Testes Automatizados)

## Pré-requisitos

Para executar este projeto, você precisará de:

1. **Docker** e **Docker Compose** instalados.
2. Uma chave de API da **OpenAI** (OPENAI_API_KEY).
3. Uma conta e chaves do **Langfuse** (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY) para visualizar a telemetria.
   * Nota: O projeto funciona sem o Langfuse, mas a telemetria será desativada.

## Configuração

1. Clone este repositório.
2. Na raiz do projeto, crie um arquivo `.env` baseado no modelo `.env.example`.
3. Preencha as variáveis de ambiente no arquivo `.env`:
```properties
OPENAI_API_KEY=sk-sua-chave-aqui
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-sua-chave
LANGFUSE_SECRET_KEY=sk-lf-sua-chave
```

## Execução

Para iniciar a aplicação em container:
```
bash
docker-compose up --build
```
A API estará disponível em http://localhost:8000.

## Como Testar

A API possui documentação interativa (Swagger UI) disponível em:
http://localhost:8000/docs. 

1. Teste de Conversação (Endpoint POST /chat)
Utilize o endpoint /chat para interagir. É fundamental enviar o parâmetro thread_id para manter a memória da conversa.

Exemplo de Payload (Início):

json{
  "message": "Gostaria de contratar um plano",
  "thread_id": "teste_01"
}

Exemplo de Payload (Resposta com dados):
json{
  "message": "Meu nome é João Silva, telefone 41 99999-9999",
  "thread_id": "teste_01"
}

### ✅ Executando Testes

O projeto possui testes unitários que validam a lógica de roteamento e extração de dados isoladamente.

Para rodar a suíte de testes dentro do container Docker:
```bash
docker-compose exec -e PYTHONPATH=. api pytest -v
```

## Verificação de Telemetria (Langfuse)

Acesse o dashboard do Langfuse (https://cloud.langfuse.com).
Navegue até a seção Traces.
Filtre pelo Session ID igual ao thread_id utilizado no teste (ex: "teste_01").
Você poderá visualizar o fluxo completo de execução, incluindo a classificação de intenção e os dados extraídos pelo parser.
