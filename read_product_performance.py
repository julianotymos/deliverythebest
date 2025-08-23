import streamlit as st
import pandas as pd
from get_bigquery_client import get_bigquery_client
from datetime import date

@st.cache_data(ttl=600, show_spinner=False)
def read_product_performance(start_date: date, end_date: date, sales_channel: str):
    """
    Retorna métricas de vendas por produto (quantidade, valor, custo, lucro, markup)
    no período informado e para o canal de vendas especificado.
    """

    client = get_bigquery_client()
    if sales_channel == '99food':
        sales_channel_id = 2
    elif sales_channel == 'iFood':
        sales_channel_id = 1
    else:
        sales_channel_id = 0

    # Converter datas para string no formato YYYY-MM-DD
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    query = f"""
    SELECT 
        p.NAME,
        SUM(BI.Quantity) AS qtd_itens,
        ROUND(SUM(bi.sub_total_value), 2) AS total_venda,
        ROUND(SUM(p.cost * BI.Quantity), 2) AS cost, 
        ROUND(SUM((bi.sub_total_value/ot.total_bag_detail) * ot.net_value), 2) AS net_item,
        ROUND(SUM((bi.sub_total_value/ot.total_bag_detail) * ot.net_value - (p.cost * BI.Quantity)), 2) AS lucro_liquido, 
        ROUND(SUM((bi.sub_total_value/ot.total_bag_detail) * ot.net_value - (p.cost * BI.Quantity)) / COUNT(1), 2) AS lucro_liquido_medio_item,
        ROUND(SUM((bi.sub_total_value/ot.total_bag_detail) * ot.net_value - (p.cost * BI.Quantity)) / SUM(p.cost * BI.Quantity) * 100, 2) AS Markup ,
       ROUND( ((SUM((bi.sub_total_value/ot.total_bag_detail) * ot.net_value - (p.cost * BI.Quantity)) / ROUND(SUM((bi.sub_total_value/ot.total_bag_detail) * ot.net_value), 2) ) * 100 ) ,2 ) AS Margem
    FROM BAG_ITEMS bi 
    INNER JOIN ORDERS_TABLE ot 
        ON ot.id = bi.ORDER_ID 
    LEFT JOIN PRODUCT p 
        ON p.name = bi.name 
       AND p.sales_channel = {sales_channel_id}
       AND DATE(ot.CREATED_AT) BETWEEN p.VALID_FROM_DATE AND p.VALID_TO_DATE
    WHERE DATE(ot.CREATED_AT) BETWEEN '{start_date_str}' AND '{end_date_str}'
      AND ot.SALES_CHANNEL = '{sales_channel}'
    GROUP BY p.NAME, bi.NAME
    ORDER BY qtd_itens DESC
    """

    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()
        df = df.rename(columns={
            "NAME": "Produto",
            "qtd_itens": "Qtd. Itens",
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
