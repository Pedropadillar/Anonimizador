from flask import Flask, render_template, request, redirect, url_for, send_file, session
import openai
from reportlab.pdfgen import canvas
import tempfile
import os
from PyPDF2 import PdfReader
from docx import Document
import json
import re
import os, io, tempfile, requests
import threading
import time
import webbrowser
import sys, os
import tkinter as tk
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'esta_es_una_clave_segura')

# Configura el cliente OpenAI para LM Studio local
client = openai.OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

def quitar_think_tags(texto):
    """Elimina el texto entre <think> y </think>."""
    return re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL)

def obtener_texto(request):
    """Extrae y decodifica el texto del archivo."""
    anon_text = request.form.get("anon_text")
    if not anon_text:
        return ""
    try:
        return json.loads(anon_text)
    except Exception:
        return anon_text

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/extraer_datos", methods=["POST"])
def extraer_datos():
    file = request.files.get("file")
    if not file:
        return render_template("index.html", error="No se ha subido ningún archivo.")

    # Extraer texto del PDF
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file.save(temp.name)
            reader = PdfReader(temp.name)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        os.unlink(temp.name)
        if not text.strip():
            return render_template("index.html", error="No se ha encontrado texto en el PDF. ¿Es un escaneo o una imagen?")
    except Exception as e:
        return render_template("index.html", error=f"Error procesando el PDF: {e}")

    # Prompt para anonimizar
    prompt = (
        "Anonimiza el siguiente texto, sustituyendo todos los datos personales por [...]"
        #"(nombre, apellidos, dirección, email, teléfono, DNI, matrículas, etc.) . "
        "Solo devuelve el texto anonimizado, sin explicaciones."
        "Respeta el formato y las negritas del texto original. "
        "Por ejemplo: Vista la instancia presentada por [...], con NIF [...] y domicilio en [...]\n\n"
        f"{text}"
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-r1-0528-qwen3-8b@q8_0",  # Cambia por el modelo disponible si usas otro en LM Studio
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4096
        )
        anon_text = response.choices[0].message.content
        anon_text = quitar_think_tags(anon_text)
        session['anon_text'] = anon_text  # Guardar para exportar
        
        return render_template("index.html", extracted_data=anon_text)
    except Exception as e:
        return render_template("index.html", error=f"Error conectando a LM Studio: {e}")

@app.route("/cancelar", methods=["GET"])
def cancelar():
    return redirect(url_for("index"))

@app.route('/crear_pdf', methods=['GET'])
def crear_pdf():
    anon_text = session.get('anon_text')
    print("Texto a crear PDF:", anon_text)  # Para depuración
    if not anon_text:
        return redirect(url_for('index'))
    pdf_bytes = generate_pdf(anon_text)
    return send_file(io.BytesIO(pdf_bytes),
            download_name='anonimizado.pdf',
            as_attachment=True,
            mimetype='application/pdf')

@app.route('/crear_word', methods=['GET'])
def crear_word():
    anon_text = session.get('anon_text')
    print("Texto a crear PDF:", anon_text)  # Para depuración
    if not anon_text:
        return redirect(url_for('index'))
    docx_bytes = generate_docx(anon_text)
    return send_file(io.BytesIO(docx_bytes),
            download_name='anonimizado.docx',
            as_attachment=True)

@app.route('/crear_txt', methods=['GET'])
def crear_txt():
    anon_text = session.get('anon_text')
    print("Texto a crear PDF:", anon_text)  # Para depuración
    if not anon_text:
        return redirect(url_for('index'))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
    tmp.write(anon_text)
    tmp.flush()
    tmp.close()
    return send_file(tmp.name,
            download_name="anonimizado.txt",
            as_attachment=True,
            mimetype='text/plain')


def generate_pdf(text: str) -> bytes:
    import textwrap
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch

    # Registrar fuente TrueType para ligaduras y caracteres especiales
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        font_name = 'DejaVuSans'
    except Exception:
        font_name = 'Helvetica'

    font_size = 10
    margin = inch * 0.5  # 0.5 inch margins
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    max_width = width - 2 * margin

    # Calcular ancho aproximado de caracteres en puntos
    avg_char_width = font_size * 0.6
    max_chars_per_line = int(max_width / avg_char_width)

    # Dividir respetando saltos de línea originales y envolver cada línea
    wrapped_lines = []
    for original_line in text.splitlines():
        if original_line.strip() == '':
            # Línea en blanco: respetar párrafo
            wrapped_lines.append('')
        else:
            # Envolver líneas largas manteniendo saltos originales
            lines = textwrap.wrap(original_line, width=max_chars_per_line)
            if lines:
                wrapped_lines.extend(lines)
            else:
                wrapped_lines.append(original_line)

    c.setFont(font_name, font_size)
    y = height - margin
    line_height = font_size * 1.2
    for line in wrapped_lines:
        if y < margin:
            c.showPage()
            c.setFont(font_name, font_size)
            y = height - margin
        c.drawString(margin, y, line)
        y -= line_height

    c.save()
    data = buffer.getvalue()
    buffer.close()
    return data


def generate_docx(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    data = buf.getvalue()
    buf.close()
    return data

def open_browser():
    # Pequeña espera para que Flask arranque
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:8000')

def start_flask():
    # Arranca Flask en este hilo
    app.run(host='0.0.0.0', port=8000, debug=False)

if __name__ == '__main__':
    # 1) Lanzar servidor Flask en hilo
    threading.Thread(target=start_flask, daemon=True).start()
    # 2) Lanzar navegador en hilo
    threading.Thread(target=open_browser, daemon=True).start()

    # 3) Crear ventana tkinter para el icono y cerrar
    root = tk.Tk()
    root.title("Datos personales")
    # base_path = os.path.abspath(os.path.dirname(__file__))
    # icon_path = os.path.join(base_path, 'icono.ico')  # <— ¡Define icon_path aquí!
    # root.iconbitmap(icon_path)       # tu .ico en el mismo directorio
    root.geometry("200x80")
    tk.Label(root, text="Servidor en localhost:8000").pack(pady=10)
    tk.Button(root, text="Cerrar app", command=lambda: sys.exit(0)).pack()
    root.mainloop()

"""
if __name__ == '__main__':
    # Lanza el thread que abrirá el navegador
    threading.Thread(target=open_browser, daemon=True).start()
    # Arranca el servidor Flask (debug=False para producción)
    app.run(host='0.0.0.0', port=8000, debug=True)
"""

# Si se utiliza un entorno virtual en desarrollo, para activarlo una vez creado:
    # Windows: venv\Scripts\activate
    # Linux/Mac: source venv/bin/activate
# Para ejecutar el script en desarrollo:# python main.py

# Para hacer un ejecutable en Windows:
    # pip install pyinstaller
    # pyinstaller --onefile --windowed --add-data "templates;templates" --add-data "README.md;." --icon=icono.ico main.py
    # Para incluir un icono (lo dejo en el repositorio) se incluye --icon=icono.ico
    # El ejecutable se generará en la carpeta dist.
# Para ejecutar el ejecutable: dist\datos_personales.exe