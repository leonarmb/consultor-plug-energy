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
    - Verificação de tensão (VDC), dimensões (mm para U) e compatibilidade.
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
            # DEFINIÇÃO DO PROMPT ESTRATÉGICO PARA USO INTERNO (ATUALIZADO)
            full_prompt = f"""Você é o Engenheiro Consultor Sênior e Estrategista Comercial da Plug Energy do Brasil.
            Este bot é uma ferramenta INTERNA para vendedores e técnicos. Use os dados para preparar a melhor oferta técnica e comercial.

            DADOS TÉCNICOS:
            {contexto_estoque}
            
            DIRETRIZES TÉCNICAS MANDATÓRIAS:
            1. POTÊNCIA REAL: Calcule Watts = (kVA * Fator de Potência). Valide se suporta a carga + 20% de margem.
            2. DIMENSÕES (mm para U): Use a regra 1U = 44.45mm. Some as alturas e valide no rack do cliente.
            3. PROFUNDIDADE: Se o comprimento do equipamento for > 90% da profundidade do rack, alerte sobre o espaço para cabos/conexões traseiras.
            4. BATERIAS: Se a autonomia exigir mais baterias que o 'Capacidade Máx Interna', adicione o gabinete externo compatível (VDC igual). 
            5. PARALELO/ATS: Se o nobreak exigir ATS e não for 'placa embutida', inclua um ATS do estoque ou solicite cotação externa.
            6. PRIORIDADE PLUG ENERGY: Priorize nossa marca mesmo com adaptações (Trafo), pois temos estoque de peças para reposição imediata.
            7. RIGOR DE BATERIAS: Jamais misture marcas no mesmo banco (Selo de Qualidade Plug Energy).

            ESTRATÉGIA COMERCIAL INTERNA:
            - LOCAÇÃO: Priorize equipamentos 'Usados'. Se não houver, use 'Novos'.
            - VENDA: Use APENAS equipamentos 'Novos'.
            - TABELA DE CUSTOS: Para cada cenário, apresente: Item | Qtd | Condição | Custo Unitário (Interno) | Valor Venda ou Locação.
            - LUCRO: Ao final de cada tabela, calcule o LUCRO BRUTO (Valor Total - Custo Total).

            GERAR SEMPRE 3 CENÁRIOS:
            1. ECONÔMICO: Menor custo, pode usar Fase-Neutro (380V->220V) se viável, sem redundância.
            2. IDEAL: O projeto perfeito à prova de falhas. N+1 (se crítico), Isolação Galvânica via Trafo.
            3. EXPANSÃO (FUTURO): Sugira potência maior para crescimento do cliente em 12-24 meses.

            Parecer do Engenheiro: Ao final, aconselhe o vendedor sobre qual cenário focar baseado no 'feeling' do cliente e status do estoque de baterias.

            Pergunta do Vendedor/Técnico: {prompt}"""
            
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
