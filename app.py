import streamlit as st
import json
import mammoth
import random
import re
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURAÇÃO DA PÁGINA & CSS
# ==========================================
st.set_page_config(page_title="Gerador Elementor", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
        h1 { font-size: 1.8rem !important; padding-bottom: 0.5rem !important; }
        h3 { font-size: 1.3rem !important; margin-bottom: 0 !important; }
        h4 { font-size: 1.1rem !important; }
        p, div, span, label { font-size: 0.9rem !important; }
        div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; align-items: center; }
        div[data-testid="stForm"] { padding: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNÇÕES DE LÓGICA
# ==========================================
def gerar_id():
    return ''.join(random.choices('0123456789abcdef', k=7))

def extrair_estilos_profundamente(obj, dicionario):
    if isinstance(obj, list):
        for item in obj: extrair_estilos_profundamente(item, dicionario)
        return
    if isinstance(obj, dict):
        for key in ["system_colors", "custom_colors"]:
            if key in obj and isinstance(obj[key], list):
                for item in obj[key]:
                    if "title" in item and "_id" in item:
                        dicionario["cores"][item["title"].strip().lower()] = item["_id"]
                        
        for key in ["system_typography", "custom_typography"]:
            if key in obj and isinstance(obj[key], list):
                for item in obj[key]:
                    if "title" in item and "_id" in item:
                        dicionario["fontes"][item["title"].strip().lower()] = item["_id"]
                        
        for key, value in obj.items():
            extrair_estilos_profundamente(value, dicionario)

def obter_id_estilo(tipo, nome_escrito, dicionario):
    nome_limpo = nome_escrito.strip().lower()
    if not nome_limpo: return ""
    id_encontrado = nome_escrito.strip()
    if nome_limpo in dicionario[tipo]:
        id_encontrado = dicionario[tipo][nome_limpo]
        
    prefixo = 'globals/colors?id=' if tipo == 'cores' else 'globals/typography?id='
    return id_encontrado if prefixo in id_encontrado else prefixo + id_encontrado

def criar_widget_titulo(texto_html, tag_html, cor_nome, fonte_nome, dicionario):
    # texto_html agora recebe o interior exato do Word, mantendo <strong> e <a>
    settings = {"title": texto_html, "header_size": tag_html.lower()}
    cor_final = obter_id_estilo('cores', cor_nome, dicionario)
    fonte_final = obter_id_estilo('fontes', fonte_nome, dicionario)
    
    if cor_final or fonte_final:
        settings["__globals__"] = {}
        if cor_final: settings["__globals__"]["title_color"] = cor_final
        if fonte_final: settings["__globals__"]["typography_typography"] = fonte_final

    return {"id": gerar_id(), "elType": "widget", "widgetType": "heading", "settings": settings, "elements": [], "isInner": False}

def criar_widget_texto(html_texto, cor_nome, fonte_nome, dicionario):
    settings = {"editor": html_texto}
    cor_final = obter_id_estilo('cores', cor_nome, dicionario)
    fonte_final = obter_id_estilo('fontes', fonte_nome, dicionario)
    
    if cor_final or fonte_final:
        settings["__globals__"] = {}
        if cor_final: settings["__globals__"]["text_color"] = cor_final
        if fonte_final: settings["__globals__"]["typography_typography"] = fonte_final

    return {"id": gerar_id(), "elType": "widget", "widgetType": "text-editor", "settings": settings, "elements": [], "isInner": False}

def identificar_marcador(texto):
    texto_limpo = texto.strip().upper()
    match = re.match(r'^[-—]+\s*(H[1-6]|TITLE|TEXT)\s*[-—]+$', texto_limpo)
    if match:
        tag = match.group(1)
        return 'H1' if tag == 'TITLE' else tag
    return None

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
st.title("Gerador Automático Elementor 📄 -> ⚙️")
st.markdown("Transforme ficheiros Word em páginas estruturadas. Mantém links e negritos nativos.")

if 'dicionario' not in st.session_state:
    st.session_state.dicionario = {"cores": {}, "fontes": {}}

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.markdown("### ⚙️ 1. Ambiente do Site")
    settings_file = st.file_uploader("Upload do site-settings.json", type=['json'])
    
    if settings_file:
        try:
            settings_json = json.load(settings_file)
            st.session_state.dicionario = {"cores": {}, "fontes": {}}
            extrair_estilos_profundamente(settings_json, st.session_state.dicionario)
            st.success("Configurações lidas com sucesso!")
            
            with st.expander("Ver Estilos Detetados", expanded=True):
                cores = list(st.session_state.dicionario['cores'].keys())
                fontes = list(st.session_state.dicionario['fontes'].keys())
                
                st.markdown("**🎨 Cores:**")
                if cores:
                    c_cols = st.columns(3)
                    for i, c in enumerate(cores): c_cols[i % 3].code(c, language=None)
                
                st.markdown("**✍️ Fontes:**")
                if fontes:
                    f_cols = st.columns(3)
                    for i, f in enumerate(fontes): f_cols[i % 3].code(f, language=None)
        except Exception:
            st.error("Erro ao ler o ficheiro JSON.")

with col2:
    st.markdown("### 📄 2. Conteúdo e Mapeamento")
    word_file = st.file_uploader("Upload do ficheiro Word", type=['docx'])
    
    lista_cores = [""] + list(st.session_state.dicionario['cores'].keys())
    lista_fontes = [""] + list(st.session_state.dicionario['fontes'].keys())
    tem_estilos = len(lista_cores) > 1 or len(lista_fontes) > 1
    
    st.markdown("#### Configuração de Estilos Individuais")
    
    cab1, cab2, cab3 = st.columns([0.5, 1.5, 1.5])
    cab1.markdown("**TAG**")
    cab2.markdown("**🎨 Cor (Dropdown ou Texto)**")
    cab3.markdown("**✍️ Fonte (Dropdown ou Texto)**")
    
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
    
    st.markdown("---")
    if word_file and st.button("Gerar Código JSON", type="primary", use_container_width=True):
        with st.spinner("A processar ficheiro..."):
            result = mammoth.convert_to_html(word_file)
            soup = BeautifulSoup(result.value, 'html.parser')
            
            widgets_gerados = []
            modo_atual = 'TEXT'
            buffer_texto = [] 
            
            for element in soup.find_all(recursive=False):
                # Mantemos o "texto_puro" apenas para avaliar se é um marcador de formatação
                texto_puro = element.get_text(strip=True)
                if not texto_puro: continue
                
                marcador = identificar_marcador(texto_puro)
                
                if marcador:
                    if buffer_texto and modo_atual == 'TEXT':
                        widgets_gerados.append(criar_widget_texto(
                            "".join(buffer_texto), 
                            estilos_configurados['TEXT']['cor'], 
                            estilos_configurados['TEXT']['fonte'], 
                            st.session_state.dicionario
                        ))
                        buffer_texto = []
                    modo_atual = marcador
                    continue
                
                if modo_atual.startswith('H'):
                    # AQUI ESTÁ A MÁGICA: decode_contents() extrai todo o HTML interno (inclui <strong> e <a>)
                    html_interno = element.decode_contents()
                    widgets_gerados.append(criar_widget_titulo(
                        html_interno, modo_atual, 
                        estilos_configurados[modo_atual]['cor'], 
                        estilos_configurados[modo_atual]['fonte'], 
                        st.session_state.dicionario
                    ))
                elif modo_atual == 'TEXT':
                    # Transforma o elemento inteiro numa String HTML preservando parágrafos, listas e formatações
                    buffer_texto.append(str(element))
            
            if buffer_texto and modo_atual == 'TEXT':
                widgets_gerados.append(criar_widget_texto(
                    "".join(buffer_texto), 
                    estilos_configurados['TEXT']['cor'], 
                    estilos_configurados['TEXT']['fonte'], 
                    st.session_state.dicionario
                ))
                    
            template_final = {
                "version": "0.4", "title": "Página Dinâmica", "type": "page",
                "content": [
                    {
                        "id": gerar_id(), "elType": "container",
                        "settings": { "content_width": "full" },
                        "elements": widgets_gerados, "isInner": False
                    }
                ],
                "page_settings": {}
            }
            
            json_string = json.dumps(template_final, indent=2)
            
            st.success("🎉 Sucesso! A sua página está pronta com todas as formatações preservadas.")
            st.download_button("⬇️ Transferir ficheiro .json", data=json_string, file_name="pagina-gerada.json", mime="application/json", use_container_width=True)
