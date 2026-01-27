import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")
st.title("🔋 Consultor Técnico Plug Energy")

# 2. Configuração de Acesso (Chaves Diretas)
# Substituindo pelas suas chaves reais conforme solicitado
MINHA_API_KEY = "AIzaSyBqGtwQ6WRDs2z8hxzWHClqSRlqfwVz2WM"
MEU_LINK_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ3NB1lKiPMuDYGflHluFFb1mJF1A31VUTzSBHh5YJtrM7MrgJ6EnZ8a95LifdS9Y5khRbNB-GbrNv-/pub?output=csv"

try:
    # Configura a IA com a sua chave do projeto BOTPLUGENERGY
    genai.configure(api_key=MINHA_API_KEY)
    
    # Define o modelo Gemini 3 (ajustado conforme o seu Playground)
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

# 4. Inteligência do Consultor
if estoque_df is not None:
    contexto_estoque = estoque_df.to_string(index=False)
    
    # Suas instruções de Engenharia do Playground
    instrucoes_engenharia = f"""
    CONTEXTO E IDENTIDADE: Você é o Engenheiro Consultor de Vendas Sênior da Plug Energy do Brasil. 
    DADOS DE ESTOQUE: {contexto_estoque}
    
    LOGICA DE ENGENHARIA:
    - Validação de Carga: Considere Consumo Total + 20% de margem.
    - Autonomia: Use a tabela de descarga de 9Ah para cálculos.
    - Upgrade: Lógica 1->3kVA e 6->10kVA (Entrega maior pelo preço do menor se necessário).
    - Prioridade: Para locação, ofereça sempre marca "Plug Energy".
    - Missão Crítica: Sempre ofereça cenário de redundância N+1.
    """

    # 5. Interface de Chat
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
                # Gerando a resposta com Gemini 3
                full_prompt = f"{instrucoes_engenharia}\n\nUsuário enviou os seguintes dados: {prompt}"
                response = model.generate_content(full_prompt)
                
                resposta_texto = response.text
                st.markdown(resposta_texto)
                st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
            except Exception as e:
                st.error(f"Erro na resposta da IA: {e}")
else:
    st.warning("Verifique o link do CSV. O sistema não conseguiu ler os dados.")
