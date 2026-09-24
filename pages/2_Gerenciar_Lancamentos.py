from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Gerenciar Lançamentos — Painel do Daniel", page_icon="✏️", layout="wide"
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
st.subheader("✏️ Gerenciar, Editar ou Excluir Lançamentos")
st.write(
    "Gerencie, edite ou exclua seus lançamentos manuais e acompanhe seus"
    " compromissos da competência selecionada."
)

try:
    conexao = obter_conexao()
    df = pd.read_sql_query(
        "SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos"
        " ORDER BY id DESC",
        conexao,
    )
    df_div = pd.read_sql_query(
        "SELECT id, credor, valor_parcela, dia_vencimento, status FROM dividas"
        " WHERE status = 'Pendente'",
        conexao,
    )
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    df = pd.DataFrame()
    df_div = pd.DataFrame()


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


if not df.empty:
    res_l = df["data"].apply(extrair_competencia)
    df["competencia"] = [x[0] for x in res_l]
    df["comp_ordem"] = [x[1] for x in res_l]
    df["data_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")

    df_mes = df[df["competencia"] == competencia_selecionada].copy()

    hoje = pd.Timestamp(datetime.now().date())
    df_futuros = (
        df[df["data_dt"] > hoje]
        .sort_values(by="data_dt", ascending=True)
        .copy()
    )

    if not df_div.empty:
        df_div_ativas = df_div[df_div["valor_parcela"] > 0].copy()

        if not df_div_ativas.empty:
            try:
                partes_comp = competencia_selecionada.split("/")
                mes_sel = int(partes_comp[0])
                ano_sel = int(partes_comp[1])
            except Exception:
                mes_sel = hoje.month
                ano_sel = hoje.year

            lista_parcelas_mes = []
            for _, row in df_div_ativas.iterrows():
                dia_v = (
                    int(row["dia_vencimento"])
                    if pd.notna(row["dia_vencimento"]) and row["dia_vencimento"] > 0
                    else 10
                )
                try:
                    data_venc_obj = datetime(ano_sel, mes_sel, dia_v)
                except ValueError:
                    data_venc_obj = datetime(ano_sel, mes_sel, 28)

                lista_parcelas_mes.append({
                    "id": f"DIV-{row['id']}",
                    "data": data_venc_obj.strftime("%d/%m/%Y"),
                    "tipo": "Despesa",
                    "categoria": "Dívida / Parcelamento",
                    "descricao": f"Parcela Acordo: {row['credor']}",
                    "valor": float(row["valor_parcela"]),
                    "data_dt": pd.Timestamp(data_venc_obj.date()),
                })

            if lista_parcelas_mes:
                df_parcelas_futuras = pd.DataFrame(lista_parcelas_mes)
                df_futuros = pd.concat(
                    [df_futuros, df_parcelas_futuras], ignore_index=True
                )
                df_futuros = df_futuros.sort_values(by="data_dt", ascending=True)

    st.write(f"### 🔄 Editar ou Excluir Registros Manuais — {competencia_selecionada}")

    if not df_mes.empty:
        st.write(
            "Selecione um lançamento abaixo para alterar os dados (exceto o tipo)"
            " ou excluí-lo."
        )

        def fmt_moeda(v):
            return (
                f"R$ {v:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        df_mes["valor_fmt"] = (
            pd.to_numeric(df_mes["valor"], errors="coerce")
            .fillna(0.0)
            .apply(fmt_moeda)
        )

        df_mes["resumo_label"] = (
            "ID: "
            + df_mes["id"].astype(str)
            + " | "
            + df_mes["data"]
            + " | "
            + df_mes["tipo"]
            + " | "
            + df_mes["categoria"]
            + " | "
            + df_mes["valor_fmt"]
            + " ("
            + df_mes["descricao"].fillna("")
            + ")"
        )

        lancamento_selecionado = st.selectbox(
            "Escolha o lançamento para gerenciar:", df_mes["resumo_label"].tolist()
        )

        id_selecionado = int(
            lancamento_selecionado.split(" | ")[0].replace("ID: ", "")
        )
        dados_atuais = df_mes[df_mes["id"] == id_selecionado].iloc[0]

        st.divider()

        col_edit1, col_edit2 = st.columns(2)

        with col_edit1:
            st.markdown("### 🔄 Atualizar Lançamento")
            st.info(
                f"💡 **Tipo Fixo:** Este registro é uma **{dados_atuais['tipo']}**. "
                "Para alterar entre Receita e Despesa, exclua o registro e crie um novo."
            )

            with st.form("form_edicao"):
                nova_categoria = st.text_input(
                    "Categoria", value=dados_atuais["categoria"]
                )
                nova_descricao = st.text_input(
                    "Descrição", value=dados_atuais["descricao"]
                )
                novo_valor = st.number_input(
                    "Valor (R$)",
                    min_value=0.0,
                    format="%.2f",
                    value=float(dados_atuais["valor"]),
                )
                nova_data = st.text_input("Data (DD/MM/AAAA)", value=dados_atuais["data"])

                salvar_alteracao = st.form_submit_button("Salvar Alterações")

                if salvar_alteracao:
                    try:
                        datetime.strptime(nova_data.strip(), "%d/%m/%Y")
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        valor_limpo = abs(float(novo_valor))

                        cursor.execute(
                            """
                            UPDATE lancamentos 
                            SET data = %s, categoria = %s, descricao = %s, valor = %s
                            WHERE id = %s
                            """,
                            (
                                nova_data.strip(),
                                nova_categoria.strip(),
                                nova_descricao.strip(),
                                valor_limpo,
                                id_selecionado,
                            ),
                        )
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Lançamento atualizado com sucesso!")
                        st.rerun()
                    except ValueError:
                        st.error("A data digitada é inválida. Utilize o formato DD/MM/AAAA.")
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")

        with col_edit2:
            st.markdown("### 🗑️ Excluir Lançamento")
            st.warning(
                "Atenção: Essa operação apagará permanentemente este registro e o saldo"
                " retornará imediatamente ao valor real."
            )

            if st.button("Excluir este Lançamento", type="primary"):
                try:
                    conexao = obter_conexao()
                    cursor = conexao.cursor()
                    cursor.execute(
                        "DELETE FROM lancamentos WHERE id = %s", (id_selecionado,)
                    )
                    conexao.commit()
                    cursor.close()
                    conexao.close()
                    st.success("Lançamento excluído com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
    else:
        st.info(f"Nenhum lançamento manual encontrado na competência {competencia_selecionada}.")

    st.divider()
    st.markdown("### ⏳ Lançamentos Futuros e Parcelamentos a Pagar")

    if not df_futuros.empty:
        st.info(
            "Aqui estão reunidos seus compromissos manuais futuros e as parcelas"
            " ativas das suas dívidas com base nos dias de vencimento."
        )

        tabela_futuros = df_futuros[
            ["id", "data", "tipo", "categoria", "descricao", "valor"]
        ].copy()
        tabela_futuros["valor"] = tabela_futuros["valor"].apply(
            lambda v: f"R$ {v:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        tabela_futuros.columns = [
            "ID",
            "Data",
            "Tipo",
            "Categoria",
            "Descrição",
            "Valor",
        ]

        st.dataframe(tabela_futuros.reset_index(drop=True), use_container_width=True)

        total_futuro_valor = (
            df_futuros[df_futuros["tipo"] == "Despesa"]["valor"].sum()
            - df_futuros[df_futuros["tipo"] == "Receita"]["valor"].sum()
        )
        total_fut_fmt = (
            f"R$ {abs(total_futuro_valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        st.metric(
            label="📉 Impacto Líquido dos Próximos Vencimentos Listados",
            value=total_fut_fmt,
        )
    else:
        st.info("Não há lançamentos futuros ou parcelamentos ativos cadastrados.")
else:
    st.info("Nenhum lançamento encontrado para gerenciar.")