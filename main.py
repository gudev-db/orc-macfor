__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import os
import streamlit as st
import pandas as pd
from io import BytesIO

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

# Dados fixos baseados na tabela fornecida
SERVICOS_POR_PLANO = {
    "Standard": [
        {"Serviços": "Layout", "MEDIDA": "horas", "CUSTO UN": 50.00, "PREÇO UNITÁRIO": 170.00, "VOLUMETRIA": 64},
        {"Serviços": "Desenvolvimento", "MEDIDA": "horas", "CUSTO UN": 187.50, "PREÇO UNITÁRIO": 301.22, "VOLUMETRIA": 64},
        {"Serviços": "Configuração e implementação do Modo/Banner de Consentimento", "MEDIDA": "Projeto", "CUSTO UN": 1875.00, "PREÇO UNITÁRIO": 3000.00, "VOLUMETRIA": 1},
        {"Serviços": "Hospedagem", "MEDIDA": "Anual", "CUSTO UN": 100.00, "PREÇO UNITÁRIO": 130.00, "VOLUMETRIA": 0},
        {"Serviços": "Plugin - ElementorPro", "MEDIDA": "Anual", "CUSTO UN": 39.90, "PREÇO UNITÁRIO": 51.87, "VOLUMETRIA": 1},
        {"Serviços": "Gestão do Projeto Sr", "MEDIDA": "horas", "CUSTO UN": 0, "PREÇO UNITÁRIO": 320.00, "VOLUMETRIA": 30},
        {"Serviços": "Reuniões", "MEDIDA": "horas", "CUSTO UN": 0, "PREÇO UNITÁRIO": 268.50, "VOLUMETRIA": 30},
        {"Serviços": "Domínio (1 ano)", "MEDIDA": "Anual", "CUSTO UN": 40.00, "PREÇO UNITÁRIO": 52.00, "VOLUMETRIA": 1}
    ],
    "Plus": [
        {"Serviços": "SEO Planejamento", "MEDIDA": "Projeto", "CUSTO UN": 0, "PREÇO UNITÁRIO": 18578.72, "VOLUMETRIA": 1},
        {"Serviços": "SEO Implementação (Desenvolvimento TECH PLAN)", "MEDIDA": "horas", "CUSTO UN": 150.00, "PREÇO UNITÁRIO": 301.22, "VOLUMETRIA": 0}
    ],
    "Pro": [
        {"Serviços": "Projeto de governança Digital", "MEDIDA": "Projeto", "CUSTO UN": 0, "PREÇO UNITÁRIO": 19646.56, "VOLUMETRIA": 1},
        {"Serviços": "BigQuery (Incluido no custo do proj. de Gov. Digital)", "MEDIDA": "Projeto", "CUSTO UN": 600.00, "PREÇO UNITÁRIO": 1200.00, "VOLUMETRIA": 0}
    ]
}

# Serviços extras e manutenções (se necessário)
SERVICOS_EXTRAS = {
    "Extras": [
        {"Serviços": "Dashboard", "MEDIDA": "Projeto", "CUSTO UN": 8000.00, "PREÇO UNITÁRIO": 22591.50, "VOLUMETRIA": 0}
    ],
    "Manutenções": [
        {"Serviços": "SEO Otimização (Manutenção SEO)", "MEDIDA": "horas", "CUSTO UN": 0, "PREÇO UNITÁRIO": 214.98, "VOLUMETRIA": 0},
        {"Serviços": "SEO Implemetação Otimização (Desenvolvimento TECH)", "MEDIDA": "horas", "CUSTO UN": 0, "PREÇO UNITÁRIO": 301.22, "VOLUMETRIA": 0}
    ]
}

def calcular_orcamento(base_servicos, num_paginas, custom_prices=None):
    resultados = {}
    
    for plano, servicos in base_servicos.items():
        dados = []
        total = 0
        
        for servico in servicos:
            # Ajusta volumetria para serviços em horas baseado no número de páginas
            if servico["MEDIDA"] == "horas":
                volumetria = servico["VOLUMETRIA"] * (num_paginas / 5)
            else:
                volumetria = servico["VOLUMETRIA"]
            
            # Verifica se há preço customizado
            preco_un = custom_prices.get(f"{plano}_{servico['Serviços']}", servico["PREÇO UNITÁRIO"])
            
            valor = preco_un * volumetria
            total += valor
            
            dados.append({
                "PLANO": plano,
                "Serviços": servico["Serviços"],
                "MEDIDA": servico["MEDIDA"],
                "CUSTO UN": f"R$ {servico['CUSTO UN']:,.2f}" if servico['CUSTO UN'] != 0 else "",
                "PREÇO UNITÁRIO": f"R$ {preco_un:,.2f}",
                "VOLUMETRIA DO ATIVO": volumetria,
                "VALOR TOTAL": f"R$ {valor:,.2f}"
            })
        
        # Adicionar linha de total
        dados.append({
            "PLANO": "TOTAL",
            "Serviços": "",
            "MEDIDA": "",
            "CUSTO UN": "",
            "PREÇO UNITÁRIO": "",
            "VOLUMETRIA DO ATIVO": "",
            "VALOR TOTAL": f"R$ {total:,.2f}"
        })
        
        resultados[plano] = pd.DataFrame(dados)
    
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
        
        num_paginas = st.number_input("Número de páginas", min_value=1, max_value=100, value=5, step=1)
    
    with col2:
        st.markdown("**Serviços Extras**")
        incluir_dashboard = st.checkbox("Dashboard (Pro)", value=False)
        incluir_seo_otimizacao = st.checkbox("SEO Otimização (Plus)", value=False)
    
    st.header("Personalização de Preços")
    custom_prices = {}
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Standard**")
        custom_prices["Standard_Layout"] = st.number_input("Preço Layout", value=170.00)
        custom_prices["Standard_Desenvolvimento"] = st.number_input("Preço Desenvolvimento", value=301.22)
    
    with col2:
        st.markdown("**Plus**")
        custom_prices["Plus_SEO Planejamento"] = st.number_input("Preço SEO Planejamento", value=18578.72)
    
    with col3:
        st.markdown("**Pro**")
        custom_prices["Pro_Projeto de governança Digital"] = st.number_input("Preço Governança Digital", value=19646.56)
    
    submitted = st.form_submit_button("Gerar Orçamento")

if submitted:
    # Ajustar serviços conforme seleção
    servicos_base = {k: v.copy() for k, v in SERVICOS_POR_PLANO.items()}
    
    if incluir_dashboard:
        servicos_base["Pro"].extend(SERVICOS_EXTRAS["Extras"])
    
    if incluir_seo_otimizacao:
        servicos_base["Plus"].extend(SERVICOS_EXTRAS["Manutenções"])
    
    orcamentos = calcular_orcamento(servicos_base, num_paginas, custom_prices)
    
    # Exibir os orçamentos
    st.header("Orçamento Detalhado")
    
    # Juntar todos os DataFrames para exibição
    df_completo = pd.concat([orcamentos["Standard"], orcamentos["Plus"], orcamentos["Pro"]])
    
    # Adicionar linhas vazias para separação visual
    df_vazio = pd.DataFrame([{"PLANO": "", "Serviços": "", "MEDIDA": "", "CUSTO UN": "", "PREÇO UNITÁRIO": "", "VOLUMETRIA DO ATIVO": "", "VALOR TOTAL": ""}])
    df_completo = pd.concat([df_completo, df_vazio])
    
    st.dataframe(
        df_completo,
        column_config={
            "CUSTO UN": st.column_config.TextColumn("CUSTO UN"),
            "PREÇO UNITÁRIO": st.column_config.TextColumn("PREÇO UNITÁRIO"),
            "VALOR TOTAL": st.column_config.TextColumn("VALOR TOTAL")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Botão para download
    @st.cache_data
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="Orçamento")
        return output.getvalue()
    
    excel_data = convert_df_to_excel(df_completo)
    
    st.download_button(
        label="Baixar Orçamento (Excel)",
        data=excel_data,
        file_name=f"orcamento_{tipo_projeto.lower().replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Explicação dos planos
    with st.expander("Detalhes dos Planos"):
        st.markdown("""
        **Standard:**
        - Layout básico
        - Desenvolvimento essencial
        - Configurações fundamentais
        - Hospedagem e domínio
        
        **Plus:**
        - Tudo do Standard
        - SEO Planejamento
        - Implementação técnica SEO
        
        **Pro:**
        - Tudo do Plus
        - Projeto de governança digital
        - BigQuery (análise de dados)
        """)
