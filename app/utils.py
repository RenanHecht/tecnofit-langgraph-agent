import json
import os
from typing import List, Dict

def load_faq_data(file_path: str = "data/faq.json") -> List[Dict]:
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def format_faq_context(faq_data: List[Dict]) -> str:
    context_parts = []
    for item in faq_data:
        title = item.get("titulo", "Sem título")
        content = item.get("conteudo", "Sem conteúdo")
        context_parts.append(f"Tópico: {title}\nInformação: {content}")
    
    return "\n---\n".join(context_parts)