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
        # Carrega o logo que você subiu no GitHub
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
    3. Para projetos de **Missão Crítica**, solicite uma análise de redundância N+1.
    
    **Notas Técnicas:**
    - Cálculos de autonomia baseados em baterias de 9Ah.
    - Prioridade para marca *Plug Energy* em contratos de locação.
    - Verificação de tensão (VDC) e compatibilidade elétrica integrada.
    """)

# 2. Configuração de Acesso via Secrets (Proteção contra Bloqueio)
try:
    # Agora o sistema busca as chaves nos Secrets do Streamlit
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_CSV = st.secrets["LINK_PLANILHA_ESTOQUE"]
    
    genai.configure(api_key=API_KEY)
    # RESTAURADO: Gemini 3.0 Flash Preview
    model = genai.GenerativeModel('gemini-3-flash-preview')
except Exception as e:
    st.error("Erro de Configuração: Certifique-se de que a 'GOOGLE_API_KEY' nova está nos Secrets do Streamlit.")
    st.stop()

# 3. Carregamento MULTI-ABA (Lê todo o Excel vivo)
@st.cache_data(ttl=60) # Atualiza a cada 60 segundos
def carregar_estoque_total():
    try:
        url = st.secrets["LINK_PLANILHA_ESTOQUE"]
        # Lê todas as abas e cria um dicionário de DataFrames
        dicionario_abas = pd.read_excel(url, sheet_name=None)
        
        texto_contexto = ""
        for nome_da_aba, df in dicionario_abas.items():
            # Limpa colunas vazias
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all')
            
            # Adiciona o conteúdo da aba ao contexto
            texto_contexto += f"\n\n--- ABA: {nome_da_aba.upper()} ---\n"
            texto_contexto += df.to_csv(index=False)
            
        return texto_contexto
    except Exception as e:
        st.error(f"Erro ao ler o Excel vivo: {e}. Verifique o link e as permissões.")
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
        # COMPACTAÇÃO TÉCNICA: Enviamos em CSV para manter dados de dimensões e custos 
        # ocupando 40% menos tokens que o formato de texto comum.
        contexto_csv = estoque_df.to_csv(index=False)
        
        full_prompt = f"""Você é o Engenheiro Consultor Sênior da Plug Energy do Brasil.
        Analise o estoque abaixo com rigor técnico (considere VDC, Dimensões e Custos para suas análises):
        
        {contexto_csv}
        
        DIRETRIZES:
        - Aplique +20% de margem de carga.
        - Verifique compatibilidade de tensão (Entrada/Saída).
        - Para locação, priorize marca Plug Energy.
        - Use os dados de dimensões para validar instalações em racks quando solicitado.
        
        Pergunta do Usuário: {prompt}"""
        
        placeholder = st.empty()
        full_response = ""
        
        try:
            # STREAMING ATIVADO: A resposta aparece enquanto é gerada
            response = model.generate_content(full_prompt, stream=True)
            for chunk in response:
                full_response += chunk.text
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Erro na comunicação: Sua chave nova pode estar demorando a propagar ou o limite de tokens foi atingido. Detalhe: {e}")
