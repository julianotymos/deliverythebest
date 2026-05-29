import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from datetime import date


def read_accompaniment_performance(start_date: date, end_date: date, sales_channel: str = None, customer_type: str = None):
    client = get_bigquery_client()

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    where_channel_clause = ""
    if sales_channel:
        where_channel_clause = f"AND ot.SALES_CHANNEL = '{sales_channel}'"

    where_customer_clause = ""
    if customer_type == "Novo":
        where_customer_clause = """
        AND (
            (ot.SALES_CHANNEL = 'iFood' AND ot.TOTAL_ORDERS = 1)
            OR (ot.SALES_CHANNEL = '99food' AND ot.TOTAL_ORDERS <= 2)
            OR (ot.SALES_CHANNEL = 'keeta' AND ot.TOTAL_ORDERS = 1)
        )
        """
    elif customer_type == "Recorrente":
        where_customer_clause = """
        AND (
            (ot.SALES_CHANNEL = 'iFood' AND ot.TOTAL_ORDERS > 1)
            OR (ot.SALES_CHANNEL = '99food' AND ot.TOTAL_ORDERS > 2)
            OR (ot.SALES_CHANNEL = 'keeta' AND ot.TOTAL_ORDERS > 1)
        )
        """

    query = f"""
    WITH base AS (
        SELECT
            bsi.NAME                                                AS acompanhamento,
            ot.SALES_CHANNEL,
            bsi.QUANTITY,
            bsi.TOTAL_EFFECTIVE_UNIT_PRICE_VALUE                   AS item_revenue,
            bsi.TOTAL_EFFECTIVE_UNIT_PRICE_VALUE
                / ot.TOTAL_BAG_DETAIL
                * CASE WHEN ot.FEE_TRANSACTION_PAYMENT IS NULL
                       THEN ot.TOTAL_BAG_DETAIL - 3
                       ELSE ot.NET_VALUE END                        AS item_received,
            bsi.QUANTITY * COALESCE(a.COST, 0)                     AS item_cost,
            CASE WHEN a.NAME IS NULL THEN 'Não' ELSE 'Sim' END     AS custo_cadastrado
        FROM BAG_SUB_ITEMS bsi
        INNER JOIN BAG_ITEMS bi ON bi.ID = bsi.BAG_ITEMS_ID
        INNER JOIN ORDERS_TABLE ot ON ot.ID = bi.ORDER_ID
        LEFT JOIN ACCOMPANIMENT a
            ON a.NAME = bsi.NAME
            AND DATE(ot.CREATED_AT) BETWEEN a.VALID_FROM_DATE AND a.VALID_TO_DATE
        LEFT JOIN PRODUCT_EXCEPTION pe ON pe.NAME = bsi.NAME
        WHERE ot.current_status IN ('CONCLUDED', 'PARTIALLY_CANCELLED', 'CONFIRMED')
          AND DATE(ot.CREATED_AT) BETWEEN '{start_date_str}' AND '{end_date_str}'
          AND bsi.TOTAL_EFFECTIVE_UNIT_PRICE_VALUE > 0
          AND pe.ID IS NULL
          {where_channel_clause}
          {where_customer_clause}
    )
    SELECT
        acompanhamento,
        STRING_AGG(DISTINCT SALES_CHANNEL, ', ' ORDER BY SALES_CHANNEL) AS canais,
        SUM(QUANTITY)                                                    AS qtd_itens,
        ROUND(SUM(item_revenue), 2)                                      AS faturamento,
        ROUND(SUM(item_received), 2)                                     AS recebido,
        ROUND(SUM(item_cost), 2)                                         AS custo,
        ROUND(SUM(item_received) - SUM(item_cost), 2)                   AS lucro_real,
        ROUND((SUM(item_received) - SUM(item_cost))
            / NULLIF(SUM(item_cost), 0) * 100, 2)                       AS markup,
        ROUND((SUM(item_received) - SUM(item_cost))
            / NULLIF(SUM(item_received), 0) * 100, 2)                   AS margem,
        MAX(custo_cadastrado)                                            AS custo_cadastrado
    FROM base
    GROUP BY acompanhamento
    ORDER BY qtd_itens DESC
    """

    try:
        df = client.query(query).to_dataframe()
        df = df.rename(columns={
            "acompanhamento":   "Acompanhamento",
            "canais":           "Canais",
            "qtd_itens":        "Quantidade",
            "faturamento":      "Faturamento",
            "recebido":         "Recebido",
            "custo":            "Custo",
            "lucro_real":       "Lucro Real",
            "markup":           "Markup (%)",
            "margem":           "Margem (%)",
            "custo_cadastrado": "Custo Cadastrado",
        })
        return df
    except Exception as e:
        st.error(f"Erro ao buscar performance de acompanhamentos: {e}")
        return pd.DataFrame()
