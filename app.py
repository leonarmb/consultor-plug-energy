import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="centered")

# --- INTERFACE VISUAL (LOGO DINÂMICA E TÍTULO) ---
@st.cache_data
def exibir_cabecalho():
    # CSS para garantir que as imagens não fiquem gigantes e respondam ao tema
    st.markdown("""
        <style>
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .logo-img {
            max-width: 250px; /* Ajusta o tamanho da logo para ~40% */
            height: auto;
        }
        /* Lógica de Alternância de Tema */
        @media (prefers-color-scheme: dark) {
            .light-mode-logo { display: none !important; }
            .dark-mode-logo { display: block !important; }
        }
        @media (prefers-color-scheme: light) {
            .light-mode-logo { display: block !important; }
            .dark-mode-logo { display: none !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    # Centralização manual com colunas
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        # Usamos HTML para permitir que o CSS acima controle a visibilidade
        # Os links apontam para o conteúdo bruto (raw) do seu GitHub
        st.markdown(f"""
            <div class="logo-container">
                <img src="https://raw.githubusercontent.com/Fisatf/bot-plug/main/logo_plugenergy.png" 
                     class="logo-img light-mode-logo" alt="Logo Plug Energy">
                <img src="https://raw.githubusercontent.com/Fisatf/bot-plug/main/logo_plugenergy_invert.png" 
                     class="logo-img dark-mode-logo" alt="Logo Plug Energy">
            </div>
        """, unsafe_allow_html=True)
        
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
    
    **Notas Técnicas e de Segurança:**
    - Prioridade para marca **Plug Energy** (Garantia de peças de reposição).
    - Verificação de **Peso (kg)**: Alertas automáticos para logística e suporte de carga.
    - Dimensões: Conversão automática de **mm para U** (1U = 44.45mm).
    - Verificação de profundidade: Alerta para espaço de cabos traseiros.
    - Fotos e Manuais: Links integrados para validação física imediata.
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
            1. POTÊNCIA REAL: Watts = (kVA * Fator de Potência). Aplique +20% de margem sobre a carga.
            2. MISSÃO CRÍTICA: Se o cliente "não pode parar", o CENÁRIO IDEAL deve ser N+1 (redundante).
            3. ESPAÇO E DIMENSÕES: 1U = 44.45mm. Converta alturas para U. Se profundidade > 90% do rack, ALERTE sobre cabos traseiros.
            4. PESO E LOGÍSTICA: Verifique a coluna 'Peso (kg)'. Se o sistema for pesado, emita um ALERTA LOGÍSTICO (necessidade de mais pessoas, empilhadeira ou reforço no rack).
            5. PRIORIDADE MARCA: Sempre prefira Plug Energy (temos peças de reposição imediata).
            6. BATERIAS E VDC: Verifique compatibilidade de VDC. Jamais misture marcas. Use 'Baterias Internas' + 'Múltiplo Expansão'.
            7. PARALELISMO/ATS: Se o nobreak exigir ATS e não for 'placa embutida', verifique estoque de ATS. Se não houver, marque "Necessário cotar externo".
            8. ADAPTAÇÃO DE TENSÃO (380V -> 220V): Econômico (Fase-Neutro) vs Ideal (Transformador Isolador).
            9. MULTIMÍDIA: Forneça obrigatoriamente a 'URL_Foto_Principal' e o 'URL_Manual'. 
               IMPORTANTE: Organize os links em uma seção dedicada chamada "### 📂 MULTIMÍDIA" com a seguinte estrutura:
               - **Link Foto:** LINK_FOTO: [URL]
               - **Manual Técnico:** [Clique aqui para abrir o Manual](URL)
               Exiba apenas a 'URL_Foto_Principal'. Traseira/Frente apenas se pedido.

            ESTRATEGIA COMERCIAL (3 CENARIOS):
            - ECONOMICO: Menor custo, sem redundancia.
            - IDEAL: Redundante (N+1) se for critico, melhor protecao (Trafo).
            - EXPANSAO: Potencia superior para crescimento futuro.

            TABELA DE CUSTOS: Item | Qtd | Condição | Custo Unitário | Valor Venda ou Locação.
            Ao final: CUSTO TOTAL, VALOR FINAL e LUCRO BRUTO.

            PARECER DO ENGENHEIRO: Finalize com conselho de venda e alertas de segurança/peso.

            Pergunta: {prompt}"""
            
            placeholder = st.empty()
            full_response = ""
            
            try:
                response = model.generate_content(full_prompt, stream=True)
                for chunk in response:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                
                # --- BUSCA DE LINKS REFORÇADA ---
                links_fotos = re.findall(r'LINK_FOTO:\s*(?:\[)?(https?://[^\s\]]+)(?:\])?', full_response)
                
                if links_fotos:
                    links_unicos = list(dict.fromkeys(links_fotos))
                    for link in links_unicos:
                        clean_link = link.strip().rstrip('.,;)]')
                        st.image(clean_link, width=500, caption="Equipamento Sugerido")

                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Erro na comunicação com a IA: {e}")
        else:
            st.error("Erro Crítico: Base de dados não carregada.")
