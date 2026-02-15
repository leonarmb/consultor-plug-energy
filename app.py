import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")

# --- FORÇAR MODO ESCURO E ESTILO (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stMarkdown table { color: #fafafa; }
    h1, h2, h3, hr { color: #ffffff !important; }
    /* Estilização do seletor de modo */
    .stRadio [data-testid="stWidgetLabel"] p { color: #ffffff; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- INTERFACE VISUAL (LOGO E TÍTULO) ---
@st.cache_data
def exibir_cabecalho():
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.image("logo_plugenergy_invert.png", use_container_width=True)
    st.markdown("<h1 style='text-align: center;'>Consultor Técnico de Engenharia</h1>", unsafe_allow_html=True)
    st.markdown("---")

exibir_cabecalho()

# --- SELETOR DE MODO DE OPERAÇÃO ---
if "modo_bot" not in st.session_state:
    st.session_state.modo_bot = "Consulta Técnica"

st.sidebar.title("Configurações do Bot")
modo_escolhido = st.sidebar.radio(
    "Selecione o objetivo da conversa:",
    ["Consulta Técnica", "Dimensionamento de Projeto"],
    index=0 if st.session_state.modo_bot == "Consulta Técnica" else 1
)
st.session_state.modo_bot = modo_escolhido

# --- GUIA DE USO (EXPANSÍVEL) ---
with st.expander("📖 Orientações de Uso e Regras de Engenharia"):
    st.info(f"**Modo Ativo:** {st.session_state.modo_bot}")
    st.write("""
    1. **Consulta Técnica:** Respostas diretas sobre estoque, preços e dúvidas pontuais.
    2. **Dimensionamento:** Análise estratégica em 3 níveis (Económico, Ideal e Expansão).
    """)

# 2. Configuração de Acesso via Secrets
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_PLANILHA = st.secrets["LINK_PLANILHA_ESTOQUE"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
except Exception as e:
    st.error("Erro de Configuração: Verifique as chaves nos Secrets.")
    st.stop()

# 3. Carregamento MULTI-ABA
@st.cache_data(ttl=60)
def carregar_estoque_total():
    try:
        dicionario_abas = pd.read_excel(LINK_PLANILHA, sheet_name=None, engine='openpyxl')
        texto_contexto = ""
        for nome_da_aba, df in dicionario_abas.items():
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all')
            if not df.empty:
                texto_contexto += f"\n\n--- CATEGORIA: {nome_da_aba.upper()} ---\n"
                texto_contexto += df.to_csv(index=False)
        return texto_contexto
    except Exception as e:
        st.error(f"Erro ao acessar a planilha: {e}")
        return None

contexto_estoque = carregar_estoque_total()

# 4. Interface de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Como posso ajudar a Plug Energy hoje?"):
    # Alternância automática de modo
    if "projeto" in prompt.lower() and st.session_state.modo_bot == "Consulta Técnica":
        st.session_state.modo_bot = "Dimensionamento de Projeto"
        st.info("Alternando para modo 'Dimensionamento de Projeto'.")
    elif ("estoque" in prompt.lower() or "informação" in prompt.lower()) and st.session_state.modo_bot == "Dimensionamento de Projeto":
        st.session_state.modo_bot = "Consulta Técnica"
        st.info("Alternando para modo 'Consulta Técnica'.")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if contexto_estoque:
            # --- LÓGICA DE COMPORTAMENTO DINÂMICO ---
            if st.session_state.modo_bot == "Consulta Técnica":
                instrucao_comportamento = "Responda de forma concisa apenas o que foi perguntado. NÃO crie cenários."
            else:
                # Se o usuário escolhe um cenário, muda para modo detalhamento
                if re.search(r'(cenário|cenario)\s*[1-3]', prompt.lower()):
                    instrucao_comportamento = """O usuário escolheu um cenário específico. 
                    - Detalhe PROFUNDAMENTE apenas este cenário.
                    - Apresente custos internos (Custo Unitário), valor final e LUCRO BRUTO.
                    - Reitere fotos e manuais. Trate o vendedor como parceiro de estratégia."""
                else:
                    instrucao_comportamento = """Atue como Engenheiro e Estrategista.
                    - Apresente 3 CENÁRIOS: ECONÔMICO (baixo custo), IDEAL (redundante N+1) e EXPANSÃO (mais que perfeito/futuro).
                    - Crie UMA TABELA POR CENÁRIO com o Total logo abaixo de cada uma.
                    - DICA DE RACK: Sugira deixar espaço (U) para expansão, exceto se o budget for crítico."""

            full_prompt = f"""Você é o Engenheiro Consultor e Estrategista Comercial da Plug Energy do Brasil. 
            DADOS DE ESTOQUE: {contexto_estoque}
            
            {instrucao_comportamento}

            DIRETRIZES TÉCNICAS MANDATÓRIAS (SIGA COM RIGOR):
            1. POTÊNCIA REAL: Watts = (kVA * Fator de Potência). Aplique +20% de margem.
            2. MISSÃO CRÍTICA: Prioridade para redundância N+1 (ATS ou paralelismo).
            3. ESPAÇO: 1U = 44.45mm. Alerta de profundidade > 90% do rack.
            4. LOGÍSTICA: Alerta de peso elevado (reforço de rack).
            5. MARCA: Preferência Plug Energy.
            6. BATERIAS (PLANILHA): Rendimento 0.96. I_total = W / (VDC * 0.96). I_bat = I_total / Strings. Use tabelas de descarga real (7Ah/9Ah). NÃO use Peukert.
            7. DINÂMICA DE USO: Em elevadores/motores, alerte sobre autoconsumo e queda de tensão no tempo de espera. Recomende uso imediato após queda.
            8. PARALELISMO/ATS: Verifique estoque de ATS se necessário.
            9. TENSÃO: Econômico (Fase-Neutro) vs Ideal (Transformador Isolador).
            10. MULTIMÍDIA (EXIBIÇÃO OBRIGATÓRIA): 
                - O link da foto DEVE estar em uma linha isolada com o prefixo 'LINK_FOTO: '.
                - Formato: ### 📂 MULTIMÍDIA
                **Link Foto:** LINK_FOTO: [URL_Foto_Principal]
                **Manual:** [Clique aqui](URL_Manual)

            Pergunta: {prompt}"""
            
            placeholder = st.empty()
            full_response = ""
            
            try:
                response = model.generate_content(full_prompt, stream=True)
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                
                # --- EXIBIÇÃO DE FOTOS ---
                links_fotos = re.findall(r'LINK_FOTO:\s*(https?://\S+)', full_response)
                if links_fotos:
                    for link in list(dict.fromkeys(links_fotos)):
                        st.image(link.strip().rstrip('.,;)]'), width=450, caption="Equipamento Sugerido")

                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Erro: {e}")
        else:
            st.error("Erro: Base de dados não carregada.")
