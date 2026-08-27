
import streamlit as st
import json
import mammoth
import random
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

def criar_widget_titulo(texto, cor_nome, fonte_nome, dicionario):
    settings = {"title": texto}
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

# ==========================================
# INTERFACE STREAMLIT
# ==========================================
st.title("Gerador Automático Elementor 📄 -> ⚙️")
st.markdown("Transforme ficheiros Word em páginas estruturadas num clique.")

# Inicializa o dicionário na sessão
if 'dicionario' not in st.session_state:
    st.session_state.dicionario = {"cores": {}, "fontes": {}}

col1, col2 = st.columns(2)

with col1:
    st.header("⚙️ 1. Ambiente do Site")
    st.markdown("Importe o ficheiro `site-settings.json` do cliente para detetar as cores nativas.")
    
    settings_file = st.file_uploader("Upload do site-settings.json", type=['json'])
    
    if settings_file:
        try:
            settings_json = json.load(settings_file)
            st.session_state.dicionario = {"cores": {}, "fontes": {}}
            extrair_estilos_profundamente(settings_json, st.session_state.dicionario)
            
            st.success("Configurações lidas com sucesso!")
            
            with st.expander("Ver Estilos Detetados neste Site"):
                cores = list(st.session_state.dicionario['cores'].keys())
                fontes = list(st.session_state.dicionario['fontes'].keys())
                
                st.markdown("**🎨 Cores:**")
                st.markdown(', '.join([f"`{c}`" for c in cores]) if cores else "Nenhuma encontrada")
                
                st.markdown("**✍️ Fontes:**")
                st.markdown(', '.join([f"`{f}`" for f in fontes]) if fontes else "Nenhuma encontrada")
        except Exception as e:
            st.error("Erro ao ler o ficheiro JSON.")

with col2:
    st.header("📄 2. Conteúdo e Mapeamento")
    
    word_file = st.file_uploader("Upload do ficheiro Word", type=['docx'])
    
    st.markdown("#### Mapeamento de Títulos")
    titulo_cor = st.text_input("Nome da Cor (Ex: Primaria)", key="t_cor")
    titulo_fonte = st.text_input("Nome da Fonte (Ex: Titulos)", key="t_fonte")
    
    st.markdown("#### Mapeamento de Parágrafos")
    texto_cor = st.text_input("Nome da Cor (Ex: Texto)", key="p_cor")
    texto_fonte = st.text_input("Nome da Fonte (Ex: Paragrafos)", key="p_fonte")
    
    if word_file and st.button("Gerar Código JSON", type="primary", use_container_width=True):
        with st.spinner("A processar ficheiro..."):
            result = mammoth.convert_to_html(word_file)
            html_extraido = result.value
            
            soup = BeautifulSoup(html_extraido, 'html.parser')
            widgets_gerados = []
            
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                if element.name.startswith('h'):
                    widgets_gerados.append(criar_widget_titulo(
                        element.get_text(), titulo_cor, titulo_fonte, st.session_state.dicionario
                    ))
                elif element.name == 'p' and element.get_text(strip=True):
                    widgets_gerados.append(criar_widget_texto(
                        str(element), texto_cor, texto_fonte, st.session_state.dicionario
                    ))
                    
            template_final = {
                "version": "0.4", "title": "Página Gerada", "type": "page",
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
            
            st.success("🎉 Sucesso! O seu ficheiro Elementor está pronto.")
            st.download_button(
                label="⬇️ Transferir ficheiro .json",
                data=json_string,
                file_name="pagina-pronta-elementor.json",
                mime="application/json",
                use_container_width=True
            )
