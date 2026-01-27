import streamlit as st
import google.generativeai as genai
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋")
st.title("🔋 Consultor Técnico Plug Energy")

# --- ÁREA DE SEGURANÇA (SECRETS) ---
# No Streamlit Cloud, você cadastrará sua API_KEY e o LINK_CSV nos 'Secrets'
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    LINK_CSV = st.secrets["LINK_PLANILHA_ESTOQUE"]
except:
    st.error("Erro: API Key ou Link da Planilha não configurados nos Secrets.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=600) # Atualiza o estoque a cada 10 minutos
def carregar_estoque():
    # O link deve ser o link de publicação CSV do Google Sheets
    df = pd.read_csv(LINK_CSV)
    return df

estoque_raw = carregar_estoque()

# --- CONFIGURAÇÃO DO BOT ---
model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
if not st.secrets["GOOGLE_API_KEY"]:
    st.error("Chave API não encontrada nos Secrets!")

system_instruction = f"""
Você é o Engenheiro Consultor Sênior da Plug Energy. 
Seu objetivo é gerar orçamentos e validar visitas técnicas.

DADOS DE ESTOQUE E PREÇOS:
{estoque_raw.to_string()}

REGRAS DE NEGÓCIO:
1. MARGEM: Carga + 20% de segurança.
2. UPGRADE: 1-3kVA e 6-10kVA (valor do menor no maior se necessário).
3. AUTONOMIA: Use a lógica de bateria 9Ah (120min=2.78A, 240min=1.77A).
4. FINANCEIRO: Calcule o Custo Total vs Venda/Locação e informe a margem de lucro apenas se solicitado pelo administrador (identifique pelo tom da conversa).
5. CENÁRIOS: Sempre apresente 3 opções: Econômico, Recomendado (Plug Energy) e Missão Crítica (Redundância N+1).
"""

# --- INTERFACE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Cole os dados da visita ou peça um orçamento..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_prompt = f"{system_instruction}\n\nUsuário diz: {prompt}"
        response = model.generate_content(full_prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
