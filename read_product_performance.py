import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from datetime import date

#@st.cache_data(ttl=600, show_spinner=False)
def read_product_performance(start_date: date, end_date: date, sales_channel: str = None, customer_type: str = None):
    """
    Retorna métricas de vendas por produto (quantidade, valor, custo, lucro, markup)
    no período informado e para o canal de vendas especificado (opcional).
    """

    client = get_bigquery_client()

    # Converter datas para string no formato YYYY-MM-DD
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

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
            CASE
                WHEN paid_subs.paid_subitems IS NOT NULL
                THEN CONCAT(p.NAME, ' / ', paid_subs.paid_subitems)
                ELSE p.NAME
            END AS NAME,
            ot.SALES_CHANNEL,
            bi.Quantity,
            -- faturamento corrigido: 99food não inclui adicionais pagos no sub_total_value
            bi.sub_total_value + CASE
                WHEN ot.SALES_CHANNEL = '99food' THEN COALESCE(paid_subs.paid_subitems_value, 0)
                ELSE 0
            END AS item_revenue,
            ot.total_bag_detail,
            ot.net_value,
            p.cost * bi.Quantity + COALESCE(acc_cost.accompaniment_cost, 0) AS item_cost
        FROM BAG_ITEMS bi
        INNER JOIN ORDERS_TABLE ot
            ON ot.id = bi.ORDER_ID
        LEFT JOIN (
            SELECT P.NAME, P.COST, P.VALID_FROM_DATE, P.VALID_TO_DATE, CH.SALES_CHANNEL_ID AS SALES_CHANNEL
            FROM PRODUCT P
            INNER JOIN SALES_CHANNEL CH ON CH.ID = P.SALES_CHANNEL
        ) p
            ON p.name = bi.name
            AND p.sales_channel = OT.SALES_CHANNEL
            AND DATE(ot.CREATED_AT) BETWEEN p.VALID_FROM_DATE AND p.VALID_TO_DATE
        LEFT JOIN (
            SELECT
                BAG_ITEMS_ID,
                STRING_AGG(NAME, ', ' ORDER BY NAME)   AS paid_subitems,
                SUM(TOTAL_EFFECTIVE_UNIT_PRICE_VALUE)  AS paid_subitems_value
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
            WHERE DATE(ot2.CREATED_AT) BETWEEN '{start_date_str}' AND '{end_date_str}'
            GROUP BY bsi.BAG_ITEMS_ID
        ) acc_cost ON acc_cost.BAG_ITEMS_ID = bi.ID
        WHERE
            DATE(ot.CREATED_AT) BETWEEN '{start_date_str}' AND '{end_date_str}'
            {where_channel_clause}
            {where_customer_clause}
    )
    SELECT
        NAME,
        STRING_AGG(DISTINCT SALES_CHANNEL, ', ' ORDER BY SALES_CHANNEL) AS Canais,
        SUM(Quantity)                                                                         AS qtd_itens,
        ROUND(SUM(item_revenue), 2)                                                           AS total_venda,
        ROUND(SUM(item_cost), 2)                                                              AS cost,
        ROUND(SUM((item_revenue / total_bag_detail) * net_value), 2)                         AS net_item,
        ROUND(SUM((item_revenue / total_bag_detail) * net_value - item_cost), 2)             AS lucro_liquido,
        ROUND(SUM((item_revenue / total_bag_detail) * net_value - item_cost) / SUM(Quantity), 2) AS lucro_liquido_medio_item,
        ROUND(SUM((item_revenue / total_bag_detail) * net_value - item_cost) / NULLIF(SUM(item_cost), 0) * 100, 2) AS Markup,
        ROUND(SUM((item_revenue / total_bag_detail) * net_value - item_cost) / NULLIF(SUM((item_revenue / total_bag_detail) * net_value), 0) * 100, 2) AS Margem
    FROM base_data
    GROUP BY NAME
    ORDER BY qtd_itens DESC
    """

    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()
        df = df.rename(columns={
            "NAME": "Produto",
            "qtd_itens": "Quantidade",
            "total_venda": "Faturamento",
            "cost": "Custo",
            "net_item": "Receita Líquida",
            "lucro_liquido": "Lucro Líquido",
            "lucro_liquido_medio_item": "Lucro Médio por Item",
            "Markup": "Markup (%)",
            "Margem": "Margem (%)",
        })
        return df
    except Exception as e:
        st.error(f"Erro ao buscar métricas de produtos: {e}")
        return pd.DataFrame()
# --------------------------
# Interface Streamlit
# --------------------------
#start_date = st.date_input("Start Date", value=date(2025, 8, 1))
#end_date = st.date_input("End Date", value=date(2025, 8, 31))
#
#
#
#df = read_product_performance(start_date, end_date, sales_channel='99food')
#print(df)
