import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from datetime import date


def read_product_inconsistencies(start_date: date, end_date: date):
    """
    Retorna produtos vendidos que não possuem cadastro válido (nome + canal + vigência)
    no período informado.
    """
    client = get_bigquery_client()

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    query = f"""
    SELECT
        bi.name AS produto_faltando,
        ot.sales_channel,

        MIN(DATE(ot.created_at)) AS primeira_data_sem_cadastro,
        MAX(DATE(ot.created_at)) AS ultima_data_sem_cadastro,

        COUNT(*) AS qtd_linhas,
        SUM(bi.quantity) AS qtd_itens,
        ROUND(SUM(bi.sub_total_value), 2) AS total_venda

    FROM BAG_ITEMS bi
    INNER JOIN ORDERS_TABLE ot
        ON ot.id = bi.order_id

    WHERE
        DATE(ot.created_at) BETWEEN '{start_date_str}' AND '{end_date_str}'

        AND NOT EXISTS (
            SELECT 1
            FROM PRODUCT p
            INNER JOIN SALES_CHANNEL ch
                ON ch.id = p.sales_channel
            WHERE
                p.name = bi.name
                AND ch.sales_channel_id = ot.sales_channel
                AND DATE(ot.created_at) BETWEEN p.valid_from_date AND p.valid_to_date
        )

    GROUP BY
        bi.name,
        ot.sales_channel

    ORDER BY
        qtd_itens DESC
    """

    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()
        df = df.rename(columns={
            "produto_faltando": "Produto",
            "sales_channel": "Canal",
            "primeira_data_sem_cadastro": "Primeira Venda Sem Cadastro",
            "ultima_data_sem_cadastro": "Última Venda Sem Cadastro",
            "qtd_linhas": "Qtd Pedidos",
            "qtd_itens": "Qtd Itens",
            "total_venda": "Total Vendido (R$)",
        })
        return df
    except Exception as e:
        st.error(f"Erro ao buscar inconsistências de produtos: {e}")
        return pd.DataFrame()


def read_product_overlap_inconsistencies():
    """
    Retorna pares de cadastros do mesmo produto/canal com vigências sobrepostas.
    """
    client = get_bigquery_client()

    query = """
    SELECT
        p1.ID AS PRODUCT_ID_1,
        p2.ID AS PRODUCT_ID_2,
        p1.NAME AS PRODUCT_NAME,
        ch.SALES_CHANNEL_ID AS SALES_CHANNEL,

        p1.VALID_FROM_DATE AS VALID_FROM_1,
        p1.VALID_TO_DATE AS VALID_TO_1,
        p1.COST AS COST_1,

        p2.VALID_FROM_DATE AS VALID_FROM_2,
        p2.VALID_TO_DATE AS VALID_TO_2,
        p2.COST AS COST_2

    FROM PRODUCT p1
    INNER JOIN PRODUCT p2
        ON p1.NAME = p2.NAME
        AND p1.ID < p2.ID
        AND p1.SALES_CHANNEL = p2.SALES_CHANNEL
        AND p1.VALID_FROM_DATE <= COALESCE(p2.VALID_TO_DATE, DATE '9999-12-31')
        AND p2.VALID_FROM_DATE <= COALESCE(p1.VALID_TO_DATE, DATE '9999-12-31')

    INNER JOIN SALES_CHANNEL ch
        ON ch.ID = p1.SALES_CHANNEL

    ORDER BY
        p1.NAME,
        ch.SALES_CHANNEL_ID,
        p1.VALID_FROM_DATE
    """

    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()
        df = df.rename(columns={
            "PRODUCT_ID_1": "ID Cadastro 1",
            "PRODUCT_ID_2": "ID Cadastro 2",
            "PRODUCT_NAME": "Produto",
            "SALES_CHANNEL": "Canal",
            "VALID_FROM_1": "Início Vigência 1",
            "VALID_TO_1": "Fim Vigência 1",
            "COST_1": "Custo 1 (R$)",
            "VALID_FROM_2": "Início Vigência 2",
            "VALID_TO_2": "Fim Vigência 2",
            "COST_2": "Custo 2 (R$)",
        })
        return df
    except Exception as e:
        st.error(f"Erro ao buscar sobreposições de vigência: {e}")
        return pd.DataFrame()
