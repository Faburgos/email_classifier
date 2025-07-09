import os
from openai import OpenAI
from dotenv import load_dotenv
from prompt_examples import EXAMPLES

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def build_prompt(email_body: str) -> str:
    prompt_intro = (
        "Clasifica el siguiente correo en una de estas categorías: Alta de usuario, Baja de usuario, No clasificable.\n"
        "Ejemplos:\n"
    )
    examples_text = ""
    for ex in EXAMPLES:
        examples_text += f"Correo: {ex['email']}\nClasificación: {ex['classification']}\n\n"

    prompt = f"{prompt_intro}{examples_text}Correo: {email_body}\nClasificación:"
    return prompt

def classify_email(email_body: str) -> str:
    prompt = build_prompt(email_body)

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "Eres un asistente que clasifica correos electrónicos."},
            {"role": "user", "content": prompt}
        ],
        temperature = 0,
        max_tokens = 10,
        stop = ["\n"]
    )

    classification = response.choices[0].message.content.strip()
    
    # Aseguramos que la respuesta sea una de las categorías esperadas:
    valid_classes = ["Alta de usuario", "Baja de usuario", "No clasificable"]
    if classification not in valid_classes:
        classification = "No clasificable"
    return classification