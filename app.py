import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)

def buscar_noticias():
    api_key = "a0129cf4cca046dd8801ae0a852815c3"

    query = (
    "(\"US economy\" OR \"US economic outlook\" OR \"US GDP\") OR "
    "(\"US trade policy\" OR \"USMCA\" OR \"tariffs\" OR \"US customs\") OR "
    "(\"US supply chain\" OR \"logistics disruptions US\" OR \"port congestion US\") OR "
    "(\"US manufacturing sector\" OR \"US industrial production\" OR \"factory orders US\") OR "
    "(\"US automotive industry\" OR \"US auto sales\" OR \"electric vehicles US\") OR "
    "(\"US agricultural policy\" OR \"US food prices\" OR \"FDA food regulation\") OR "
    "(\"US energy prices\" OR \"US oil and gas\" OR \"US renewable energy policy\") OR "
    "(\"US labor market\" OR \"US employment report\" OR \"wage growth US\") OR "
    "(\"Federal Reserve\" OR \"US inflation report\" OR \"US interest rates\") OR "
    "(\"nearshoring\" OR \"friendshoring\" OR \"US investment Mexico\" OR \"Mexico sourcing\") OR "
    "(\"US environmental regulation\" OR \"EPA ruling\" OR \"industrial emissions US\") OR "
    "(\"US technology trends\" OR \"AI in US industry\" OR \"semiconductor US\")"
    )

    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={query}"
        f"&language=en"
        f"&sortBy=publishedAt"
        f"&pageSize=10"
        f"&apiKey={api_key}"
    )

    print("🔗 URL de NewsAPI:", url)

    response = requests.get(url)
    noticias = []

    print("🔄 Código de respuesta NewsAPI:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        print("📰 Noticias encontradas:", data)
        for articulo in data.get("articles", []):
            noticias.append({
                'titulo': articulo['title'],
                'enlace': articulo['url'],
                'descripcion': articulo.get('description', '')
            })
        print("📰 Noticias encontradas:", len(noticias))
    else:
        print("❌ Error en NewsAPI:", response.status_code, response.text)

    return noticias

def analizar_con_gemini(empresa, pregunta, noticias): # Renombramos la función
    # Instancia el modelo de Gemini. 'gemini-pro' es un buen punto de partida para texto.
    model = genai.GenerativeModel('gemini-1.5-flash')

    contenido = f"Empresa: {empresa}\nPregunta del usuario: {pregunta}\n\nNoticias encontradas:\n"
for i, noticia in enumerate(noticias, 1):
    contenido += (
        f"\nNoticia {i}:\n"
        f"Título: {noticia.get('titulo', 'N/A')}\n"
        f"Link: {noticia.get('enlace', 'N/A')}\n" # Yo no accederé al link, es para tu referencia
        f"Descripción: {noticia.get('descripcion', 'No disponible')}\n" # Aquí la descripción
    )
contenido += "\n--- Fin de las Noticias ---\n"
    # El prompt para Gemini es similar, pero no necesitas la estructura de "messages" de OpenAI
# En tu función analizar_con_gemini(empresa, pregunta, noticias):
# ... (asegúrate que 'contenido' se construya como sugerí arriba, incluyendo descripciones) ...

prompt = f"""
Eres un analista económico y estratégico altamente competente. Tu tarea es analizar la información proporcionada, que incluye detalles sobre una EMPRESA, una PREGUNTA específica del usuario, y un LISTADO DE NOTICIAS (con títulos, enlaces de referencia y, crucialmente, sus DESCRIPCIONES). Debes ofrecer una respuesta concisa, precisa y bien fundamentada.

Considerando la siguiente información que has recibido:
{contenido} 
# El bloque anterior ({contenido}) ya incluye la "Empresa:", la "Pregunta del usuario:" y el listado de "Noticias encontradas:" con sus títulos, links y descripciones.

Por favor, estructura tu respuesta de la siguiente manera:

1.  🧠 **Resumen del Contexto Económico Clave (basado en las DESCripciones de las noticias):**
    * Identifica y resume brevemente (2-3 puntos) las tendencias o eventos económicos más relevantes presentes en las **descripciones** de las noticias proporcionadas que se relacionan directamente con la EMPRESA y la PREGUNTA del usuario.

2.  📈 **Impacto Potencial Específico (en la Empresa y en relación a la Pregunta):**
    * Describe cómo el contexto económico identificado podría impactar específicamente a la EMPRESA mencionada.
    * Enlaza este impacto directamente con la PREGUNTA formulada por el usuario.
    * Sé específico sobre los posibles efectos (positivos/negativos).
    * Reconoce explícitamente que tu análisis se basa en la información limitada de los títulos y, sobre todo, las **descripciones** de las noticias.

3.  🧐 **Análisis Crítico Breve y Perspectiva:**
    * Desde una perspectiva crítica, ¿cuáles son las principales OPORTUNIDADES o los RIESGOS más evidentes para la EMPRESA en el contexto de la PREGUNTA y las noticias analizadas?
    * Ofrece una breve perspectiva (ej. cautelosa, optimista con reservas, desafiante).

4.  🔑 **Palabras Clave Útiles (en español):**
    * Lista 3-5 palabras clave concisas en español que sinteticen los hallazgos más importantes de tu análisis.

5.  ✅ **Respuesta Directa y Accionable a la Pregunta del Usuario:**
    * Proporciona una respuesta clara, directa y, si es posible, accionable a la PREGUNTA del usuario, integrando los hallazgos de tu análisis (puntos 1, 2 y 3).

**Instrucciones Adicionales Importantes:**
* Basa tus respuestas primordialmente en la información textual contenida en los títulos y, de forma crucial, en las **DESCRIPCIONES de las noticias** listadas en el bloque de "Noticias encontradas".
* Si las descripciones son muy breves, generales o insuficientes para un análisis profundo, es válido y necesario que menciones esta limitación en tu respuesta.
* Prioriza la precisión, la concisión y la relevancia directa para la empresa y la pregunta.
"""
    print("📝 Prompt generado para Gemini:")
    print(prompt)

    try:
        # Llama a la API de Gemini
        response = model.generate_content(prompt)
        print("✅ Respuesta de Gemini:", response)
        # Accede al texto de la respuesta
        return response.text
    except Exception as e:
        print(f"❌ Error al llamar a la API de Gemini: {e}")
        return f"Error al realizar el análisis: {e}"


@app.route('/')
def home():
    return "✅ API de análisis económico funcionando con Gemini."

@app.route('/analizar-tema', methods=['POST'])
def analizar_tema():
    data = request.get_json()
    print("📥 Datos recibidos:", data)
    empresa = data.get('empresa')
    pregunta = data.get('pregunta', '')

    if not empresa:
        return jsonify({"error": "Falta el dato requerido: empresa"}), 400

    noticias = buscar_noticias()
    print("📊 Noticias obtenidas:", noticias)
    if not noticias:
        return jsonify({"error": "No se encontraron noticias"}), 404

    analisis = analizar_con_gemini(empresa, pregunta, noticias)

    return jsonify({
        "empresa": empresa,
        "pregunta": pregunta,
        "noticias": noticias,
        "analisis": analisis
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
