import streamlit as st
from datetime import date, timedelta
from read_item_sales_analysis import read_item_sales_analysis
import plotly.express as px
import pandas as pd

def _agrupar_menores(df, col_nome, col_valor, limite_pct=5, label='Outros (<5%)'):
    total = df[col_valor].sum()
    pct = df[col_valor] / total * 100
    principais = df[pct >= limite_pct]
    menores = df[pct < limite_pct]
    if menores.empty:
        return df[[col_nome, col_valor]].copy()
    return pd.concat([
        principais[[col_nome, col_valor]],
        pd.DataFrame([{col_nome: label, col_valor: menores[col_valor].sum()}])
    ], ignore_index=True)

def tab_subitem_analysis(start_date: date, end_date: date, sales_channel: str , customer_type: str = None):
    """
    Exibe a aba de Performance de Produtos.
    Inclui métricas resumidas, top 5 produtos e tabela completa de produtos.
    """

    # ---- Buscar dados ----
    sub_item_df = read_item_sales_analysis(start_date=start_date, end_date=end_date, sales_channel=sales_channel)

    if not sub_item_df.empty:

        # ---- Gráficos em pizza ----
        col1, col2 = st.columns(2)

        with col1:
            acai_sorvete_df = (
                sub_item_df[sub_item_df['Categoria'].isin(['Açaí', 'Sorvete'])]
                .groupby('Categoria', as_index=False)['Quantidade']
                .sum()
            )
            fig1 = px.pie(
                acai_sorvete_df,
                values='Quantidade',
                names='Categoria',
                title='Açaí vs Sorvete',
                height=280,
            )
            fig1.update_layout(
                margin=dict(l=5, r=5, t=40, b=5),
                legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            acai_df = sub_item_df[sub_item_df['Categoria'] == 'Açaí']
            fig2 = px.pie(
                acai_df,
                values='Quantidade',
                names='Subitem',
                title='Distribuição dos Açaís',
                height=280,
            )
            fig2.update_layout(
                margin=dict(l=5, r=5, t=40, b=5),
                legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            frutas_outros_df = (
                sub_item_df[sub_item_df['Categoria'].isin(['Frutas', 'Outros'])]
                .groupby('Categoria', as_index=False)['Quantidade']
                .sum()
            )
            fig3 = px.pie(
                frutas_outros_df,
                values='Quantidade',
                names='Categoria',
                title='Frutas vs Outros',
                height=280,
            )
            fig3.update_layout(
                margin=dict(l=5, r=5, t=40, b=5),
                legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            frutas_df = sub_item_df[sub_item_df['Categoria'] == 'Frutas']
            fig4 = px.pie(
                frutas_df,
                values='Quantidade',
                names='Subitem',
                title='Distribuição das Frutas',
                height=280,
            )
            fig4.update_layout(
                margin=dict(l=5, r=5, t=40, b=5),
                legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig4, use_container_width=True)

        col5, col6 = st.columns(2)

        with col5:
            sorvete_df = _agrupar_menores(
                sub_item_df[sub_item_df['Categoria'] == 'Sorvete'],
                'Subitem', 'Quantidade'
            )
            fig5 = px.pie(
                sorvete_df,
                values='Quantidade',
                names='Subitem',
                title='Distribuição dos Sorvetes',
                height=280,
            )
            fig5.update_layout(
                margin=dict(l=5, r=5, t=40, b=5),
                legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig5, use_container_width=True)

        with col6:
            outros_df = _agrupar_menores(
                sub_item_df[sub_item_df['Categoria'] == 'Outros'],
                'Subitem', 'Quantidade'
            )
            fig6 = px.pie(
                outros_df,
                values='Quantidade',
                names='Subitem',
                title='Distribuição dos Outros',
                height=280,
            )
            fig6.update_layout(
                margin=dict(l=5, r=5, t=40, b=5),
                legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig6, use_container_width=True)

        # ---- Tabela completa de produtos ----
        st.subheader("Preferencia dos Clientes")
        st.dataframe(sub_item_df, use_container_width=True ,hide_index=True )

    else:
        st.info("Nenhum dado Preferencia dos Clientes encontrado para o período e canal selecionados.")
