import streamlit as st
import json
import mammoth
import random
import re
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURAÇÃO E DESIGN SYSTEM "LUMINOUS PRECISION"
# ==========================================
st.set_page_config(page_title="Elementor Generator", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        /* Tipografia global e fundo */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }
        .stApp { background-color: #f8f9fa; }
        
        /* Estilos dos Botões Primary */
        .stButton>button {
            background-color: #0058be;
            color: #ffffff;
            border-radius: 0.5rem;
            border: none;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
        }
        .stButton>button:hover { background-color: #2170e4; color: #ffffff; }
        
        /* Ajuste de Headers */
        h1 { font-size: 32px !important; font-weight: 600 !important; color: #0058be; }
        h2, h3 { font-weight: 600 !important; color: #191c1d; }
        
        /* Caixas estílo "Cards" com fundo branco e borda */
        .block-container { padding-top: 2rem; }
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] {
            background-color: #ffffff;
            border: 1px solid #e1e3e4;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# (AS FUNÇÕES DE LÓGICA MANTÊM-SE IGUAIS)
def gerar_id(): return ''.join(random.choices('0123456789abcdef', k=7))

def extrair_estilos_profundamente(obj, dicionario):
    if isinstance(obj, list):
        for item in obj: extrair_estilos_profundamente(item, dicionario)
        return
    if isinstance(obj, dict):
        for key in ["system_colors", "custom_colors", "system_typography", "custom_typography"]:
            if key in obj and isinstance(obj[key], list):
                for item in obj[key]:
                    if "title" in item and "_id" in item:
                        tipo = "cores" if "color" in key else "fontes"
                        dicionario[tipo][item["title"].strip().lower()] = item["_id"]
        for key, value in obj.items(): extrair_estilos_profundamente(value, dicionario)

def obter_id_estilo(tipo, nome_escrito, dicionario):
    nome_limpo = nome_escrito.strip().lower()
    if not nome_limpo: return ""
    id_encontrado = dicionario[tipo].get(nome_limpo, nome_escrito.strip())
    prefixo = 'globals/colors?id=' if tipo == 'cores' else 'globals/typography?id='
    return id_encontrado if prefixo in id_encontrado else prefixo + id_encontrado

def criar_widget(tipo_widget, texto_html, tag_html, cor_nome, fonte_nome, cor_link, cor_hover, dicionario, css_id=None):
    settings = {"editor": texto_html} if tipo_widget == "text-editor" else {"title": texto_html, "header_size": tag_html.lower()}
    if css_id: settings["_css_id"] = css_id
    
    globais = {}
    cor_f = obter_id_estilo('cores', cor_nome, dicionario)
    fonte_f = obter_id_estilo('fontes', fonte_nome, dicionario)
    link_f = obter_id_estilo('cores', cor_link, dicionario)
    hover_f = obter_id_estilo('cores', cor_hover, dicionario)
    
    prefixo_cor = "text_color" if tipo_widget == "text-editor" else "title_color"
    if cor_f: globais[prefixo_cor] = cor_f
    if fonte_f: globais["typography_typography"] = fonte_f
    if link_f: globais["link_color"] = link_f
    if hover_f: globais["link_hover_color"] = hover_f
    if globais: settings["__globals__"] = globais

    return {"id": gerar_id(), "elType": "widget", "widgetType": tipo_widget, "settings": settings, "elements": [], "isInner": False}

def identificar_marcador(texto):
    match = re.match(r'^[-—]+\s*(H[1-6]|TITLE|TEXT)\s*[-—]+$', texto.strip().upper())
    return 'H1' if match and match.group(1) == 'TITLE' else (match.group(1) if match else None)

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
if 'dicionario' not in st.session_state:
    st.session_state.dicionario = {"cores": {}, "fontes": {}}

# BARRA LATERAL (Imitando o Menu)
with st.sidebar:
    st.markdown("### Elementor Gen")
    st.markdown("---")
    st.markdown("📁 **Dashboard**")
    st.markdown("🎨 **Style Library**")
    st.markdown("⚙️ **Settings**")

# CABEÇALHO PRINCIPAL
st.title("Design to Code")
st.markdown("Upload your design file and configure style mappings to generate production-ready Elementor JSON structures.")

col1, col2 = st.columns([1, 1.8], gap="large")

with col1:
    st.markdown("### Drag & Drop Design File")
    settings_file = st.file_uploader("1. Upload site-settings.json", type=['json'])
    word_file = st.file_uploader("2. Upload Content (.docx)", type=['docx'])
    
    if settings_file:
        settings_json = json.load(settings_file)
        st.session_state.dicionario = {"cores": {}, "fontes": {}}
        extrair_estilos_profundamente(settings_json, st.session_state.dicionario)
        
        st.markdown("### Detected Styles")
        cores = list(st.session_state.dicionario['cores'].keys())
        fontes = list(st.session_state.dicionario['fontes'].keys())
        
        st.markdown("**COLORS**")
        if cores: st.markdown(', '.join([f"`{c}`" for c in cores]))
        st.markdown("**TYPOGRAPHY**")
        if fontes: st.markdown(', '.join([f"`{f}`" for f in fontes]))

with col2:
    st.markdown("### Style Mapping")
    lista_cores = [""] + list(st.session_state.dicionario['cores'].keys())
    lista_fontes = [""] + list(st.session_state.dicionario['fontes'].keys())
    tem_estilos = len(lista_cores) > 1 or len(lista_fontes) > 1
    
    estilos_configurados = {}
    elementos = ["H1", "H2", "H3", "TEXT"]
    
    for el in elementos:
        c1, c2, c3 = st.columns([0.4, 1.5, 1.5])
        c1.markdown(f"**{el} Mapping**")
        c2.selectbox(f"Cor", options=lista_cores, key=f"cor_{el}", label_visibility="collapsed") if tem_estilos else c2.text_input("Cor", key=f"cor_{el}", label_visibility="collapsed")
        c3.selectbox(f"Fonte", options=lista_fontes, key=f"fonte_{el}", label_visibility="collapsed") if tem_estilos else c3.text_input("Fonte", key=f"fonte_{el}", label_visibility="collapsed")
        estilos_configurados[el] = {"cor": st.session_state[f"cor_{el}"], "fonte": st.session_state[f"fonte_{el}"]}
        
    st.markdown("#### Global Links")
    cl1, cl2 = st.columns(2)
    link_cor = cl1.selectbox("Link Color", options=lista_cores) if tem_estilos else cl1.text_input("Link Color")
    link_hover = cl2.selectbox("Hover Color", options=lista_cores) if tem_estilos else cl2.text_input("Hover Color")
    
    st.markdown("---")
    if word_file and st.button("{ } Generate JSON", use_container_width=True):
        with st.spinner("Processing..."):
            result = mammoth.convert_to_html(word_file)
            soup = BeautifulSoup(result.value, 'html.parser')
            widgets_gerados, buffer_texto, modo_atual = [], [], 'TEXT'
            
            for element in soup.find_all(recursive=False):
                texto_puro = element.get_text(strip=True)
                if not texto_puro: continue
                marcador = identificar_marcador(texto_puro)
                
                if marcador:
                    if buffer_texto and modo_atual == 'TEXT':
                        widgets_gerados.append(criar_widget("text-editor", "".join(buffer_texto), None, estilos_configurados['TEXT']['cor'], estilos_configurados['TEXT']['fonte'], link_cor, link_hover, st.session_state.dicionario))
                        buffer_texto = []
                    modo_atual = marcador
                    continue
                
                if modo_atual.startswith('H'):
                    id_ancora = "ral" if "resolução alternativa de litígios de consumo" in texto_puro.lower() else None
                    widgets_gerados.append(criar_widget("heading", element.decode_contents(), modo_atual, estilos_configurados[modo_atual]['cor'], estilos_configurados[modo_atual]['fonte'], link_cor, link_hover, st.session_state.dicionario, id_ancora))
                elif modo_atual == 'TEXT':
                    buffer_texto.append(str(element))
            
            if buffer_texto and modo_atual == 'TEXT':
                widgets_gerados.append(criar_widget("text-editor", "".join(buffer_texto), None, estilos_configurados['TEXT']['cor'], estilos_configurados['TEXT']['fonte'], link_cor, link_hover, st.session_state.dicionario))
            
            json_string = json.dumps({"version": "0.4", "title": "Generated Page", "type": "page", "content": [{"id": gerar_id(), "elType": "container", "settings": {"content_width": "full"}, "elements": widgets_gerados, "isInner": False}], "page_settings": {}}, indent=2)
            st.success("Ready!")
            st.download_button("Download JSON", data=json_string, file_name="elementor-gen.json", mime="application/json", use_container_width=True)
