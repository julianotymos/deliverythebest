import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from read_customer_frequency_data import  read_total_customers_count , read_customer_frequency_data
st.set_page_config(layout="wide")
st.title("Frequência de Compras de Clientes")

sales_channels = [
    "",          # opção para não enviar filtro
    "Loja",
    "iFood",
    "99food",
    "Loja/iFood",
    "Loja/99food",
    "iFood/99food",
    "Loja/iFood/99food"
]

# Filtros na barra lateral
with st.sidebar:
    st.subheader("Filtros")
    f_sales_channel = st.selectbox("Selecione o canal de vendas:",
    sales_channels
)
    f_name = st.text_input("Nome do Cliente")
    f_phone = st.text_input("Telefone")
    f_doc = st.text_input("CPF")

# Total de clientes considerando filtros
total_customers = read_total_customers_count(
    sales_channel=f_sales_channel or None,
    name=f_name or None,
    phone_number=f_phone or None,
    document_number=f_doc or None
)

rows_per_page_options = [25, 50, 100, 200]

bottom_menu = st.columns((4, 1, 1))
with bottom_menu[2]:
    rows_per_page = st.selectbox("Linhas por Página", options=rows_per_page_options)

with bottom_menu[1]:
    total_pages = (total_customers // rows_per_page) + (1 if total_customers % rows_per_page > 0 else 0)
    current_page = st.number_input("Página", min_value=1, max_value=max(total_pages,1), step=1)

with bottom_menu[0]:
    st.markdown(f"Página **{current_page}** de **{total_pages}** ")

# Dados da página atual
df_customers = read_customer_frequency_data(
    page_number=current_page,
    rows_per_page=rows_per_page,
    sales_channel=f_sales_channel or None,
    name=f_name or None,
    phone_number=f_phone or None,
    document_number=f_doc or None
)

if not df_customers.empty:
    st.dataframe(df_customers, use_container_width=True)
    st.caption(
        f"Exibindo clientes de {((current_page - 1) * rows_per_page) + 1} "
        f"a {min(current_page * rows_per_page, total_customers)} "
        f"de um total de {total_customers}."
    )
else:
    st.info("Não foi possível carregar os dados. Verifique os filtros ou a conexão com o BigQuery.")