import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")

# --- FORÇAR MODO ESCURO E ESTILO (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stMarkdown table { color: #fafafa; }
    h1, h2, h3, hr { color: #ffffff !important; }
    /* Estilização do seletor de modo */
    .stRadio [data-testid="stWidgetLabel"] p { color: #ffffff; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- INTERFACE VISUAL (LOGO E TÍTULO) ---
@st.cache_data
def exibir_cabecalho():
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.image("logo_plugenergy_invert.png", use_container_width=True)
    st.markdown("<h1 style='text-align: center;'>Consultor Técnico de Engenharia</h1>", unsafe_allow_html=True)
    st.markdown("---")

exibir_cabecalho()

# --- SELETOR DE MODO DE OPERAÇÃO ---
if "modo_bot" not in st.session_state:
    st.session_state.modo_bot = "Consulta Técnica"

st.sidebar.title("Configurações do Bot")
modo_escolhido = st.sidebar.radio(
    "Selecione o objetivo da conversa:",
    ["Consulta Técnica", "Dimensionamento de Projeto"],
    index=0 if st.session_state.modo_bot == "Consulta Técnica" else 1
)
st.session_state.modo_bot = modo_escolhido

# --- GUIA DE USO (EXPANSÍVEL) ---
with st.expander("📖 Orientações de Uso e Regras de Engenharia"):
    st.info(f"**Modo Ativo:** {st.session_state.modo_bot}")
    st.write("""
    1. **Consulta Técnica:** Respostas diretas sobre estoque, preços e dúvidas pontuais.
    2. **Dimensionamento:** Análise estratégica em 3 níveis (Económico, Ideal e Expansão).
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
    if "projeto" in prompt.lower() and st.session_state.modo_bot == "Consulta Técnica":
        st.session_state.modo_bot = "Dimensionamento de Projeto"
        st.info("Alternando automaticamente para modo 'Dimensionamento de Projeto'.")
    elif ("estoque" in prompt.lower() or "informação" in prompt.lower()) and st.session_state.modo_bot == "Dimensionamento de Projeto":
        st.session_state.modo_bot = "Consulta Técnica"
        st.info("Alternando automaticamente para modo 'Consulta Técnica'.")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if contexto_estoque:
            if st.session_state.modo_bot == "Consulta Técnica":
                instrucao_comportamento = """
                COMPORTAMENTO: Responda de forma direta e concisa apenas o que foi perguntado. 
                - Se pedirem estoque, informe apenas quantidades e estados (novo/usado).
                - Se pedirem sobre um modelo, resuma as características cruciais e OBSERVAÇÕES.
                - NÃO crie os 3 cenários comerciais nem tabelas financeiras completas.
                - Siga rigorosamente as regras de engenharia para tirar dúvidas pontuais.
                """
            else:
                instrucao_comportamento = """
                COMPORTAMENTO: Atue como Consultor de Projetos e Estrategista Comercial da Plug Energy.
                Apresente sempre a ESTRATÉGIA COMERCIAL EM 3 CENÁRIOS:
                1. ECONÔMICO: Menor custo inicial, sem redundância.
                2. IDEAL: Atendimento perfeito das necessidades atuais. Inclua redundância (N+1) se for Missão Crítica.
                3. EXPANSÃO (MAIS QUE IDEAL/PERFEITO): Mantém a redundância do ideal, mas com potência superior para suportar o crescimento futuro do cliente.
                
                DICA DE RACK: Sugira sempre deixar espaço (U) sobrando para futuros nobreaks ou módulos. 
                EXCEÇÃO: Se o orçamento (budget) for muito apertado, ofereça o rack preenchido para garantir a venda pelo preço, mas mencione a limitação de crescimento.
                """

            full_prompt = f"""Você é o Engenheiro Consultor e Estrategista Comercial da Plug Energy do Brasil. 
            Esta é uma ferramenta interna para técnicos e vendedores.

            {instrucao_comportamento}

            DADOS DE ESTOQUE:
            {contexto_estoque}
            
            DIRETRIZES TÉCNICAS MANDATÓRIAS (SIGA COM RIGOR):
            1. POTÊNCIA REAL: Watts = (kVA * Fator de Potência). Aplique +20% de margem sobre a carga.
            2. MISSÃO CRÍTICA: Prioridade para redundância N+1 (via ATS ou paralelismo).
            3. ESPAÇO E DIMENSÕES: 1U = 44.45mm. Converta alturas para U. Se profundidade > 90% do rack, ALERTE sobre cabos traseiros.
            4. PESO E LOGÍSTICA: Verifique a coluna 'Peso (kg)'. Emita ALERTA LOGÍSTICO se o sistema for pesado.
            5. PRIORIDADE MARCA: Sempre prefira Plug Energy.
            6. BATERIAS E VDC (LÓGICA DA PLANILHA): 
               - Rendimento do Inversor: 0.96.
               - Corrente Total: I_total = Carga(W) / (VDC * 0.96).
               - Corrente por Bateria: I_bat = I_total / Número de Strings.
               - AUTONOMIA: Use estritamente as tabelas de descarga real (7Ah e 9Ah) da planilha. NÃO use Peukert.
            7. DINÂMICA DE USO E AUTOCONSUMO: 
               - Em cenários de uso esporádico (ex: elevadores), alerte que o autoconsumo do UPS e a queda de tensão nas baterias reduzem a capacidade de pico ao longo do tempo. 
               - Recomende o uso/resgate logo no início da queda para maior segurança.
            8. PARALELISMO/ATS: Verifique estoque de ATS se o nobreak não tiver placa embutida.
            9. ADAPTAÇÃO DE TENSÃO: Económico (Fase-Neutro) vs Ideal (Transformador Isolador).
            10. MULTIMÍDIA: Organize a saída: ### 📂 MULTIMÍDIA -> **Link Foto:** LINK_FOTO: [URL] -> **Manual Técnico:** [URL].

            ESTRATEGIA COMERCIAL: Cenários Económico, Ideal e Expansão.
            TABELA DE CUSTOS: Item | Qtd | Condição | Custo Unitário | Valor Venda ou Locação.
            Ao final: CUSTO TOTAL, VALOR FINAL e LUCRO BRUTO.

            PARECER DO ENGENHEIRO: Finalize com conselho de venda e alertas de segurança/peso/rack e boas práticas de uso em apagões.

            Pergunta: {prompt}"""
            
            placeholder = st.empty()
            full_response = ""
            
            try:
                response = model.generate_content(full_prompt, stream=True)
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                
                links_fotos = re.findall(r'LINK_FOTO:\s*(https?://\S+)', full_response)
                if links_fotos:
                    for link in list(dict.fromkeys(links_fotos)):
                        st.image(link.strip().rstrip('.,;)]'), width=450, caption="Equipamento Sugerido")

                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Erro na comunicação com a IA: {e}")
        else:
            st.error("Erro Crítico: Base de dados não carregada.")
