from typing import TypedDict, Annotated, List, Optional
import operator
from langchain_core.messages import BaseMessage

class UserInfo(TypedDict):
    nome: Optional[str]
    email: Optional[str]
    telefone: Optional[str]

class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    intent: str
    user_question: str
    user_info: Optional[UserInfo]