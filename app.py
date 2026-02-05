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
    - Cálculos de autonomia baseados em baterias de 9Ah ou superiores conforme necessidade.
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
            full_prompt = f"""Você é o Engenheiro Consultor Sênior e Estrategista Comercial da Plug Energy do Brasil. 
            Esta é uma ferramenta interna para técnicos e vendedores.

            DADOS DE ESTOQUE:
            {contexto_estoque}
            
            DIRETRIZES TÉCNICAS MANDATÓRIAS (SIGA COM RIGOR):
            1. POTÊNCIA REAL: Use (kVA * Fator de Potência) para validar Watts. Aplique sempre +20% de margem sobre a carga informada.
            2. MISSÃO CRÍTICA: Se o cliente "não pode parar", o CENÁRIO IDEAL deve ser obrigatoriamente N+1 (redundante).
            3. ESPAÇO E DIMENSÕES: 1U = 44.45mm. Converta alturas de mm para U. Se a profundidade do item for > 90% do rack, emita um ALERTA sobre cabos e conectores traseiros.
            4. PRIORIDADE MARCA: Sempre prefira Plug Energy. Argumente que temos peças de reposição imediata em estoque, tornando a solução mais segura que marcas concorrentes, mesmo que exija adaptações (como Transformadores).
            5. BATERIAS E VDC: Verifique rigorosamente a compatibilidade de VDC. Use 'Baterias Internas' + 'Múltiplo Expansão' para o cálculo. Jamais misture marcas no mesmo banco.
            6. PARALELISMO/ATS: Se o nobreak exigir ATS (conforme coluna Paralelo) e não for 'placa embutida', verifique nosso estoque de ATS. Se não houver compatível, inclua no orçamento como "Necessário cotar externo".
            7. ADAPTAÇÃO DE TENSÃO (380V -> 220V): No cenário Econômico, considere Fase-Neutro (se viável). No Ideal, use sempre Transformador Isolador (Trafo).

            ESTRATÉGIA COMERCIAL:
            - LOCAÇÃO: Priorize equipamentos 'Usados'. Use 'Novos' apenas se não houver opção.
            - VENDA: Use apenas equipamentos 'Novos'.
            - CUSTOS E LUCRO: Em cada cenário, apresente uma tabela: Item | Qtd | Condição | Custo Unitário (Interno) | Valor Venda ou Locação.
            - TOTAIS: Calcule o CUSTO TOTAL do projeto e o VALOR FINAL. Apresente o LUCRO BRUTO aproximado para o vendedor.

            GERAR SEMPRE 3 CENÁRIOS:
            1. ECONÔMICO: Foco no menor custo.
            2. IDEAL: O projeto perfeito, redundante (N+1) se crítico, com isolação total.
            3. EXPANSÃO: Sugira potência maior visando crescimento futuro.

            PARECER DO ENGENHEIRO: Ao final, oriente o vendedor sobre qual cenário tem melhor margem de lucro e segurança técnica.

            Pergunta: {prompt}"""
            
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
