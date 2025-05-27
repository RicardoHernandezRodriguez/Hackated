import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

# Configuración de la API de Google Gemini
try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        print("ADVERTENCIA: La variable de entorno GOOGLE_API_KEY no está configurada.")
        # Podrías querer detener la app aquí si es crítico
    else:
        genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configurando la API de Google: {e}")

app = Flask(__name__)

# --- Constantes y Configuración ---
NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"

def buscar_noticias(custom_query, language_code):
    """
    Busca noticias utilizando NewsAPI con una query e idioma específicos.
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        api_key = "a0129cf4cca046dd8801ae0a852815c3" # FALLBACK - NO RECOMENDADO PARA PRODUCCIÓN
        print("ADVERTENCIA: NEWSAPI_KEY no encontrada en variables de entorno. Usando clave hardcodeada (NO SEGURO).")

    params = {
        'q': custom_query,
        'language': language_code,
        'sortBy': 'publishedAt',
        'pageSize': 5,  # Obtener hasta 5 noticias por idioma/solicitud
        'apiKey': api_key
    }

    print(f"🔗 URL de NewsAPI ({language_code}): {NEWSAPI_BASE_URL} con query: {custom_query[:100]}...") # Imprime solo parte de la query
    noticias_procesadas = []

    try:
        response = requests.get(NEWSAPI_BASE_URL, params=params, timeout=10)
        response.raise_for_status() # Genera HTTPError para respuestas 4xx/5xx

        data = response.json()
        print(f"🔄 Código de respuesta NewsAPI ({language_code}): {response.status_code}")

        articulos = data.get("articles", [])
        for articulo in articulos:
            noticias_procesadas.append({
                'titulo': articulo.get('title', 'Título no disponible'),
                'enlace': articulo.get('url', 'Enlace no disponible'),
                'descripcion': articulo.get('description', 'Descripción no disponible'),
                'fuente': articulo.get('source', {}).get('name', 'Fuente no disponible'),
                'fecha_publicacion': articulo.get('publishedAt', 'Fecha no disponible')
            })
        print(f"📰 Noticias ({language_code}) procesadas: {len(noticias_procesadas)}")

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Error HTTP en NewsAPI ({language_code}): {http_err} - {response.text if 'response' in locals() and response else 'No response'}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"❌ Error de Conexión con NewsAPI ({language_code}): {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"❌ Timeout con NewsAPI ({language_code}): {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"❌ Error general en la solicitud a NewsAPI ({language_code}): {req_err}")
    except ValueError as json_err: # Captura errores si la respuesta no es JSON válido
        print(f"❌ Error decodificando JSON de NewsAPI ({language_code}): {json_err}")
        
    return noticias_procesadas

def analizar_con_gemini(empresa, pregunta, noticias, descripcion_empresa=None):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"❌ Error instanciando el modelo Gemini: {e}")
        return f"Error al instanciar el modelo Gemini: {e}"

    # Construcción del contexto para Gemini
    info_empresa_str = f"Empresa Target del Análisis: {empresa}\n"
    if descripcion_empresa:
        info_empresa_str += f"Descripción Adicional de la Empresa: {descripcion_empresa}\n"
    info_empresa_str += f"Pregunta Específica del Usuario: {pregunta}\n"

    info_noticias_str = "\nContexto Noticioso Reciente (Títulos y Descripciones):\n"
    if noticias:
        for i, noticia in enumerate(noticias, 1):
            info_noticias_str += (
                f"\nNoticia {i}:\n"
                f"  Título: {noticia.get('titulo', 'N/A')}\n"
                # No incluimos el 'enlace' ya que el LLM no puede acceder a URLs.
                f"  Fuente: {noticia.get('fuente', 'N/A')} ({noticia.get('fecha_publicacion', 'N/A')})\n"
                f"  Descripción: {noticia.get('descripcion', 'No disponible o irrelevante.')}\n"
            )
    else:
        info_noticias_str += "  No se encontraron noticias específicas o relevantes para esta solicitud.\n"
    info_noticias_str += "\n--- Fin del Contexto Noticioso ---\n"

    contexto_completo_para_gemini = info_empresa_str + info_noticias_str

    prompt = f"""
Eres un analista económico y consultor estratégico senior, altamente competente y con experiencia en la industria mexicana y su interrelación con el entorno económico y político de Estados Unidos. Tu tarea es analizar la información de contexto proporcionada (empresa, pregunta del usuario, y un listado de noticias con títulos y descripciones) y generar recomendaciones de acciones concretas.

**Información de Contexto para tu Análisis:**
{contexto_completo_para_gemini}

**Tu Misión:**
Basándote en la "Pregunta Específica del Usuario" y el "Contexto Noticioso Reciente", considera y detalla acciones que la "Empresa Target del Análisis" debería tomar para anticipar, mitigar o superar posibles obstáculos, bloqueos o efectos negativos que puedan afectarla, ya sea directa o indirectamente.

Clasifica tus recomendaciones de acción de manera clara y detallada en las siguientes cuatro áreas funcionales:
* **Recursos Humanos:** (Ej. planes de capacitación, estrategias de retención, comunicación interna, ajustes organizacionales, etc.)
* **Administración y Operaciones:** (Ej. optimización de procesos, gestión de la cadena de suministro, diversificación, adopción tecnológica, planes de contingencia, etc.)
* **Marketing y Ventas:** (Ej. reevaluación de mercados, ajuste de propuestas de valor, estrategias de comunicación, inteligencia de mercado, etc.)
* **Finanzas:** (Ej. revisión de presupuestos, gestión de riesgos (cambiario, tasas), análisis de costos, fuentes de financiamiento, evaluación de inversiones, etc.)

**Instrucción Crucial sobre la Calidad de la Información:**
Si el "Contexto Noticioso Reciente" es limitado, vago, o no parece directamente relevante para la "Empresa Target del Análisis" o la "Pregunta Específica del Usuario", DEBES AÚN ASÍ CUMPLIR LA TAREA. En tal caso, fundamenta tus recomendaciones en principios generales de negocio, estrategias comunes para el tipo de empresa y el tipo de desafíos que el contexto (aunque sea general) podría implicar. No indiques "no hay suficiente información" o "no puedo responder"; en su lugar, ofrece las mejores acciones plausibles y estratégicas posibles para cada una de las cuatro áreas, adaptadas al escenario más probable. Realiza justo lo que se te pide de forma completa.
"""
    print("📝 Prompt generado para Gemini (primeros 500 caracteres):", prompt[:500] + "...")

    try:
        response_gemini = model.generate_content(prompt)
        if hasattr(response_gemini, 'text') and response_gemini.text:
            return response_gemini.text
        elif response_gemini.parts:
             # Intenta concatenar el texto de todas las partes si es una respuesta multiparte
            return "".join(part.text for part in response_gemini.parts if hasattr(part, 'text'))
        else:
            print("❌ Respuesta de Gemini no contiene texto o 'parts' válidas. Feedback:", response_gemini.prompt_feedback if hasattr(response_gemini, 'prompt_feedback') else "No feedback available.")
            return "Error: La respuesta de Gemini no fue como se esperaba o fue bloqueada (revisar feedback en consola)."
            
    except Exception as e:
        print(f"❌ Error al llamar a la API de Gemini: {e}")
        return f"Error al realizar el análisis con Gemini: {e}"

# --- Rutas de la API Flask ---
@app.route('/')
def home():
    return "✅ API de análisis económico funcionando con Gemini (v2 - bilingüe)."

@app.route('/analizar-tema', methods=['POST'])
def analizar_tema_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Cuerpo de la solicitud JSON inválido o vacío."}), 400
        
    print("📥 Datos recibidos:", data)
    empresa = data.get('empresa')
    descripcion_empresa = data.get('descripcion') # Descripción opcional de la empresa
    pregunta = data.get('pregunta', '¿Cuáles son los principales riesgos y oportunidades y qué acciones deberíamos considerar?') # Pregunta por defecto

    if not empresa:
        return jsonify({"error": "Falta el dato requerido: 'empresa'."}), 400

    # Definición de las queries "puro OR"
    query_en_str = (
        "\"USA business\" OR \"USA politics\" OR \"USA economy\" OR \"USA exports\" OR \"USA imports\" OR "
        "duty OR \"Trump duty\" OR \"Donald Trump\" OR "
        "\"Mexico business\" OR \"Mexico politics\" OR \"Mexican economy\" OR \"Mexico exports\" OR \"Mexican imports\" OR "
        "dollar OR \"exchange rate\" OR "
        "\"export index\" OR \"export data\" OR \"production index\" OR \"industrial output\" OR "
        "\"border closure\" OR \"border restrictions\" OR "
        "\"cost increase\" OR \"rising costs\" OR inflation OR "
        "\"market reduction\" OR \"market contraction\" OR "
        "impact OR speculation OR "
        "\"interest rate hike\" OR \"interest rates\" OR \"monetary policy\""
    )
    query_es_str = (
        "\"negocios EEUU\" OR \"política EEUU\" OR \"economía EEUU\" OR \"exportaciones EEUU\" OR \"importaciones EEUU\" OR "
        "arancel OR \"aranceles Trump\" OR \"Donald Trump\" OR "
        "\"negocios México\" OR \"política México\" OR \"economía México\" OR \"exportaciones México\" OR \"importaciones México\" OR "
        "dólar OR \"tipo de cambio\" OR "
        "\"índices de exportación\" OR \"datos de exportación\" OR \"índices de producción\" OR \"producción industrial\" OR "
        "\"cierre de fronteras\" OR \"restricciones fronterizas\" OR "
        "\"aumento de costos\" OR \"costos crecientes\" OR inflación OR "
        "\"reducción de mercado\" OR \"contracción de mercado\" OR "
        "impacto OR especulación OR "
        "\"aumento de tasas de interés\" OR \"tasas de interés\" OR \"política monetaria\""
    )

    print("🗣️ Buscando noticias en inglés...")
    noticias_en = buscar_noticias(custom_query=query_en_str, language_code='en')
    print("🗣️ Buscando noticias en español...")
    noticias_es = buscar_noticias(custom_query=query_es_str, language_code='es')
    
    noticias_combinadas = noticias_en + noticias_es
    
    # Opcional: Eliminar duplicados basados en URL o título si fuera necesario
    # temp_dict = {noticia['enlace']: noticia for noticia in noticias_combinadas if noticia.get('enlace')}
    # noticias_combinadas_unicas = list(temp_dict.values())
    # print(f"📰 Total de noticias únicas combinadas: {len(noticias_combinadas_unicas)}")
    
    print(f"📊 Total de noticias combinadas (antes de filtrar duplicados si aplica): {len(noticias_combinadas)}")
    
    if not noticias_combinadas and GOOGLE_API_KEY: # Solo analiza si hay clave de Google
        print("⚠️ No se encontraron noticias en ninguno de los idiomas. Se enviará la solicitud a Gemini sin contexto noticioso.")
        # Se podría devolver un error aquí si se prefiere no llamar a Gemini sin noticias
        # return jsonify({"error": "No se encontraron noticias relevantes para el análisis"}), 404


    analisis_resultado = "No se pudo generar análisis: GOOGLE_API_KEY no configurada."
    if GOOGLE_API_KEY: # Solo intenta analizar si la clave de Gemini está configurada
        analisis_resultado = analizar_con_gemini(empresa, pregunta, noticias_combinadas, descripcion_empresa)

    return jsonify({
        "empresa_analizada": empresa,
        "pregunta_usuario": pregunta,
        "descripcion_empresa_entrada": descripcion_empresa,
        "numero_noticias_consideradas": len(noticias_combinadas),
        "noticias_usadas_para_analisis": noticias_combinadas, 
        "analisis_estrategico_gemini": analisis_resultado
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # debug=False para producción
    app.run(host='0.0.0.0', port=port, debug=True)
