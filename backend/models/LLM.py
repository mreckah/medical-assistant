import os
import json
from typing import List, Dict
from groq import Groq
from models.rag import RagEngine

# --- CONFIGURATION ---
API_KEY = os.getenv("GROQ_API_KEY", "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")
client = Groq(api_key=API_KEY)

# Utilisation de doubles accolades {{ }} pour que .format() ne crash pas sur le JSON
# --- NEW ROLEPLAY TEMPLATE ---
SYSTEM_TEMPLATE = """
You are a warm, human medical companion. Talk to the user as a real person, not an AI model.

=====================
CORE INSTRUCTION
=====================
- Integrate the "KNOWLEDGE" below into your speech as if you already knew it.
- NEVER cite a source. NEVER say "Based on...", "The context says...", or "According to...".
- Speak in the FIRST PERSON ("I recommend", "You should", "I've found that").

=====================
EXAMPLES (DO vs. DON'T)
=====================
ROBOT: "Based on the provided info, Gazoogleitis is treated by eating bananas."
HUMAN: "I understand your concern about Gazoogleitis. To treat it, you should eat three purple bananas while standing on one leg."

ROBOT: "The context indicates that you should rest."
HUMAN: "I really think you should get some rest; it's the best thing for you right now."

=====================
FORBIDDEN PHRASES
=====================
If you use any of these, you fail:
- "Based on the information..."
- "According to the context..."
- "The documents state..."
- "As per the records..."

=====================
OUTPUT FORMAT
=====================
Return ONLY valid JSON:
{{
  "messages": [
    {{
      "text": "<your warm, direct response here>",
      "facialExpression": "neutral | calm | concerned | reassuring | attentive",
      "animation": "idle | nod | explain | reassure"
    }}
  ]
}}

=====================
KNOWLEDGE (USE THIS NATURALLY):
=====================
{retrieved_context}
"""

def call_groq_to_rewrite(message: str, history: List[Dict]) -> str:
    """Réécrit la requête pour optimiser la recherche RAG."""
    try:
        history_context = "\n".join([f"{m['role']}: {m['text']}" for m in history[-3:]])
        prompt = f"Based on history:\n{history_context}\n\nRewrite this message into a short medical search query: {message}\nQuery:"

        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="allam-2-7b",
            temperature=0,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Rewrite Error: {e}")
        return message


def ask_llm(message: str, image_path: str = None, history: List[Dict] = []) -> List[Dict]:
    print(f"--- Processing request (History: {len(history)} turns) ---")

    # 1. RAG Step
    search_query = call_groq_to_rewrite(message, history) if history else message
    retrieved_docs = RagEngine.search(search_query)
    context_text = "\n".join(retrieved_docs) if retrieved_docs else "No specific context found."

    # 2. Prepare Messages
    messages_payload = [
        {"role": "system", "content": SYSTEM_TEMPLATE.format(retrieved_context=context_text)}
    ]

    # 3. Add History (Natural language, NOT JSON strings)
    for msg in history:
        # On convertit le format frontend/db vers le format attendu par Groq
        role = "assistant" if msg.get('role') in ["models", "assistant"] else "user"
        messages_payload.append({"role": role, "content": msg.get('text', '')})

    # 4. Add Current Message
    messages_payload.append({"role": "user", "content": message})

    try:
        # 5. API Call
        chat_completion = client.chat.completions.create(
            messages=messages_payload,
            model="allam-2-7b",
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_content = chat_completion.choices[0].message.content
        print(f"--- LLM Output: {raw_content} ---")

        return json.loads(raw_content).get("messages", [])

    except Exception as e:
        print(f"Groq/JSON Error: {e}")
        return [{
            "text": "Désolé, j'ai rencontré une erreur lors de l'analyse de votre demande.",
            "facialExpression": "concerned",
            "animation": "reassure"
        }]