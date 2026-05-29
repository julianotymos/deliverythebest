import streamlit as st
import pandas as pd
from datetime import date
from manage_accompaniments import (
    list_all_accompaniments,
    check_accompaniment_overlap,
    insert_accompaniment,
    update_accompaniment,
    delete_accompaniment,
    get_status_options,
)
from read_accompaniment_inconsistencies import (
    read_accompaniment_inconsistencies,
    read_accompaniment_overlap_inconsistencies,
)
from manage_product_exceptions import list_exceptions, insert_exception, delete_exception

def tab_accompaniment_management(start_date=None, end_date=None):
    st.header("🥣 Gestão de Acompanhamentos")

    df_status_opt = get_status_options()
    status_list = df_status_opt['SHORT_DESC'].tolist()

    subtab_list, subtab_create, subtab_inconsistencies = st.tabs(["🔍 Consultar e Gerenciar", "➕ Novo Cadastro", "⚠️ Inconsistências"])

    # --- ABA 1: CONSULTA E EDIÇÃO ---
    with subtab_list:
        st.subheader("Acompanhamentos Cadastrados")

        f_col1, f_col2 = st.columns([3, 1])
        with f_col1:
            search = st.text_input("🔍 Buscar por nome:", placeholder="Filtrar por nome...", key="search_accompaniment")
        with f_col2:
            status_filter = st.selectbox("Status:", ["Todos"] + status_list, key="filter_acc_status")

        df = list_all_accompaniments()
        df_display = df.copy()

        if search:
            df_display = df_display[df_display['Acompanhamento'].str.contains(search, case=False, na=False)]
        if status_filter != "Todos":
            df_display = df_display[df_display['Status'] == status_filter]

        selection = st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="acc_grid",
            column_config={
                "ID": None,
                "Custo": st.column_config.NumberColumn(format="R$ %.2f"),
                "Vigencia_Inicio": st.column_config.DateColumn("Início"),
                "Vigencia_Fim": st.column_config.DateColumn("Fim"),
                "INSERT_DATE": None,
                "UPDATE_DATE": None,
            }
        )

        selected_rows = selection.get("selection", {}).get("rows", [])
        if selected_rows:
            st.divider()
            selected_data = df_display.iloc[selected_rows[0]]
            st.subheader(f"📝 Editar: {selected_data['Acompanhamento']}")

            with st.form("form_edit_accompaniment"):
                col1, col2 = st.columns(2)
                with col1:
                    e_name = st.text_input("Nome do Acompanhamento", value=selected_data['Acompanhamento'])
                    idx_st = status_list.index(selected_data['Status']) if selected_data['Status'] in status_list else 0
                    e_status_name = st.selectbox("Status", options=status_list, index=idx_st)
                    e_status_id = df_status_opt[df_status_opt['SHORT_DESC'] == e_status_name]['ID'].iloc[0]

                with col2:
                    e_cost = st.number_input("Custo", min_value=0.0, format="%.2f", value=float(selected_data['Custo']))
                    e_start = st.date_input("Início Vigência", value=pd.to_datetime(selected_data['Vigencia_Inicio']).date(), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))
                    e_end = st.date_input("Fim Vigência", value=pd.to_datetime(selected_data['Vigencia_Fim']).date(), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))

                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if st.form_submit_button("Atualizar", type="primary", use_container_width=True):
                        if not check_accompaniment_overlap(e_name, e_start, e_end, exclude_id=selected_data['ID']):
                            if update_accompaniment(selected_data['ID'], e_name, e_cost, e_start, e_end, e_status_id):
                                st.success("Atualizado!")
                                st.rerun()
                        else:
                            st.error("⚠️ Sobreposição de vigência detectada para este acompanhamento.")
                with btn_col2:
                    if st.form_submit_button("🗑️ Excluir", type="secondary", use_container_width=True):
                        if delete_accompaniment(selected_data['ID']):
                            st.success("Excluído!")
                            st.rerun()
                with btn_col3:
                    if st.form_submit_button("❌ Cancelar", use_container_width=True):
                        st.rerun()
        else:
            st.info("💡 Selecione um acompanhamento na tabela acima para editar ou excluir.")

    # --- ABA 2: NOVO CADASTRO ---
    with subtab_create:
        st.subheader("➕ Cadastrar Novo Acompanhamento")

        with st.form("form_new_accompaniment", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                n_name = st.text_input("Nome do Acompanhamento")
                n_status_name = st.selectbox("Status Inicial", options=status_list)
                n_status_id = df_status_opt[df_status_opt['SHORT_DESC'] == n_status_name]['ID'].iloc[0]

            with col2:
                n_cost = st.number_input("Custo", min_value=0.0, format="%.2f")
                n_start = st.date_input("Início da Vigência", value=date.today(), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))
                n_end = st.date_input("Fim da Vigência", value=date(2099, 12, 31), min_value=date(2000, 1, 1), max_value=date(2199, 12, 31))

            if st.form_submit_button("Salvar", type="primary"):
                if not n_name:
                    st.error("Nome é obrigatório.")
                else:
                    if not check_accompaniment_overlap(n_name, n_start, n_end):
                        if insert_accompaniment(n_name, n_cost, n_start, n_end, n_status_id):
                            st.success(f"Acompanhamento '{n_name}' cadastrado!")
                            st.rerun()
                    else:
                        st.error("⚠️ Já existe este acompanhamento cadastrado com vigência para este período.")

    # --- ABA 3: INCONSISTÊNCIAS ---
    with subtab_inconsistencies:

        # --- Seção 1: Acompanhamentos sem cadastro válido ---
        st.subheader("⚠️ Acompanhamentos Cobrados Sem Cadastro Válido")
        st.caption("Acompanhamentos vendidos com valor > R$ 0,00 no período selecionado, mas sem cadastro ativo (nome + vigência) correspondente.")

        if start_date is None or end_date is None:
            st.warning("Selecione um período na barra lateral para visualizar as inconsistências.")
        else:
            if st.button("🔍 Carregar Inconsistências", key="btn_load_acc_inc"):
                st.session_state['acc_inc_loaded'] = True
                st.session_state['acc_inc_start'] = start_date
                st.session_state['acc_inc_end'] = end_date

            datas_mudaram = (
                st.session_state.get('acc_inc_start') != start_date or
                st.session_state.get('acc_inc_end') != end_date
            )
            if datas_mudaram:
                st.session_state['acc_inc_loaded'] = False

            if not st.session_state.get('acc_inc_loaded'):
                st.info("Clique em 'Carregar Inconsistências' para visualizar.")
            else:
                try:
                    df_inc = read_accompaniment_inconsistencies(start_date, end_date)
                except Exception as e:
                    st.error(f"Erro ao buscar inconsistências: {e}")
                    df_inc = pd.DataFrame()

            if st.session_state.get('acc_inc_loaded'):
                if df_inc.empty:
                    st.success("✅ Nenhuma inconsistência encontrada no período selecionado.")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Acompanhamentos sem cadastro", df_inc["Acompanhamento"].nunique())
                    with col2:
                        st.metric("Total de itens vendidos", int(df_inc["Qtd Itens"].sum()))
                    with col3:
                        st.metric("Total cobrado (R$)", f"R$ {df_inc['Total Cobrado (R$)'].sum():,.2f}")

                    st.dataframe(
                        df_inc,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Total Cobrado (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                            "Primeira Venda Sem Cadastro": st.column_config.DateColumn("Primeira Venda"),
                            "Última Venda Sem Cadastro": st.column_config.DateColumn("Última Venda"),
                        }
                    )

        st.divider()

        # --- Seção 2: Vigências sobrepostas ---
        st.subheader("🔁 Cadastros com Vigências Sobrepostas")
        st.caption("Pares de cadastros do mesmo acompanhamento com períodos de vigência que se sobrepõem.")

        try:
            df_ov = read_accompaniment_overlap_inconsistencies()
        except Exception as e:
            st.error(f"Erro ao buscar sobreposições: {e}")
            df_ov = pd.DataFrame()

        if df_ov.empty:
            st.success("✅ Nenhuma sobreposição de vigência encontrada no cadastro.")
        else:
            col_ov1, col_ov2 = st.columns(2)
            with col_ov1:
                st.metric("Acompanhamentos com sobreposição", df_ov["Acompanhamento"].nunique())
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

        st.divider()

        # --- Seção 3: Exceções ---
        st.subheader("🚫 Exceções de Sub-item")
        st.caption("Produtos que aparecem como sub-itens em combos e não devem ser considerados como acompanhamentos sem cadastro.")

        df_exc = list_exceptions()

        if not df_exc.empty:
            sel_exc = st.dataframe(
                df_exc,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="exc_grid",
                column_config={
                    "ID": None,
                    "Cadastrado_Em": st.column_config.DatetimeColumn("Cadastrado em", format="DD/MM/YYYY HH:mm"),
                }
            )
            exc_rows = sel_exc.get("selection", {}).get("rows", [])
            if exc_rows:
                exc_data = df_exc.iloc[exc_rows[0]]
                if st.button(f"🗑️ Remover: {exc_data['Produto']}", type="secondary"):
                    if delete_exception(exc_data['ID']):
                        st.success("Exceção removida!")
                        st.rerun()

        st.markdown("**Adicionar nova exceção:**")
        with st.form("form_new_exception", clear_on_submit=True):
            col1, col2 = st.columns([2, 3])
            with col1:
                exc_name = st.text_input("Nome exato do sub-item")
            with col2:
                exc_reason = st.text_input("Motivo", placeholder="ex: Componente de combo")
            if st.form_submit_button("Adicionar", type="primary"):
                if not exc_name:
                    st.error("Nome é obrigatório.")
                else:
                    if insert_exception(exc_name, exc_reason):
                        st.success(f"'{exc_name}' adicionado às exceções.")
                        st.rerun()
