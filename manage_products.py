from get_bigquery_client import get_bigquery_client
import streamlit as st
import pandas as pd
from datetime import date

def list_all_products_detailed():
    """Retorna todos os produtos cadastrados com nomes de canais e status."""
    client = get_bigquery_client()
    query = """
    SELECT 
        P.ID,
        P.NAME as Produto,
        SC.SALES_CHANNEL_ID AS Canal,
        P.CATEGORY as Categoria,
        P.COST as Custo,
        S.SHORT_DESC AS Status,
        P.VALID_FROM_DATE as Vigencia_Inicio,
        P.VALID_TO_DATE as Vigencia_Fim
    FROM
        PRODUCT P
    INNER JOIN
        STATUS S ON S.ID = P.STATUS
    INNER JOIN
        SALES_CHANNEL SC ON SC.ID = P.SALES_CHANNEL
    ORDER BY
        P.VALID_FROM_DATE DESC, P.NAME ASC
    """
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return pd.DataFrame()

def check_product_overlap(name, channel_id, start_date, end_date, exclude_id=None):
    """Verifica sobreposição de vigência."""
    client = get_bigquery_client()
    where_id = f"AND ID != {exclude_id}" if exclude_id else ""
    query = f"""
    SELECT COUNT(1) as total
    FROM PRODUCT
    WHERE NAME = '{name}'
      AND SALES_CHANNEL = {channel_id}
      AND VALID_FROM_DATE <= '{end_date}'
      AND VALID_TO_DATE >= '{start_date}'
      {where_id}
    """
    try:
        df = client.query(query).to_dataframe()
        return df.iloc[0]['total'] > 0
    except Exception:
        return True

def insert_product(name, channel_id, category, cost, start_date, end_date, status_id):
    """Insere um novo produto com status."""
    client = get_bigquery_client()
    query_id = "SELECT COALESCE(MAX(ID), 0) + 1 as next_id FROM PRODUCT"
    next_id = client.query(query_id).to_dataframe().iloc[0]['next_id']

    query = f"""
    INSERT INTO PRODUCT (ID, NAME, SALES_CHANNEL, CATEGORY, COST, STATUS, VALID_FROM_DATE, VALID_TO_DATE)
    VALUES ({next_id}, '{name}', {channel_id}, '{category}', {cost}, {status_id}, '{start_date}', '{end_date}')
    """
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir: {e}")
        return False

def update_product(product_id, name, channel_id, category, cost, start_date, end_date, status_id):
    """Atualiza produto incluindo o status."""
    client = get_bigquery_client()
    query = f"""
    UPDATE PRODUCT 
    SET NAME = '{name}', 
        SALES_CHANNEL = {channel_id}, 
        CATEGORY = '{category}', 
        COST = {cost}, 
        STATUS = {status_id},
        VALID_FROM_DATE = '{start_date}', 
        VALID_TO_DATE = '{end_date}'
    WHERE ID = {product_id}
    """
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False

def delete_product(product_id):
    """Remove produto."""
    client = get_bigquery_client()
    query = f"DELETE FROM PRODUCT WHERE ID = {product_id}"
    try:
        client.query(query).result()
        return True
    except Exception:
        return False

def get_channels():
    """Busca canais."""
    client = get_bigquery_client()
    query = "SELECT ID, SALES_CHANNEL_ID FROM SALES_CHANNEL"
    return client.query(query).to_dataframe()

def get_status_options():
    """Busca opções de status disponíveis."""
    client = get_bigquery_client()
    query = "SELECT ID, SHORT_DESC FROM STATUS WHERE ID IN (1, 2)" # 1=Disponível, 2=Indisponível (Padrão)
    return client.query(query).to_dataframe()
