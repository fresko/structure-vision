import os
from hashlib import blake2b
from tempfile import NamedTemporaryFile

import dotenv
from grobid_client.grobid_client import GrobidClient
from streamlit_pdf_viewer import pdf_viewer

from grobid.grobid_processor import GrobidProcessor

dotenv.load_dotenv(override=True)

import streamlit as st

_URL_ID = "grobid"
os.environ["_URL_"] = _URL_ID

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

st.set_page_config(
    page_title="Structure vision",
    page_icon="",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/lfoppiano/pdf-struct',
        'Report a bug': "https://github.com/lfoppiano/pdf-struct/issues",
        'About': "View the structures extracted by Grobid."
    }
)

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
# from glob import glob
# import streamlit as st
#
# paths = glob("/Users/lfoppiano/kDrive/library/articles/materials informatics/polymers/*.pdf")
# for id, (tab,path) in enumerate(zip(st.tabs(paths),paths)):
#     with tab:
#         with st.container(height=600):
#             pdf_viewer(path, width=500, render_text=True)


with st.sidebar:
    st.header("Contenido")
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
            'git_rev'] + "](https://github.com/lfoppiano/structure-vision/commit/" + st.session_state['git_rev'] + ")")


def new_file():
    st.session_state['doc_id'] = None
    st.session_state['uploaded'] = True
    st.session_state['annotations'] = []
    st.session_state['binary'] = None


@st.cache_resource
def init_grobid():
    grobid_client = GrobidClient(
        grobid_server=os.environ["_URL_"],
        batch_size=1000,
        coordinates=["p", "s", "persName", "biblStruct", "figure", "formula", "head", "note", "title", "ref",
                     "affiliation"],
        sleep_time=5,
        timeout=60,
        check_server=True
    )
    grobid_processor = GrobidProcessor(grobid_client)

    return grobid_processor


#init_grobid()


def get_file_hash(fname):
    hash_md5 = blake2b()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


st.title("Formulario de Aprobación ")
st.subheader("**Aprobación** de Alojamientos - Interpretados.")

uploaded_file = st.file_uploader("Upload an article",
                                 type=("pdf"),
                                 on_change=new_file,
                                 help="The full-text is extracted using Grobid. ")

if uploaded_file:
    if not st.session_state['binary']:
        with (st.spinner('Reading file, calling Grobid...')):
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
            options=list(range(1, st.session_state['pages'])),
            default=[],
            help="The page number considered is the PDF number and not the document page number.",
            disabled=not st.session_state['pages'],
            key=2
        )

    with (st.spinner("Rendering PDF document")):
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
