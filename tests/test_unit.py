import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import classify_intent, sales_node, route_step, LeadData

@pytest.fixture
def mock_runnables():
    with patch("langchain_core.runnables.RunnableSequence.invoke") as mock_seq, \
         patch("langchain_core.runnables.RunnableBinding.invoke") as mock_bind:
        
        manager = MagicMock()
        mock_seq.side_effect = manager
        mock_bind.side_effect = manager
        yield manager

def test_classify_intent_sticky_sales(mock_runnables):
    mock_response = MagicMock()
    mock_response.content = "vendas"
    mock_runnables.return_value = mock_response

    state = {
        "messages": [
            HumanMessage(content="Quero contratar"),
            AIMessage(content="Qual seu nome?"),
            HumanMessage(content="Renan")
        ]
    }

    result = classify_intent(state)
    assert result["intent"] == "vendas"

def test_sales_node_extraction(mock_runnables):
    lead_real = LeadData(nome="Carlos", telefone="4199999999", email="carlos@test.com", empresa=None)
    mock_runnables.return_value = lead_real

    state = {
        "messages": [HumanMessage(content="Sou Carlos, 4199999999")]
    }

    result = sales_node(state)
    
    data = result["lead_data"]
    assert data["nome"] == "Carlos"

def test_sales_node_fallback(mock_runnables):
    lead_vazio = LeadData(nome=None, telefone=None)
    mock_runnables.return_value = lead_vazio

    state = {
        "messages": [HumanMessage(content="Não quero informar")]
    }

    result = sales_node(state)
    
    data = result.get("lead_data", {})
    assert data.get("nome") is None

def test_route_step_logic():
    assert route_step({"intent": "vendas"}) == "vendas"
    assert route_step({"intent": "faq"}) == "faq"
    assert route_step({"intent": "geral"}) == "geral"