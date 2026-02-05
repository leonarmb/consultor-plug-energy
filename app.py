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
    3. Para projetos de **Missão Crítica**, a redundância N+1 será a prioridade.
    
    **Notas Técnicas:**
    - Cálculos de autonomia baseados em baterias de 9Ah.
    - Prioridade para marca *Plug Energy* em todos os cenários.
    - Verificação de tensão (VDC) e compatibilidade elétrica integrada.
    """)

# 2. Configuração de Acesso via Secrets
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    LINK_PLANILHA = st.secrets["LINK_PLANILHA_ESTOQUE"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
except Exception as e:
    st.error("Erro de Configuração: Verifique as chaves nos Secrets.")
    st.stop()

# 3. Carregamento MULTI-ABA
@st.cache_data(ttl=60)
def carregar_estoque_total():
    try:
        dicionario_abas = pd.read_excel(LINK_PLANILHA, sheet_name=None, engine='openpyxl')
        texto_contexto = ""
        for nome_da_aba, df in dicionario_abas.items():
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all')
            if not df.empty:
                texto_contexto += f"\n\n--- CATEGORIA: {nome_da_aba.upper()} ---\n"
                texto_contexto += df.to_csv(index=False)
        return texto_contexto
    except Exception as e:
        st.error(f"Erro ao acessar a planilha: {e}")
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
        if contexto_estoque:
            full_prompt = f"""Você é o Engenheiro Consultor Sênior da Plug Energy do Brasil.
            Use os dados técnicos abaixo para sua análise:
            
            {contexto_estoque}
            
            DIRETRIZES DE ENGENHARIA E NEGÓCIO (MANDATÓRIAS):
            1. MARGEM E SEGURANÇA: Adicione +20% de margem sobre a carga real informada (W ou kVA). Respeite rigorosamente a potência calculada ao buscar no estoque (não sugira 10kVA para cargas de 3kVA sem justificativa extrema).
            2. REDUNDÂNCIA (N+1): Para clientes críticos (ISPs, Hospitais, Data Centers), sua 'Recomendação do Engenheiro' DEVE ser obrigatoriamente um sistema redundante N+1 (2 nobreaks dividindo a carga).
            3. COTAÇÃO IMEDIATA: Sempre apresente uma tabela com os valores de VENDA e LOCAÇÃO para os itens sugeridos já na primeira resposta.
            4. RIGOR TÉCNICO: Verifique tensão e VDC na planilha. Não assuma tensões; relate o que está nos dados oficiais.
            5. PRIORIDADE PLUG ENERGY: Priorize nossa marca em TODOS os cenários.
            6. REGRA DAS BATERIAS: Jamais misture marcas diferentes no mesmo banco. Isso é um selo de qualidade Plug Energy.
            7. FLEXIBILIDADE DE TENSÃO (380V -> 220V):
               - Se rede=380V e nobreak=220V, apresente duas opções: Profissional (Com Transformador) e Econômica (Fase-Neutro).
            8. DEFESA DA LOCAÇÃO: Sempre argumente por que a LOCAÇÃO é mais vantajosa (Manutenção e baterias inclusas).
            9. VALIDAÇÃO FÍSICA: Use os dados de U (altura) para garantir que a solução cabe no rack do cliente.

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
            st.error("Erro Crítico: Base de dados não carregada.")
