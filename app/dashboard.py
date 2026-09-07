import sys
import os

# 🚀 Linha mágica: Garante que o Streamlit enxergue as pastas na raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from dags.ingestion_dag import gerar_dados_logistica_hibrida
from src.silver_processing import processar_camada_silver
from src.gold_metrics import consolidar_camada_gold

# 1. Configuração da Página
st.set_page_config(
    page_title="SaaS Supply Chain Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS para o tema Dark Premium com Cards Brancos
st.markdown("""
    <style>
    .stApp { background-color: #0f141c; }
    [data-testid="stSidebar"] { background-color: #161b22; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 6px;
        padding: 20px 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #a3e635;
    }
    div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 14px !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] { color: #0f172a !important; font-size: 36px !important; font-weight: 700 !important; }
    div[data-testid="stMetricDelta"] { color: #16a34a !important; font-size: 14px !important; }
    h1, h2, h3, p, span { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

def mapear_e_processar_upload(df_bruto):
    mapeamento = {
        'order_id': ['order_id', 'id_pedido', 'pedido', 'codigo_pedido', 'order'],
        'route': ['route', 'rota', 'regiao', 'uf', 'destino', 'state', 'cidade', 'custos/guarulhos'],
        'created_at': ['created_at', 'data_criacao', 'criado_em', 'aprovado_em', 'data_pedido'],
        'picked_at': ['picked_at', 'data_separacao', 'separado_em', 'picking_at'],
        'shipped_at': ['shipped_at', 'data_expedicao', 'expedido_em', 'shipped_date'],
        'promised_date': ['promised_date', 'data_prometida', 'prazo_entrega', 'prazo', 'prazo_dias'],
        'delivered_at': ['delivered_at', 'data_entrega', 'entregue_em', 'data_real_entrega'],
        'is_infull': ['is_infull', 'completo', 'pedido_correto', 'infull', 'status_entrega'],
        'freight_cost': ['freight_cost', 'custo_frete', 'valor_frete', 'frete', 'custo_frete_base'],
        'product_margin': ['product_margin', 'margem_produto', 'lucro_produto', 'margem', 'peso_kg']
    }
    
    df_novo = pd.DataFrame()
    colunas_originais = {col.lower().strip(): col for col in df_bruto.columns}
    
    for chave, sinonimos in mapeamento.items():
        achou = False
        for s in sinonimos:
            if s in colunas_originais:
                if chave == 'is_infull' and df_bruto[colunas_originais[s]].dtype == 'object':
                    df_novo[chave] = np.where(df_bruto[colunas_originais[s]].astype(str).str.lower().str.contains('entregue|sucesso|ok|1'), 1, 0)
                else:
                    df_novo[chave] = df_bruto[colunas_originais[s]]
                achou = True
                break
        if not achou:
            if chave in ['created_at', 'picked_at', 'shipped_at', 'promised_date', 'delivered_at']:
                continue 
            elif chave == 'is_infull': df_novo['is_infull'] = 1
            elif chave == 'freight_cost': df_novo['freight_cost'] = 25.0
            elif chave == 'product_margin': df_novo['product_margin'] = 60.0
            else:
                st.error(f"❌ Coluna vital não identificada: precisamos de algo parecido com **{chave}** na planilha.")
                return False

    data_base = pd.to_datetime('2026-09-01 10:00:00')
    if 'created_at' not in df_novo.columns:
        df_novo['created_at'] = data_base
        df_novo['picked_at'] = data_base + pd.to_timedelta('2h')
        df_novo['shipped_at'] = data_base + pd.to_timedelta('6h')
        
        if 'promised_date' in df_novo.columns:
            dias_prazo = pd.to_numeric(df_novo['promised_date'], errors='coerce').fillna(3).astype(int)
            df_novo['promised_date'] = data_base + pd.to_timedelta(dias_prazo, unit='D')
            df_novo['delivered_at'] = data_base + pd.to_timedelta(dias_prazo, unit='D') - pd.to_timedelta('4h')
        else:
            df_novo['promised_date'] = data_base + pd.to_timedelta('3D')
            df_novo['delivered_at'] = data_base + pd.to_timedelta('2D')
                
    if 'source_type' in colunas_originais:
        df_novo['source_type'] = df_bruto[colunas_originais['source_type']]
    else:
        df_novo['source_type'] = 'UPLOAD_MANUAL'
                
    colunas_data = ["created_at", "picked_at", "shipped_at", "promised_date", "delivered_at"]
    for col in colunas_data:
        df_novo[col] = pd.to_datetime(df_novo[col], errors='coerce')
        
    for col in ['freight_cost', 'product_margin']:
        if df_novo[col].dtype == 'object':
            df_novo[col] = df_novo[col].astype(str).str.replace(',', '.').astype(float)
        df_novo[col] = pd.to_numeric(df_novo[col], errors='coerce').fillna(0.0)
            
    os.makedirs("data/bronze", exist_ok=True)
    df_novo.to_csv("data/bronze/orders_raw.csv", index=False)
    
    processar_camada_silver()
    consolidar_camada_gold()
    return True

# 🎛️ 2. BARRA LATERAL
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #a3e635;'>🛡️ LOGIX HUB</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("📥 Upload Your Data")
    arquivo_usuario = st.file_uploader("Arraste o arquivo CSV ou Excel da sua operação:", type=["csv", "xlsx"])
    
    if arquivo_usuario is not None:
        if "ultimo_arquivo" not in st.session_state or st.session_state.ultimo_arquivo != arquivo_usuario.name:
            try:
                with st.spinner("⚡ Processando e limpando dados..."):
                    df_bruto = pd.read_csv(arquivo_usuario) if arquivo_usuario.name.endswith('.csv') else pd.read_excel(arquivo_usuario)
                    if mapear_e_processar_upload(df_bruto):
                        st.session_state.ultimo_arquivo = arquivo_usuario.name
                        st.success("🎉 Arquivo integrado!")
                        st.rerun()
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")
            
    st.markdown("---")
    st.subheader("🕹️ Demo Environment")
    if st.button("⚡ Generate Demo Data (60k)", type="secondary"):
        with st.spinner("⏳ Criando massa analítica de teste..."):
            if "ultimo_arquivo" in st.session_state:
                del st.session_state["ultimo_arquivo"]
            gerar_dados_logistica_hibrida(num_pedidos=60000)
            processar_camada_silver()
            consolidar_camada_gold()
            st.session_state.ultimo_arquivo = "demo_60k"
        st.success("✅ Ambiente pronto!")
        st.rerun()

    st.markdown("---")
    st.subheader("Filtros Dinâmicos")
    PATH_ROTAS = "data/gold/kpi_performance_rotas.csv"
    
    if os.path.exists(PATH_ROTAS):
        df_rotas_init = pd.read_csv(PATH_ROTAS)
        todas_rotas = df_rotas_init['route'].dropna().unique().tolist()
    else:
        todas_rotas = []
    rotas_selecionadas = st.multiselect("Filtrar por Rota", options=todas_rotas, default=todas_rotas)

# 📊 3. PAINEL PRINCIPAL
st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>Logistics & Supply Chain Hub</h1>", unsafe_allow_html=True)

if not os.path.exists(PATH_ROTAS) or len(todas_rotas) == 0:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("👋 **Bem-vindo ao SaaS Logix Hub!** Faça o upload de uma planilha na barra lateral ou clique em **'Generate Demo Data (60k)'**.")
else:
    df_rotas = pd.read_csv(PATH_ROTAS)
    df_filtrado = df_rotas[df_rotas['route'].isin(rotas_selecionadas)].copy()

    if df_filtrado.empty:
        st.warning("Selecione ao menos uma rota para renderizar o painel.")
    else:
        total_pedidos = int(df_filtrado['total_pedidos'].sum())
        otif_medio = (df_filtrado['otif_geral_pct'] * df_filtrado['total_pedidos']).sum() / total_pedidos
        custo_frete = df_filtrado['custo_total_frete'].sum()
        lead_time_last_mile = df_filtrado['lead_time_last_mile_horas'].mean()

        c1, c2, c3 = st.columns(3)
        with c1: st.metric(label="TOTAL FREIGHT COST", value=f"R$ {custo_frete:,.2f}")
        with c2: st.metric(label="OTIF PERFORMANCE", value=f"{otif_medio:.1f}%")
        with c3: st.metric(label="TOTAL VOLUMETRIA", value=f"{total_pedidos:,} pacotes")

        st.markdown("<br>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("### Distribuição de Volume por Região/Rota")
            df_g1 = df_filtrado.sort_values(by="total_pedidos", ascending=True)
            st.bar_chart(data=df_g1, x="route", y="total_pedidos", color="#a3e635", horizontal=True)
        with col_g2:
            st.markdown("### Taxa de Lucratividade Operacional (%)")
            df_g2 = df_filtrado.sort_values(by="rotas_lucrativas_pct", ascending=True)
            st.bar_chart(data=df_g2, x="route", y="rotas_lucrativas_pct", color="#84cc16", horizontal=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_inf1, col_inf2 = st.columns(2)
        with col_inf1:
            st.markdown("<p style='text-align: center; font-weight: bold; color: white;'>Tempo Médio de Envio Last-Mile (Dias)</p>", unsafe_allow_html=True)
            valor_dias = round(lead_time_last_mile / 24, 1)
            max_escala = max(10.0, valor_dias * 1.5)
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = valor_dias,
                number = {'font': {'color': "white", 'size': 45}, 'suffix': ' dias'},
                gauge = {
                    'axis': {'range': [0, max_escala], 'tickwidth': 1, 'tickcolor': "white"},
