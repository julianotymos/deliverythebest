from get_bigquery_client import get_bigquery_client
import streamlit as st
import pandas as pd


def list_exceptions():
    client = get_bigquery_client()
    query = """
    SELECT ID, NAME AS Produto, REASON AS Motivo, INSERT_DATE AS Cadastrado_Em
    FROM PRODUCT_EXCEPTION
    ORDER BY NAME ASC
    """
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao listar exceções: {e}")
        return pd.DataFrame()


def insert_exception(name, reason):
    client = get_bigquery_client()
    query_id = "SELECT COALESCE(MAX(ID), 0) + 1 AS next_id FROM PRODUCT_EXCEPTION"
    next_id = client.query(query_id).to_dataframe().iloc[0]['next_id']

    name_escaped = name.replace("'", "\\'")
    reason_escaped = reason.replace("'", "\\'")

    query = f"""
    INSERT INTO PRODUCT_EXCEPTION (ID, NAME, REASON, INSERT_DATE)
    VALUES ({next_id}, '{name_escaped}', '{reason_escaped}', CURRENT_TIMESTAMP())
    """
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir exceção: {e}")
        return False


def delete_exception(exception_id):
    client = get_bigquery_client()
    query = f"DELETE FROM PRODUCT_EXCEPTION WHERE ID = {exception_id}"
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao remover exceção: {e}")
        return False
