import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")

# --- INTERFACE VISUAL (LOGO E TÍTULO) ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Usando o link direto do servidor de média para evitar bloqueios de segurança
    url_logo = "https://www.plugenergy.com.br/wp-content/uploads/2021/05/logo-plug-energy.png"
    st.image(url_logo, use_container_width=True)

st.markdown("<h1 style='text-align: center;'>Consultor Técnico de Engenharia</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Inteligência Artificial aplicada a Nobreaks e Infraestrutura</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. Configuração de Acesso (Chaves de Segurança)
MINHA_API_KEY = "AIzaSyBqGtwQ6WRDs2z8hxzWHClqSRlqfwVz2WM"
MEU_LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3NB1lKiPMuDYGflHluFFb1mJF1A31VUTzSBHh5YJtrM7MrgJ6EnZ8a95LifdS9Y5khRbNB-GbrNv-/pub?output=csv"

try:
    genai.configure(api_key=MINHA_API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
except Exception as e:
    st.error(f"Erro na configuração da API: {e}")
    st.stop()

# 3. Carregamento do Estoque
@st.cache_data(ttl=300)
def carregar_dados():
    try:
        df = pd.read_csv(MEU_LINK_CSV)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

estoque_df = carregar_dados()

# 4. Construção da Inteligência
if estoque_df is not None:
    contexto_estoque = estoque_df.to_string(index=False)
    
    instrucoes_engenharia = f"""
    CONTEXTO E IDENTIDADE: Você é o Engenheiro Consultor de Vendas Sênior da Plug Energy do Brasil. 
    DADOS DE ESTOQUE: 
    {contexto_estoque}
    
    LOGICA DE ENGENHARIA:
    - Validação de Carga: + 20% de margem.
    - Upgrade: 1->3kVA e 6->10kVA.
    - Prioridade Comercial: Marca "Plug Energy" para LOCAÇÃO.
    - Missão Crítica: Sempre apresente um cenário N+1.
    """

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
                full_prompt = f"{instrucoes_engenharia}\n\nPergunta do usuário: {prompt}"
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro na resposta da IA: {e}")
else:
    st.warning("Aguardando sincronização com a base de dados.")
