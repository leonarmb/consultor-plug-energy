import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")

# --- INTERFACE VISUAL (LOGO E TÍTULO) ---
@st.cache_data
def exibir_cabecalho():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo_plugenergy.png", use_container_width=True)
    st.markdown("<h1 style='text-align: center;'>Consultor Técnico de Engenharia</h1>", unsafe_allow_html=True)
    st.markdown("---")

exibir_cabecalho()

# --- GUIA DE USO (EXPANSÍVEL) ---
with st.expander("📖 Orientações de Uso e Regras de Engenharia"):
    st.info("""
    **Como utilizar:**
    1. Descreva a carga total ou o modelo de nobreak desejado.
    2. O sistema aplicará automaticamente **20% de margem** sobre a carga.
    3. Para projetos de **Missão Crítica**, a redundância N+1 será a prioridade.
    
    **Notas Técnicas:**
    - Cálculos de autonomia baseados em baterias de 9Ah.
    - Prioridade para marca *Plug Energy* em todos os cenários.
    - Verificação de tensão (VDC) e compatibilidade elétrica integrada.
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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if contexto_estoque:
            full_prompt = f"""Você é o Engenheiro Consultor Sênior e Estrategista Comercial da Plug Energy do Brasil.
            Este bot é uma ferramenta INTERNA para vendedores e técnicos. Sua missão é preparar o vendedor com as melhores opções antes da proposta final.

            DADOS TÉCNICOS:
            {contexto_estoque}
            
            DIRETRIZES DE RESPOSTA (GERAR SEMPRE 3 CENÁRIOS):
            
            1. CENÁRIO ECONÔMICO: Foco no menor custo. Sem redundância, conexão Fase-Neutro (se possível) e baterias estritamente para o tempo solicitado.
            2. CENÁRIO IDEAL: A solução técnica perfeita. Redundância N+1 (se for missão crítica), isolação galvânica via Transformador e margem de 20%. É o cenário "à prova de falhas".
            3. CENÁRIO EXPANSÃO (FUTURO): Sugira um Nobreak de maior potência (ex: se pediu 3kVA, sugira 6kVA ou 10kVA). Argumente sobre escalabilidade e evitar novos gastos com infraestrutura em 12-24 meses.

            REGRAS MANDATÓRIAS:
            - TABELA DE CUSTOS: Para CADA cenário, apresente uma tabela com itens, valor de VENDA TOTAL e valor de LOCAÇÃO TOTAL.
            - RIGOR DE BATERIAS: Jamais misture marcas no mesmo banco (Selo Plug Energy).
            - PARECER DO ENGENHEIRO: Ao final, escreva um parágrafo aconselhando o vendedor sobre qual cenário ele deve enfatizar baseado no perfil do cliente descrito.
            - PRIORIDADE PLUG ENERGY: Priorize nossa marca em todos os itens.
            - VALIDAÇÃO DE ESPAÇO: Verifique se cada cenário cabe no rack/espaço informado.

            Pergunta do Vendedor/Técnico: {prompt}"""
            
            try:
                response = model.generate_content(full_prompt, stream=True)
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Erro na comunicação com a IA: {e}")
        else:
            st.error("Erro Crítico: Base de dados não carregada.")
