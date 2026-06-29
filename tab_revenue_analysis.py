import streamlit as st
from datetime import date
import altair as alt

from read_revenue_period import read_revenue_period
from read_order_performance import read_order_performance
from read_product_performance import read_product_performance

def tab_revenue_analysis(start_date: date, end_date: date, sales_channel: str , customer_type: str = None):
    """
    Exibe o conteúdo da aba "Resumo Geral" do dashboard de vendas,
    incluindo métricas de faturamento, pedidos e produtos.
    """
    #st.header(f" {sales_channel}")

    # ---- CHAMADAS DE DADOS ----
    revenue_df = read_revenue_period(start_date, end_date, sales_channel , customer_type = customer_type)

    if not revenue_df.empty:
        # ---- TOTAL (última linha somada) ----
        total_row = revenue_df.sum(numeric_only=True)

        # Criar 8 colunas
        col1, col2, col3, col4, col5, col6,  = st.columns(6)

        with col1:
            st.metric("💰 Faturamento", f"{total_row['Faturamento']:.2f}")
            st.metric("💰 Ticket Médio", f"{total_row['Faturamento']/total_row['Qtd. Pedidos']:.2f}")
            st.metric("👥 Pedidos", int(total_row['Qtd. Pedidos']))

        with col2:
            st.metric("💳 Recebido", f"{total_row['Recebido']:.2f}")
            st.metric("💳 Recebido Médio", f"{total_row['Recebido']/total_row['Qtd. Pedidos']:.2f}")
            st.metric("📦 Itens Vendidos", int(total_row['Itens Vendidos']))

        with col3:
            st.metric("💵 Custo", f"{total_row['Custo']:.2f}")
            st.metric("💵 Custo Médio", f"{total_row['Custo']/total_row['Qtd. Pedidos']:.2f}")
            
            st.metric("🆕 Novos Clientes", int(total_row['Novos Clientes']))

        with col4:
            st.metric("🤑 Lucro ", f"{total_row['Lucro Líquido']:.2f}")
            st.metric("🤑 Lucro Médio ", f"{total_row['Lucro Líquido']/total_row['Qtd. Pedidos']:.2f}")
            
            st.metric("🔁 Clientes Recorrentes", int(total_row['Clientes Recorrentes']))

        with col5:
            st.metric("📈 Markup (%)",f"{(total_row['Lucro Líquido'] / total_row['Custo'] * 100):.2f}%")
            st.metric("         ", "-") 
            recorrentes = int(total_row['Clientes Recorrentes'])
            novos = int(total_row['Novos Clientes'])
            total_clientes = recorrentes + novos
            pct_recorrentes = (recorrentes / total_clientes * 100) if total_clientes else 0
            st.metric("🔁 % Clientes Recorrentes", f"{pct_recorrentes:.2f}%")

        with col6:
            st.metric("📊 Margem (%)",f"{(total_row['Lucro Líquido'] / total_row['Recebido'] * 100):.2f}%")


            
        st.markdown("---")

        # ---- Analise periodo ----
        st.subheader("Analise periodo")
        if not revenue_df.empty:
            selection = st.dataframe(
                revenue_df,
                use_container_width=True,
                on_select="rerun",  # Roda o script novamente quando uma linha é clicada
                selection_mode="single-row",
                hide_index=True
            )
            
            # Exibe as transações do cliente selecionado
            if selection["selection"]["rows"]:
                selected_index = selection["selection"]["rows"][0]
                selected_row = revenue_df.iloc[[selected_index]]
                
                order_date = selected_row["Data"].iloc[0]

                st.subheader(f"Transações de {order_date}")
                transactions_df = read_order_performance(order_date = order_date , sales_channel=sales_channel , customer_type= customer_type)
                
                if not transactions_df.empty:
                    st.dataframe(transactions_df, use_container_width=True , hide_index=True)
                else:
                    st.info("Não há transações para esta data.")
        else:
            st.info("Nenhum dado encontrado no período.")




    else:
        st.warning("⚠️ Não há dados de vendas para o período selecionado. Por favor, ajuste o filtro de datas.")
