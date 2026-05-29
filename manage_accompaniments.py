from get_bigquery_client import get_bigquery_client
import streamlit as st
import pandas as pd

def list_all_accompaniments():
    client = get_bigquery_client()
    query = """
    SELECT
        A.ID,
        A.NAME        AS Acompanhamento,
        A.COST        AS Custo,
        S.SHORT_DESC  AS Status,
        A.VALID_FROM_DATE AS Vigencia_Inicio,
        A.VALID_TO_DATE   AS Vigencia_Fim,
        A.INSERT_DATE,
        A.UPDATE_DATE
    FROM
        ACCOMPANIMENT A
    INNER JOIN
        STATUS S ON S.ID = A.STATUS
    ORDER BY
        A.VALID_FROM_DATE DESC, A.NAME ASC
    """
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao listar acompanhamentos: {e}")
        return pd.DataFrame()

def check_accompaniment_overlap(name, start_date, end_date, exclude_id=None):
    client = get_bigquery_client()
    where_id = f"AND ID != {exclude_id}" if exclude_id else ""
    query = f"""
    SELECT COUNT(1) as total
    FROM ACCOMPANIMENT
    WHERE NAME = '{name}'
      AND VALID_FROM_DATE <= '{end_date}'
      AND VALID_TO_DATE >= '{start_date}'
      {where_id}
    """
    try:
        df = client.query(query).to_dataframe()
        return df.iloc[0]['total'] > 0
    except Exception:
        return True

def insert_accompaniment(name, cost, start_date, end_date, status_id):
    client = get_bigquery_client()
    query_id = "SELECT COALESCE(MAX(ID), 0) + 1 as next_id FROM ACCOMPANIMENT"
    next_id = client.query(query_id).to_dataframe().iloc[0]['next_id']

    query = f"""
    INSERT INTO ACCOMPANIMENT (ID, NAME, COST, STATUS, VALID_FROM_DATE, VALID_TO_DATE, INSERT_DATE, UPDATE_DATE)
    VALUES ({next_id}, '{name}', {cost}, {status_id}, '{start_date}', '{end_date}', CURRENT_TIMESTAMP(), NULL)
    """
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir: {e}")
        return False

def update_accompaniment(accompaniment_id, name, cost, start_date, end_date, status_id):
    client = get_bigquery_client()
    query = f"""
    UPDATE ACCOMPANIMENT
    SET NAME            = '{name}',
        COST            = {cost},
        STATUS          = {status_id},
        VALID_FROM_DATE = '{start_date}',
        VALID_TO_DATE   = '{end_date}',
        UPDATE_DATE     = CURRENT_TIMESTAMP()
    WHERE ID = {accompaniment_id}
    """
    try:
        client.query(query).result()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False

def delete_accompaniment(accompaniment_id):
    client = get_bigquery_client()
    query = f"DELETE FROM ACCOMPANIMENT WHERE ID = {accompaniment_id}"
    try:
        client.query(query).result()
        return True
    except Exception:
        return False

def get_status_options():
    client = get_bigquery_client()
    query = "SELECT ID, SHORT_DESC FROM STATUS WHERE ID IN (1, 2)"
    return client.query(query).to_dataframe()
