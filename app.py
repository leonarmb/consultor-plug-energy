import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")

# --- ESTILO VISUAL (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stMarkdown table { color: #fafafa; }
    h1, h2, h3, hr { color: #ffffff !important; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; border: 1px solid #464b5d; }
    .stButton>button:hover { border: 1px solid #ffffff; color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
@st.cache_data
def exibir_cabecalho():
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.image("logo_plugenergy_invert.png", use_container_width=True)
    st.markdown("<h1 style='text-align: center;'>Consultor Técnico de Engenharia</h1>", unsafe_allow_html=True)
    st.markdown("---")

exibir_cabecalho()

# --- ESTADO DO PROJETO E MEMÓRIA ---
if "projeto_ativo" not in st.session_state:
    st.session_state.projeto_ativo = False
if "dados_projeto" not in st.session_state:
    st.session_state.dados_projeto = ""
if "modo_bot" not in st.session_state:
    st.session_state.modo_bot = "Consulta Técnica"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("Configurações")
    modo_escolhido = st.radio("Objetivo:", ["Consulta Técnica", "Dimensionamento de Projeto"])
    st.session_state.modo_bot = modo_escolhido
    
    if st.button("🆕 Iniciar Novo Projeto"):
        st.session_state.projeto_ativo = False
        st.session_state.dados_projeto = ""
        st.session_state.messages = []
        st.rerun()

# --- CARREGAMENTO DA PLANILHA ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_PLANILHA = st.secrets["LINK_PLANILHA_ESTOQUE"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
except:
    st.error("Erro nos Secrets da API.")
    st.stop()

@st.cache_data(ttl=60)
def carregar_estoque():
    try:
        dict_abas = pd.read_excel(LINK_PLANILHA, sheet_name=None)
        return "\n".join([f"CAT: {n}\n{df.to_csv(index=False)}" for n, df in dict_abas.items()])
    except: return None

contexto_estoque = carregar_estoque()

# --- CHAT INTERFACE ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Como posso ajudar a Plug Energy hoje?"):
    # Salvar contexto se for o início de um projeto
    if st.session_state.modo_bot == "Dimensionamento de Projeto" and not st.session_state.projeto_ativo:
        st.session_state.projeto_ativo = True
        st.session_state.dados_projeto = prompt

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if contexto_estoque:
            # Definição de Comportamento (A "Cereja do Bolo")
            if st.session_state.modo_bot == "Consulta Técnica":
                behavior = "Responda de forma curta e técnica. Sem cenários comerciais."
            elif re.search(r'(cenário|cenario)\s*[1-3]', prompt.lower()):
                behavior = f"""O usuário escolheu detalhar um cenário do PROJETO ATIVO: {st.session_state.dados_projeto}.
                - Mantenha-se fiel aos equipamentos e modalidade (Locação/Venda) definidos no início.
                - Apresente Tabela de Custos Internos, Valor Final e LUCRO BRUTO.
                - NÃO se ofereça para gerar propostas, PDFs ou contratos externos.
                - Foque em convencer o cliente tecnicamente."""
            else:
                behavior = """Apresente 3 CENÁRIOS (Econômico, Ideal e Expansão). 
                - Crie uma tabela individual com TOTAL para cada cenário.
                - Use a modalidade solicitada (Venda ou Locação)."""

            full_prompt = f"""Você é o Engenheiro Consultor da Plug Energy.
            DADOS DE ESTOQUE: {contexto_estoque}
            CONTEXTO ATUAL: {behavior}

            DIRETRIZES TÉCNICAS (OBRIGATÓRIAS):
            1. Watts = kVA * FP (+20% margem).
            2. BATERIAS: Rendimento 0.96. I_total = W / (VDC * 0.96). Use descarga real da planilha.
            3. MULTIMÍDIA: Link da foto isolado com 'LINK_FOTO: '.
            4. ELEVADORES: Alerta de autoconsumo e queda de tensão. Uso apenas para resgate.
            5. RACK: Sugerir sobra de espaço (U) e trilhos se > 30kg.
            6. MODALIDADE: Se o usuário pediu Locação, mantenha Locação até o fim.

            Pergunta atual: {prompt}"""

            placeholder = st.empty()
            full_response = ""
            try:
                response = model.generate_content(full_prompt, stream=True)
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)

                # Fotos
                links = re.findall(r'LINK_FOTO:\s*(https?://\S+)', full_response)
                for link in list(dict.fromkeys(links)):
                    st.image(link.strip().rstrip('.,;)]'), width=450, caption="Equipamento Sugerido")

                st.session_state.messages.append({"role": "assistant", "content": full_response})

                # --- MENU DE OPÇÕES (Apenas no modo Projeto) ---
                if st.session_state.modo_bot == "Dimensionamento de Projeto":
                    st.markdown("---")
                    st.write("**Ações para este projeto:**")
                    c1, c2, c3 = st.columns(3)
                    if c1.button("🔍 Detalhar Cenário 2"):
                        st.session_state.messages.append({"role": "user", "content": "Me detalhe o cenário 2 (custos e lucro)"})
                        st.rerun()
                    if c2.button("📉 Ver Cenário 3"):
                        st.session_state.messages.append({"role": "user", "content": "Me detalhe o cenário 3"})
                        st.rerun()
                    if c3.button("🔄 Novo Projeto"):
                        st.session_state.projeto_ativo = False
                        st.session_state.messages = []
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
