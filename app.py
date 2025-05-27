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
                'enlace': articulo['url']
            })
        print("📰 Noticias encontradas:", len(noticias))
    else:
        print("❌ Error en NewsAPI:", response.status_code, response.text)

    return noticias

def analizar_con_gemini(empresa, pregunta, noticias): # Renombramos la función
    # Instancia el modelo de Gemini. 'gemini-pro' es un buen punto de partida para texto.
    model = genai.GenerativeModel('gemini-1.5-flash')

    contenido = f"Empresa: {empresa}\nPregunta del usuario: {pregunta}\n\nNoticias encontradas:\n"
    for noticia in noticias:
        contenido += f"- {noticia['titulo']} ({noticia['enlace']})\n"

    # El prompt para Gemini es similar, pero no necesitas la estructura de "messages" de OpenAI
    prompt = f"""
Eres un analista económico. Con base en la empresa, la pregunta del usuario y las noticias listadas, responde de forma precisa:

1. 🧠 Resumen del contexto económico
2. 📈 Cómo puede impactar al sector o empresa
3. 🧐 Análisis crítico
4. 🔑 Palabras clave útiles (en español)
5. ✅ Respuesta directa a la pregunta del usuario

{contenido}
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
