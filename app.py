import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import openai
import requests

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def buscar_noticias(sector):
    api_key = "a0129cf4cca046dd8801ae0a852815c3"

    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={sector}+economía"
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
    else:
        print("❌ Error en NewsAPI:", response.status_code, response.text)

    return noticias

def analizar_con_chatgpt(empresa, sector, pregunta, noticias):
    contenido = f"Empresa: {empresa}\nSector: {sector}\nPregunta del usuario: {pregunta}\n\nNoticias encontradas:\n"
    for noticia in noticias:
        contenido += f"- {noticia['titulo']} ({noticia['enlace']})\n"

    prompt = f"""
Eres un analista económico. Con base en la empresa, sector, pregunta del usuario y las noticias listadas, responde de forma precisa:

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
    sector = data.get('sector')
    pregunta = data.get('pregunta', '')

    if not all([empresa, sector]):
        return jsonify({"error": "Faltan datos requeridos: tema, empresa o sector"}), 400
        
    busqueda = f"{sector} economía"

    noticias = buscar_noticias(busqueda)
    if not noticias:
        return jsonify({"error": "No se encontraron noticias"}), 404

    analisis = analizar_con_chatgpt(empresa, sector, pregunta, noticias)

    return jsonify({
        "empresa": empresa,
        "sector": sector,
        "pregunta": pregunta,
        "noticias": noticias,
        "analisis": analisis
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
