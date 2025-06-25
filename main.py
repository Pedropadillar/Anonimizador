from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import openai
import tempfile
import os
import json
import re
from PyPDF2 import PdfReader
from fpdf import FPDF
from docx import Document

# Configuración de la API de OpenAI para LM Studio local
client = openai.OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed"
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def quitar_think_tags(texto: str) -> str:
    """Elimina el texto entre <think> y </think>."""
    return re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL)

async def obtener_texto(anon_text: str) -> str:
    """Procesa el campo de texto anonimizado recibido del formulario."""
    if not anon_text:
        return ""
    try:
        return json.loads(anon_text)
    except json.JSONDecodeError:
        return anon_text

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/extraer_datos", response_class=HTMLResponse)
async def extraer_datos(request: Request, file: UploadFile = File(...)):
    # Verificar que se haya subido un archivo
    if not file:
        return templates.TemplateResponse("index.html", {"request": request, "error": "No se ha subido ningún archivo."})

    # Guardar y leer el PDF
    try:
        suffix = os.path.splitext(str(file.filename))[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contenido = await file.read()
            tmp.write(contenido)
            tmp.flush()
            reader = PdfReader(tmp.name)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        os.unlink(tmp.name)
        if not text.strip():
            return templates.TemplateResponse("index.html", {"request": request, "error": "No se ha encontrado texto en el PDF. ¿Es un escaneo o una imagen?"})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": f"Error procesando el PDF: {e}"})

    # Preparar prompt para anonimizar
    prompt = (
        "Anonimiza el siguiente texto, sustituyendo todos los datos personales "
        "(nombres, apellidos, direcciones, emails, teléfonos, DNIs, matrículas, etc.) por '[...]'. "
        "Solo devuelve el texto anonimizado, sin explicaciones. "
        "Por ejemplo: Vista la instancia presentada por [...], con NIF [...] y domicilio en [...]"
        f"{text}"
    )

    # Llamada a LM Studio
    try:
        response = client.chat.completions.create(
            model="deepseek-r1-0528",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4096
        )
        anon_text = response.choices[0].message.content
        return templates.TemplateResponse("index.html", {"request": request, "extracted_data": anon_text})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": f"Error conectando a LM Studio: {e}"})

@app.get("/cancelar")
async def cancelar():
    return RedirectResponse(url="/")

@app.post("/crear_pdf")
async def crear_pdf(anon_text: str = Form("")):
    contenido = await obtener_texto(anon_text)
    contenido = quitar_think_tags(contenido)

    # Generar PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for linea in contenido.splitlines():
        pdf.multi_cell(0, 10, linea)

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    temp_pdf.flush()
    return FileResponse(path=temp_pdf.name, filename="anonimizado.pdf", media_type='application/pdf')

@app.post("/crear_word")
async def crear_word(anon_text: str = Form("")):
    contenido = await obtener_texto(anon_text)
    contenido = quitar_think_tags(contenido)

    doc = Document()
    for linea in contenido.splitlines():
        doc.add_paragraph(linea)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    temp_file.flush()
    return FileResponse(path=temp_file.name, filename="anonimizado.docx", media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

@app.post("/crear_txt")
async def crear_txt(anon_text: str = Form("")):
    contenido = await obtener_texto(anon_text)
    contenido = quitar_think_tags(contenido)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
    temp_file.write(contenido)
    temp_file.flush()
    temp_file.close()
    return FileResponse(path=temp_file.name, filename="anonimizado.txt", media_type='text/plain')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
