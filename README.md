# Anonimizador
Esta aplicación web en Python anonimiza los datos personales que aparecen en el fichero subido y los sustituye por [...]

# Descripción
El fichero principal es main.py, creado con Flask, que llama a index.html para subir el fichero y dar los resultados.
La aplicación funciona con LM Studio como servidor de IA. Se ha utilizado el modelo "deepseek-r1-0528-qwen3-8b@q8_0". Si se quiere usar otro es recomendable cambiarlo en la variable model de main.py

Es aconsejable probar la aplicación con distintos modelos de archivo pdf e ir ajustando el prompt para obtener los mejores resultados. 
Aunque Deepseek me ha dado buenos resultados, también se aconseja probar otros modelos.

Una vez que la aplicación da los resultados, aparecen unos botones para exportarlos a pdf, txt o docx.

# Hacer un ejecutable en Windows desde python:

    pip install pyinstaller
    pyinstaller --onefile main.py --add-data "templates:templates" --windowed --icon=icono.ico

    Para incluir un icono (lo dejo en el repositorio) se incluye la última instrucción anterior --icon=icono.ico
    El ejecutable se generará en la carpeta dist/.
    

# Utilizar el ejecutable .exe

1. Ejecutar LM Studio
2. Cargar un modelo de IA. En el main.py tengo configurado "deepseek-r1-0528-qwen3-8b@q8_0"
3. Activar el server de LM Studio
4. Ejecutar la aplicación dist/main.exe. Abrirá el navegador y una pequeña ventana para poder cerrar la aplicación
5. Usar