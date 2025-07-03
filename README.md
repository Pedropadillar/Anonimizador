# Anonimizador

Esta aplicación web en Python anonimiza los datos personales que aparecen en el fichero subido y los sustituye por `[...]`.

---

## Descripción

El fichero principal es **main.py**, creado con Flask, que utiliza la plantilla **index.html** para subir el fichero y mostrar los resultados.

* **Servidor IA**: usa LM Studio como backend de IA, configurado por defecto en la variable `LM_STUDIO_URL` (p.ej. http\://localhost:1234/v1).
* **Modelo**: por defecto `"deepseek-r1-0528-qwen3-8b@q8_0"`. Si quieres cambiar de modelo, modifica la clave `model` en `main.py`.
* **Ajuste de prompt**: es aconsejable probar distintos PDFs y adaptar el `prompt` en `main.py` para optimizar la anonimización. Aunque Deepseek da buenos resultados, se recomienda experimentar con otros modelos.

Al procesar, la aplicación extrae el texto, lo envía al servidor de IA y reemplaza todos los datos personales por `[...]`. Después muestra el texto anonimizado y ofrece botones para exportarlo a **PDF**, **TXT** o **DOCX**.

---

## Requisitos

* Python 3.8+
* Virtualenv (recomendado)
* Dependencias (ver `requirements.txt`):


  Flask
  PyPDF2
  requests
  reportlab
  python-docx

---

## Instalación y ejecución

1. Clona el repositorio:


   git clone <URL_DEL_REPOSITORIO>
   cd <DIRECTORIO_DEL_PROYECTO>


2. Crea y activa un entorno virtual:


   python -m venv venv
   # Linux/macOS
   source venv/bin/activate
   # Windows
   venv\Scripts\activate


3. Instala las dependencias:


   pip install -r requirements.txt


4. Configura variables de entorno (opcional):

   * `LM_STUDIO_URL`: URL de tu servidor LM Studio.
   * `LM_STUDIO_API_KEY`: tu token para LM Studio.

5. Ejecuta la aplicación:


   python main.py


6. Abre el navegador en `http://127.0.0.1:8000`.

---

## Crear un ejecutable en Windows

Para generar un `.exe` independiente usando PyInstaller:


pip install pyinstaller
pyinstaller --onefile main.py --add-data "templates;templates" --windowed --icon=icono.ico


* El ejecutable se creará en `dist/main.exe`.
* `--add-data "templates;templates"` incorpora la carpeta de plantillas.
* `--windowed` evita la consola adicional.
* `--icon=icono.ico` añade un icono al `.exe`.

El directorio build/ debe estar en la misma carpeta que dist/
---

## Uso del ejecutable `.exe`

1. Inicia LM Studio y carga el modelo (`deepseek-r1-0528-qwen3-8b@q8_0` u otro).
2. Asegúrate de activar el servidor (p.ej. botón **Start server** en la interfaz de LM Studio).
3. Ejecuta `dist/main.exe`:

   * Se abrirá el navegador en la interfaz web.
   * Aparecerá una ventana de control para cerrar la aplicación.
4. Sube un PDF, procesa y descarga el resultado en el formato deseado.

---

## Estructura del proyecto


├── main.py           # Script principal de Flask
├── requirements.txt  # Dependencias del proyecto
├── templates/        # Carpeta con index.html
│   └── index.html    # Plantilla de subida y descarga
├── uploads/          # Carpeta temporal para archivos subidos
└── README.md         # Documentación del proyecto

---

## Licencia

Este proyecto está licenciado bajo MIT.
