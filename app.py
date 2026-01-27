import streamlit as st
import google.generativeai as genai
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")

# Exibição do Logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo_plugenergy.png", use_container_width=True)

st.markdown("<h1 style='text-align: center;'>Consultor Técnico de Engenharia</h1>", unsafe_allow_html=True)
st.markdown("---")

# BUSCA A CHAVE DE FORMA SEGURA (Configurada no menu Secrets do Streamlit)
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_CSV = st.secrets["LINK_PLANILHA_ESTOQUE"]
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erro de Segurança: Configure a 'GOOGLE_API_KEY' nos Secrets do Streamlit.")
    st.stop()

# Carregamento de Dados (Mantendo 100% das suas colunas e dimensões)
@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv(LINK_CSV)
        return df
    except:
        return None

estoque_df = carregar_dados()

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
        # Enviamos os dados em formato CSV para economizar tokens sem perder informação
        contexto_csv = estoque_df.to_csv(index=False)
        
        full_prompt = f"Você é o Engenheiro Sênior da Plug Energy. Analise o estoque completo: \n\n{contexto_csv}\n\nPergunta: {prompt}"
        
        placeholder = st.empty()
        full_response = ""
        
        try:
            response = model.generate_content(full_prompt, stream=True)
            for chunk in response:
                full_response += chunk.text
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Erro na resposta: {e}")
