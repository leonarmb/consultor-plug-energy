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
    .stButton>button { width: 100%; border-radius: 5px; background-color: #262730; color: white; border: 1px solid #464b5d; }
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
if "projeto_ativo" not in st.session_state: st.session_state.projeto_ativo = False
if "dados_projeto" not in st.session_state: st.session_state.dados_projeto = ""
if "modo_bot" not in st.session_state: st.session_state.modo_bot = "Consulta Técnica"
if "messages" not in st.session_state: st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("Configurações")
    st.session_state.modo_bot = st.radio("Objetivo:", ["Consulta Técnica", "Dimensionamento de Projeto"])
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
        texto = ""
        for nome, df in dict_abas.items():
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all')
            texto += f"\n\n--- CATEGORIA: {nome.upper()} ---\n{df.to_csv(index=False)}"
        return texto
    except: return None

contexto_estoque = carregar_estoque()

# --- FUNÇÃO DE PROCESSAMENTO ---
def enviar_mensagem(texto_input):
    if st.session_state.modo_bot == "Dimensionamento de Projeto" and not st.session_state.projeto_ativo:
        st.session_state.projeto_ativo = True
        st.session_state.dados_projeto = texto_input

    st.session_state.messages.append({"role": "user", "content": texto_input})
    
    # Comportamento Dinâmico (Restaurando a complexidade do prompt)
    if st.session_state.modo_bot == "Consulta Técnica":
        instrucao_comportamento = "Responda de forma concisa e técnica apenas o que foi perguntado. Sem cenários."
    elif re.search(r'(cenário|cenario)\s*[1-3]', texto_input.lower()):
        num = re.findall(r'[1-3]', texto_input)[0]
        instrucao_comportamento = f"""O usuário ESCOLHEU detalhar o CENÁRIO {num} do PROJETO: {st.session_state.dados_projeto}.
        - Detalhe PROFUNDAMENTE apenas este cenário escolhido.
        - Apresente custos internos (Custo Unitário), Valor Final e LUCRO BRUTO.
        - Mantenha a modalidade (Venda ou Locação) e use os equipamentos citados no histórico para este cenário {num}."""
    else:
        instrucao_comportamento = """Atue como Engenheiro e Estrategista Comercial.
        - Apresente 3 CENÁRIOS: ECONÔMICO (menor custo), IDEAL (redundante N+1) e EXPANSÃO (mais que perfeito/futuro).
        - Crie UMA TABELA POR CENÁRIO com o Valor Total logo abaixo de cada uma.
        - DICA DE RACK: Sugira sempre deixar espaço (U) sobrando para expansão futura."""

    full_prompt = f"""Você é o Engenheiro Consultor Sênior e Estrategista Comercial da Plug Energy do Brasil. 
    Esta é uma ferramenta interna para técnicos e vendedores.

    {instrucao_comportamento}

    DADOS DE ESTOQUE:
    {contexto_estoque}
    
    DIRETRIZES TÉCNICAS MANDATÓRIAS (SIGA COM RIGOR):
    1. POTÊNCIA REAL: Watts = (kVA * Fator de Potência). Aplique +20% de margem sobre a carga.
    2. MISSÃO CRÍTICA: Se o cliente "não pode parar", o CENÁRIO IDEAL deve ser N+1 (redundante).
    3. ESPAÇO E DIMENSÕES: 1U = 44.45mm. Converta alturas para U. Se profundidade > 90% do rack, ALERTE sobre cabos traseiros.
    4. PESO E LOGÍSTICA: Verifique a coluna 'Peso (kg)'. Emita um ALERTA LOGÍSTICO (necessidade de mais pessoas, empilhadeira ou reforço no rack).
    5. PRIORIDADE MARCA: Sempre prefira Plug Energy (temos peças de reposição imediata).
    6. BATERIAS (LÓGICA DA PLANILHA): Rendimento 0.96. I_total = W / (VDC * 0.96). I_bat = I_total / Strings. Use tabelas de descarga real da planilha (7Ah/9Ah). NÃO use Peukert.
    7. DINÂMICA DE USO: Em elevadores/motores, alerte sobre autoconsumo e queda de tensão no tempo de espera. Recomende uso imediato.
    8. PARALELISMO/ATS: Verifique estoque de ATS se o nobreak não tiver placa embutida.
    9. ADAPTAÇÃO DE TENSÃO (380V -> 220V): Econômico (Fase-Neutro) vs Ideal (Transformador Isolador).
    10. MULTIMÍDIA: 
        Organize os links exatamente assim:
        ### 📂 MULTIMÍDIA
        **Link Foto:** LINK_FOTO: [URL_Foto_Principal]
        **Manual Técnico:** [Clique aqui para abrir o Manual](URL_Manual)
        Exiba apenas a 'URL_Foto_Principal'. Traseira/Frente apenas se pedido.
        REGRA: Escreva o link da imagem sozinho em uma linha com o prefixo 'LINK_FOTO: '.

    ESTRATÉGIA COMERCIAL: Cenários Econômico, Ideal e Expansão.
    TABELA DE CUSTOS: Item | Qtd | Condição | Custo Unitário | Valor Venda ou Locação.
    PARECER DO ENGENHEIRO: Finalize com conselho de venda e alertas de segurança/peso/rack.

    Pergunta: {texto_input}"""

    try:
        response = model.generate_content(full_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Erro na IA: {e}")

# --- RENDERIZAÇÃO DO CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            links = re.findall(r'LINK_FOTO:\s*(https?://\S+)', msg["content"])
            for link in list(dict.fromkeys(links)):
                # Limpa a URL de caracteres residuais (pontos, parênteses)
                clean_url = link.strip().split(' ')[0].rstrip('.,;)]')
                st.image(clean_url, width=450, caption="Equipamento Sugerido")

# Chat Input
if p := st.chat_input("Como posso ajudar a Plug Energy hoje?"):
    enviar_mensagem(p)
    st.rerun()

# --- BOTÕES DE AÇÃO ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and st.session_state.modo_bot == "Dimensionamento de Projeto":
    st.markdown("---")
    st.write("**Ações Rápidas para este Projeto:**")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("1️⃣ Detalhar C1"):
        enviar_mensagem("Me detalhe melhor o Cenário 1 (custos e lucro)")
        st.rerun()
    if c2.button("2️⃣ Detalhar C2"):
        enviar_mensagem("Me detalhe melhor o Cenário 2 (custos e lucro)")
        st.rerun()
    if c3.button("3️⃣ Detalhar C3"):
        enviar_mensagem("Me detalhe melhor o Cenário 3 (custos e lucro)")
        st.rerun()
    if c4.button("🔄 Novo Projeto"):
        st.session_state.projeto_ativo = False
        st.session_state.messages = []
        st.rerun()}")
