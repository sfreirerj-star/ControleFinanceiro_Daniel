from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Novo Lançamento - Daniel", page_icon="📝", layout="wide"
)


def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


def garantir_tabelas():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor NUMERIC(10,2) NOT NULL
            )
        """)
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception:
        pass


garantir_tabelas()


# --- FUNÇÃO PARA GERENCIAR A COMPETÊNCIA GLOBALMENTE NA BARRA LATERAL ---
def configurar_sidebar_competencia():
    try:
        conexao = obter_conexao()
        df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
        df_a = pd.read_sql_query("SELECT data FROM desafio_aportes", conexao)
        conexao.close()
    except Exception:
        df_l = pd.DataFrame(columns=["data"])
        df_a = pd.DataFrame(columns=["data"])

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

    for df in [df_l, df_a]:
        if not df.empty and "data" in df.columns:
            res = df["data"].apply(extrair_competencia)
            df["competencia"] = [x[0] for x in res]
            df["comp_ordem"] = [x[1] for x in res]
        else:
            df["competencia"] = "Indefinido"
            df["comp_ordem"] = "9999-99"

    mapeamento_comps = pd.concat([
        df_l[["competencia", "comp_ordem"]],
        df_a[["competencia", "comp_ordem"]],
    ]).drop_duplicates()

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
st.subheader("📝 Novo Lançamento & Registo de Caixa")
st.write(
    "Registe as suas receitas e despesas do dia a dia com abatimento automático"
    " dos aportes de investimentos."
)

# Formulário de Novo Lançamento
with st.form("form_novo_lancamento", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        data_lancamento = st.text_input(
            "Data do Lançamento (DD/MM/AAAA)",
            value=datetime.now().strftime("%d/%m/%Y"),
        )
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
    with col2:
        categoria = st.text_input(
            "Categoria (Ex: Alimentação, Transporte...)", value=""
        )
        valor = st.number_input(
            "Valor (R$)", min_value=0.0, value=0.0, step=10.0, format="%.2f"
        )
    with col3:
        descricao = st.text_input("Descrição / Estabelecimento", value="")

    submitted = st.form_submit_button("Salvar Lançamento")
    if submitted:
        try:
            datetime.strptime(data_lancamento.strip(), "%d/%m/%Y")
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)"
                " VALUES (%s, %s, %s, %s, %s)",
                (data_lancamento.strip(), tipo, categoria, descricao, valor),
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.success("Lançamento guardado com sucesso!")
            st.rerun()
        except ValueError:
            st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

st.divider()

# Carregamento robusto dos dados (Lançamentos e Aportes)
df_lancamentos = pd.DataFrame(
    columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
)
df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])

try:
    conexao = obter_conexao()
    try:
        df_lancamentos = pd.read_sql_query(
            "SELECT * FROM lancamentos ORDER BY id DESC", conexao
        )
    except Exception:
        conexao.rollback()

    try:
        df_aportes = pd.read_sql_query(
            "SELECT id, data, valor, local_aplicacao FROM desafio_aportes",
            conexao,
        )
    except Exception:
        conexao.rollback()
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar dados do banco: {e}")


# Função para extrair competência para filtragem
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


if not df_lancamentos.empty and "data" in df_lancamentos.columns:
    res_lanc = df_lancamentos["data"].apply(extrair_competencia)
    df_lancamentos["competencia"] = [x[0] for x in res_lanc]
    df_lancamentos["comp_ordem"] = [x[1] for x in res_lanc]
    df_lancamentos["valor_num"] = (
        pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
    )
    df_lancamentos["tipo_clean"] = (
        df_lancamentos["tipo"].str.strip().str.lower()
    )
else:
    df_lancamentos["competencia"] = "Indefinido"
    df_lancamentos["comp_ordem"] = "9999-99"
    df_lancamentos["tipo_clean"] = ""

if not df_aportes.empty and "data" in df_aportes.columns:
    res_ap = df_aportes["data"].apply(extrair_competencia)
    df_aportes["competencia"] = [x[0] for x in res_ap]
    df_aportes["comp_ordem"] = [x[1] for x in res_ap]
    df_aportes["valor_num"] = (
        pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
    )
else:
    df_aportes["competencia"] = "Indefinido"
    df_aportes["comp_ordem"] = "9999-99"

# Filtrar apenas para o mês de competência selecionado
df_lanc_mes = (
    df_lancamentos[
        df_lancamentos["competencia"] == competencia_selecionada
    ].copy()
    if not df_lancamentos.empty
    else pd.DataFrame()
)
df_aportes_mes = (
    df_aportes[df_aportes["competencia"] == competencia_selecionada].copy()
    if not df_aportes.empty
    else pd.DataFrame()
)

total_aportes_mes = (
    df_aportes_mes["valor_num"].sum() if not df_aportes_mes.empty else 0.0
)

total_receitas = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(
            ["receita", "crédito", "credito", "entrada"]
        )
    ]["valor_num"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

total_gastos = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])
    ]["valor_num"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

saldo_atual = total_receitas - total_gastos - total_aportes_mes


def fmt_moeda(v):
    return (
        f"R$ {v:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


st.subheader(
    f"📊 Resumo da Competência: {competencia_selecionada} (Créditos, Débitos e"
    " Aportes)"
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Créditos", fmt_moeda(total_receitas))
c2.metric("Total Débitos", fmt_moeda(total_gastos))
c3.metric("Total em Aportes", fmt_moeda(total_aportes_mes))

if saldo_atual >= 0:
    c4.metric(
        "Saldo da Competência", fmt_moeda(saldo_atual), delta="No Azul 💙"
    )
else:
    c4.metric(
        "Saldo da Competência",
        fmt_moeda(saldo_atual),
        delta="No Vermelho 🔴",
        delta_color="inverse",
    )

st.divider()

st.subheader(
    f"Histórico de Lançamentos da Competência: {competencia_selecionada}"
)
if not df_lanc_mes.empty:
    df_exibicao = df_lanc_mes.drop(
        columns=[
            "tipo_clean",
            "valor_num",
            "competencia",
            "comp_ordem",
            "local_aplicacao",
            "is_aporte",
        ],
        errors="ignore",
    )
    df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
    st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
else:
    st.info("Nenhum lançamento registado nesta competência.")
