import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from datetime import date


#@st.cache_data(ttl=600, show_spinner=False)
def read_revenue_period(start_date: date, end_date: date, sales_channel: str = None, customer_type: str = None):
    """
    Retorna métricas de faturamento, custo, lucro, margem e clientes
    entre as datas informadas (inclusive).

    :param start_date: Data inicial (datetime.date)
    :param end_date: Data final (datetime.date)
    :param sales_channel: Canal de vendas (opcional)
    """

    client = get_bigquery_client()

    # Converter para string no formato YYYY-MM-DD
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Cláusula WHERE condicional para o canal de vendas
    where_channel_clause = ""
    if sales_channel:
        where_channel_clause = f"AND ot.sales_channel = '{sales_channel}'"

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
            OR (ot.SALES_CHANNEL = 'keeta' AND ot.TOTAL_ORDERS > 1 )
        )
        """

    query = f"""
    WITH base_data AS (
        SELECT
            DATE(ot.CREATED_AT, "America/Sao_Paulo") AS order_date,
            ot.SALES_CHANNEL,
            bi.quantity,
            -- faturamento corrigido: 99food não inclui adicionais pagos no sub_total_value
            bi.sub_total_value + CASE
                WHEN ot.SALES_CHANNEL = '99food' THEN COALESCE(paid_subs.paid_subitems_value, 0)
                ELSE 0
            END AS item_revenue,
            ot.total_bag_detail,
            -- valor recebido: usa net_value quando disponível, senão estima total - R$3 de taxa
            CASE WHEN ot.FEE_TRANSACTION_PAYMENT IS NULL
                 THEN ot.total_bag_detail - 3
                 ELSE ot.net_value END AS order_net_value,
            p.cost * bi.quantity + COALESCE(acc_cost.accompaniment_cost, 0) AS item_cost
        FROM BAG_ITEMS bi
        INNER JOIN ORDERS_TABLE ot ON ot.id = bi.ORDER_ID
        LEFT JOIN (
            SELECT P.NAME, P.COST, P.VALID_FROM_DATE, P.VALID_TO_DATE, CH.SALES_CHANNEL_ID AS SALES_CHANNEL
            FROM PRODUCT P
            INNER JOIN SALES_CHANNEL CH ON CH.ID = P.SALES_CHANNEL
        ) p ON p.name = bi.name
            AND p.sales_channel = ot.SALES_CHANNEL
            AND DATE(ot.CREATED_AT, "America/Sao_Paulo") BETWEEN p.VALID_FROM_DATE AND p.VALID_TO_DATE
        LEFT JOIN (
            SELECT
                BAG_ITEMS_ID,
                SUM(TOTAL_EFFECTIVE_UNIT_PRICE_VALUE) AS paid_subitems_value
            FROM BAG_SUB_ITEMS
            WHERE TOTAL_EFFECTIVE_UNIT_PRICE_VALUE > 0
            GROUP BY BAG_ITEMS_ID
        ) paid_subs ON paid_subs.BAG_ITEMS_ID = bi.ID
        LEFT JOIN (
            SELECT
                bsi.BAG_ITEMS_ID,
                SUM(bsi.QUANTITY * a.COST) AS accompaniment_cost
            FROM BAG_SUB_ITEMS bsi
            INNER JOIN BAG_ITEMS bi2 ON bi2.ID = bsi.BAG_ITEMS_ID
            INNER JOIN ORDERS_TABLE ot2 ON ot2.ID = bi2.ORDER_ID
            INNER JOIN ACCOMPANIMENT a
                ON a.NAME = bsi.NAME
                AND DATE(ot2.CREATED_AT, "America/Sao_Paulo") BETWEEN a.VALID_FROM_DATE AND a.VALID_TO_DATE
            WHERE DATE(ot2.CREATED_AT, "America/Sao_Paulo") BETWEEN '{start_date_str}' AND '{end_date_str}'
            GROUP BY bsi.BAG_ITEMS_ID
        ) acc_cost ON acc_cost.BAG_ITEMS_ID = bi.ID
        WHERE ot.current_status IN ('CONCLUDED', 'PARTIALLY_CANCELLED', 'CONFIRMED')
          AND DATE(ot.CREATED_AT, "America/Sao_Paulo") BETWEEN '{start_date_str}' AND '{end_date_str}'
          {where_channel_clause}
          {where_customer_clause}
    )
    SELECT
        bd.order_date,
        STRING_AGG(DISTINCT bd.SALES_CHANNEL, ', ' ORDER BY bd.SALES_CHANNEL) AS Canais,
        SUM(bd.item_revenue)                                                                          AS revenue,
        SUM(bd.item_cost)                                                                             AS cost,
        ROUND(SUM((bd.item_revenue / bd.total_bag_detail) * bd.order_net_value), 2)                  AS received,
        ROUND(SUM((bd.item_revenue / bd.total_bag_detail) * bd.order_net_value - bd.item_cost), 2)   AS net_profit,
        ROUND(SUM((bd.item_revenue / bd.total_bag_detail) * bd.order_net_value - bd.item_cost)
            / NULLIF(SUM((bd.item_revenue / bd.total_bag_detail) * bd.order_net_value), 0) * 100, 2) AS margin,
        ROUND(SUM((bd.item_revenue / bd.total_bag_detail) * bd.order_net_value - bd.item_cost)
            / NULLIF(SUM(bd.item_cost), 0) * 100, 2)                                                 AS markup,
        COUNT(1)                                                                  AS items,
        QOT.QTY_PEDIDOS                                                           AS orders_count,
        QOT.NOVOS_CLIENTES                                                        AS new_customers,
        QOT.CLIENTES_RECORRENTES                                                  AS returning_customers,
        ROUND(ANY_VALUE(QOT.TP7) / QOT.QTY_PEDIDOS * 100, 2)                    AS TP7,
        ROUND(ANY_VALUE(QOT.TP6) / QOT.QTY_PEDIDOS * 100, 2)                    AS TP6,
        ROUND(ANY_VALUE(QOT.TP5) / QOT.QTY_PEDIDOS * 100, 2)                    AS TP5
    FROM base_data bd
    LEFT JOIN (
        SELECT DATE(ot.CREATED_AT, "America/Sao_Paulo") AS order_date,
               COUNT(1) AS QTY_PEDIDOS,
               SUM(CASE
                   WHEN ot.SALES_CHANNEL = 'iFood'  AND ot.TOTAL_ORDERS = 1  THEN 1
                   WHEN ot.SALES_CHANNEL = 'keeta'  AND ot.TOTAL_ORDERS = 1  THEN 1
                   WHEN ot.SALES_CHANNEL = '99food' AND ot.TOTAL_ORDERS <= 2 THEN 1
                   ELSE 0
               END) AS NOVOS_CLIENTES,
               SUM(CASE
                   WHEN ot.SALES_CHANNEL = 'iFood'  AND ot.TOTAL_ORDERS > 1 THEN 1
                   WHEN ot.SALES_CHANNEL = 'keeta'  AND ot.TOTAL_ORDERS > 1 THEN 1
                   WHEN ot.SALES_CHANNEL = '99food' AND ot.TOTAL_ORDERS > 2 THEN 1
                   ELSE 0
               END) AS CLIENTES_RECORRENTES,
               SUM(CASE WHEN ot.PREPARATION_TIME > 7 THEN 1 ELSE 0 END) AS TP7,
               SUM(CASE WHEN ot.PREPARATION_TIME > 6 THEN 1 ELSE 0 END) AS TP6,
               SUM(CASE WHEN ot.PREPARATION_TIME > 5 THEN 1 ELSE 0 END) AS TP5
        FROM ORDERS_TABLE ot
        WHERE ot.current_status IN ('CONCLUDED', 'PARTIALLY_CANCELLED', 'CONFIRMED')
          AND DATE(ot.CREATED_AT, "America/Sao_Paulo") BETWEEN '{start_date_str}' AND '{end_date_str}'
          {where_channel_clause}
          {where_customer_clause}
        GROUP BY DATE(ot.CREATED_AT, "America/Sao_Paulo")
    ) QOT ON QOT.order_date = bd.order_date
    GROUP BY
        bd.order_date,
        QOT.QTY_PEDIDOS,
        QOT.NOVOS_CLIENTES,
        QOT.CLIENTES_RECORRENTES
    ORDER BY bd.order_date DESC
    """

    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()
        df = df.rename(columns={
            'order_date': 'Data',
            'revenue': 'Faturamento',
            'cost': 'Custo',
            'received': 'Recebido',
            'net_profit': 'Lucro Líquido',
            'margin': 'Margem (%)',
            'markup': 'Markup (%)',
            'items': 'Itens Vendidos',
            'orders_count': 'Qtd. Pedidos',
            'new_customers': 'Novos Clientes',
            'returning_customers': 'Clientes Recorrentes',
            'TP7': 'TP>7 (%)',
            'TP6': 'TP>6 (%)',
            'TP5': 'TP>5 (%)'
            
        })
        return df
    except Exception as e:
        st.error(f"Erro ao buscar métricas de faturamento: {e}")
        return pd.DataFrame()
    
#start_date = st.date_input("Start Date", value=date(2025, 8, 1))
#end_date = st.date_input("End Date", value=date(2025, 8, 31))
##
#df = read_revenue_period(start_date, end_date , sales_channel='iFood' , customer_type = 'new')
#print(df)