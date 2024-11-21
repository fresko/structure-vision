import os
from hashlib import blake2b
from tempfile import NamedTemporaryFile
import dotenv
from streamlit_pdf_viewer import pdf_viewer
import json  # Importar el módulo json
dotenv.load_dotenv(override=True)
import streamlit as st

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
        if tab2.button("Iniciar Interpretación"):
            tab2.write("Interpretación iniciada...")

    # Formulario con cuatro campos y un botón de envío
    with col3:

        # Cargar el contenido del archivo JSON
        json_data = load_json('json/contrato_v1.json')   

        # Extraer los datos del JSON
        features = json_data['Features']['Feature']
        hotel_category = json_data['HotelCategory']['#text']
        hotel_name = json_data['HotelName']
        hotel_rooms = json_data['HotelRooms']['HotelRoom']

        tab2.text_area(features)
        tab2.text_area( hotel_category)

         # Título del formulario
            
        tab2.header("Formulario de Aprobación")
        # Mostrar el nombre del hotel
        tab2.header("🏨 Nombre del Hotel")
        tab2.text(hotel_name)

            # Mostrar la categoría del hotel
        tab2.header("Categoría del Hotel")
        tab2.text(hotel_category)

            # Mostrar las características del hotel
        tab2.header("Características del Hotel")
        for feature in features:
            tab2.text(f"{feature['#text']} ({feature['@Type']})")

            # Mostrar las habitaciones del hotel
            tab2.header("Habitaciones del Hotel")
        for room in hotel_rooms:
                tab2.subheader(f"Habitación {room['@Type']}")
                tab2.text(f"Descripción: {room['Description']}")
                tab2.text(f"Capacidad: {room['Capacity']}")
                tab2.text(f"Precio: {room['Price']}")      


          # Botón de envío    
        submit_button = tab2.button(label='Enviar')

        if submit_button:
                tab2.success("Formulario enviado con éxito!") 




