import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋")
st.title("🔋 Consultor Técnico Plug Energy")

# 2. Segurança e Configuração da API
try:
    # Busca as chaves diretamente do Secrets
    minha_chave = st.secrets["GOOGLE_API_KEY"]
    link_estoque = st.secrets["LINK_PLANILHA_ESTOQUE"]
    
    genai.configure(api_key=minha_chave)
except Exception as e:
    st.error(f"Erro ao carregar configurações: {e}")
    st.stop()

# 3. Carregamento dos Dados
@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv(link_estoque)
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

estoque_raw = carregar_dados()

# 4. Inicialização do Modelo
# Se models/gemini-1.5-flash falhar, o código tentará o gemini-1.5-flash puro
try:
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except:
    model = genai.GenerativeModel('gemini-1.5-flash')

if estoque_raw is not None:
    system_instruction = f"""
    Você é o Engenheiro Consultor Sênior da Plug Energy. 
    Seu objetivo é gerar orçamentos e validar visitas técnicas.

    DADOS DE ESTOQUE E PREÇOS:
    {estoque_raw.to_string()}

    REGRAS DE NEGÓCIO:
    1. MARGEM: Carga + 20% de segurança.
    2. UPGRADE: 1-3kVA e 6-10kVA (valor do menor no maior se necessário).
    3. AUTONOMIA: Use a lógica de bateria 9Ah (120min=2.78A, 240min=1.77A).
    4. FINANCEIRO: Calcule o Custo Total vs Venda/Locação e informe a margem de lucro apenas se solicitado.
    5. CENÁRIOS: Econômico, Recomendado e Redundância N+1.
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
                # Chamada simplificada da API
                response = model.generate_content(system_instruction + "\n\nPergunta: " + prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erro na resposta da IA: {e}")
else:
    st.warning("Aguardando carregamento dos dados da planilha...")
