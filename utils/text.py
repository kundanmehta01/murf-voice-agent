import re
from typing import Any, Dict, List, Optional


def chunk_text(text: str, limit: int = 3000) -> List[str]:
    text = text.strip()
    if len(text) <= limit:
        return [text]
    sentences = re.split(r"(?<=[\.\!\?])\s+", text)
    chunks: List[str] = []
    current = ""
    for sent in sentences:
        if not current:
            current = sent
        elif len(current) + 1 + len(sent) <= limit:
            current += " " + sent
        else:
            chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    final: List[str] = []
    for ch in chunks:
        if len(ch) <= limit:
            final.append(ch)
        else:
            for i in range(0, len(ch), limit):
                final.append(ch[i : i + limit])
    return final


def build_prompt_from_history(history: List[Dict[str, Any]], persona_id: Optional[str] = None) -> str:
    lines: List[str] = []
    
    # Get persona-specific system prompt
    if persona_id:
        try:
            from personas import get_persona_system_prompt
            system_preamble = get_persona_system_prompt(persona_id)
        except ImportError:
            system_preamble = "You are a helpful, concise voice assistant. Keep responses clear and short."
    else:
        system_preamble = "You are a helpful, concise voice assistant. Keep responses clear and short."
    
    lines.append(f"System: {system_preamble}")
    
    # Add weather capability context
    lines.append("\nSKILLS: You have access to real-time weather information. When users ask about weather, temperature, forecasts, or weather conditions for any location, you can provide accurate, up-to-date information. Stay in character while delivering weather reports.")
    
    for msg in history:
        role = msg.get("role", "user")
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        prefix = "User" if role == "user" else "Assistant"
        lines.append(f"{prefix}: {content}")
    lines.append("Assistant:")
    return "\n".join(lines)

