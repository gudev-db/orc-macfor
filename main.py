__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import os
import streamlit as st
from google import genai
import pandas as pd

# Configuração da página
st.set_page_config(
    layout="wide",
    page_title="Macfor Orçamentos",
    page_icon="📊"
)

st.image('static/macLogo.png', width=300)
st.title("Planejador de Orçamento para Construção de Sites")
st.markdown("""
    **Sistema automatizado para geração de orçamentos**  
    Preencha os campos abaixo para gerar orçamentos detalhados para diferentes pacotes de desenvolvimento de sites.
""")

# Configuração do Gemini
gemini_api_key = os.getenv("GEM_API_KEY")
client = genai.Client(api_key=gemini_api_key)

# Função para gerar recomendações de volumetria
def gerar_recomendacoes_volumetria(tipo_projeto, complexidade, funcionalidades):
    prompt = f"""
    Com base nas seguintes informações do projeto:
    - Tipo: {tipo_projeto}
    - Nível de complexidade: {complexidade}
    - Funcionalidades principais: {funcionalidades}

    Gere recomendações realistas de volumetria (horas/projetos) para cada item de um orçamento de desenvolvimento de site, considerando os seguintes itens:
    1. Desenvolvimento (horas)
    2. Layout/Conteúdo (horas)
    3. BigQuery (projeto - 0 ou 1)
    4. Projeto de governança (projeto - 0 ou 1)
    5. Configuração do Modo/Banner de Consentimento (projeto - 0 ou 1)

    Retorne APENAS um dicionário Python no formato:
    {{
        "Desenvolvimento": [horas_standard, horas_plus, horas_pro],
        "Layout / Conteúdo": [horas_standard, horas_plus, horas_pro],
        "BigQuery": [0 ou 1 para standard, 0 ou 1 para plus, 0 ou 1 para pro],
        "Projeto de governança": [0 ou 1 para standard, 0 ou 1 para plus, 0 ou 1 para pro],
        "Modo/Banner de Consentimento": [0 ou 1 para standard, 0 ou 1 para plus, 0 ou 1 para pro]
    }}

    Seja realista e considere que:
    - Standard é o pacote básico
    - Plus inclui mais funcionalidades
    - Pro é o pacote completo
    """
    
    response = client.generate_text(prompt=prompt)
    try:
        # Extrai o dicionário da resposta
        start_idx = response.text.find('{')
        end_idx = response.text.rfind('}') + 1
        dict_str = response.text[start_idx:end_idx]
        return eval(dict_str)
    except:
        # Retorno padrão em caso de erro
        return {
            "Desenvolvimento": [60, 80, 80],
            "Layout / Conteúdo": [70, 100, 100],
            "BigQuery": [0, 0, 1],
            "Projeto de governança": [0, 1, 1],
            "Modo/Banner de Consentimento": [1, 1, 1]
        }

# Função para calcular orçamento
def calcular_orcamento(volumetria, precos):
    pacotes = ["STANDARD", "PLUS", "PRO"]
    resultados = {}
    
    for i, pacote in enumerate(pacotes):
        dados = {
            "CONSTRUÇÃO DE SITE": ["MEDIDA", "PREÇO UNITÁRIO", "VOLUMETRIA DO ATIVO", "VALOR POR PROJETO"],
            "Desenvolvimento": ["horas", precos["Desenvolvimento"], volumetria["Desenvolvimento"][i], precos["Desenvolvimento"] * volumetria["Desenvolvimento"][i]],
            "Layout / Conteúdo": ["horas", precos["Layout / Conteúdo"], volumetria["Layout / Conteúdo"][i], precos["Layout / Conteúdo"] * volumetria["Layout / Conteúdo"][i]],
            "BigQuery": ["projeto", precos["BigQuery"], volumetria["BigQuery"][i], precos["BigQuery"] * volumetria["BigQuery"][i]],
            "Projeto de governança": ["Projeto", precos["Projeto de governança"], volumetria["Projeto de governança"][i], precos["Projeto de governança"] * volumetria["Projeto de governança"][i]],
            "Configuração e implementação do Modo/Banner de Consentimento": ["Projeto", precos["Modo/Banner de Consentimento"], volumetria["Modo/Banner de Consentimento"][i], precos["Modo/Banner de Consentimento"] * volumetria["Modo/Banner de Consentimento"][i]],
            "TOTAL": ["", "", "", sum([
                precos["Desenvolvimento"] * volumetria["Desenvolvimento"][i],
                precos["Layout / Conteúdo"] * volumetria["Layout / Conteúdo"][i],
                precos["BigQuery"] * volumetria["BigQuery"][i],
                precos["Projeto de governança"] * volumetria["Projeto de governança"][i],
                precos["Modo/Banner de Consentimento"] * volumetria["Modo/Banner de Consentimento"][i]
            ])]
        }
        resultados[pacote] = pd.DataFrame.from_dict(dados, orient='index')
    
    return resultados

# Interface do usuário
with st.form("dados_projeto"):
    st.header("Informações do Projeto")
    
    col1, col2 = st.columns(2)
    with col1:
        tipo_projeto = st.selectbox(
            "Tipo de Projeto",
            ["Site Institucional", "E-commerce", "Portal Corporativo", "Aplicativo Web", "Landing Page"]
        )
        
        complexidade = st.select_slider(
            "Nível de Complexidade",
            options=["Baixa", "Média", "Alta", "Muito Alta"]
        )
    
    with col2:
        funcionalidades = st.multiselect(
            "Funcionalidades Principais",
            ["Blog integrado", "Formulários complexos", "Integração com ERP", "Área de membros", 
             "Pagamentos online", "Catálogo de produtos", "Multi-idiomas", "Busca avançada"]
        )
        
        st.markdown("**Preços Unitários (R$)**")
        preco_desenvolvimento = st.number_input("Desenvolvimento (por hora)", value=301.22)
        preco_layout = st.number_input("Layout/Conteúdo (por hora)", value=170.00)
        preco_bigquery = st.number_input("BigQuery (por projeto)", value=1200.00)
        preco_governanca = st.number_input("Projeto de governança", value=8000.00)
        preco_consentimento = st.number_input("Modo/Banner de Consentimento", value=3000.00)
    
    submitted = st.form_submit_button("Gerar Orçamento")

if submitted:
    precos = {
        "Desenvolvimento": preco_desenvolvimento,
        "Layout / Conteúdo": preco_layout,
        "BigQuery": preco_bigquery,
        "Projeto de governança": preco_governanca,
        "Modo/Banner de Consentimento": preco_consentimento
    }
    
    with st.spinner("Gerando recomendações de volumetria..."):
        volumetria = gerar_recomendacoes_volumetria(tipo_projeto, complexidade, funcionalidades)
    
    st.success("Recomendações geradas com sucesso!")
    
    orcamentos = calcular_orcamento(volumetria, precos)
    
    # Exibir os orçamentos em abas
    tab1, tab2, tab3 = st.tabs(["STANDARD", "PLUS", "PRO"])
    
    with tab1:
        st.subheader("Orçamento STANDARD")
        st.dataframe(orcamentos["STANDARD"].style.format({
            "PREÇO UNITÁRIO": "R$ {:,.2f}",
            "VALOR POR PROJETO": "R$ {:,.2f}"
        }), use_container_width=True)
    
    with tab2:
        st.subheader("Orçamento PLUS")
        st.dataframe(orcamentos["PLUS"].style.format({
            "PREÇO UNITÁRIO": "R$ {:,.2f}",
            "VALOR POR PROJETO": "R$ {:,.2f}"
        }), use_container_width=True)
    
    with tab3:
        st.subheader("Orçamento PRO")
        st.dataframe(orcamentos["PRO"].style.format({
            "PREÇO UNITÁRIO": "R$ {:,.2f}",
            "VALOR POR PROJETO": "R$ {:,.2f}"
        }), use_container_width=True)
    
    # Botão para download
    @st.cache_data
    def convert_df_to_csv(df_dict):
        csv = ""
        for pacote, df in df_dict.items():
            csv += f"{pacote}\n\n"
            csv += df.to_csv(sep='\t')
            csv += "\n\n"
        return csv.encode('utf-8')
    
    csv = convert_df_to_csv(orcamentos)
    
    st.download_button(
        label="Baixar Orçamentos como CSV",
        data=csv,
        file_name=f"orcamento_{tipo_projeto.lower().replace(' ', '_')}.csv",
        mime="text/csv"
    )
