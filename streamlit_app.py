import os
from hashlib import blake2b
from tempfile import NamedTemporaryFile
import dotenv
from streamlit_pdf_viewer import pdf_viewer
import json  # Importar el módulo json
dotenv.load_dotenv(override=True)
import streamlit as st
from flatten_json import flatten 
import tempfile

import google.generativeai as genai
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import google.generativeai as genai




# Manejo de Sessiones
if 'doc_id' not in st.session_state:
    st.session_state['doc_id'] = None

if 'hash' not in st.session_state:
    st.session_state['hash'] = None

if 'git_rev' not in st.session_state:
    st.session_state['git_rev'] = "unknown"
    if os.path.exists("revision.txt"):
        with open("revision.txt", 'r') as fr:
            from_file = fr.read()
            st.session_state['git_rev'] = from_file if len(from_file) > 0 else "unknown"

if 'uploaded' not in st.session_state:
    st.session_state['uploaded'] = False

if 'binary' not in st.session_state:
    st.session_state['binary'] = None

if 'annotations' not in st.session_state:
    st.session_state['annotations'] = []

if 'pages' not in st.session_state:
    st.session_state['pages'] = None

if 'page_selection' not in st.session_state:
    st.session_state['page_selection'] = []

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Formulario de Aprobación",
    page_icon="🤖",
    initial_sidebar_state="expanded",  # Cambiar a 'collapsed' para permitir ocultar la barra lateral   
    menu_items={
        'Get Help': 'https://www.digitalmagia.com',
        'Report a bug': "https://www.digitalmagia.com",
        'About': "Forma para completar ,corregir y aprobar los datos antes de enviarlo a plataforma de alojamiento."
    }
)
#Crear Tablas 
tab1, tab2 = st.tabs(["📄 PDF", "🤖 Agent AI"])
# Crear dos columnas
col1, col2 ,col3 = st.columns(3)

# Ejemplo de estructura para annotations
annotations = [
    {
        "page": 1,
        "type": "title",
        "content": "Análisis de Datos con Python",
        "coordinates": [100, 200, 300, 400]
    },
    {
        "page": 1,
        "type": "author",
        "content": "Juan Pérez",
        "coordinates": [100, 450, 300, 500]
    },
    {
        "page": 2,
        "type": "section",
        "content": "Introducción",
        "coordinates": [100, 100, 300, 150]
    }
]

# Ejemplo de estructura para pages
pages = [
    {
        "page_number": 1,
        "text": "Análisis de Datos con Python\nJuan Pérez\n...",
        "dimensions": [595, 842]
    },
    {
        "page_number": 2,
        "text": "Introducción\nEn este documento, exploraremos...",
        "dimensions": [595, 842]
    }
]

# Función para manejar la carga de un nuevo archivo
def new_file():
    st.session_state['doc_id'] = None
    st.session_state['uploaded'] = True
    st.session_state['annotations'] = []
    st.session_state['binary'] = None

# Función para cargar el archivo JSON
def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def text_to_json(text_data):
    try:
        # Convertir texto a JSON
        json_data = json.loads(text_data)
        return json_data
    except json.JSONDecodeError as e:
        st.error(f"Error al convertir texto a JSON: {str(e)}")
        return None

    
# Función para aplanar y limpiar datos JSON
def flatten_json_data(json_data):
    # Aplanar JSON anidado a estructura simple
    flat_json = flatten(json_data)
    # Filtrar y limpiar claves
    cleaned_data = {}
    for key, value in flat_json.items():
        # Convertir listas y diccionarios a string
        if isinstance(value, (list, dict)):
            value = str(value)
        # Limpiar nombres de campos
        clean_key = key.replace('_', ' ').title()
        cleaned_data[clean_key] = value
    return cleaned_data

def create_dynamic_form(json_data, tab):
        tab.title("Formulario Dinámico")
    
    # Crear formulario
        form_approve = tab.form(key='dynamic_form')
        form_data = {}
        
        # Crear campos de formulario dinámicamente
        for key, value in json_data.items():
            # Determinar el tipo de campo según el valor
            if isinstance(value, bool):
                form_data[key] = form_approve.checkbox(key, value=value)
            elif isinstance(value, (int, float)):
                form_data[key] = form_approve.number_input(key, value=value)
            else:
                form_data[key] = form_approve.text_input(key, value=str(value))
        
        # Botón de envío
        submit_button = form_approve.form_submit_button(label='Enviar')
        
        if submit_button:
            tab.success("Formulario enviado exitosamente!")
            #st.json(form_data)
#-------------------------------

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()

def crete_prompt(file_content):
    prompt = "identifica los grupos de informacion o entidades de negocio y regeresalo en formato json simple clave valor con los datos  contenidos en el archivo adjunto"
    # Create the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
    #"response_schema": schema,  # Add the schema here
    }

    model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-002",
    generation_config=generation_config,
    )

    # TODO Make these files available on the local file system
    # You may need to update the file paths
    #files = [
    ##upload_to_gemini("/content/INTERCONTINENTAL MIAMI.pdf", mime_type="application/pdf"),
    #upload_to_gemini(up_pathtmp, mime_type="application/pdf"),
    #]
    files = genai.upload_file(file_content, mime_type="application/pdf")
    print(f"Uploaded file '{files.display_name}' as: {files.uri}")

    # Some files have a processing delay. Wait for them to be ready.
    #wait_for_files_active(files)

    chat_session = model.start_chat(
    history=[
        {
        "role": "user",
        "parts": [
            files,
            prompt,
        ],
        },
    ]
    )

    response = chat_session.send_message("INSERT_INPUT_HERE")
    
    return response


# Configuración de la barra lateral
with st.sidebar:
    # Título y subtítulo de la aplicación
    st.title("Formulario de Aprobación ")
    st.subheader("Cargue de Alojammiento con Agentes AI .")

    # Carga de archivo PDF
    uploaded_file = st.file_uploader("Upload an article",
                                 type=("pdf"),
                                 on_change=new_file,
                                 help="The full-text is extracted using Gen AI Gemini,GPT4. ")
    st.header("Contenido del PDF")
    enable_text = st.toggle('Render text in PDF', value=False, disabled=not st.session_state['uploaded'],
                            help="Enable the selection and copy-paste on the PDF")

    st.header("Alojamientos - Secciones")
    highlight_title = st.toggle('Hotel', value=True, disabled=not st.session_state['uploaded'])
    highlight_person_names = st.toggle('General', value=True, disabled=not st.session_state['uploaded'])
    highlight_affiliations = st.toggle('Habitaciones', value=True, disabled=not st.session_state['uploaded'])
    highlight_head = st.toggle('Acomodaciones', value=True, disabled=not st.session_state['uploaded'])
    highlight_sentences = st.toggle('Compra', value=False, disabled=not st.session_state['uploaded'])
    highlight_paragraphs = st.toggle('Venta', value=True, disabled=not st.session_state['uploaded'])
    highlight_notes = st.toggle('Notes', value=True, disabled=not st.session_state['uploaded'])
    highlight_formulas = st.toggle('Politicas', value=True, disabled=not st.session_state['uploaded'])
    highlight_figures = st.toggle('Figutas - Tablas', value=True, disabled=not st.session_state['uploaded'])
    highlight_callout = st.toggle('Refe', value=True, disabled=not st.session_state['uploaded'])
    highlight_citations = st.toggle('Citas', value=True, disabled=not st.session_state['uploaded'])

    st.header("Anotaciones")
    annotation_thickness = st.slider(label="Annotation boxes border thickness", min_value=1, max_value=6, value=1)
    pages_vertical_spacing = st.slider(label="Pages vertical spacing", min_value=0, max_value=10, value=2)

    st.header("Altura y Ancho")
    resolution_boost = st.slider(label="Resolution boost", min_value=1, max_value=10, value=1)
    width = st.slider(label="PDF width", min_value=100, max_value=1000, value=700)
    height = st.slider(label="PDF height", min_value=-1, max_value=10000, value=-1)

    st.header("Selección de Pagina")
    placeholder = st.empty()

    if not st.session_state['pages']:
        st.session_state['page_selection'] = placeholder.multiselect(
            "Select pages to display",
            options=[],
            default=[],
            help="The page number considered is the PDF number and not the document page number.",
            disabled=not st.session_state['pages'],
            key=1
        )

    st.header("Soporte y Ayuda")
    
    st.markdown(
        """Cargue de Alojammiento con Agentes AI - Gemini Google""")

    if st.session_state['git_rev'] != "unknown":
        st.markdown("**Revision number**: [" + st.session_state[
            'git_rev'] + "](http://digitalmagia.com" + st.session_state['git_rev'] + ")")

    
# Inicialización del cliente Grobid
#@st.cache_resource
#def init_grobid():
#    grobid_client = GrobidClient(
#        grobid_server=os.environ["_URL_"],
#        batch_size=1000,
#        coordinates=["p", "s", "persName", "biblStruct", "figure", "formula", "head", "note", "title", "ref",
#                     "affiliation"],
#        sleep_time=5,
#        timeout=60,
#        check_server=True
#    )
#    grobid_processor = GrobidProcessor(grobid_client)
#
#    return grobid_processor


# Función para obtener el hash de un archivo
def get_file_hash(fname):
    hash_md5 = blake2b()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()




if uploaded_file:
    if not st.session_state['binary']:
        with col1:
            st.spinner('Reading file, calling ...')
            binary = uploaded_file.getvalue()
            tmp_file = NamedTemporaryFile()
            tmp_file.write(bytearray(binary))
            st.session_state['binary'] = binary
           # annotations, pages = init_grobid().process_structure(tmp_file.name)

            st.session_state['annotations'] = annotations if not st.session_state['annotations'] else st.session_state[
                'annotations']
            st.session_state['pages'] = pages if not st.session_state['pages'] else st.session_state['pages']

    if st.session_state['pages']:
        st.session_state['page_selection'] = placeholder.multiselect(
            "Select pages to display",
            #options=list(range(1, st.session_state['pages'])),
            options=list(range(1, 1)),
            default=[],
            help="The page number considered is the PDF number and not the document page number.",
            disabled=not 1,
            key=2
        )

    # Renderizado del documento PDF
    with tab1:
        with st.spinner("Rendering PDF document"):
            annotations = st.session_state['annotations']

            if not highlight_sentences:
                annotations = list(filter(lambda a: a['type'] != 's', annotations))

            if not highlight_paragraphs:
                annotations = list(filter(lambda a: a['type'] != 'p', annotations))

            if not highlight_title:
                annotations = list(filter(lambda a: a['type'] != 'title', annotations))

            if not highlight_head:
                annotations = list(filter(lambda a: a['type'] != 'head', annotations))

            if not highlight_citations:
                annotations = list(filter(lambda a: a['type'] != 'biblStruct', annotations))

            if not highlight_notes:
                annotations = list(filter(lambda a: a['type'] != 'note', annotations))

            if not highlight_callout:
                annotations = list(filter(lambda a: a['type'] != 'ref', annotations))

            if not highlight_formulas:
                annotations = list(filter(lambda a: a['type'] != 'formula', annotations))

            if not highlight_person_names:
                annotations = list(filter(lambda a: a['type'] != 'persName', annotations))

            if not highlight_figures:
                annotations = list(filter(lambda a: a['type'] != 'figure', annotations))

            if not highlight_affiliations:
                annotations = list(filter(lambda a: a['type'] != 'affiliation', annotations))

            if height > -1:
                pdf_viewer(
                    input=st.session_state['binary'],
                    width=width,
                    height=height,
                    annotations=annotations,
                    pages_vertical_spacing=pages_vertical_spacing,
                    annotation_outline_size=annotation_thickness,
                    pages_to_render=st.session_state['page_selection'],
                    render_text=enable_text,
                    resolution_boost=resolution_boost
                )
            else:
                pdf_viewer(
                    input=st.session_state['binary'],
                    width=width,
                    annotations=annotations,
                    pages_vertical_spacing=pages_vertical_spacing,
                    annotation_outline_size=annotation_thickness,
                    pages_to_render=st.session_state['page_selection'],
                    render_text=enable_text,
                    resolution_boost=resolution_boost
                )
    with col2:
        tab2.subheader("AGENT IA - Utiliza el agente para Interpretar tu PDF")
        tab2.write("Este agente utiliza inteligencia artificial para interpretar y analizar el contenido de tu PDF.")
        tab2.image("https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif", caption="AI en acción")
        
        GOOGLE_API_KEY = tab2.text_input('GOOGLE_API_KEY', type='password')
        os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

        prompt_jsonsimple = "identifica los grupos de informacion o entidades de negocio y regeresalo en formato json simple clave valor con los datos  contenidos en el archivo adjunto"
        
        #myfile = genai.get_file(uploaded_file.name)       

        btn_agente = tab2.button("Iniciar Interpretación")

        if btn_agente:
            tab2.write("Interpretación iniciada...")

            #temp_dir = tempfile.mkdtemp()
            #pathtmp = os.path.join(temp_dir,uploaded_file.name)
            #with open(pathtmp, "wb") as f:
             #   f.write(uploaded_file.getvalue())

            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                file_path = tmp_file.name    

            #file_content = uploaded_file.read()  # Get the file content as bytes           

            response_llm = crete_prompt(file_path)
            tab2.subheader("Visualizador de JSON")           
            json_data = text_to_json(response_llm.text)

            # Convertir el diccionario a una cadena JSON con formato
            json_str = json.dumps(json_data, indent=4)

            # Mostrar el JSON en un expander
            with tab2.expander("Ver JSON", expanded=False):
                tab2.json(json_data)

            #flat_data = flatten_json_data(json_data)

            #tab2.write("JSON : " + flat_data.text)

            # Define the file name and path
            #file_name = "contrato_test4.json"
            #file_path = "/json/" + file_name

            #with open(file_path, "w") as file:
             #file.write(resonpse_llm.text)

    # Formulario con cuatro campos y un botón de envío
        with col3:

        # Cargar el contenido del archivo JSON
            #json_data = load_json('/json/contrato_test4.json') 
            #flat_data = flatten_json_data(json_data)
            
            #if btn_agente:
             #   form = tab2.form(key='approval_form')
              #     form.text_input(label=key, value=value)            

                # Botón de envío    
               # submit_button = form.form_submit_button(label='Enviar')

                #if submit_button:
                 #   tab2.success("Formulario enviado con éxito!") 

            if btn_agente:
                create_dynamic_form(json_data,tab2)
                #tab2.json(json_data)
                     # Crear formulario
                
                #if submit_button:
                 #   tab2.success("Formulario enviado con éxito!") 






