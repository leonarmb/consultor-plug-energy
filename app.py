# ==================================================================================
# ATENÇÃO DESENVOLVEDOR GEMINI: JAMAIS ELIMINAR OU SIMPLIFICAR NENHUMA DIRETRIZ 
# TÉCNICA OU ELEMENTO DE INTELIGÊNCIA DESTE BOT. CADA REGRA É ESSENCIAL.
# MANTENHA A LISTA DE 10 DIRETRIZES TÉCNICAS E A LÓGICA DE MEMÓRIA SEMPRE ATIVAS.
# ==================================================================================

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

# --- ESTADO DO PROJETO E MEMÓRIA PERSISTENTE ---
if "projeto_ativo" not in st.session_state: st.session_state.projeto_ativo = False
if "dados_projeto" not in st.session_state: st.session_state.dados_projeto = ""
if "modo_bot" not in st.session_state: st.session_state.modo_bot = "Consulta Técnica"
if "messages" not in st.session_state: st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("Configurações")
    st.session_state.modo_bot = st.radio("Objetivo do Atendimento:", ["Consulta Técnica", "Dimensionamento de Projeto"])
    st.markdown("---")
    if st.button("🆕 Iniciar Novo Projeto (Reset)"):
        st.session_state.projeto_ativo = False
        st.session_state.dados_projeto = ""
        st.session_state.messages = []
        st.rerun()

# --- INTEGRAÇÃO COM GOOGLE AI ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_PLANILHA = st.secrets["LINK_PLANILHA_ESTOQUE"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
except:
    st.error("Erro técnico: Chaves de API não encontradas.")
    st.stop()

@st.cache_data(ttl=60)
def carregar_estoque_completo():
    try:
        dict_abas = pd.read_excel(LINK_PLANILHA, sheet_name=None)
        texto_final = ""
        for nome_aba, df in dict_abas.items():
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')].dropna(how='all')
            texto_final += f"\n\n### CATEGORIA: {nome_aba.upper()} ###\n{df.to_csv(index=False)}"
        return texto_final
    except: return None

contexto_estoque = carregar_estoque_completo()

# --- MOTOR DE RESPOSTA ESTABILIZADO ---
def processar_chat(texto_usuario):
    # Trava de início de projeto
    if st.session_state.modo_bot == "Dimensionamento de Projeto" and not st.session_state.projeto_ativo:
        st.session_state.projeto_ativo = True
        st.session_state.dados_projeto = texto_usuario

    st.session_state.messages.append({"role": "user", "content": texto_usuario})
    
    # Comportamento dinâmico
    if st.session_state.modo_bot == "Consulta Técnica":
        comportamento = "Responda de forma curta e técnica. Sem cenários comerciais."
    elif re.search(r'(cenário|cenario)\s*[1-3]', texto_usuario.lower()):
        num = re.findall(r'[1-3]', texto_usuario)[0]
        comportamento = f"""DETALHE O CENÁRIO {num} do projeto: {st.session_state.dados_projeto}. 
        REGRAS: 1. Use EXATAMENTE os mesmos modelos sugeridos anteriormente para este cenário {num}. 
        2. Mantenha a modalidade (Locação/Venda). 3. Mostre Custos, Venda e LUCRO BRUTO."""
    else:
        comportamento = f"Atue como Consultor Estrategista para o projeto '{st.session_state.dados_projeto}'. Apresente 3 CENÁRIOS (Econômico, Ideal e Expansão) com tabelas individuais e totais."

    # PROMPT DE ENGENHARIA TOTAL (AS 10 DIRETRIZES)
    prompt_mestre = f"""Você é o Engenheiro Consultor e Estrategista Comercial da Plug Energy do Brasil.
    DADOS: {contexto_estoque} | CONTEXTO: {comportamento}

    DIRETRIZES MANDATÓRIAS:
    1. POTÊNCIA REAL: Watts = kVA * FP (+20% margem).
    2. MISSÃO CRÍTICA: Cenário Ideal deve ser N+1 (ATS ou Paralelismo).
    3. DIMENSÕES: 1U = 44.45mm. Alerta profundidade > 90% rack.
    4. LOGÍSTICA: Alerta peso >30kg (trilhos), >60kg (piso/empilhadeira).
    5. PRIORIDADE MARCA: Sempre prefira Plug Energy.
    6. BATERIAS (LÓGICA PLANILHA): Rendimento 0.96. I_total = W / (VDC * 0.96). I_bat = I_total / Strings. Use tabelas de descarga real (7Ah/9Ah). JAMAIS use Peukert.
    7. DINÂMICA DE USO: Em elevadores, alerte sobre autoconsumo e queda de tensão no tempo de espera.
    8. ADAPTAÇÃO TENSÃO: 380V->220V use Transformador Isolador (Ideal).
    9. RACK: Sugerir sobra de espaço (U) para expansão.
    10. MULTIMÍDIA: Use '### 📂 MULTIMÍDIA' e o prefixo 'LINK_FOTO: ' em linha isolada.

    Pergunta: {texto_usuario}"""

    try:
        response = model.generate_content(prompt_mestre)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erro na IA: {e}")

# --- RENDERIZAÇÃO ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            links = re.findall(r'LINK_FOTO:\s*(https?://\S+)', msg["content"])
            for link in list(dict.fromkeys(links)):
                url_limpa = link.strip().split(' ')[0].rstrip('.,;)]')
                st.image(url_limpa, width=450)

# Input
if p := st.chat_input("Como posso ajudar a Plug Energy hoje?"):
    processar_chat(p)
    st.rerun()

# --- MENU DE AÇÕES ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.modo_bot == "Dimensionamento de Projeto":
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("1️⃣ Detalhar C1"):
        processar_chat("Me detalhe melhor o Cenário 1 (custos e lucro)")
        st.rerun()
    if c2.button("2️⃣ Detalhar C2"):
        processar_chat("Me detalhe melhor o Cenário 2 (custos e lucro)")
        st.rerun()
    if c3.button("3️⃣ Detalhar C3"):
        processar_chat("Me detalhe melhor o Cenário 3 (custos e lucro)")
        st.rerun()
    if c4.button("🔄 Novo Projeto"):
        st.session_state.projeto_ativo = False
        st.session_state.messages = []
        st.rerun()
