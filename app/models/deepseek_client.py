# app/clients/deepseek_client.py

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class DeepSeekClient:
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")

        if not api_key:
            raise ValueError("❌ Falta la variable DEEPSEEK_API_KEY en tu entorno")

        # Cliente OpenAI con base_url apuntando a DeepSeek
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )

    def get_response(self, prompt: str, temperature: float = 0.7, model: str = "deepseek-chat") -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente experto en machine learning que explica métricas y modelos de forma clara y amigable para usuarios sin experiencia técnica, envía únicamente el razonamiento, sin pregunas al final y que empiece por explicación del modelo."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print("❌ Error al consultar DeepSeek:", e)
            return "Hubo un problema al generar la respuesta con DeepSeek."
