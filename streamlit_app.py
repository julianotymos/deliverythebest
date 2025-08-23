import datetime
import random
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from read_process_last_run import read_process_last_run
from datetime import datetime, timedelta
from typing import List
from tab_revenue_analysis import tab_revenue_analysis  # <-- substitui tab_sales_total
from tab_product_analysis import tab_product_analysis  # <-- substitui tab_sales_total
from tab_subitem_analysis import tab_subitem_analysis

# --- Início da Aplicação Streamlit ---

st.set_page_config(
    page_title="Dashboard de Vendas",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Performance Delivery")
st.markdown("Visão geral de performance ( iFood e 99food).")

# --- Barra Lateral para Filtros e Status ---
st.sidebar.header("🗓️ Período de Análise")
sales_channels = ["","iFood", "99food"]

start_date = st.sidebar.date_input("Data Inicial", (datetime.now() - timedelta(days=1)).date())
end_date = st.sidebar.date_input("Data Final", datetime.now().date())

# ✅ Canal de vendas na barra lateral
f_sales_channel = st.sidebar.selectbox("Selecione o canal de vendas:", sales_channels)

if start_date > end_date:
    st.sidebar.error("⚠️ Erro: A data inicial não pode ser posterior à data final.")
else:
    # --- Criação das Abas ---
    tab_revenue, tab_products , tab_subitem = st.tabs(["Performance Vendas", "Performance de Produtos", "Preferencias Cliente"])

    # ---- Aba de Resumo de Receita ----
    with tab_revenue:
        tab_revenue_analysis(start_date, end_date, sales_channel=f_sales_channel)

    # ---- Aba de Performance de Produtos ----
    with tab_products:
        product_df = tab_product_analysis(start_date, end_date, f_sales_channel)
        
    with tab_subitem:
        product_df = tab_subitem_analysis(start_date, end_date, f_sales_channel)

    # --- Status de Processamento na Barra Lateral ---
    st.sidebar.markdown("---")
    st.sidebar.header("🔄 Status de Processamento")
    last_run_df = read_process_last_run(["BIG_QUERY_PROCESS"])
    if not last_run_df.empty:
        for index, row in last_run_df.iterrows():
            st.sidebar.info(f"**{row['name']}**\nÚltima atualização: {row['last_run_date'].strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        st.sidebar.warning("Nenhum dado de status encontrado.")