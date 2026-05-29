import streamlit as st
from datetime import date, timedelta
from read_product_performance import read_product_performance
from read_accompaniment_performance import read_accompaniment_performance
from read_product import read_product
# --- Configurações da Página ---
def tab_product_analysis(start_date: date, end_date: date, sales_channel: str , customer_type: str = None):
    """
    Exibe a aba de Performance de Produtos.
    Inclui métricas resumidas, top 5 produtos e tabela completa de produtos.
    """
    #st.header(f"📦 Performance de Produtos - Canal: {sales_channel}")

    # ---- Buscar dados ----
    product_df_performance = read_product_performance(start_date, end_date, sales_channel, customer_type=customer_type)
    acc_df_performance = read_accompaniment_performance(start_date, end_date, sales_channel, customer_type=customer_type)
    product_df, product_df_0 = read_product(start_date=start_date, end_date=end_date, sales_channel=sales_channel)
    #print(product_df)
    product_df_display = product_df.drop(columns=['ID', 'CATEGORY'])

    if not product_df_performance.empty:

        # ---- Filtro por nome de produto ----
        search_product = st.text_input("Filtrar por produto", placeholder="Digite o nome do produto...")
        if search_product:
            product_df_performance = product_df_performance[
                product_df_performance["Produto"].str.contains(search_product, case=False, na=False)
            ]

        # ---- Tabela completa de produtos ----
        st.subheader("Resultado por Produto")
        st.dataframe(product_df_performance, use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum dado de performance de produtos encontrado para o período e canal selecionados.")

    # ---- Resultado por Acompanhamento ----
    st.subheader("Resultado por Acompanhamento")
    if not acc_df_performance.empty:
        search_acc = st.text_input("Filtrar por acompanhamento", placeholder="Digite o nome...", key="search_acc_perf")
        if search_acc:
            acc_df_performance = acc_df_performance[
                acc_df_performance["Acompanhamento"].str.contains(search_acc, case=False, na=False)
            ]
        st.dataframe(
            acc_df_performance,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Faturamento":  st.column_config.NumberColumn(format="R$ %.2f"),
                "Recebido":     st.column_config.NumberColumn(format="R$ %.2f"),
                "Custo":        st.column_config.NumberColumn(format="R$ %.2f"),
                "Lucro Real":   st.column_config.NumberColumn(format="R$ %.2f"),
                "Markup (%)":   st.column_config.NumberColumn(format="%.2f %%"),
                "Margem (%)":   st.column_config.NumberColumn(format="%.2f %%"),
            }
        )
    else:
        st.info("Nenhum dado de acompanhamentos encontrado para o período e canal selecionados.")

    if not product_df.empty:

        st.subheader("Vingencia de custos de Produtos")
        st.dataframe(product_df_display, use_container_width=True ,hide_index=True )
        
    else:
        st.info("Nenhum dado de custos de produtos encontrado para o período e canal selecionados.")