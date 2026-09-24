from datetime import datetime
import io
import urllib.parse
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Relatórios e Consultas - Daniel", page_icon="📈", layout="wide"
)


def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


# --- FUNÇÃO PARA GERENCIAR A COMPETÊNCIA GLOBALMENTE NA BARRA LATERAL ---
def configurar_sidebar_competencia():
    try:
        conexao = obter_conexao()
        df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
        conexao.close()
    except Exception:
        df_l = pd.DataFrame(columns=["data"])

    def extrair_competencia(data_str):
        try:
            dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
            if pd.isna(dt):
                dt = pd.to_datetime(data_str, errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%m/%Y"), dt.strftime("%Y-%m")
        except Exception:
            pass
        return "Indefinido", "9999-99"

    if not df_l.empty and "data" in df_l.columns:
        res = df_l["data"].apply(extrair_competencia)
        df_l["competencia"] = [x[0] for x in res]
        df_l["comp_ordem"] = [x[1] for x in res]
    else:
        df_l["competencia"] = "Indefinido"
        df_l["comp_ordem"] = "9999-99"

    mapeamento_comps = (
        df_l[["competencia", "comp_ordem"]]
        .drop_duplicates()
        .copy()
    )
    mapeamento_comps = mapeamento_comps[
        mapeamento_comps["competencia"] != "Indefinido"
    ].sort_values("comp_ordem", ascending=False)

    competencias_disponiveis = mapeamento_comps["competencia"].tolist()
    mes_atual_sistema = datetime.now().strftime("%m/%Y")

    if not competencias_disponiveis:
        competencias_disponiveis = [mes_atual_sistema]

    if "competencia_selecionada" not in st.session_state:
        st.session_state["competencia_selecionada"] = (
            mes_atual_sistema
            if mes_atual_sistema in competencias_disponiveis
            else competencias_disponiveis[0]
        )

    try:
        index_atual = competencias_disponiveis.index(
            st.session_state["competencia_selecionada"]
        )
    except ValueError:
        index_atual = 0

    st.sidebar.header("📅 Competência (Mês/Ano)")
    st.session_state["competencia_selecionada"] = st.sidebar.selectbox(
        "Selecione o Mês de Referência",
        options=competencias_disponiveis,
        index=index_atual,
        key="selectbox_competencia",
    )

    ordem_sel = (
        mapeamento_comps[
            mapeamento_comps["competencia"]
            == st.session_state["competencia_selecionada"]
        ]["comp_ordem"].values[0]
        if st.session_state["competencia_selecionada"]
        in mapeamento_comps["competencia"].values
        else datetime.now().strftime("%Y-%m")
    )

    return st.session_state["competencia_selecionada"], ordem_sel


# Chamar o seletor na barra lateral
competencia_selecionada, ordem_selecionada = configurar_sidebar_competencia()

st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("📈 Relatórios, Consultas e Fechamento de Mês")
st.write(
    f"Análise e relatórios para a competência: **{competencia_selecionada}**."
    " Filtre seus lançamentos detalhadamente, gerencie registros, exporte"
    " relatórios e projete seu saldo futuro."
)

# Carregar todos os lançamentos do banco
try:
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query(
        "SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos"
        " ORDER BY id DESC",
        conexao,
    )
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar lançamentos: {e}")
    df_lancamentos = pd.DataFrame()

if not df_lancamentos.empty:
    df_lancamentos["data_dt"] = pd.to_datetime(
        df_lancamentos["data"], format="%d/%m/%Y", errors="coerce"
    )

    aba1, aba2, aba3 = st.tabs([
        "🔍 Consulta, Filtros e Ações",
        "📅 Fechamento de Mês (Saldo Remanescente)",
        "🔮 Projeção de Saldo Futuro",
    ])


    def fmt_moeda(v):
        return (
            f"R$ {v:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )


    # --- ABA 1: CONSULTA, FILTROS E AÇÕES ---
    with aba1:
        st.markdown(
            f"### 🔎 Filtrar Lançamentos (Foco inicial:"
            f" {competencia_selecionada})"
        )

        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            tipos_disponiveis = ["Todos"] + list(
                df_lancamentos["tipo"].dropna().unique()
            )
            filtro_tipo = st.selectbox("Filtrar por Tipo", tipos_disponiveis)

        with col_f2:
            categorias_disponiveis = sorted(
                list(df_lancamentos["categoria"].dropna().unique())
            )
            filtro_categorias = st.multiselect(
                "Filtrar por Categoria(s)", categorias_disponiveis, default=[]
            )

        with col_f3:
            filtro_texto = st.text_input("Buscar na Descrição (Palavra-chave)")

        # Aplicação dos filtros (incluindo filtro automático de competência da barra lateral)
        df_filtrado = df_lancamentos.copy()


        def extrair_mes_ano(data_str):
            try:
                dt = pd.to_datetime(
                    data_str, format="%d/%m/%Y", errors="coerce"
                )
                if pd.isna(dt):
                    dt = pd.to_datetime(data_str, errors="coerce")
                if pd.notna(dt):
                    return dt.strftime("%m/%Y")
            except Exception:
                pass
            return ""


        df_filtrado["competencia_mes"] = df_filtrado["data"].apply(
            extrair_mes_ano
        )
        df_filtrado = df_filtrado[
            df_filtrado["competencia_mes"] == competencia_selecionada
        ]

        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["tipo"] == filtro_tipo]

        if filtro_categorias:
            df_filtrado = df_filtrado[
                df_filtrado["categoria"].isin(filtro_categorias)
            ]

        if filtro_texto:
            df_filtrado = df_filtrado[
                df_filtrado["descricao"].str.contains(
                    filtro_texto, case=False, na=False
                )
            ]

        df_exibicao = df_filtrado.copy()
        df_exibicao["valor_num"] = (
            pd.to_numeric(df_exibicao["valor"], errors="coerce")
            .fillna(0.0)
        )
        df_exibicao["valor_formatado"] = df_exibicao["valor_num"].apply(
            fmt_moeda
        )

        colunas_mostrar = [
            "id",
            "data",
            "tipo",
            "categoria",
            "descricao",
            "valor_formatado",
        ]

        st.dataframe(
            df_exibicao[colunas_mostrar]
            .rename(columns={"valor_formatado": "valor"})
            .set_index("id"),
            use_container_width=True,
            height=210,
        )

        total_filtrado = df_exibicao["valor_num"].sum()
        cat_str = ", ".join(filtro_categorias) if filtro_categorias else "Todas"
        st.info(
            f"📊 **Total dos lançamentos filtrados ({competencia_selecionada}):**"
            f" {fmt_moeda(total_filtrado)}"
        )

        # --- BOTÕES DE EXPORTAÇÃO E IMPRESSÃO ---
        col_exp1, col_exp2, col_exp3 = st.columns(3)

        df_para_exportar = df_exibicao[
            ["id", "data", "tipo", "categoria", "descricao", "valor_num"]
        ].rename(columns={"valor_num": "valor"})

        with col_exp1:
            csv_data = df_para_exportar.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar em CSV",
                data=csv_data,
                file_name=(
                    f"relatorio_lancamentos_{competencia_selecionada.replace('/', '_')}.csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

        with col_exp2:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                df_para_exportar.to_excel(
                    writer, index=False, sheet_name="Lancamentos"
                )
            excel_data = output_excel.getvalue()
            st.download_button(
                label="📊 Baixar em Excel (.xlsx)",
                data=excel_data,
                file_name=(
                    f"relatorio_lancamentos_{competencia_selecionada.replace('/', '_')}.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        with col_exp3:
            html_tabela = df_para_exportar.to_html(
                index=False, classes="table table-striped"
            )
            html_code = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Relatório de Lançamentos</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; }}
        h2 {{ color: #111; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; font-size: 14px; }}
        th {{ background-color: #f5f5f5; }}
        .total {{ margin-top: 20px; font-weight: bold; font-size: 18px; }}
    </style>
</head>
<body>
    <h2>Relatório de Lançamentos - Competência {competencia_selecionada}</h2>
    <p><b>Filtros Aplicados:</b> Mês ({competencia_selecionada}) | Tipo ({filtro_tipo}) | Categorias ({cat_str})</p>
    {html_tabela}
    <div class="total">Total Filtrado: {fmt_moeda(total_filtrado)}</div>
    <script>
        window.onload = function() {{ window.print(); }}
    </script>
</body>
</html>"""

            html_encoded = urllib.parse.quote(html_code)
            st.markdown(
                f"""
                <a href="data:text/html;charset=utf-8,{html_encoded}" target="_blank" style="text-decoration: none; display: block; width: 100%;">
                    <div style="background-color: #ff4b4b; color: white; text-align: center; padding: 10px 18px; border-radius: 4px; font-weight: bold; cursor: pointer; width: 100%;">
                        🖨️ Imprimir / PDF
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # --- SEÇÃO DE EDIÇÃO E EXCLUSÃO RÁPIDA NA CONSULTA ---
        st.markdown(
            "### ✏️ Gerenciar Lançamento Filtrado (Editar ou Excluir)"
        )
        if not df_filtrado.empty:
            df_filtrado["resumo_acao"] = (
                "ID: "
                + df_filtrado["id"].astype(str)
                + " | "
                + df_filtrado["data"]
                + " | "
                + df_filtrado["categoria"]
                + " | "
                + df_filtrado["descricao"].fillna("")
            )

            lanc_sel = st.selectbox(
                "Selecione o lançamento para alterar ou excluir:",
                df_filtrado["resumo_acao"].tolist(),
            )
            id_sel = int(
                lanc_sel.split(" | ")[0].replace("ID: ", "")
            )
            dado_reg = df_filtrado[df_filtrado["id"] == id_sel].iloc[0]

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                with st.form("form_edicao_relatorio"):
                    st.markdown("#### Corrigir Registro")
                    ntipo = st.selectbox(
                        "Tipo",
                        ["Despesa", "Receita"],
                        index=0 if dado_reg["tipo"] == "Despesa" else 1,
                    )
                    ncateg = st.text_input(
                        "Categoria", value=dado_reg["categoria"]
                    )
                    ndesc = st.text_input(
                        "Descrição", value=dado_reg["descricao"]
                    )
                    nval = st.number_input(
                        "Valor (R$)",
                        value=float(dado_reg["valor"]),
                        format="%.2f",
                    )
                    ndata = st.text_input(
                        "Data (DD/MM/AAAA)", value=dado_reg["data"]
                    )

                    if st.form_submit_button("Salvar Alterações"):
                        try:
                            datetime.strptime(ndata.strip(), "%d/%m/%Y")
                            conexao = obter_conexao()
                            cursor = conexao.cursor()
                            cursor.execute(
                                """
                                UPDATE lancamentos 
                                SET data = %s, tipo = %s, categoria = %s, descricao = %s, valor = %s 
                                WHERE id = %s
                                """,
                                (
                                    ndata.strip(),
                                    ntipo,
                                    ncateg,
                                    ndesc,
                                    nval,
                                    id_sel,
                                ),
                            )
                            conexao.commit()
                            cursor.close()
                            conexao.close()
                            st.success("Atualizado com sucesso!")
                            st.rerun()
                        except ValueError:
                            st.error(
                                "Data inválida. Use o formato DD/MM/AAAA."
                            )
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")

            with col_a2:
                st.markdown("#### Excluir Registro")
                st.warning(
                    "Atenção: Essa operação apagará o registro"
                    " permanentemente."
                )
                if st.button(
                    "Excluir Lançamento Selecionado", type="primary"
                ):
                    try:
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        cursor.execute(
                            "DELETE FROM lancamentos WHERE id = %s",
                            (id_sel,),
                        )
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
        else:
            st.info(
                f"Nenhum registro disponível para gerenciar na competência"
                f" {competencia_selecionada} com os filtros atuais."
            )

    # --- ABA 2: FECHAMENTO DE MÊS (FLUXO E SALDO REMANESCENTE) ---
    with aba2:
        st.markdown("### 📅 Fechamento Mensal e Evolução de Saldo")
        st.write(
            "Visão consolidada de entradas, saídas, resultado líquido do mês e"
            " o saldo remanescente acumulado."
        )

        df_lancamentos["ano_mes"] = df_lancamentos["data_dt"].dt.to_period("M")

        if df_lancamentos["ano_mes"].notna().any():
            df_receitas = (
                df_lancamentos[df_lancamentos["tipo"] == "Receita"]
                .groupby("ano_mes")["valor"]
                .sum()
                .reset_index(name="entradas")
            )
            df_despesas = (
                df_lancamentos[df_lancamentos["tipo"] == "Despesa"]
                .groupby("ano_mes")["valor"]
                .sum()
                .reset_index(name="saidas")
            )

            df_fechamento = pd.merge(
                df_receitas, df_despesas, on="ano_mes", how="outer"
            ).fillna(0.0)
            df_fechamento = df_fechamento.sort_values(
                by="ano_mes", ascending=True
            ).reset_index(drop=True)

            df_fechamento["resultado_mes"] = (
                df_fechamento["entradas"] - df_fechamento["saidas"]
            )
            df_fechamento["saldo_remanescente"] = df_fechamento[
                "resultado_mes"
            ].cumsum()
            df_fechamento["mes_ano_str"] = df_fechamento[
                "ano_mes"
            ].dt.strftime("%m/%Y")

            df_tabela_mensal = pd.DataFrame({
                "Mês/Ano": df_fechamento["mes_ano_str"],
                "Total Entradas": df_fechamento["entradas"].apply(fmt_moeda),
                "Total Saídas": df_fechamento["saidas"].apply(fmt_moeda),
                "Resultado do Mês": df_fechamento["resultado_mes"].apply(
                    fmt_moeda
                ),
                "Saldo Remanescente (Acumulado)": df_fechamento[
                    "saldo_remanescente"
                ].apply(fmt_moeda),
            })

            st.dataframe(
                df_tabela_mensal, use_container_width=True, height=210
            )
        else:
            st.warning(
                "Não há datas válidas o suficiente para gerar o fechamento"
                " mensal."
            )

    # --- ABA 3: PROJEÇÃO DE SALDO FUTURO ---
    with aba3:
        st.markdown("### 🔮 Simulador de Projeção de Saldo Futuro")
        st.write(
            "Projete o crescimento do seu saldo com base nas médias históricas"
            " de entradas e saídas ou defina valores personalizados."
        )

        df_lancamentos["ano_mes"] = df_lancamentos["data_dt"].dt.to_period("M")

        if not df_lancamentos.empty and df_lancamentos["ano_mes"].notna().any():
            df_rec_m = df_lancamentos[
                df_lancamentos["tipo"] == "Receita"
            ].groupby("ano_mes")["valor"].sum()
            df_desp_m = df_lancamentos[
                df_lancamentos["tipo"] == "Despesa"
            ].groupby("ano_mes")["valor"].sum()

            media_entradas_hist = (
                df_rec_m.mean() if not df_rec_m.empty else 0.0
            )
            media_saidas_hist = (
                df_desp_m.mean() if not df_desp_m.empty else 0.0
            )

            df_receitas_tot = (
                df_lancamentos[df_lancamentos["tipo"] == "Receita"]
                .groupby("ano_mes")["valor"]
                .sum()
                .reset_index(name="entradas")
            )
            df_despesas_tot = (
                df_lancamentos[df_lancamentos["tipo"] == "Despesa"]
                .groupby("ano_mes")["valor"]
                .sum()
                .reset_index(name="saidas")
            )
            df_fech_tot = pd.merge(
                df_receitas_tot, df_despesas_tot, on="ano_mes", how="outer"
            ).fillna(0.0)
            df_fech_tot["resultado"] = (
                df_fech_tot["entradas"] - df_fech_tot["saidas"]
            )
            saldo_atual_base = (
                df_fech_tot["resultado"].sum()
                if not df_fech_tot.empty
                else 0.0
            )

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                patrimonio_inicial_proj = st.number_input(
                    "Saldo Base Inicial (R$)",
                    value=float(saldo_atual_base),
                    step=100.0,
                    format="%.2f",
                )
            with col_p2:
                entrada_mensal_proj = st.number_input(
                    "Média de Entradas Mensais (R$)",
                    value=float(media_entradas_hist),
                    step=100.0,
                    format="%.2f",
                )
            with col_p3:
                saida_mensal_proj = st.number_input(
                    "Média de Saídas Mensais (R$)",
                    value=float(media_saidas_hist),
                    step=100.0,
                    format="%.2f",
                )

            meses_proj = st.slider(
                "Meses à Frente para Projeção",
                min_value=1,
                max_value=24,
                value=6,
                step=1,
            )

            lista_proj = []
            saldo_loop = patrimonio_inicial_proj
            data_base = datetime.now()

            for i in range(1, meses_proj + 1):
                mes_futuro = (
                    data_base.replace(day=1) + pd.DateOffset(months=i)
                ).strftime("%m/%Y")
                resultado_mes_proj = entrada_mensal_proj - saida_mensal_proj
                saldo_loop += resultado_mes_proj

                lista_proj.append({
                    "Mês Projeção": mes_futuro,
                    "Entradas Previstas (R$)": round(
                        entrada_mensal_proj, 2
                    ),
                    "Saídas Previstas (R$)": round(saida_mensal_proj, 2),
                    "Resultado do Mês (R$)": round(
                        resultado_mes_proj, 2
                    ),
                    "Saldo Acumulado Projetado (R$)": round(saldo_loop, 2),
                })

            df_projecao = pd.DataFrame(lista_proj)

            st.write("")
            st.markdown("### 📊 Resultado da Projeção Mês a Mês")

            df_proj_exibe = df_projecao.copy()
            df_proj_exibe["Entradas Previstas (R$)"] = df_proj_exibe[
                "Entradas Previstas (R$)"
            ].apply(fmt_moeda)
            df_proj_exibe["Saídas Previstas (R$)"] = df_proj_exibe[
                "Saídas Previstas (R$)"
            ].apply(fmt_moeda)
            df_proj_exibe["Resultado do Mês (R$)"] = df_proj_exibe[
                "Resultado do Mês (R$)"
            ].apply(fmt_moeda)
            df_proj_exibe[
                "Saldo Acumulado Projetado (R$)"
            ] = df_proj_exibe["Saldo Acumulado Projetado (R$)"].apply(
                fmt_moeda
            )

            st.dataframe(
                df_proj_exibe.set_index("Mês Projeção"),
                use_container_width=True,
            )

            st.write("")
            st.markdown("### 📈 Gráfico de Evolução Patrimonial Projetada")
            st.line_chart(
                df_projecao.set_index("Mês Projeção")[[
                    "Saldo Acumulado Projetado (R$)"
                ]]
            )
        else:
            st.info(
                "Cadastre mais lançamentos com datas válidas para habilitar a"
                " projeção baseada em histórico."
            )
else:
    st.info("Nenhum lançamento cadastrado no sistema para gerar relatórios.")