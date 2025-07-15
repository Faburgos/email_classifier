import os
from openai import OpenAI
from dotenv import load_dotenv
from prompt_examples import EXAMPLES

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key = api_key)

def build_prompt(email_body: str) -> str:
    """
    Construye un prompt estructurado y optimizado para clasificación de emails.
    
    Estructura del prompt:
    1. Contexto del rol y sistema
    2. Instrucciones claras y específicas
    3. Definiciones detalladas de categorías
    4. Palabras clave específicas
    5. Ejemplos de clasificación
    6. Formato de respuesta esperado
    """

    # 1. CONTEXTO DEL ROL
    context = """
    Eres un especialista en clasificación de solicitudes de gestión de personal para SIMAN en la plataforma IVANTI. Tu expertise se centra en el análisis semántico de correos electrónicos para determinar si se trata de solicitudes de incorporación o desvinculación de personal."""

    # 2. INSTRUCCIONES PRINCIPALES
    instructions = """
    TAREA: Analiza el siguiente correo electrónico y clasifícalo en una de estas TRES categorías exactas:

    **CATEGORÍAS DISPONIBLES:**
    • ALTA/BAJA
    • NO CLASIFICABLE

    **REGLAS DE CLASIFICACIÓN:**
    1. Lee todo el contenido del correo cuidadosamente
    2. Identifica la acción principal solicitada
    3. Si hay múltiples acciones, prioriza la más prominente
    4. Si el correo es ambiguo o no se puede determinar claramente, usa "NO CLASIFICABLE"
    5. Si el correo no trata sobre gestión de personal, usa "NO CLASIFICABLE"
    6. Solo responde con una de las tres categorías exactas"""

    # 3. DEFINICIONES DETALLADAS
    definitions = """
    **ALTA DE PERSONAL** - Incluye solicitudes de:
    • Incorporación de nuevos empleados
    • Creación de usuarios y cuentas
    • Asignación de recursos y accesos
    • Procesos de onboarding
    • Habilitación de servicios
    • Ingreso de personal temporal o permanente
    • Activación de permisos y credenciales

    **BAJA DE PERSONAL** - Incluye solicitudes de:
    • Desvinculación de empleados
    • Terminación de contratos
    • Cierre de accesos y cuentas
    • Procesos de offboarding
    • Desactivación de servicios
    • Retiro de personal por cualquier motivo
    • Revocación de permisos y credenciales

    **NO CLASIFICABLE** - Usar cuando:
    • El correo es ambiguo o confuso
    • No hay suficiente información para determinar la acción
    • El correo trata sobre otros temas no relacionados con altas/bajas
    • Hay información contradictoria en el mismo correo
    • El correo requiere más contexto para ser clasificado correctamente"""

    # 4. PALABRAS CLAVE ESPECÍFICAS
    keywords = """
    **INDICADORES CLAVE:**

    Para ALTA/BAJA:
    - "nuevo ingreso", "nuevos ingresos", "alta de usuario", "altas de usuarios"
    - "creación", "crear usuario", "habilitar", "activar"
    - "onboarding", "incorporación", "asignación"
    - "formato ABC" (cuando es para nuevos ingresos)
    - "baja de usuario", "bajas de usuarios", "desactivar", "deshabilitar"
    - "terminación", "retiro", "desvinculación", "renuncia"
    - "cierre de accesos", "revocación", "offboarding"
    - "formato ABC" (cuando es para bajas/retiros)"""

    # 5. EJEMPLOS DE CLASIFICACIÓN
    examples_section = "\n**EJEMPLOS DE CLASIFICACIÓN:**\n"
    for i, example in enumerate(EXAMPLES[:5], 1):  # Limitado a 5 ejemplos
        examples_section += f"\nEjemplo {i}:\n"
        examples_section += f"Correo: \"{example['Descripción']}\"\n"
        examples_section += f"Clasificación: {example['Clasificación']}\n"

    # 6. FORMATO DE RESPUESTA
    response_format = """
    **FORMATO DE RESPUESTA:**
    Responde únicamente con una de estas tres opciones exactas:
    - ALTA/BAJA
    - NO CLASIFICABLE

    No incluyas explicaciones adicionales, solo la clasificación."""

    # 7. CORREO A CLASIFICAR
    email_to_classify = f"""
    **CORREO A CLASIFICAR:**
    {email_body}

    **CLASIFICACIÓN:**"""

    # CONSTRUCCIÓN DEL PROMPT FINAL
    prompt = f"""{context}

    {instructions}

    {definitions}

    {keywords}

    {examples_section}

    {response_format}

    {email_to_classify}"""
    
    return prompt

def classify_email(email_body: str) -> str:
    """
    Clasifica el cuerpo del correo electrónico utilizando GPT-4.1-nano con prompt mejorado.
    
    Args:
        email_body (str): Contenido del correo a clasificar
        
    Returns:
        str: Clasificación del correo ('ALTA DE PERSONAL' o 'BAJA DE PERSONAL')
    """
    prompt = build_prompt(email_body)

    try:
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [
                {
                    "role": "system", 
                    "content": "Eres un especialista en clasificación de solicitudes de gestión de personal. Responde únicamente con la clasificación solicitada, sin explicaciones adicionales."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature = 0, 
            max_tokens = 10,  
            stop = ["\n", ".", "**", "Explicación"] 
        )

        classification = response.choices[0].message.content.strip()
        
        # Limpieza y normalización de la respuesta
        classification = classification.replace('"', '').replace("'", '').replace('`', '')
        classification = classification.upper()
        
        # Mapeo de posibles variaciones
        classification_mapping = {
            "ALTA DE PERSONAL": "ALTA/BAJA",
            "BAJA DE PERSONAL": "ALTA/BAJA",
            "NO CLASIFICABLE": "NO CLASIFICABLE",
            "ALTA": "ALTA/BAJA",
            "BAJA": "ALTA/BAJA",
            "ALTA DE USUARIO": "ALTA/BAJA",
            "BAJA DE USUARIO": "ALTA/BAJA",
            "NUEVO INGRESO": "ALTA/BAJA",
            "INGRESO": "ALTA/BAJA",
            "INCORPORACIÓN": "ALTA/BAJA",
            "DESVINCULACIÓN": "ALTA/BAJA",
            "RETIRO": "ALTA/BAJA",
            "TERMINACIÓN": "ALTA/BAJA",
            "AMBIGUO": "NO CLASIFICABLE",
            "CONFUSO": "NO CLASIFICABLE",
            "INCIERTO": "NO CLASIFICABLE"
        }
        
        # Normalización usando el mapeo
        if classification in classification_mapping:
            return classification_mapping[classification]
        
        # Si contiene palabras clave, intentar extraer la clasificación
        if "ALTA" in classification:
            return "ALTA/BAJA"
        elif "BAJA" in classification:
            return "ALTA/BAJA"
        elif any(word in classification for word in ["NO", "CLASIFICABLE", "AMBIGUO", "CONFUSO"]):
            return "NO CLASIFICABLE"
        
        # Si no se puede determinar, loggear y devolver NO CLASIFICABLE
        print(f"Respuesta no estándar del modelo: '{classification}' - Clasificando como NO CLASIFICABLE")
        return "NO CLASIFICABLE"
            
    except Exception as e:
        print(f"Error al clasificar correo: {e}")
        return "ERROR" 