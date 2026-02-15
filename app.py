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
    /* Estilização dos botões e rádio */
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; border: 1px solid #464b5d; }
    .stButton>button:hover { border: 1px solid #ffffff; color: #ffffff; }
    .stRadio [data-testid="stWidgetLabel"] p { color: #ffffff; font-weight: bold; }
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

# Sidebar com controles
with st.sidebar:
    st.title("Configurações")
    st.session_state.modo_bot = st.radio("Objetivo do Atendimento:", ["Consulta Técnica", "Dimensionamento de Projeto"])
    
    st.markdown("---")
    if st.button("🆕 Iniciar Novo Projeto (Reset)"):
        st.session_state.projeto_ativo = False
        st.session_state.dados_projeto = ""
        st.session_state.messages = []
        st.rerun()

# --- INTEGRAÇÃO COM GOOGLE GENERATIVE AI ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_PLANILHA = st.secrets["LINK_PLANILHA_ESTOQUE"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
except:
    st.error("Erro técnico: Verifique as chaves de API nos Secrets.")
    st.stop()

@st.cache_data(ttl=60)
def carregar_estoque_completo():
    try:
        dict_abas = pd.read_excel(LINK_PLANILHA, sheet_name=None)
        texto_final = ""
        for nome_aba, df in dict_abas.items():
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all')
            texto_final += f"\n\n### CATEGORIA: {nome_aba.upper()} ###\n{df.to_csv(index=False)}"
        return texto_final
    except: return None

contexto_estoque = carregar_estoque_completo()

# --- MOTOR DE RESPOSTA ESTABILIZADO ---
def processar_chat(pergunta_usuario):
    # Travar contexto de projeto no primeiro input
    if st.session_state.modo_bot == "Dimensionamento de Projeto" and not st.session_state.projeto_ativo:
        st.session_state.projeto_ativo = True
        st.session_state.dados_projeto = pergunta_usuario

    st.session_state.messages.append({"role": "user", "content": pergunta_usuario})
    
    # Comportamento Dinâmico (Lógica de Seguimento Blindada)
    if st.session_state.modo_bot == "Consulta Técnica":
        comportamento = "Responda de forma curta, técnica e direta. Informe estoque e características sem criar cenários comerciais."
    elif re.search(r'(cenário|cenario)\s*[1-3]', pergunta_usuario.lower()):
        num = re.findall(r'[1-3]', pergunta_usuario)[0]
        comportamento = f"""O usuário ESCOLHEU detalhar o CENÁRIO {num} do projeto: {st.session_state.dados_projeto}.
        REGRAS DE OURO:
        1. Use EXATAMENTE os mesmos modelos de nobreak sugeridos inicialmente para este cenário {num}.
        2. Mantenha a modalidade (Venda ou Locação) e os dados de carga fielmente.
        3. Apresente Tabela de Custos (Custo Unitário), Valor Final e o LUCRO BRUTO da operação.
        4. NÃO ofereça gerar documentos externos (PDF/Contratos)."""
    else:
        comportamento = f"""Atue como Consultor Estrategista para o projeto: '{st.session_state.dados_projeto}'.
        - Apresente 3 CENÁRIOS: ECONÔMICO (Menor custo), IDEAL (Redundante N+1) e EXPANSÃO (Mais que perfeito/Futuro).
        - Mantenha os modelos distintos entre os cenários.
        - Crie UMA TABELA INDIVIDUAL para cada cenário com o Valor Total ao final de cada uma."""

    # O PROMPT MESTRE (AS 10 DIRETRIZES TÉCNICAS)
    prompt_completo = f"""Você é o Engenheiro Consultor Sênior e Estrategista Comercial da Plug Energy do Brasil.
    DADOS DE ESTOQUE ATUALIZADOS:
    {contexto_estoque}

    CONTEXTO DE OPERAÇÃO:
    {comportamento}

    DIRETRIZES TÉCNICAS MANDATÓRIAS (SIGA COM RIGOR):
    1. POTÊNCIA REAL: Watts = kVA * Fator de Potência. Aplique SEMPRE +20% de margem sobre a carga real.
    2. MISSÃO CRÍTICA: Se a aplicação não pode parar, o Cenário Ideal DEVE ser N+1 (Redundante via ATS ou Paralelismo).
    3. DIMENSÕES: 1U = 44.45mm. Alerte sobre profundidade > 90% do rack (espaço para cabos).
    4. LOGÍSTICA: Alerte sobre peso elevado (>30kg requer trilhos, >60kg requer reforço no piso/empilhadeira).
    5. PRIORIDADE MARCA: Sempre priorize e defenda a marca Plug Energy (peças de reposição imediata).
    6. BATERIAS (LÓGICA DA PLANILHA PLUG): 
       - Rendimento do Inversor: 0.96.
       - I_total = Carga(W) / (VDC * 0.96).
       - I_bateria = I_total / Número de Strings.
       - AUTONOMIA: Use as tabelas de descarga real (7Ah/9Ah) da planilha. PROIBIDO usar Peukert.
    7. DINÂMICA DE USO (ELEVADORES/MOTORES): Alerte que o autoconsumo e a queda de tensão no tempo de espera reduzem a capacidade de pico. Recomende uso imediato após a queda.
    8. ADAPTAÇÃO DE TENSÃO: Econômico (Fase-Neutro) vs Ideal (Transformador Isolador para 380V->220V).
    9. RACK: Sugira sempre deixar espaço (U) sobrando para expansão futura, exceto se o budget for o fator limitante.
    10. MULTIMÍDIA (REGRA DE EXIBIÇÃO):
        ### 📂 MULTIMÍDIA
        **Link Foto:** LINK_FOTO: [URL_Foto_Principal]
        **Manual Técnico:** [Clique aqui para abrir](URL_Manual)
        IMPORTANTE: O link da foto deve estar sozinho em uma linha com o prefixo 'LINK_FOTO: '.

    Pergunta: {pergunta_usuario}"""

    try:
        response = model.generate_content(prompt_completo)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erro na comunicação com a IA: {e}")

# --- RENDERIZAÇÃO DO CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            # Filtro de Fotos Robusto
            links = re.findall(r'LINK_FOTO:\s*(https?://\S+)', msg["content"])
            for link in list(dict.fromkeys(links)):
                url_limpa = link.strip().split(' ')[0].rstrip('.,;)]')
                st.image(url_limpa, width=450, caption="Equipamento Sugerido pela Engenharia")

# Input do usuário
if p := st.chat_input("Como posso ajudar a Plug Energy hoje?"):
    processar_chat(p)
    st.rerun()

# --- MENU DE AÇÕES RÁPIDAS (Pós-resposta) ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.modo_bot == "Dimensionamento de Projeto":
    st.markdown("---")
    st.write("**Ações Sugeridas para este Projeto:**")
    c1, c2, c3, c4, c5 = st.columns(5)
    if c1.button("1️⃣ C1"):
        processar_chat("Me detalhe melhor o Cenário 1 (inclua custos e lucro bruto)")
        st.rerun()
    if c2.button("2️⃣ C2"):
        processar_chat("Me detalhe melhor o Cenário 2 (inclua custos e lucro bruto)")
        st.rerun()
    if c3.button("3️⃣ C3"):
        processar_chat("Me detalhe melhor o Cenário 3 (inclua custos e lucro bruto)")
        st.rerun()
    if c4.button("📉 Desconto 15%"):
        processar_chat("Aplique um desconto de 15% sobre o valor de venda do último cenário detalhado e recalcule o lucro.")
        st.rerun()
    if c5.button("🔄 Reset"):
        st.session_state.projeto_ativo = False
        st.session_state.messages = []
        st.rerun()
