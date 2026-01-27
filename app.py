import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")
st.title("🔋 Consultor Técnico Plug Energy")

# 2. Inicialização de Segurança e Dados
if "messages" not in st.session_state:
    st.session_state.messages = []

try:
    # Busca as chaves do Secrets
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_CSV = st.secrets["LINK_PLANILHA_ESTOQUE"]
    
    # Configuração Global da IA
    genai.configure(api_key=API_KEY)
    
    # Definição do Modelo (Nome simplificado para evitar erro 404 v1beta)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
except Exception as e:
    st.error(f"Erro de configuração inicial: {e}")
    st.stop()

# 3. Função para Carregar Estoque
@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # Lendo a planilha publicada
        df = pd.read_csv(LINK_CSV)
        return df
    except Exception as e:
        st.error(f"Não consegui ler os dados da planilha: {e}")
        return None

estoque_df = carregar_dados()

# 4. Construção da Inteligência do Bot
if estoque_df is not None:
    # Transformamos o estoque em texto para a IA ler
    contexto_estoque = estoque_df.to_string(index=False)
    
    instrucoes_engenharia = f"""
    Você é o Engenheiro Consultor da Plug Energy. 
    Use os dados abaixo para orçamentos e consultoria técnica:
    
    ESTOQUE E PREÇOS ATUAIS:
    {contexto_estoque}
    
    REGRAS DE OURO:
    1. SEGURANÇA: Sempre adicione 20% de margem sobre a carga informada.
    2. UPGRADE: Se o cliente precisar de 1kVA e não houver, ofereça 3kVA. O mesmo para 6kVA -> 10kVA.
    3. FINANCEIRO: Calcule Custo vs Venda e informe a margem de lucro apenas se o tom da conversa for de gestão/diretoria.
    4. CENÁRIOS: Apresente sempre: 1. Econômico, 2. Recomendado e 3. Missão Crítica (N+1).
    """

    # 5. Interface do Chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Como posso ajudar a Plug Energy hoje?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Criando a resposta
                full_query = f"{instrucoes_engenharia}\n\nPergunta do usuário: {prompt}"
                response = model.generate_content(full_query)
                
                resposta_texto = response.text
                st.markdown(resposta_texto)
                st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
            except Exception as e:
                # Caso o erro 404 persista, ele mostrará uma dica amigável
                if "404" in str(e):
                    st.error("Erro 404: O Google ainda não reconheceu este modelo para sua chave. Tente aguardar 5 minutos ou verifique se o modelo está ativo no seu AI Studio.")
                else:
                    st.error(f"Ocorreu um erro na IA: {e}")
else:
    st.warning("
