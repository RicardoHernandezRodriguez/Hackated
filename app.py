import os
import requests
from flask import Flask, request, jsonify
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def buscar_noticias():
    api_key = "a0129cf4cca046dd8801ae0a852815c3"

    query = (
        "business OR economy OR imports OR exports OR \"Donald Trump\""
    )

    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={query}"
        f"&language=en"
        f"&sortBy=publishedAt"
        f"&pageSize=5"
        f"&apiKey={api_key}"
    )

    response = requests.get(url)
    noticias = []

    if response.status_code == 200:
        data = response.json()
        for articulo in data.get("articles", []):
            noticias.append({
                'titulo': articulo['title'],
                'enlace': articulo['url']
            })
        print("📰 Noticias encontradas:", len(noticias))
    else:
        print("❌ Error en NewsAPI:", response.status_code, response.text)

    return noticias

def analizar_con_chatgpt(empresa, pregunta, noticias):
    contenido = f"Empresa: {empresa}\nPregunta del usuario: {pregunta}\n\nNoticias encontradas:\n"
    for noticia in noticias:
        contenido += f"- {noticia['titulo']} ({noticia['enlace']})\n"

    prompt = f"""
Eres un analista económico. Con base en la empresa, la pregunta del usuario y las noticias listadas, responde de forma precisa:

1. 🧠 Resumen del contexto económico
2. 📈 Cómo puede impactar al sector o empresa
3. 🧐 Análisis crítico
4. 🔑 Palabras clave útiles (en español)
5. ✅ Respuesta directa a la pregunta del usuario

{contenido}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un analista económico profesional especializado en noticias financieras y políticas."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message["content"]

@app.route('/')
def home():
    return "✅ API de análisis económico funcionando."

@app.route('/analizar-tema', methods=['POST'])
def analizar_tema():
    data = request.get_json()
    empresa = data.get('empresa')
    pregunta = data.get('pregunta', '')

    if not empresa:
        return jsonify({"error": "Falta el dato requerido: empresa"}), 400

    noticias = buscar_noticias()
    if not noticias:
        return jsonify({"error": "No se encontraron noticias"}), 404

    analisis = analizar_con_chatgpt(empresa, pregunta, noticias)

    return jsonify({
        "empresa": empresa,
        "pregunta": pregunta,
        "noticias": noticias,
        "analisis": analisis
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
