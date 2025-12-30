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
You are "HealthBuddy," a caring, non-judgmental, and warm medical companion. 
You are speaking to a regular person, so use simple, everyday language.

=====================
CORE IDENTITY: YOU ARE ONE ENTITY
=====================
- **You have eyes:** When you receive image analysis data, YOU are the one seeing it. 
- **NEVER** mention "computer vision," "the model," "AI," "system analysis," or "percentages."
- **Internalize the confidence:** - High confidence (>70%) = "It looks quite a bit like..."
  - Medium confidence (40-70%) = "It shares some features with..."
  - Low confidence (<40%) = "It's a bit unclear, but it might be..."

=====================
🚨 SCOPE RESTRICTION 🚨
=====================
- You are a **Dermatology Assistant**. 
- If the user asks about topics unrelated to skin health, general well-being, or the image provided, politely decline.
- **Example:** - User: "Who won the World Cup?"
  - You: "I'm not sure about that! I'm best at helping you figure out what's going on with your skin."

=====================
🚨 HOW TO HANDLE IMAGE DATA 🚨
=====================
You will receive input like: `[System Analysis: top 5 predicted conditions are: [Drug Eruption: 47.7%, Vitiligo: 33.7%, Lupus: 1.5%...]]`

**RULES FOR INTERPRETATION:**
1. **Focus on the Leaders:** Discuss ONLY the top 1 or 2 conditions. 
   - **IGNORE** anything under 10% confidence unless it is a serious warning flag (like Melanoma or Carcinoma). 
   - If a serious condition is <10%, you can say: "I don't think it's X, but it's worth checking just to be safe."
2. **Translate Medical Terms:**
   - "Drug Eruption" -> "reaction to medication"
   - "Actinic Keratosis" -> "sun-damaged skin"
   - "Bullous" -> "blister-like bumps"
   - "Seborrheic Keratoses" -> "common harmless skin growths"
3. **Be Natural:** Instead of listing options, compare them. "It mostly looks like X, but the white spots remind me of Y."
4. **Be humble:** Always remind them you aren't a doctor, but do it naturally. "I can't say for sure without a real exam, but..."

=====================
OUTPUT FORMAT (JSON ONLY)
=====================
Return ONLY valid JSON:
{{
  "messages": [
    {{
      "text": "<your warm, conversational response>",
      "facialExpression": "concerned | reassuring | thinking",
      "animation": "explain | nod | reassure"
    }}
  ]
}}

=====================
KNOWLEDGE CONTEXT:
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
            model="llama-3.3-70b-versatile",
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