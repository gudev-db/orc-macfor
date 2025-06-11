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
    Selecione o plano e os serviços desejados para gerar seu orçamento personalizado.
""")

# Estrutura básica dos serviços (sem preços fixos)
SERVICOS_ESTRUTURA = {
    "Standard": [
        {"Serviço": "Layout", "MEDIDA": "horas", "VOLUMETRIA": 64, "Obrigatório": True},
        {"Serviço": "Desenvolvimento", "MEDIDA": "horas", "VOLUMETRIA": 64, "Obrigatório": True},
        {"Serviço": "Configuração do Modo/Banner de Consentimento", "MEDIDA": "Projeto", "VOLUMETRIA": 1, "Obrigatório": True},
        {"Serviço": "Hospedagem", "MEDIDA": "Anual", "VOLUMETRIA": 0, "Obrigatório": False},
        {"Serviço": "Plugin - ElementorPro", "MEDIDA": "Anual", "VOLUMETRIA": 1, "Obrigatório": False},
        {"Serviço": "Gestão do Projeto Sr", "MEDIDA": "horas", "VOLUMETRIA": 30, "Obrigatório": False},
        {"Serviço": "Reuniões", "MEDIDA": "horas", "VOLUMETRIA": 30, "Obrigatório": False},
        {"Serviço": "Domínio (1 ano)", "MEDIDA": "Anual", "VOLUMETRIA": 1, "Obrigatório": False}
    ],
    "Plus": [
        {"Serviço": "SEO Planejamento", "MEDIDA": "Projeto", "VOLUMETRIA": 1, "Obrigatório": False},
        {"Serviço": "SEO Implementação (TECH PLAN)", "MEDIDA": "horas", "VOLUMETRIA": 0, "Obrigatório": False},
        {"Serviço": "SEO Otimização (Manutenção)", "MEDIDA": "horas", "VOLUMETRIA": 60, "Obrigatório": False}
    ],
    "Pro": [
        {"Serviço": "Projeto de governança Digital", "MEDIDA": "Projeto", "VOLUMETRIA": 1, "Obrigatório": False},
        {"Serviço": "BigQuery", "MEDIDA": "Projeto", "VOLUMETRIA": 0, "Obrigatório": False},
        {"Serviço": "Dashboard", "MEDIDA": "Projeto", "VOLUMETRIA": 1, "Obrigatório": False}
    ]
}

def inicializar_precos():
    """Retorna um dicionário com os preços padrão"""
    return {
        # Standard
        "Standard_Layout": 170.00,
        "Standard_Desenvolvimento": 301.22,
        "Standard_Configuração do Modo/Banner de Consentimento": 3000.00,
        "Standard_Hospedagem": 130.00,
        "Standard_Plugin - ElementorPro": 51.87,
        "Standard_Gestão do Projeto Sr": 320.00,
        "Standard_Reuniões": 268.50,
        "Standard_Domínio (1 ano)": 52.00,
        
        # Plus
        "Plus_SEO Planejamento": 18578.72,
        "Plus_SEO Implementação (TECH PLAN)": 301.22,
        "Plus_SEO Otimização (Manutenção)": 214.98,
        
        # Pro
        "Pro_Projeto de governança Digital": 19646.56,
        "Pro_BigQuery": 1200.00,
        "Pro_Dashboard": 22591.50
    }

def calcular_orcamento(plano, servicos_selecionados, num_paginas, precos):
    dados = []
    total = 0
    
    for servico in servicos_selecionados:
        # Ajusta volumetria para serviços em horas
        if servico["MEDIDA"] == "horas":
            volumetria = servico["VOLUMETRIA"] * (num_paginas / 5)
        else:
            volumetria = servico["VOLUMETRIA"]
        
        # Obtém o preço do serviço
        preco_key = f"{plano}_{servico['Serviço']}"
        preco_un = precos.get(preco_key, 0)  # 0 como fallback
        
        valor = preco_un * volumetria
        total += valor
        
        dados.append({
            "PLANO": plano,
            "Serviços": servico["Serviço"],
            "MEDIDA": servico["MEDIDA"],
            "PREÇO UNITÁRIO": f"R$ {preco_un:,.2f}",
            "VOLUMETRIA DO ATIVO": f"{volumetria:,.2f}" if isinstance(volumetria, float) else f"{volumetria}",
            "VALOR TOTAL": f"R$ {valor:,.2f}"
        })
    
    # Adicionar linha de total
    dados.append({
        "PLANO": "TOTAL",
        "Serviços": "",
        "MEDIDA": "",
        "PREÇO UNITÁRIO": "",
        "VOLUMETRIA DO ATIVO": "",
        "VALOR TOTAL": f"R$ {total:,.2f}"
    })
    
    return pd.DataFrame(dados)

# Interface do usuário
with st.form("dados_projeto"):
    st.header("Selecione seu Plano")
    
    # Seleção do plano
    plano_selecionado = st.radio(
        "Escolha o plano desejado:",
        options=["Standard", "Plus", "Pro"],
        horizontal=True
    )
    
    # Inicializar preços (pode ser carregado de um banco de dados ou arquivo)
    precos = inicializar_precos()
    
    st.header(f"Configuração de Preços - Plano {plano_selecionado}")
    
    # Obter serviços do plano selecionado e planos inferiores
    servicos_disponiveis = SERVICOS_ESTRUTURA["Standard"].copy()
    
    if plano_selecionado in ["Plus", "Pro"]:
        servicos_disponiveis.extend(SERVICOS_ESTRUTURA["Plus"])
    
    if plano_selecionado == "Pro":
        servicos_disponiveis.extend(SERVICOS_ESTRUTURA["Pro"])
    
    # Configuração de preços para cada serviço
    novos_precos = {}
    for servico in servicos_disponiveis:
        preco_key = f"{plano_selecionado}_{servico['Serviço']}"
        preco_padrao = precos.get(preco_key, 0)
        
        novo_preco = st.number_input(
            f"Preço para {servico['Serviço']} ({servico['MEDIDA']})",
            min_value=0.0,
            value=preco_padrao,
            step=0.01,
            key=f"preco_{preco_key}"
        )
        novos_precos[preco_key] = novo_preco
    
    st.header("Seleção de Serviços")
    
    # Seleção de serviços
    servicos_selecionados = []
    for servico in servicos_disponiveis:
        col1, col2 = st.columns([3, 1])
        with col1:
            # Serviços obrigatórios são marcados automaticamente
            if servico.get("Obrigatório", False):
                st.markdown(f"**{servico['Serviço']}** (Obrigatório)")
                servicos_selecionados.append(servico)
            else:
                if st.checkbox(servico["Serviço"], value=False, key=f"check_{servico['Serviço']}"):
                    servicos_selecionados.append(servico)
        
        with col2:
            st.markdown(f"*Preço: R$ {novos_precos.get(f'{plano_selecionado}_{servico['Serviço']}', 0):,.2f}*")
    
    # Configurações adicionais
    st.header("Configurações do Projeto")
    num_paginas = st.number_input("Número de páginas", min_value=1, max_value=100, value=5, step=1)
    
    submitted = st.form_submit_button("Gerar Orçamento")

if submitted and servicos_selecionados:
    # Atualiza os preços com os valores configurados
    precos.update(novos_precos)
    
    orcamento = calcular_orcamento(plano_selecionado, servicos_selecionados, num_paginas, precos)
    
    # Exibir o orçamento
    st.header(f"Orçamento - Plano {plano_selecionado}")
    
    st.dataframe(
        orcamento,
        column_config={
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
        file_name=f"orcamento_{plano_selecionado}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif submitted:
    st.warning("Por favor, selecione pelo menos um serviço para gerar o orçamento.")

# Descrição dos planos
with st.expander("ℹ️ Sobre os Planos"):
    st.markdown("""
    **Standard** - Ideal para sites institucionais básicos:
    - Layout e desenvolvimento essencial
    - Configurações fundamentais
    - Opcionais: Hospedagem, domínio, gestão de projeto

    **Plus** - Para sites com necessidades de SEO:
    - Tudo do Standard
    - Serviços especializados em SEO
    - Otimização para mecanismos de busca

    **Pro** - Solução completa para grandes projetos:
    - Tudo do Plus
    - Governança digital
    - BigQuery para análise de dados
    - Dashboards personalizados
    """)
