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

# 2. Configuração de Acesso via Secrets
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    # Configuramos o link que será usado na função de carga
    LINK_PLANILHA = st.secrets["LINK_PLANILHA_ESTOQUE"]
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
except Exception as e:
    st.error("Erro de Configuração: Certifique-se de que as chaves estão nos Secrets do Streamlit.")
    st.stop()

# 3. Carregamento MULTI-ABA (Lê todo o Excel vivo)
@st.cache_data(ttl=60)
def carregar_estoque_total():
    try:
        # O pandas precisa do engine='openpyxl' para ler .xlsx direto da web
        dicionario_abas = pd.read_excel(LINK_PLANILHA, sheet_name=None, engine='openpyxl')
        
        texto_contexto = ""
        for nome_da_aba, df in dicionario_abas.items():
            # Limpa colunas e linhas vazias
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all')
            
            if not df.empty:
                texto_contexto += f"\n\n--- CATEGORIA: {nome_da_aba.upper()} ---\n"
                # Transformamos cada aba em CSV para a IA ler de forma leve
                texto_contexto += df.to_csv(index=False)
            
        return texto_contexto
    except Exception as e:
        st.error(f"Erro ao acessar a planilha: {e}")
        return None

# Chamada da função para carregar os dados
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
        # SEGURANÇA: Só prossegue se o estoque foi carregado
        if contexto_estoque:
with st.chat_message("assistant"):
        if contexto_estoque:
            full_prompt = f"""Você é o Engenheiro Consultor Sênior da Plug Energy do Brasil.
            Use os dados técnicos abaixo (que abrangem Nobreaks, Baterias, Racks e Infraestrutura):
            
            {contexto_estoque}
            
            DIRETRIZES DE ENGENHARIA E NEGÓCIO:
            1. MARGEM E SEGURANÇA: Adicione sempre +20% de margem sobre a carga informada.
            2. RIGOR TÉCNICO: Verifique rigorosamente a tensão de Entrada/Saída e o VDC na planilha. Não assuma tensões padrão; reporte exatamente o que consta nos dados.
            3. PRIORIDADE DE MARCA: Priorize a marca Plug Energy em TODOS os cenários (Venda e Locação). Só sugira outras marcas se não houver um modelo Plug Energy compatível.
            4. PENSAMENTO DE SISTEMA: Se o usuário pedir um sistema ou houver divergência de tensão, procure itens compatíveis nas abas de Racks, Baterias, Transformadores e Infraestrutura.
            5. ESTRATÉGIA COMERCIAL: Sempre que o cliente solicitar COMPRA, apresente os valores de venda, mas argumente em seguida que a LOCAÇÃO é mais vantajosa (Manutenção inclusa, troca de baterias sem custo, suporte 24h e preservação de caixa).
            6. MISSÃO CRÍTICA: Para Provedores (ISPs), Hospitais ou Data Centers, sugira sempre redundância N+1.
            
            Pergunta do Usuário: {prompt}"""
            
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
                st.error(f"Erro na comunicação com a IA: {e}")
        else:
            st.error("Erro Crítico: Não foi possível ler a base de dados. Verifique o link no Secrets.")
