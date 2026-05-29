import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from datetime import date

#@st.cache_data(ttl=600, show_spinner=False)
def read_order_performance(order_date: date, sales_channel: str = None , customer_type: str = None):
    """
    Retorna métricas detalhadas por pedido (itens, valor, custo, lucro, markup)
    no período informado e para o canal de vendas especificado (opcional).
    """

    client = get_bigquery_client()
    
    # Removi a lógica de sales_channel_id, pois não é utilizada na query SQL.
    # O filtro agora é feito diretamente pelo nome do canal.

    # Converter datas para string no formato YYYY-MM-DD
    order_date_str = order_date.strftime("%Y-%m-%d")
    
    # Cláusula WHERE condicional para o canal de vendas
    where_channel_clause = ""
    if sales_channel:
        where_channel_clause = f"AND ot.SALES_CHANNEL = '{sales_channel}'"

    where_customer_clause = ""
    if customer_type == "Novo":
        where_customer_clause = """
        AND (
            (ot.SALES_CHANNEL = 'iFood' AND ot.TOTAL_ORDERS = 1)
            OR (ot.SALES_CHANNEL = '99food' AND ot.TOTAL_ORDERS <= 2)
            OR (ot.SALES_CHANNEL = 'keeta' AND ot.TOTAL_ORDERS = 1 )
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
            ot.ID                   AS order_id,
            ot.SHORT_ID,
            ot.SALES_CHANNEL,
            ot.TOTAL_ORDERS,
            ot.CREATED_AT,
            ot.PREPARATION_TIME,
            ot.TOTAL_BAG_DETAIL,
            p.NAME                  AS product_name,
            bi.QUANTITY,
            bi.sub_total_value + CASE
                WHEN ot.SALES_CHANNEL = '99food' THEN COALESCE(paid_subs.paid_subitems_value, 0)
                ELSE 0
            END AS item_revenue,
            CASE WHEN ot.FEE_TRANSACTION_PAYMENT IS NULL
                 THEN ot.total_bag_detail - 3
                 ELSE ot.net_value END AS order_net_value,
            p.cost * bi.QUANTITY + COALESCE(acc_cost.accompaniment_cost, 0) AS item_cost
        FROM BAG_ITEMS bi
        INNER JOIN ORDERS_TABLE ot ON ot.ID = bi.ORDER_ID
        LEFT JOIN (
            SELECT P.NAME, P.COST, P.VALID_FROM_DATE, P.VALID_TO_DATE, CH.SALES_CHANNEL_ID AS SALES_CHANNEL
            FROM PRODUCT P
            INNER JOIN SALES_CHANNEL CH ON CH.ID = P.SALES_CHANNEL
        ) p ON p.name = bi.name
            AND p.sales_channel = ot.SALES_CHANNEL
            AND DATE(ot.CREATED_AT) BETWEEN p.VALID_FROM_DATE AND p.VALID_TO_DATE
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
                AND DATE(ot2.CREATED_AT) BETWEEN a.VALID_FROM_DATE AND a.VALID_TO_DATE
            WHERE DATE(ot2.CREATED_AT) = '{order_date_str}'
            GROUP BY bsi.BAG_ITEMS_ID
        ) acc_cost ON acc_cost.BAG_ITEMS_ID = bi.ID
        WHERE ot.current_status IN ('CONCLUDED', 'PARTIALLY_CANCELLED', 'CONFIRMED')
          AND DATE(ot.CREATED_AT) = '{order_date_str}'
          {where_channel_clause}
          {where_customer_clause}
    )
    SELECT
        FORMAT_TIMESTAMP('%d/%m/%Y %H:%M', MAX(CREATED_AT), 'America/Sao_Paulo') AS Data_Pedido,
        MAX(SHORT_ID)                                                              AS N_Pedido,
        SALES_CHANNEL                                                              AS Canal,
        MAX(TOTAL_ORDERS)                                                          AS N_Pedidos_Cliente,
        STRING_AGG(product_name, ' / ')                                            AS Itens,
        SUM(QUANTITY)                                                              AS qtd_itens,
        ROUND(SUM(item_revenue), 2)                                                AS total_venda,
        ROUND(SUM(item_cost), 2)                                                   AS cost,
        ROUND(SUM((item_revenue / TOTAL_BAG_DETAIL) * order_net_value), 2)        AS net_item,
        ROUND(SUM((item_revenue / TOTAL_BAG_DETAIL) * order_net_value - item_cost), 2) AS lucro_liquido,
        ROUND(SUM((item_revenue / TOTAL_BAG_DETAIL) * order_net_value - item_cost) / NULLIF(SUM(QUANTITY), 0), 2) AS lucro_liquido_medio_item,
        ROUND(SUM((item_revenue / TOTAL_BAG_DETAIL) * order_net_value - item_cost) / NULLIF(SUM(item_cost), 0) * 100, 2) AS Markup,
        ANY_VALUE(PREPARATION_TIME)                                                AS preparation_time,
        order_id                                                                   AS id
    FROM base_data
    GROUP BY order_id, SALES_CHANNEL
    ORDER BY Data_Pedido DESC
    """

    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()
        df = df.rename(columns={
            "Data_Pedido": "Data do Pedido",
            "N_Pedido": "Nº Pedido",
            "N_Pedidos_Cliente": "Qtd. Pedidos Cliente",
            "Itens": "Itens do Pedido",
            "qtd_itens": "Qtd. Itens",
            "total_venda": "Faturamento",
            "cost": "Custo",
            "net_item": "Receita Líquida",
            "lucro_liquido": "Lucro Líquido",
            "lucro_liquido_medio_item": "Lucro Médio por Item",
            "Markup": "Markup (%)",
            "preparation_time" : "Tempo de Preparo",
            "id": "ID Interno" ,
        })
        return df
    except Exception as e:
        st.error(f"Erro ao buscar detalhes de pedidos: {e}")
        return pd.DataFrame()
    
#order_date = st.date_input("Start Date", value=date(2025, 8, 21))
#end_date = st.date_input("End Date", value=date(2025, 8, 31))
#df = read_order_performance(order_date = order_date , sales_channel='99food')
#print(df)