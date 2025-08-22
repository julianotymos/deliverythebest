from get_bigquery_client import get_bigquery_client
import streamlit as st
import pandas as pd

@st.cache_data(ttl=600)
def read_products_for_editing(product_name, sales_channel):
    """
    Busca todos os registros de um produto específico em um canal de vendas.
    """
    client = get_bigquery_client()
    
    query = f"""
    SELECT 
        P.ID,
        P.NAME,
        P.CATEGORY,
        P.COST,
        SC.SALES_CHANNEL_ID AS CHANNEL,
        S.SHORT_DESC AS STATUS,
        P.VALID_FROM_DATE,
        P.VALID_TO_DATE
    FROM
        PRODUCT P
    INNER JOIN
        STATUS S ON S.ID = P.STATUS
    INNER JOIN
        SALES_CHANNEL SC ON SC.ID = P.SALES_CHANNEL
    WHERE
        1=1
        AND P.NAME = '{product_name}'
        AND SC.SALES_CHANNEL_ID = '{sales_channel}'
    ORDER BY
        P.VALID_FROM_DATE DESC
    """
    
    try:
        query_job = client.query(query)
        df = query_job.to_dataframe()

        return df , df.iloc[0]
    except Exception as e:
        st.error(f"Erro ao buscar dados para edição: {e}")
        return pd.DataFrame()

# ---

# Exemplo de uso
#df_joined = read_products_for_editing()
#print(df_joined)

product_name_to_search = 'Barato do Dia - Marmita de Açaí Tradicional 1100 ml'
sales_channel_to_search = 'iFood'

all_records_df , last_df = read_products_for_editing(product_name=product_name_to_search, sales_channel=sales_channel_to_search)
print(all_records_df) 
print(last_df) 