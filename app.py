from flask import Flask, request, render_template, send_file
import requests
import os
from werkzeug.utils import secure_filename
import io
from PyPDF2 import PdfReader
from docx import Document
from reportlab.pdfgen import canvas

# Configura el cliente OpenAI para LM Studio local
client = openai.OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Página de carga
@app.route('/', methods=['GET'])
def index():
    return render_template('index1.html')

# Ruta para anonimizar
@app.route('/anonymize', methods=['POST'])
def anonymize():
    # Validación de archivo
    if 'file' not in request.files:
        return 'No se ha enviado ningún archivo', 400
    file = request.files['file']
    if file.filename == '':
        return 'No se ha seleccionado archivo', 400

    # Guardar temporalmente
    filename = secure_filename(file.filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extraer texto del PDF
    reader = PdfReader(filepath)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'

    # Llamada a LM Studio para anonimizar
    prompt = (
        "Anonymize personal data in the following text by replacing all personal data with '[...]':\n\n" +
        text
    )
    headers = {'Authorization': f'Bearer {LM_STUDIO_API_KEY}'} if LM_STUDIO_API_KEY else {}
    payload = {
        "model": "llama2-7b-chat",  # Ajusta el modelo si es necesario
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    resp = requests.post(LM_STUDIO_URL, json=payload, headers=headers)
    resp.raise_for_status()
    anonymized_text = resp.json()['choices'][0]['message']['content']

    # Generar archivos
    pdf_bytes = generate_pdf(anonymized_text)
    docx_bytes = generate_docx(anonymized_text)

    # Enviar según formato solicitado
    fmt = request.form.get('format', 'pdf')
    if fmt == 'docx':
        return send_file(io.BytesIO(docx_bytes), download_name='anonymized.docx', as_attachment=True)
    else:
        return send_file(io.BytesIO(pdf_bytes), download_name='anonymized.pdf', as_attachment=True)

# Función para generar PDF desde texto

def generate_pdf(text: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    width, height = c._pagesize
    y = height - 40
    for line in text.split('\n'):
        if y < 40:
            c.showPage()
            y = height - 40
        c.drawString(40, y, line)
        y -= 15
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# Función para generar DOCX desde texto

def generate_docx(text: str) -> bytes:
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    docx_data = buffer.getvalue()
    buffer.close()
    return docx_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)