from get_bigquery_client import get_bigquery_client
import streamlit as st
import pandas as pd
from datetime import date

@st.cache_data(ttl=600)
def read_item_sales_analysis(start_date: date, end_date: date, sales_channel: str):
    """
    Busca e retorna a análise de vendas de itens por categoria e quantidade,
    dentro de um período e para um canal de vendas específico.
    """
    client = get_bigquery_client()

    query = f"""
    SELECT
        BSI.NAME AS Subitem,
        SUM(BSI.Quantity) AS Quantidade,
        CASE
            WHEN BSI.NAME LIKE '%Açaí%' THEN 'Açaí'
            WHEN BSI.NAME LIKE '%Sorvete%' OR BSI.NAME LIKE '%Sorbet%' THEN 'Sorvete'
            WHEN BSI.NAME LIKE '%Morango%' OR BSI.NAME LIKE '%Banana%' OR BSI.NAME LIKE '%Uva%' OR BSI.NAME LIKE '%Kiwi%' THEN 'Frutas'
            ELSE 'Outros'
        END AS Categoria
    FROM
        BAG_SUB_ITEMS BSI
    INNER JOIN
        BAG_ITEMS BI ON BI.ID = BSI.BAG_ITEMS_ID
    INNER JOIN
        ORDERS_TABLE OT ON OT.ID = BI.ORDER_ID
    WHERE 1=1
        AND DATE(OT.CREATED_AT) BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        AND OT.SALES_CHANNEL = '{sales_channel}'
    GROUP BY
        BSI.NAME
    ORDER BY
        CASE
            WHEN BSI.NAME LIKE '%Açaí%' THEN 1
            WHEN BSI.NAME LIKE '%Sorvete%' OR BSI.NAME LIKE '%Sorbet%' THEN 2
            WHEN BSI.NAME LIKE '%Morango%' OR BSI.NAME LIKE '%Banana%' OR BSI.NAME LIKE '%Uva%' OR BSI.NAME LIKE '%Kiwi%' THEN 3
            ELSE 4
        END,
        Quantidade DESC,
        BSI.NAME ASC
    """

    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()
        return df

    except Exception as e:
        st.error(f"Erro ao buscar dados de análise de itens: {e}")
        return pd.DataFrame()


### Exemplo de Uso
# Suponha que você queira buscar os dados para agosto de 2025 no iFood
#start_date_example = date(2025, 8, 1)
#end_date_example = date(2025, 8, 25)
#sales_channel_example = "99food"
#
#df_analise = read_item_sales_analysis(start_date_example, end_date_example, sales_channel_example)
#
#print(df_analise)