import streamlit as st
import json
import mammoth
import random
import re
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E DESIGN
# ==========================================
st.set_page_config(page_title="Elementor Generator", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Geist:wght@100..900&family=Ubuntu:wght@400;500;700&display=swap');

        /* Fonte base e Cor do Texto Escuro */
        html, body, [class*="css"] {
            font-family: 'Geist', sans-serif !important;
            color: #2E3132 !important;
        }

        /* Cor de fundo da App */
        .stApp {
            background-color: #F9FAFB !important;
        }

        /* Títulos em Azul e Fonte Ubuntu */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Ubuntu', sans-serif !important;
            color: #3B82F6 !important;
        }
        
        /* Estilo dos Cartões */
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] {
            background-color: #FFFFFF !important;
            border-color: #E5E7EB !important;
            border-radius: 0.75rem !important;
        }

        /* 🟦 BORDA TRACEJADA NOS UPLOADS 🟦 */
        [data-testid="stFileUploaderDropzone"] {
            border: 1px dashed #3B82F6 !important;
            background-color: transparent !important;
            border-radius: 0.5rem !important;
        }

        /* 🟦 BORDA SÓLIDA NAS CAIXAS DE ESTILOS 🟦 */
        div[data-testid="stCodeBlock"] {
            border: 1px solid #3B82F6 !important;
            border-radius: 0.5rem !important;
            background-color: transparent !important;
            margin-bottom: 0.2rem !important;
        }
        div[data-testid="stCodeBlock"] code {
            color: #2E3132 !important;
            font-family: 'Geist', sans-serif !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNÇÕES DE LÓGICA
# ==========================================
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
                        tipo = 'cores' if 'color' in key else 'fontes'
                        dicionario[tipo][item["title"].strip().lower()] = item["_id"]
        for key, value in obj.items(): extrair_estilos_profundamente(value, dicionario)

def obter_id_estilo(tipo, nome_escrito, dicionario):
    nome_limpo = nome_escrito.strip().lower()
    if not nome_limpo: return ""
    id_encontrado = dicionario[tipo].get(nome_limpo, nome_escrito.strip())
    prefixo = 'globals/colors?id=' if tipo == 'cores' else 'globals/typography?id='
    return id_encontrado if prefixo in id_encontrado else prefixo + id_encontrado

def criar_widget_titulo(texto_html, tag_html, cor_nome, fonte_nome, cor_link, cor_hover, dicionario, css_id=None):
    settings = {"title": texto_html, "header_size": tag_html.lower()}
    if css_id: settings["_css_id"] = css_id
    
    cor_f = obter_id_estilo('cores', cor_nome, dicionario)
    fonte_f = obter_id_estilo('fontes', fonte_nome, dicionario)
    link_f = obter_id_estilo('cores', cor_link, dicionario)
    hover_f = obter_id_estilo('cores', cor_hover, dicionario)
    
    globals_dict = {}
    if cor_f: globals_dict["title_color"] = cor_f
    if fonte_f: globals_dict["typography_typography"] = fonte_f
    if link_f: globals_dict["link_color"] = link_f
    if hover_f: globals_dict["link_hover_color"] = hover_f
    if globals_dict: settings["__globals__"] = globals_dict

    return {"id": gerar_id(), "elType": "widget", "widgetType": "heading", "settings": settings, "elements": [], "isInner": False}

def criar_widget_texto(html_texto, cor_nome, fonte_nome, cor_link, cor_hover, dicionario):
    settings = {"editor": html_texto}
    
    cor_f = obter_id_estilo('cores', cor_nome, dicionario)
    fonte_f = obter_id_estilo('fontes', fonte_nome, dicionario)
    link_f = obter_id_estilo('cores', cor_link, dicionario)
    hover_f = obter_id_estilo('cores', cor_hover, dicionario)
    
    globals_dict = {}
    if cor_f: globals_dict["text_color"] = cor_f
    if fonte_f: globals_dict["typography_typography"] = fonte_f
    if link_f: globals_dict["link_color"] = link_f
    if hover_f: globals_dict["link_hover_color"] = hover_f
    if globals_dict: settings["__globals__"] = globals_dict

    return {"id": gerar_id(), "elType": "widget", "widgetType": "text-editor", "settings": settings, "elements": [], "isInner": False}

def identificar_marcador(texto):
    match = re.match(r'^[-—]+\s*(H[1-6]|TITLE|TEXT)\s*[-—]+$', texto.strip().upper())
    return 'H1' if match and match.group(1) == 'TITLE' else (match.group(1) if match else None)

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
st.title("Elementor Generator", anchor=False)
st.markdown("Faça o upload do seu ficheiro de design e mapeie os estilos para gerar o JSON estruturado.")

if 'dicionario' not in st.session_state:
    st.session_state.dicionario = {"cores": {}, "fontes": {}}

col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    with st.container(border=True):
        st.subheader("Drag & Drop Files", anchor=False)
        settings_file = st.file_uploader("1. Configurações do Site (.json)", type=['json'])
        word_file = st.file_uploader("2. Documento de Texto (.docx)", type=['docx'])
        
        if settings_file:
            try:
                settings_json = json.load(settings_file)
                st.session_state.dicionario = {"cores": {}, "fontes": {}}
                extrair_estilos_profundamente(settings_json, st.session_state.dicionario)
                st.success("Configurações importadas!")
            except Exception:
                st.error("Erro ao ler o ficheiro JSON.")

    if settings_file:
        with st.container(border=True):
            st.subheader("Detected Styles", anchor=False)
            cores = list(st.session_state.dicionario['cores'].keys())
            fontes = list(st.session_state.dicionario['fontes'].keys())
            
            with st.expander("Ver lista de estilos extraídos", expanded=True):
                col_estilos_1, col_estilos_2 = st.columns(2)
                
                with col_estilos_1:
                    st.markdown("**Cores**")
                    if cores:
                        for c in cores: st.code(c, language=None)
                    else:
                        st.caption("Nenhuma cor encontrada.")
                        
                with col_estilos_2:
                    st.markdown("**Tipografia**")
                    if fontes:
                        for f in fontes: st.code(f, language=None)
                    else:
                        st.caption("Nenhuma fonte encontrada.")

with col2:
    with st.container(border=True):
        st.subheader("Style Mapping", anchor=False)
        
        lista_cores = [""] + list(st.session_state.dicionario['cores'].keys())
        lista_fontes = [""] + list(st.session_state.dicionario['fontes'].keys())
        tem_estilos = len(lista_cores) > 1 or len(lista_fontes) > 1
        
        cab1, cab2, cab3 = st.columns([0.5, 1.5, 1.5])
        cab1.markdown("**TAG**")
        cab2.markdown("**Cor**")
        cab3.markdown("**Fonte**")
        
        estilos_configurados = {}
        elementos = ["H1", "H2", "H3", "H4", "H5", "H6", "TEXT"]
        
        for el in elementos:
            col_tag, col_cor, col_fonte = st.columns([0.5, 1.5, 1.5])
            col_tag.markdown(f"<div style='margin-top:10px;'><b>{el}</b></div>", unsafe_allow_html=True)
            
            with col_cor:
                if tem_estilos:
                    c = st.selectbox(f"Cor {el}", options=lista_cores, key=f"cor_{el}", label_visibility="collapsed")
                else:
                    c = st.text_input(f"Cor {el}", placeholder="Nome da Cor", key=f"cor_{el}", label_visibility="collapsed")
            
            with col_fonte:
                if tem_estilos:
                    f = st.selectbox(f"Fonte {el}", options=lista_fontes, key=f"fonte_{el}", label_visibility="collapsed")
                else:
                    f = st.text_input(f"Fonte {el}", placeholder="Nome da Fonte", key=f"fonte_{el}", label_visibility="collapsed")
                    
            estilos_configurados[el] = {"cor": c, "fonte": f}
            
        st.divider()
        
        st.markdown("**Configuração de Links Globais**")
        col_link1, col_link2 = st.columns(2)
        with col_link1:
            if tem_estilos:
                link_cor = st.selectbox("Cor do Link", options=lista_cores, key="link_cor_normal")
            else:
                link_cor = st.text_input("Cor do Link", placeholder="Nome da Cor", key="link_cor_normal")
                
        with col_link2:
            if tem_estilos:
                link_hover = st.selectbox("Cor do Hover", options=lista_cores, key="link_cor_hover")
            else:
                link_hover = st.text_input("Cor do Hover", placeholder="Nome da Cor", key="link_cor_hover")

    # NOVO CARTÃO: Configuração de Layout / Margens
    with st.container(border=True):
        st.subheader("Layout Settings", anchor=False)
        
        st.markdown("**Padding (Espaço Interior do Container)**")
        col_p_unit, col_p_t, col_p_r, col_p_b, col_p_l = st.columns(5)
        p_unit = col_p_unit.selectbox("Unidade", ["px", "%", "em", "rem"], key="p_unit")
        p_top = col_p_t.text_input("Topo", value="40", key="p_top")
        p_right = col_p_r.text_input("Direita", value="20", key="p_right")
        p_bottom = col_p_b.text_input("Fundo", value="40", key="p_bottom")
        p_left = col_p_l.text_input("Esquerda", value="20", key="p_left")
        
        st.markdown("**Margin (Espaço Exterior do Container)**")
        col_m_unit, col_m_t, col_m_r, col_m_b, col_m_l = st.columns(5)
        m_unit = col_m_unit.selectbox("Unidade", ["px", "%", "em", "rem"], key="m_unit")
        m_top = col_m_t.text_input("Topo", value="0", key="m_top")
        m_right = col_m_r.text_input("Direita", value="0", key="m_right")
        m_bottom = col_m_b.text_input("Fundo", value="0", key="m_bottom")
        m_left = col_m_l.text_input("Esquerda", value="0", key="m_left")

    if word_file and st.button("Generate JSON", type="primary", use_container_width=True):
        with st.spinner("Processing design elements..."):
            result = mammoth.convert_to_html(word_file)
            soup = BeautifulSoup(result.value, 'html.parser')
            
            widgets_gerados = []
            modo_atual = 'TEXT'
            buffer_texto = [] 
            
            for element in soup.find_all(recursive=False):
                texto_puro = element.get_text(strip=True)
                if not texto_puro: continue
                
                marcador = identificar_marcador(texto_puro)
                
                if marcador:
                    if buffer_texto and modo_atual == 'TEXT':
                        widgets_gerados.append(criar_widget_texto(
                            "".join(buffer_texto), estilos_configurados['TEXT']['cor'], 
                            estilos_configurados['TEXT']['fonte'], link_cor, link_hover, st.session_state.dicionario
                        ))
                        buffer_texto = []
                    modo_atual = marcador
                    continue
                
                if modo_atual.startswith('H'):
                    html_interno = element.decode_contents()
                    texto_minusculo = texto_puro.lower()
                    id_ancora = None
                    
                    termos_ral = [
                        "resolução alternativa de litígios", "litígios de consumo",
                        "alternative dispute resolution", "consumer dispute",
                        "resolución alternativa", "litigios de consumo",
                        "règlement extrajudiciaire", "litiges de consommation",
                        "alternative streitbeilegung", "verbraucherstreitbeilegung"
                    ]
                    
                    if any(termo in texto_minusculo for termo in termos_ral):
                        id_ancora = "ral"
                    
                    widgets_gerados.append(criar_widget_titulo(
                        html_interno, modo_atual, estilos_configurados[modo_atual]['cor'], 
                        estilos_configurados[modo_atual]['fonte'], link_cor, link_hover, 
                        st.session_state.dicionario, id_ancora
                    ))
                elif modo_atual == 'TEXT':
                    buffer_texto.append(str(element))
            
            if buffer_texto and modo_atual == 'TEXT':
                widgets_gerados.append(criar_widget_texto(
                    "".join(buffer_texto), estilos_configurados['TEXT']['cor'], 
                    estilos_configurados['TEXT']['fonte'], link_cor, link_hover, st.session_state.dicionario
                ))
            
            # Montar as definições do container com base no que foi introduzido
            container_settings = {
                "content_width": "full",
                "padding": {
                    "unit": p_unit, "top": p_top, "right": p_right, "bottom": p_bottom, "left": p_left, "isLinked": False
                },
                "margin": {
                    "unit": m_unit, "top": m_top, "right": m_right, "bottom": m_bottom, "left": m_left, "isLinked": False
                }
            }
            
            template_final = {
                "version": "0.4", "title": "Página Dinâmica", "type": "page",
                "content": [{
                    "id": gerar_id(), "elType": "container",
                    "settings": container_settings,
                    "elements": widgets_gerados, "isInner": False
                }],
                "page_settings": {}
            }
            
            json_string = json.dumps(template_final, indent=2)
            
            st.success("Produção Concluída!")
            st.download_button("Download Elementor JSON", data=json_string, file_name="elementor-gen.json", mime="application/json", use_container_width=True)
