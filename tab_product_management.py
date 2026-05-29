import streamlit as st
import pandas as pd
from datetime import date
from manage_products import (
    list_all_products_detailed,
    check_product_overlap,
    insert_product,
    update_product,
    delete_product,
    get_channels,
    get_status_options
)
from read_product_inconsistencies import read_product_inconsistencies, read_product_overlap_inconsistencies

def tab_product_management(start_date=None, end_date=None):
    st.header("📦 Gestão de Produtos e Vigências")
    
    # 1. Preparação de Dados Comuns
    df_channels = get_channels()
    channels_list = df_channels['SALES_CHANNEL_ID'].tolist()
    df_status_opt = get_status_options()
    status_list = df_status_opt['SHORT_DESC'].tolist()
    category_options = ["Pronto", "A montar"]

    # Criar abas principais
    subtab_list, subtab_create, subtab_inconsistencies = st.tabs(["🔍 Consultar e Gerenciar", "➕ Novo Cadastro", "⚠️ Inconsistências"])
    
    # --- ABA 1: CONSULTA E EDIÇÃO ---
    with subtab_list:
        st.subheader("Produtos Cadastrados")
        
        # Filtros Superiores
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])
        with f_col1:
            search = st.text_input("🔍 Buscar por nome:", placeholder="Filtrar por nome...", key="search_manage")
        with f_col2:
            status_filter = st.selectbox("Status:", ["Todos"] + status_list, key="filter_status")
        with f_col3:
            channel_filter = st.selectbox("Canal:", ["Todos"] + channels_list, key="filter_channel")
        with f_col4:
            category_filter = st.selectbox("Categoria:", ["Todos"] + category_options, key="filter_category")
        
        df_products = list_all_products_detailed()
        df_display = df_products.copy()
        
        # Aplicar Filtros
        if search:
            df_display = df_display[df_display['Produto'].str.contains(search, case=False, na=False)]
        if status_filter != "Todos":
            df_display = df_display[df_display['Status'] == status_filter]
        if channel_filter != "Todos":
            df_display = df_display[df_display['Canal'] == channel_filter]
        if category_filter != "Todos":
            df_display = df_display[df_display['Categoria'] == category_filter]

        selection = st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="manage_grid_v4",
            column_config={
                "Custo": st.column_config.NumberColumn(format="R$ %.2f"),
                "Vigencia_Inicio": st.column_config.DateColumn("Início"),
                "Vigencia_Fim": st.column_config.DateColumn("Fim"),
            }
        )

        # Lógica de Edição
        selected_rows = selection.get("selection", {}).get("rows", [])
        if selected_rows:
            st.divider()
            selected_data = df_display.iloc[selected_rows[0]]
            st.subheader(f"📝 Editar Produto: {selected_data['Produto']}")
            
            with st.form("form_edit_product_v4"):
                col1, col2 = st.columns(2)
                with col1:
                    e_name = st.text_input("Nome do Produto", value=selected_data['Produto'])
                    
                    # Seleção de Categoria na Edição
                    idx_cat = category_options.index(selected_data['Categoria']) if selected_data['Categoria'] in category_options else 0
                    e_cat = st.selectbox("Categoria", options=category_options, index=idx_cat)
                    
                    idx_ch = channels_list.index(selected_data['Canal']) if selected_data['Canal'] in channels_list else 0
                    e_channel_name = st.selectbox("Canal", options=channels_list, index=idx_ch)
                    e_channel_id = df_channels[df_channels['SALES_CHANNEL_ID'] == e_channel_name]['ID'].iloc[0]
                    
                    idx_st = status_list.index(selected_data['Status']) if selected_data['Status'] in status_list else 0
                    e_status_name = st.selectbox("Status", options=status_list, index=idx_st)
                    e_status_id = df_status_opt[df_status_opt['SHORT_DESC'] == e_status_name]['ID'].iloc[0]
                
                with col2:
                    e_cost = st.number_input("Custo", min_value=0.0, format="%.2f", value=float(selected_data['Custo']))
                    e_start = st.date_input("Início Vigência", value=pd.to_datetime(selected_data['Vigencia_Inicio']).date(), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))
                    e_end = st.date_input("Fim Vigência", value=pd.to_datetime(selected_data['Vigencia_Fim']).date(), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))

                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                with btn_col1:
                    if st.form_submit_button("Atualizar Dados", type="primary", use_container_width=True):
                        if not check_product_overlap(e_name, e_channel_id, e_start, e_end, exclude_id=selected_data['ID']):
                            if update_product(selected_data['ID'], e_name, e_channel_id, e_cat, e_cost, e_start, e_end, e_status_id):
                                st.success("Atualizado!")
                                st.rerun()
                        else:
                            st.error("⚠️ Erro: Sobreposição de vigência detectada.")
                
                with btn_col2:
                    if st.form_submit_button("🗑️ Excluir", type="secondary", use_container_width=True):
                        if delete_product(selected_data['ID']):
                            st.success("Excluído!")
                            st.rerun()
                
                with btn_col3:
                    if st.form_submit_button("❌ Cancelar", use_container_width=True):
                        st.rerun()
        else:
            st.info("💡 Selecione um produto na tabela acima para editar ou excluir.")

    # --- ABA 2: NOVO CADASTRO ---
    with subtab_create:
        st.subheader("➕ Cadastrar Novo Produto")
        
        with st.form("form_new_product_v4", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_name = st.text_input("Nome do Produto")
                
                # Seleção de Categoria na Inserção
                n_cat = st.selectbox("Categoria", options=category_options)
                
                n_channel_name = st.selectbox("Canal de Venda", options=channels_list)
                n_channel_id = df_channels[df_channels['SALES_CHANNEL_ID'] == n_channel_name]['ID'].iloc[0]
                n_status_name = st.selectbox("Status Inicial", options=status_list)
                n_status_id = df_status_opt[df_status_opt['SHORT_DESC'] == n_status_name]['ID'].iloc[0]
            
            with col2:
                n_cost = st.number_input("Custo de Matéria Prima", min_value=0.0, format="%.2f")
                n_start = st.date_input("Início da Vigência", value=date.today(), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))
                n_end = st.date_input("Fim da Vigência", value=date(2099, 12, 31), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))
            
            if st.form_submit_button("Salvar Novo Produto", type="primary"):
                if not n_name:
                    st.error("Nome é obrigatório.")
                else:
                    if not check_product_overlap(n_name, n_channel_id, n_start, n_end):
                        if insert_product(n_name, n_channel_id, n_cat, n_cost, n_start, n_end, n_status_id):
                            st.success(f"Produto '{n_name}' cadastrado!")
                            st.rerun()
                    else:
                        st.error("⚠️ Já existe este produto cadastrado com vigência para este período.")

    # --- ABA 3: INCONSISTÊNCIAS ---
    with subtab_inconsistencies:

        # --- Seção 1: Produtos sem cadastro válido ---
        st.subheader("⚠️ Produtos Vendidos Sem Cadastro Válido")
        st.caption("Produtos que apareceram em pedidos no período selecionado, mas não possuem cadastro ativo (nome + canal + vigência) correspondente.")

        if start_date is None or end_date is None:
            st.warning("Selecione um período na barra lateral para visualizar as inconsistências.")
        else:
            df_inc = read_product_inconsistencies(start_date, end_date)

            if df_inc.empty:
                st.success("✅ Nenhuma inconsistência encontrada no período selecionado.")
            else:
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Produtos sem cadastro", df_inc["Produto"].nunique())
                with col_info2:
                    st.metric("Total de itens vendidos", int(df_inc["Qtd Itens"].sum()))
                with col_info3:
                    st.metric("Total faturado (R$)", f"R$ {df_inc['Total Vendido (R$)'].sum():,.2f}")

                st.dataframe(
                    df_inc,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Total Vendido (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Primeira Venda Sem Cadastro": st.column_config.DateColumn("Primeira Venda"),
                        "Última Venda Sem Cadastro": st.column_config.DateColumn("Última Venda"),
                    }
                )

        st.divider()

        # --- Seção 2: Vigências sobrepostas no cadastro ---
        st.subheader("🔁 Cadastros com Vigências Sobrepostas")
        st.caption("Pares de cadastros do mesmo produto e canal com períodos de vigência que se sobrepõem.")

        df_ov = read_product_overlap_inconsistencies()

        if df_ov.empty:
            st.success("✅ Nenhuma sobreposição de vigência encontrada no cadastro.")
        else:
            col_ov1, col_ov2 = st.columns(2)
            with col_ov1:
                st.metric("Produtos com sobreposição", df_ov["Produto"].nunique())
            with col_ov2:
                st.metric("Pares sobrepostos", len(df_ov))

            st.dataframe(
                df_ov,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Custo 1 (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Custo 2 (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Início Vigência 1": st.column_config.DateColumn("Início 1"),
                    "Fim Vigência 1": st.column_config.DateColumn("Fim 1"),
                    "Início Vigência 2": st.column_config.DateColumn("Início 2"),
                    "Fim Vigência 2": st.column_config.DateColumn("Fim 2"),
                }
            )

