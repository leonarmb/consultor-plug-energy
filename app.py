import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# 1. Configuração da Página
st.set_page_config(page_title="Plug Energy - Consultor", page_icon="🔋", layout="wide")

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
            # SEU PROMPT ORIGINAL MANTIDO INTEGRALMENTE
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
            9. MULTIMÍDIA: Para cada equipamento sugerido, forneça os links: URL_Foto_Principal, URL_Foto_Frente, URL_Foto_Traseira e URL_Manual.
               IMPORTANTE: Para que eu exiba a foto, escreva o link da imagem sozinho em uma linha com o prefixo 'LINK_FOTO: '. Exemplo: LINK_FOTO: https://link.com/imagem.jpg

            ESTRATÉGIA COMERCIAL (3 CENÁRIOS):
            - ECONÔMICO: Menor custo, sem redundância.
            - IDEAL: Redundante (N+1) se for crítico, melhor proteção (Trafo).
            - EXPANSÃO: Potência superior para crescimento futuro.

            TABELA DE CUSTOS: Para cada cenário, apresente Item | Qtd | Condição | Custo Unitário (Interno) | Valor Venda ou Locação.
            Ao final de cada tabela: CUSTO TOTAL, VALOR FINAL e LUCRO BRUTO.

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
                
                # --- LÓGICA DE EXIBIÇÃO DE FOTOS APRIMORADA ---
                # A Regex agora é mais robusta para pegar links que podem terminar com espaços ou quebras
                links_fotos = re.findall(r'LINK_FOTO:\s*(https?://\S+)', full_response)
                
                if links_fotos:
                    st.write("---")
                    st.subheader("📸 Galeria de Equipamentos Sugeridos")
                    # Remove duplicatas mantendo a ordem
                    links_unicos = list(dict.fromkeys(links_fotos))
                    cols = st.columns(len(links_unicos))
                    
                    for i, link in enumerate(links_unicos):
                        with cols[i]:
                            # Limpeza profunda do link do Google Drive para visualização direta
                            # Remove parâmetros de download e força o ID para o modo 'view'
                            clean_link = link.strip().split(' ')[0] # Garante que pega só a URL
                            direct_link = clean_link.replace("file/d/", "uc?export=view&id=").replace("/view?usp=sharing", "").replace("/view", "").replace("&export=download", "")
                            
                            # Extração do ID via Regex para segurança extra se o replace falhar
                            id_match = re.search(r'(?:id=|[dD]/|folders/|file/d/)([a-zA-Z0-9_-]{25,})', direct_link)
                            if id_match:
                                direct_link = f"https://drive.google.com/uc?export=view&id={id_match.group(1)}"
                            
                            st.image(direct_link, use_container_width=True, caption=f"Visualização {i+1}")

                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Erro na comunicação com a IA: {e}")
        else:
            st.error("Erro Crítico: Base de dados não carregada.")
