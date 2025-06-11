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
    Selecione o plano base e adicione os serviços adicionais desejados.
""")

# Dados completos baseados na tabela fornecida
SERVICOS_POR_PLANO = {
    "Standard": [
        {"Serviço": "Layout", "MEDIDA": "horas", "CUSTO UN": 50.00, "PREÇO UNITÁRIO": 170.00, "VOLUMETRIA": 64, "Obrigatório": True},
        {"Serviço": "Desenvolvimento", "MEDIDA": "horas", "CUSTO UN": 187.50, "PREÇO UNITÁRIO": 301.22, "VOLUMETRIA": 64, "Obrigatório": True},
        {"Serviço": "Configuração e implementação do Modo/Banner de Consentimento", "MEDIDA": "Projeto", "CUSTO UN": 1875.00, "PREÇO UNITÁRIO": 3000.00, "VOLUMETRIA": 1, "Obrigatório": True},
        {"Serviço": "Hospedagem", "MEDIDA": "Anual", "CUSTO UN": 100.00, "PREÇO UNITÁRIO": 130.00, "VOLUMETRIA": 0, "Obrigatório": False},
        {"Serviço": "Plugin - ElementorPro", "MEDIDA": "Anual", "CUSTO UN": 39.90, "PREÇO UNITÁRIO": 51.87, "VOLUMETRIA": 1, "Obrigatório": False},
        {"Serviço": "Gestão do Projeto Sr", "MEDIDA": "horas", "CUSTO UN": 0, "PREÇO UNITÁRIO": 320.00, "VOLUMETRIA": 30, "Obrigatório": False},
        {"Serviço": "Reuniões", "MEDIDA": "horas", "CUSTO UN": 0, "PREÇO UNITÁRIO": 268.50, "VOLUMETRIA": 30, "Obrigatório": False},
        {"Serviço": "Domínio (1 ano)", "MEDIDA": "Anual", "CUSTO UN": 40.00, "PREÇO UNITÁRIO": 52.00, "VOLUMETRIA": 1, "Obrigatório": False}
    ],
    "Plus": [
        {"Serviço": "SEO Planejamento", "MEDIDA": "Projeto", "CUSTO UN": 0, "PREÇO UNITÁRIO": 18578.72, "VOLUMETRIA": 1, "Obrigatório": False},
        {"Serviço": "SEO Implementação (Desenvolvimento TECH PLAN)", "MEDIDA": "horas", "CUSTO UN": 150.00, "PREÇO UNITÁRIO": 301.22, "VOLUMETRIA": 0, "Obrigatório": False}
    ],
    "Pro": [
        {"Serviço": "Projeto de governança Digital", "MEDIDA": "Projeto", "CUSTO UN": 0, "PREÇO UNITÁRIO": 19646.56, "VOLUMETRIA": 1, "Obrigatório": False},
        {"Serviço": "BigQuery (Incluido no custo do proj. de Gov. Digital)", "MEDIDA": "Projeto", "CUSTO UN": 600.00, "PREÇO UNITÁRIO": 1200.00, "VOLUMETRIA": 0, "Obrigatório": False}
    ]
}

def calcular_orcamento(servicos_selecionados, num_paginas, custom_prices=None):
    dados = []
    total = 0
    
    for servico in servicos_selecionados:
        # Ajusta volumetria para serviços em horas
        if servico["MEDIDA"] == "horas":
            volumetria = servico["VOLUMETRIA"] * (num_paginas / 5)
        else:
            volumetria = servico["VOLUMETRIA"]
        
        # Verifica se há preço customizado
        preco_key = f"{servico['Serviço']}"
        preco_un = custom_prices.get(preco_key, servico["PREÇO UNITÁRIO"])
        
        valor = preco_un * volumetria
        total += valor
        
        dados.append({
            "PLANO": servico.get("Plano", "Standard"),
            "Serviços": servico["Serviço"],
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
    
    return pd.DataFrame(dados)

# Interface do usuário
with st.form("dados_projeto"):
    st.header("Selecione o Plano Base")
    plano_base = st.radio(
        "Plano Base:",
        options=["Standard", "Plus", "Pro"],
        horizontal=True
    )
    
    st.header("Serviços do Plano Standard")
    st.markdown("Todos os serviços abaixo estão incluídos no plano Standard:")
    
    # Serviços Standard (sempre incluídos)
    servicos_standard = [s for s in SERVICOS_POR_PLANO["Standard"] if s["Obrigatório"]]
    servicos_selecionados = servicos_standard.copy()
    
    # Mostrar serviços Standard obrigatórios
    for servico in servicos_standard:
        st.markdown(f"✓ **{servico['Serviço']}** - {servico['MEDIDA']} - R$ {servico['PREÇO UNITÁRIO']:,.2f}")
    
    # Serviços Standard opcionais
    st.markdown("**Opcionais:**")
    for servico in [s for s in SERVICOS_POR_PLANO["Standard"] if not s["Obrigatório"]]:
        if st.checkbox(f"{servico['Serviço']} (+R$ {servico['PREÇO UNITÁRIO']:,.2f})", key=f"std_{servico['Serviço']}"):
            servicos_selecionados.append(servico)
    
    # Serviços Plus (se selecionado Plus ou Pro como plano base)
    if plano_base in ["Plus", "Pro"]:
        st.header("Serviços Adicionais do Plano Plus")
        st.markdown("Selecione os serviços Plus que deseja incluir:")
        
        for servico in SERVICOS_POR_PLANO["Plus"]:
            if st.checkbox(f"{servico['Serviço']} (+R$ {servico['PREÇO UNITÁRIO']:,.2f})", key=f"plus_{servico['Serviço']}"):
                servico_com_plano = servico.copy()
                servico_com_plano["Plano"] = "Plus"
                servicos_selecionados.append(servico_com_plano)
    
    # Serviços Pro (se selecionado Pro como plano base)
    if plano_base == "Pro":
        st.header("Serviços Adicionais do Plano Pro")
        st.markdown("Selecione os serviços Pro que deseja incluir:")
        
        for servico in SERVICOS_POR_PLANO["Pro"]:
            if st.checkbox(f"{servico['Serviço']} (+R$ {servico['PREÇO UNITÁRIO']:,.2f})", key=f"pro_{servico['Serviço']}"):
                servico_com_plano = servico.copy()
                servico_com_plano["Plano"] = "Pro"
                servicos_selecionados.append(servico_com_plano)
    
    # Configurações adicionais
    st.header("Configurações do Projeto")
    num_paginas = st.number_input("Número de páginas", min_value=1, max_value=100, value=5, step=1)
    
    # Personalização de preços
    st.header("Personalização de Preços")
    custom_prices = {}
    
    # Permitir editar preços dos serviços selecionados
    for servico in servicos_selecionados:
        if not servico["Obrigatório"]:  # Só permite customizar preços de serviços opcionais
            novo_preco = st.number_input(
                f"Preço para {servico['Serviço']}",
                min_value=0.0,
                value=float(servico["PREÇO UNITÁRIO"]),
                step=0.01,
                key=f"preco_{servico['Serviço']}"
            )
            custom_prices[servico["Serviço"]] = novo_preco
    
    submitted = st.form_submit_button("Gerar Orçamento")

if submitted and servicos_selecionados:
    orcamento = calcular_orçamento(servicos_selecionados, num_paginas, custom_prices)
    
    # Exibir o orçamento
    st.header("Orçamento Detalhado")
    st.dataframe(
        orcamento,
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
    
    excel_data = convert_df_to_excel(orcamento)
    
    st.download_button(
        label="Baixar Orçamento (Excel)",
        data=excel_data,
        file_name=f"orcamento_{plano_base}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif submitted:
    st.warning("Por favor, selecione pelo menos um serviço para gerar o orçamento.")

# Descrição dos planos
with st.expander("ℹ️ Informações sobre os Planos"):
    st.markdown("""
    **Standard** - Serviços básicos para construção de sites:
    - Layout e desenvolvimento (obrigatórios)
    - Configuração de consentimento (obrigatório)
    - Hospedagem, domínio e gestão (opcionais)

    **Plus** - Adiciona ao Standard:
    - SEO Planejamento
    - Implementação técnica SEO

    **Pro** - Adiciona ao Plus:
    - Projeto de governança digital
    - BigQuery para análise de dados
    """)
