import streamlit as st
import json
import mammoth
import random
import re
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Gerador Elementor", page_icon="⚙️", layout="wide")

# ==========================================
# FUNÇÕES DE LÓGICA
# ==========================================
def gerar_id():
    """Gera um ID aleatório de 7 caracteres (estilo Elementor)"""
    return ''.join(random.choices('0123456789abcdef', k=7))

def extrair_estilos_profundamente(obj, dicionario):
    """Procura recursivamente por cores e fontes no ficheiro JSON do Elementor"""
    if isinstance(obj, list):
        for item in obj:
            extrair_estilos_profundamente(item, dicionario)
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
    """Converte o nome humano no ID do Elementor com base no dicionário"""
    nome_limpo = nome_escrito.strip().lower()
    if not nome_limpo:
        return ""
    
    id_encontrado = nome_escrito.strip()
    if nome_limpo in dicionario[tipo]:
        id_encontrado = dicionario[tipo][nome_limpo]
        
    prefixo = 'globals/colors?id=' if tipo == 'cores' else 'globals/typography?id='
    if prefixo in id_encontrado:
        return id_encontrado
    return prefixo + id_encontrado

def criar_widget_titulo(texto, tag_html, cor_nome, fonte_nome, dicionario):
    """Cria um widget de Título (Heading) e define a tag HTML (H1, H2, etc)"""
    settings = {
        "title": texto,
        "header_size": tag_html.lower()
    }
    cor_final = obter_id_estilo('cores', cor_nome, dicionario)
    fonte_final = obter_id_estilo('fontes', fonte_nome, dicionario)
    
    if cor_final or fonte_final:
        settings["__globals__"] = {}
        if cor_final: settings["__globals__"]["title_color"] = cor_final
        if fonte_final: settings["__globals__"]["typography_typography"] = fonte_final

    return {
        "id": gerar_id(), "elType": "widget", "widgetType": "heading",
        "settings": settings, "elements": [], "isInner": False
    }

def criar_widget_texto(html_texto, cor_nome, fonte_nome, dicionario):
    """Cria um widget de Texto (Text Editor)"""
    settings = {"editor": html_texto}
    cor_final = obter_id_estilo('cores', cor_nome, dicionario)
    fonte_final = obter_id_estilo('fontes', fonte_nome, dicionario)
    
    if cor_final or fonte_final:
        settings["__globals__"] = {}
        if cor_final: settings["__globals__"]["text_color"] = cor_final
        if fonte_final: settings["__globals__"]["typography_typography"] = fonte_final

    return {
        "id": gerar_id(), "elType": "widget", "widgetType": "text-editor",
        "settings": settings, "elements": [], "isInner": False
    }

def identificar_marcador(texto):
    """Verifica se o texto é uma TAG de marcação."""
    texto_limpo = texto.strip().upper()
    match = re.match(r'^[-—]+\s*(H[1-6]|TITLE|TEXT)\s*[-—]+$', texto_limpo)
    if match:
        tag = match.group(1)
        if tag == 'TITLE': return 'H1'
        return tag
    return None

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
st.title("Gerador Automático Elementor 📄 -> ⚙️")
st.markdown("Transforme ficheiros Word em páginas estruturadas num clique, usando tags como `--- H1 ---` ou `--- TEXT ---`.")

if 'dicionario' not in st.session_state:
    st.session_state.dicionario = {"cores": {}, "fontes": {}}

col1, col2 = st.columns(2, gap="large")

with col1:
    st.header("⚙️ 1. Ambiente do Site")
    st.markdown("Importe o ficheiro `site-settings.json` do cliente.")
    
    settings_file = st.file_uploader("Upload do site-settings.json", type=['json'])
    
    if settings_file:
        try:
            settings_json = json.load(settings_file)
            st.session_state.dicionario = {"cores": {}, "fontes": {}}
            extrair_estilos_profundamente(settings_json, st.session_state.dicionario)
            st.success("Configurações lidas com sucesso!")
            
            with st.expander("Ver Estilos Detetados (Passe o rato e clique para copiar)", expanded=True):
                cores = list(st.session_state.dicionario['cores'].keys())
                fontes = list(st.session_state.dicionario['fontes'].keys())
                
                st.markdown("**🎨 Cores:**")
                if cores:
                    c_cols = st.columns(3)
                    for i, c in enumerate(cores): c_cols[i % 3].code(c, language=None)
                else:
                    st.markdown("Nenhuma encontrada")
                
                st.markdown("**✍️ Fontes:**")
                if fontes:
                    f_cols = st.columns(3)
                    for i, f in enumerate(fontes): f_cols[i % 3].code(f, language=None)
                else:
                    st.markdown("Nenhuma encontrada")
        except Exception:
            st.error("Erro ao ler o ficheiro JSON.")

with col2:
    st.header("📄 2. Conteúdo e Mapeamento")
    
    word_file = st.file_uploader("Upload do ficheiro Word", type=['docx'])
    
    lista_cores = [""] + list(st.session_state.dicionario['cores'].keys())
    lista_fontes = [""] + list(st.session_state.dicionario['fontes'].keys())
    tem_estilos = len(lista_cores) > 1 or len(lista_fontes) > 1
    
    st.markdown("#### Estilo Padrão para Títulos (H1 a H6)")
    if tem_estilos:
        titulo_cor = st.selectbox("Cor dos Títulos", options=lista_cores, key="t_cor")
        titulo_fonte = st.selectbox("Fonte dos Títulos", options=lista_fontes, key="t_fonte")
    else:
        titulo_cor = st.text_input("Nome da Cor (Ex: Primaria)", key="t_cor")
        titulo_fonte = st.text_input("Nome da Fonte (Ex: Titulos)", key="t_fonte")
    
    st.markdown("#### Estilo Padrão para Parágrafos (TEXT)")
    if tem_estilos:
        texto_cor = st.selectbox("Cor dos Textos", options=lista_cores, key="p_cor")
        texto_fonte = st.selectbox("Fonte dos Textos", options=lista_fontes, key="p_fonte")
    else:
        texto_cor = st.text_input("Nome da Cor (Ex: Texto)", key="p_cor")
        texto_fonte = st.text_input("Nome da Fonte (Ex: Paragrafos)", key="p_fonte")
    
    st.markdown("---")
    if word_file and st.button("Gerar Código JSON", type="primary", use_container_width=True):
        with st.spinner("A processar ficheiro..."):
            result = mammoth.convert_to_html(word_file)
            soup = BeautifulSoup(result.value, 'html.parser')
            
            widgets_gerados = []
            modo_atual = 'TEXT'
            buffer_texto = [] # Armazena parágrafos e listas consecutivas
            
            # Percorre os elementos de topo (tags <p>, <ul>, <ol>, etc)
            for element in soup.find_all(recursive=False):
                texto_puro = element.get_text(strip=True)
                if not texto_puro:
                    continue
                
                marcador = identificar_marcador(texto_puro)
                
                if marcador:
                    # Se encontrou um marcador, guarda o texto que estava pendente no buffer
                    if buffer_texto and modo_atual == 'TEXT':
                        widgets_gerados.append(criar_widget_texto(
                            "".join(buffer_texto), texto_cor, texto_fonte, st.session_state.dicionario
                        ))
                        buffer_texto = []
                    
                    modo_atual = marcador
                    continue
                
                # Trata o conteúdo baseado no modo atual
                if modo_atual.startswith('H'):
                    widgets_gerados.append(criar_widget_titulo(
                        texto_puro, modo_atual, titulo_cor, titulo_fonte, st.session_state.dicionario
                    ))
                elif modo_atual == 'TEXT':
                    # Acumula o HTML real (inclui <ul>, <li>, <strong>, etc)
                    buffer_texto.append(str(element))
            
            # No final do documento, se sobrar texto no buffer, cria o último widget
            if buffer_texto and modo_atual == 'TEXT':
                widgets_gerados.append(criar_widget_texto(
                    "".join(buffer_texto), texto_cor, texto_fonte, st.session_state.dicionario
                ))
                    
            template_final = {
                "version": "0.4", "title": "Página Dinâmica", "type": "page",
                "content": [
                    {
                        "id": gerar_id(), "elType": "container",
                        "settings": { "content_width": "full", "padding": { "unit": "px", "top": "40", "right": "20", "bottom": "40", "left": "20", "isLinked": False } },
                        "elements": widgets_gerados, "isInner": False
                    }
                ],
                "page_settings": {}
            }
            
            json_string = json.dumps(template_final, indent=2)
            
            st.success("🎉 Sucesso! A sua página com formatação avançada está pronta.")
            st.download_button(
                label="⬇️ Transferir ficheiro .json",
                data=json_string,
                file_name="pagina-dinamica.json",
                mime="application/json",
                use_container_width=True
            )
