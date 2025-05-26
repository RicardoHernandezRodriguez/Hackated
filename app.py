import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def buscar_noticias(tema):
    url = f"https://www.google.com/search?q={tema}+site:bbc.com&tbm=nws"
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    noticias = []

    for item in soup.select('.dbsr')[:5]:
        titulo = item.select_one('.nDgy9d').text if item.select_one('.nDgy9d') else 'Sin título'
        enlace = item.a['href']
        noticias.append({'titulo': titulo, 'enlace': enlace})
    return noticias

def analizar_con_chatgpt(tema, noticias):
    contenido = f"Analiza este tema: '{tema}' usando estas noticias:\n"
    for noticia in noticias:
        contenido += f"- {noticia['titulo']} ({noticia['enlace']})\n"

    prompt = f"""
Eres un analista experto. Dado el siguiente tema y noticias, responde:
1. Resumen
2. Análisis crítico
3. Palabras clave

{contenido}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un analista experto en noticias."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message["content"]

@app.route('/')
def home():
    return "✅ API de noticias funcionando."

@app.route('/analizar-tema', methods=['POST'])
def analizar_tema():
    data = request.get_json()
    tema = data.get('tema')
    if not tema:
        return jsonify({"error": "Tema no proporcionado"}), 400

    noticias = buscar_noticias(tema)
    analisis = analizar_con_chatgpt(tema, noticias)
    
    return jsonify({
        "tema": tema,
        "noticias": noticias,
        "analisis": analisis
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
