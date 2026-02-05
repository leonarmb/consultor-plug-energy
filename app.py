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

# 3. Carregamento MULTI-ABA Otimizado
@st.cache_data(ttl=60)
def carregar_estoque_total():
    try:
        url = st.secrets["LINK_PLANILHA_ESTOQUE"]
        
        # O pandas precisa do engine='openpyxl' para ler links de Excel (.xlsx)
        dicionario_abas = pd.read_excel(url, sheet_name=None, engine='openpyxl')
        
        texto_contexto = ""
        for nome_da_aba, df in dicionario_abas.items():
            # Limpa colunas e linhas fantasmas
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all')
            
            if not df.empty:
                texto_contexto += f"\n\n--- CATEGORIA: {nome_da_aba.upper()} ---\n"
                # Usamos CSV para o contexto da IA por ser mais leve que Excel
                texto_contexto += df.to_csv(index=False)
            
        return texto_contexto
    except Exception as e:
        # Exibe o erro exato para diagnóstico
        st.error(f"Erro ao acessar a planilha: {e}")
        return None

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
        Use os dados técnicos abaixo (extraídos de várias abas de estoque) para sua análise:
        
        {contexto_estoque}
        
        DIRETRIZES DE ENGENHARIA:
        - Aplique +20% de margem de carga sobre o que o usuário informar.
        - Verifique rigorosamente a tensão de Entrada/Saída e o VDC informados na planilha.
        - Não assuma uma tensão padrão; reporte exatamente o que consta nos dados.
        - Priorize a marca Plug Energy para locações.
        - Se o usuário pedir um sistema completo, procure itens nas abas de Racks, Baterias e Infraestrutura que sejam compatíveis.
        
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
