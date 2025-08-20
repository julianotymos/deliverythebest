import datetime
import random

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from read_products_joined_data import read_products_joined_data
from read_products_for_editing import read_products_for_editing
# Show app title and description.
# Título da Aplicação
# Título da Aplicação
st.title("Gerenciamento de Produtos")

# 1. Exibir o Grid Principal e Capturar a Linha Clicada
st.subheader("Lista de Produtos")
df_products_list = read_products_joined_data()
selection = st.dataframe(
    df_products_list,
    on_select="rerun",
    selection_mode="single-row",
    hide_index=True
)

# 2. Exibir a Tela de Histórico e Edição se uma Linha for Selecionada
if selection["selection"]["rows"]:
    selected_index = selection["selection"]["rows"][0]
    selected_row = df_products_list.iloc[[selected_index]]
    
    product_name_to_search = selected_row['NAME'].iloc[0]
    sales_channel_to_search = selected_row['CHANNEL'].iloc[0]

    all_records, last_record = read_products_for_editing(product_name_to_search, sales_channel_to_search)

    st.markdown("---")
    st.subheader(f"Histórico de Vigências para: {product_name_to_search} ({sales_channel_to_search})")
    st.dataframe(all_records.reset_index(drop=True))

    st.markdown("---")
    st.subheader("Editar Último Registro de Vigência")

    if not last_record.empty:
        category_options = ['Preparado', 'Pronto']
        status_options = ['Disponível', 'Indisponível']
        channel_options = ['iFood', '99Food']

        default_category_index = category_options.index(last_record['CATEGORY']) if last_record['CATEGORY'] in category_options else 0
        default_status_index = status_options.index(last_record['STATUS']) if last_record['STATUS'] in status_options else 0
        default_channel_index = channel_options.index(last_record['CHANNEL']) if last_record['CHANNEL'] in channel_options else 0
        
        valid_from = pd.to_datetime(last_record['VALID_FROM_DATE']).date()
        valid_to = pd.to_datetime(last_record['VALID_TO_DATE']).date()

        with st.form(key="edit_form"):
            # **Capturando os valores de cada campo em variáveis**
            name = st.text_input("Nome", value=last_record['NAME'])
            cost = st.number_input("Custo", value=last_record['COST'])

            category = st.selectbox("Categoria", options=category_options, index=default_category_index)
            status = st.selectbox("Status", options=status_options, index=default_status_index)
            channel = st.selectbox("Canal", options=channel_options, index=default_channel_index)

            date_start = st.date_input("Data de Início da Vigência", value=valid_from)
            date_end = st.date_input("Data de Fim da Vigência", value=valid_to)

            submit_button = st.form_submit_button(label="Salvar Alterações")
            
            if submit_button:
                # **Aqui você acessa os valores e formata as datas**
                st.success("Valores capturados no submit:")
                st.write(f"Nome: {name}")
                st.write(f"Custo: {cost}")
                st.write(f"Categoria: {category}")
                st.write(f"Status: {status}")
                st.write(f"Canal: {channel}")

                # **Formatando as datas para o padrão dd/mm/yyyy**
                formatted_date_start = date_start.strftime("%d/%m/%Y")
                formatted_date_end = date_end.strftime("%d/%m/%Y")
                st.write(f"Data de Início (formatada): {formatted_date_start}")
                st.write(f"Data de Fim (formatada): {formatted_date_end}")

                # A lógica de UPDATE seria chamada aqui, usando as variáveis.
                # Exemplo: update_product_in_bigquery(name, cost, category, ...)