import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from datetime import date


@st.cache_data(ttl=300, show_spinner=False)
def read_accompaniment_inconsistencies(start_date: date, end_date: date):
    client = get_bigquery_client()

    start_ts = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    end_ts   = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"

    query = f"""
    SELECT
        bsi.name                        AS acompanhamento_faltando,
        MIN(DATE(ot.created_at))        AS primeira_data_sem_cadastro,
        MAX(DATE(ot.created_at))        AS ultima_data_sem_cadastro,
        COUNT(*)                        AS qtd_linhas,
        SUM(bsi.quantity)               AS qtd_itens,
        ROUND(SUM(bsi.total_effective_unit_price_value), 2) AS total_cobrado

    FROM BAG_SUB_ITEMS bsi
    INNER JOIN BAG_ITEMS bi
        ON bi.id = bsi.bag_items_id
    INNER JOIN ORDERS_TABLE ot
        ON ot.id = bi.order_id
    LEFT JOIN ACCOMPANIMENT a
        ON a.name = bsi.name
        AND DATE(ot.created_at) BETWEEN a.valid_from_date AND a.valid_to_date
    LEFT JOIN PRODUCT_EXCEPTION pe
        ON pe.name = bsi.name

    WHERE
        ot.created_at BETWEEN TIMESTAMP('{start_ts}') AND TIMESTAMP('{end_ts}')
        AND bsi.total_effective_unit_price_value > 0
        AND a.name IS NULL
        AND pe.name IS NULL

    GROUP BY
        bsi.name

    ORDER BY
        qtd_itens DESC
    """

    df = client.query(query).to_dataframe()
    df = df.rename(columns={
        "acompanhamento_faltando": "Acompanhamento",
        "primeira_data_sem_cadastro": "Primeira Venda Sem Cadastro",
        "ultima_data_sem_cadastro": "Última Venda Sem Cadastro",
        "qtd_linhas": "Qtd Pedidos",
        "qtd_itens": "Qtd Itens",
        "total_cobrado": "Total Cobrado (R$)",
    })
    return df


@st.cache_data(ttl=300, show_spinner=False)
def read_accompaniment_overlap_inconsistencies():
    """
    Retorna pares de cadastros do mesmo acompanhamento com vigências sobrepostas.
    """
    client = get_bigquery_client()

    query = """
    SELECT
        a1.ID           AS ID_1,
        a2.ID           AS ID_2,
        a1.NAME         AS ACCOMPANIMENT_NAME,
        a1.VALID_FROM_DATE AS VALID_FROM_1,
        a1.VALID_TO_DATE   AS VALID_TO_1,
        a1.COST            AS COST_1,
        a2.VALID_FROM_DATE AS VALID_FROM_2,
        a2.VALID_TO_DATE   AS VALID_TO_2,
        a2.COST            AS COST_2

    FROM ACCOMPANIMENT a1
    INNER JOIN ACCOMPANIMENT a2
        ON a1.NAME = a2.NAME
        AND a1.ID < a2.ID
        AND a1.VALID_FROM_DATE <= COALESCE(a2.VALID_TO_DATE, DATE '9999-12-31')
        AND a2.VALID_FROM_DATE <= COALESCE(a1.VALID_TO_DATE, DATE '9999-12-31')

    ORDER BY
        a1.NAME,
        a1.VALID_FROM_DATE
    """

    df = client.query(query).to_dataframe()
    df = df.rename(columns={
        "ID_1": "ID Cadastro 1",
        "ID_2": "ID Cadastro 2",
        "ACCOMPANIMENT_NAME": "Acompanhamento",
        "VALID_FROM_1": "Início Vigência 1",
        "VALID_TO_1": "Fim Vigência 1",
        "COST_1": "Custo 1 (R$)",
        "VALID_FROM_2": "Início Vigência 2",
        "VALID_TO_2": "Fim Vigência 2",
        "COST_2": "Custo 2 (R$)",
    })
    return df
