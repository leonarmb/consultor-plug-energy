import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Configuração da Página e Identidade Visual
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")
st.title("🔋 Consultor Técnico Plug Energy")

# 2. Conexão Segura com API
try:
    # Busca as chaves cadastradas nos Secrets do Streamlit
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_CSV = st.secrets["LINK_PLANILHA_ESTOQUE"]
    
    genai.configure(api_key=API_KEY)
    
    # Modelo Gemini 3 Flash (Alta velocidade e precisão)
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
except Exception as e:
    st.error("Erro ao carregar chaves de segurança. Verifique os Secrets no Streamlit.")
    st.stop()

# 3. Carregamento Inteligente de Estoque
@st.cache_data(ttl=600)
def carregar_dados():
    try:
        return pd.read_csv(LINK_CSV)
    except Exception:
        return None

estoque_df = carregar_dados()

# 4. Prompt de Engenharia (A "Mente" do Bot)
if estoque_df is not None:
    contexto_estoque = estoque_df.to_string(index=False)
    
    instrucoes_engenharia = f"""
    CONTEXTO: Você é o Engenheiro Consultor Sênior da Plug Energy do Brasil.
    ESTOQUE ATUALIZADO: {contexto_estoque}
    
    DIRETRIZES TÉCNICAS:
    - Aplique sempre +20% de margem de segurança sobre a carga do cliente.
    - Se a carga + margem ultrapassar a potência do nobreak, sugira upgrade ou paralelismo.
    - Use a lógica de bateria 9Ah para cálculos de autonomia.
    - PRIORIDADE COMERCIAL: Marca Plug Energy para Locação.
    - MISSÃO CRÍTICA: Ofereça Redundância N+1 (Paralelismo).
    """

    # Interface de Chat
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
            try:
                full_prompt = f"{instrucoes_engenharia}\n\nPergunta: {prompt}"
                response = model.generate_content(full_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro na resposta da IA: {e}")
else:
    st.warning("Aguardando sincronização com a planilha de estoque...")
