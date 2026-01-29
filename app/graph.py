from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import GraphState
from app.utils import load_faq_data

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class LeadData(BaseModel):
    nome: str | None = Field(default=None, description="Nome do cliente")
    telefone: str | None = Field(default=None, description="Telefone ou WhatsApp com DDD")
    email: str | None = Field(default=None, description="E-mail de contato")
    empresa: str | None = Field(default=None, description="Nome da academia ou empresa")

def classify_intent(state: GraphState):
    messages = state["messages"]
    last_user_message = messages[-1].content
    
    last_bot_context = ""
    if len(messages) > 1 and isinstance(messages[-2], AIMessage):
        last_bot_context = messages[-2].content

    faq_data = load_faq_data()
    faq_questions = "\n".join([f"- {item['pergunta']}" for item in faq_data])
    
    system_prompt = f"""
    Você é um classificador de intenções.
    
    CONTEXTO ANTERIOR (Pergunta do Bot):
    "{last_bot_context}"
    
    REGRAS DE CLASSIFICAÇÃO:
    1. vendas: SE o usuário está respondendo a uma pergunta sobre dados (nome, telefone) OU demonstrando interesse em contratar/preços.
    2. faq: SE a mensagem for semanticamente similar a:
    {faq_questions}
    3. geral: Apenas saudações, agradecimentos ou conversas fora do escopo.
    
    Responda APENAS a categoria.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"input": last_user_message})
    intent = response.content.strip().lower()
    
    if intent not in ["faq", "vendas", "geral"]:
        intent = "geral"
        
    return {"intent": intent, "user_question": last_user_message}

def faq_node(state: GraphState):
    user_question = state.get("user_question", "")
    faq_data = load_faq_data()
    
    context_str = "\n\n".join([f"P: {item['pergunta']}\nR: {item['resposta']}" for item in faq_data])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um especialista técnico. Responda ESTRITAMENTE com base no contexto abaixo.\n\nCONTEXTO:\n{context}"),
        ("user", "{question}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"context": context_str, "question": user_question})
    
    return {"messages": [response]}

def sales_node(state: GraphState):
    messages = state["messages"]
    last_user_msg = messages[-1].content
    
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", "Extraia nome, telefone e empresa. Retorne null se não encontrar."),
        ("user", "{text}")
    ])
    
    extractor = extraction_prompt | llm.with_structured_output(LeadData)
    lead_info = extractor.invoke({"text": last_user_msg})
    
    if lead_info.nome and (lead_info.telefone or lead_info.email):
        print(f"LEAD: {lead_info}")
        msg = f"Obrigado {lead_info.nome}. Recebi seus dados. Um consultor entrará em contato. Te ajudo com mais algum assunto?"
        return {
            "messages": [AIMessage(content=msg)],
            "lead_data": lead_info.model_dump()
        }
    
    sales_prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é de Vendas. Peça NOME e TELEFONE para prosseguir."),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    chain = sales_prompt | llm
    response = chain.invoke({"messages": messages})
    
    return {"messages": [response]}

def general_node(state: GraphState):
    system_prompt = """
    Você é o Assistente Virtual da Tecnofit.
    Seu foco exclusivo é gestão de academias, crossfit e centros esportivos.

    DIRETRIZES:
    1. Para saudações ("Oi", "Tudo bem"): Seja cordial, breve e pergunte como pode ajudar a academia do usuário.
    2. Para assuntos FORA DO CONTEXTO (Clima, política, piadas, conhecimentos gerais):
       - Explique educadamente que seu foco é apenas no sistema Tecnofit.
       - Tente redirecionar o usuário perguntando se ele quer saber sobre Funcionalidades ou Planos.

    Mantenha tom profissional e prestativo.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    return {"messages": [response]}

def route_step(state: GraphState):
    return state.get("intent", "geral")

workflow = StateGraph(GraphState)
memory = MemorySaver()

workflow.add_node("classifier", classify_intent)
workflow.add_node("faq", faq_node)
workflow.add_node("vendas", sales_node)
workflow.add_node("geral", general_node)

workflow.set_entry_point("classifier")

workflow.add_conditional_edges(
    "classifier",
    route_step,
    {
        "faq": "faq",
        "vendas": "vendas",
        "geral": "geral"
    }
)

workflow.add_edge("faq", END)
workflow.add_edge("vendas", END)
workflow.add_edge("geral", END)

app_graph = workflow.compile(checkpointer=memory)