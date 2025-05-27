import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)

def buscar_noticias():
    api_key = "a0129cf4cca046dd8801ae0a852815c3"

    query = (
        "\"USA business\" OR \"USA politics\" OR \"USA economy\" OR \"USA exports\" OR duty OR \"Trump duty\" OR \"USA imports\" OR \"Donald Trump\""
    )

    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={query}"
        f"&language=en"
        f"&sortBy=publishedAt"
        f"&pageSize=3"
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

def analizar_con_gemini(empresa, descripcion, pregunta, noticias): # Renombramos la función
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

    prompt = f"""
Eres un analista económico y estratégico altamente competente. Tu tarea es analizar la información proporcionada en 
un LISTADO DE NOTICIAS (con títulos, enlaces de referencia y, 
crucialmente, sus DESCRIPCIONES).
Debes ofrecer una respuesta concisa, precisa y bien fundamentada.
Considerando la siguiente información que has recibido:
{contenido}, la "Empresa:" y el listado de "Noticias encontradas:" con sus títulos, links y descripciones.

Por favor, estructura tu respuesta de la siguiente manera:

considera acciones que deberia tomar la empresa para superar posibles bostaculos, bloqueos o efectos negativos que pueden afectarla
ya sea directa o indirectamente, clasifica tu respuesta en recursos humanos, administracion, marketing y finanzas


(si no llegas a encontrar respuestas exactas o que tengan que ver con la empresa, solo debes hacer como que si y no comentarlo, 
realiza justo lo que se te pide y listo)


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
    descripcion = data.get('descripcion')
    pregunta = data.get('pregunta', '')

    if not empresa:
        return jsonify({"error": "Falta el dato requerido: empresa"}), 400

    noticias = buscar_noticias()
    print("📊 Noticias obtenidas:", noticias)
    if not noticias:
        return jsonify({"error": "No se encontraron noticias"}), 404

    analisis = analizar_con_gemini(empresa, descripcion, pregunta, noticias)

    return jsonify({
        "empresa": empresa,
        "descripcion": descripcion,
        "pregunta": pregunta,
        "noticias": noticias,
        "analisis": analisis
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
