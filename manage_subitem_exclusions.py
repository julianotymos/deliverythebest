from get_bigquery_client import get_bigquery_client
import streamlit as st
import pandas as pd


def list_subitem_exclusions():
    client = get_bigquery_client()
    query = """
    SELECT ID, NAME AS Subitem, REASON AS Motivo, INSERT_DATE AS Cadastrado_Em
    FROM SUBITEM_EXCLUSION
    ORDER BY NAME ASC
    """
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao listar exclusões: {e}")
        return pd.DataFrame()


def insert_subitem_exclusion(name, reason):
    client = get_bigquery_client()
    query_id = "SELECT COALESCE(MAX(ID), 0) + 1 AS next_id FROM SUBITEM_EXCLUSION"
    next_id = client.query(query_id).to_dataframe().iloc[0]['next_id']

    name_escaped = name.replace("'", "\\'")
    reason_escaped = reason.replace("'", "\\'")

    query = f"""
    INSERT INTO SUBITEM_EXCLUSION (ID, NAME, REASON, INSERT_DATE)
    VALUES ({next_id}, '{name_escaped}', '{reason_escaped}', CURRENT_TIMESTAMP())
    """
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir exclusão: {e}")
        return False


def delete_subitem_exclusion(exclusion_id):
    client = get_bigquery_client()
    query = f"DELETE FROM SUBITEM_EXCLUSION WHERE ID = {exclusion_id}"
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao remover exclusão: {e}")
        return False
