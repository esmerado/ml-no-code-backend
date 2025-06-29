import os
from typing import List, Dict, Any

import httpx
from fastapi import HTTPException


def build_prompt(items: List[Dict[str, Any]], max_items: int = 30) -> str:
    trimmed = items[:max_items]

    rows = []
    for i, item in enumerate(trimmed, 1):
        line = ", ".join(f"{key}: {value}" for key, value in item.items())
        rows.append(f"{i}. {line}")

    joined = "\n".join(rows)
    return (
        f"Este conjunto contiene {len(items)} registros, pero solo se muestran los primeros {len(trimmed)}.\n\n"
        "Redacta un resumen en lenguaje natural a partir de los siguientes datos:\n\n"
        f"{joined}\n\n"
        "Identifica patrones relevantes, tendencias o agrupaciones destacadas."
    )


async def send_to_deepseek(prompt: str) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key no configurada.")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Eres un asistente experto en análisis de datos."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=50.0) as client:
        response = await client.post(url, json=body, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"DeepSeek error: {response.text}")
        return response.json()["choices"][0]["message"]["content"]
