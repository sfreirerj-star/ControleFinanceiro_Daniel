from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

# 1. Configuração da Página e Aplicação do Estilo DEVEM ser chamadas juntas no topo
st.set_page_config(
    page_title="Controle Financeiro - Daniel", page_icon="💰", layout="wide"
)
aplicar_estilo_moderno()  # <-- Essencial logo após o set_page_config

st.set_page_config(
    page_title="Diagnóstico & Reserva - Painel do Daniel", page_icon="🎯", layout="wide"
)

# Aplica o estilo moderno padrão do painel
aplicar_estilo_moderno()

st.title("💰 Controle Financeiro — Painel do Daniel")
st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")
st.markdown(
    "Esta aba analisa os seus lançamentos, mapeia os principais gargalos de"
    " despesas e traça a rota para construir sua reserva de segurança com foco"
    " em autonomia e aprendizado patrimonial."
)


# Função flexível para buscar a URL do banco e carregar os dados
def carregar_dados():
    try:
        db_url = None
        if "DATABASE_URL" in st.secrets:
            db_url = st.secrets["DATABASE_URL"]
        elif "database_url" in st.secrets:
            db_url = st.secrets["database_url"]
        elif (
            "connections" in st.secrets
            and "postgresql" in st.secrets["connections"]
        ):
            db_url = st.secrets["connections"]["postgresql"]["url"]
        else:
            for key in st.secrets:
                if isinstance(st.secrets[key], str) and "postgresql://" in st.secrets[key]:
                    db_url = st.secrets[key]
                    break

        if not db_url:
            st.error(
                "⚠️ A chave de conexão com o banco não foi encontrada no arquivo"
                " `.streamlit/secrets.toml`."
            )
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        conn = psycopg2.connect(db_url)
        df_lancamentos = pd.read_sql("SELECT * FROM lancamentos;", con=conn)
        df_dividas = pd.read_sql("SELECT * FROM dividas;", con=conn)

        try:
            df_aportes = pd.read_sql("SELECT * FROM desafio_aportes;", con=conn)
        except Exception:
            df_aportes = pd.DataFrame()

        conn.close()
        return df_lancamentos, df_dividas, df_aportes
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados na nuvem: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# Carregando os dados originais
df_lancamentos, df_dividas, df_aportes = carregar_dados()

# ==========================================================
# FILTRO DE COMPETÊNCIA DINÂMICO (APENAS MESES COM LANÇAMENTOS)
# ==========================================================
st.sidebar.header("📅 Filtro de Competência")

competencias_disponiveis = []

if not df_lancamentos.empty and "data" in df_lancamentos.columns:
    df_lancamentos["data_dt"] = pd.to_datetime(
        df_lancamentos["data"], errors="coerce", dayfirst=True
    )
    mask = df_lancamentos["data_dt"].isna()
    if mask.any():
        df_lancamentos.loc[mask, "data_dt"] = pd.to_datetime(
            df_lancamentos.loc[mask, "data"], errors="coerce"
        )

    df_lancamentos["competencia"] = df_lancamentos["data_dt"].dt.strftime("%m/%Y")

    comps_reais = df_lancamentos["competencia"].dropna().unique().tolist()


    def ordenar_comp(c):
        try:
            m, a = c.split("/")
            return f"{a}{m}"
        except Exception:
            return c


    competencias_disponiveis = sorted(comps_reais, key=ordenar_comp)

if competencias_disponiveis:
    opcoes_menu = ["Todos os Meses"] + competencias_disponiveis
else:
    opcoes_menu = ["Todos os Meses"]

competencia_selecionada = st.sidebar.selectbox(
    "Mês de Referência", options=opcoes_menu, index=0
)

if (
    competencia_selecionada != "Todos os Meses"
    and not df_lancamentos.empty
    and "competencia" in df_lancamentos.columns
):
    df_filtrado = df_lancamentos[
        df_lancamentos["competencia"] == competencia_selecionada
    ]
else:
    df_filtrado = df_lancamentos.copy()
# ==========================================================

if df_filtrado.empty:
    st.info(
        f"Nenhum lançamento encontrado para {competencia_selecionada}. Selecione"
        " 'Todos os Meses' no menu lateral."
    )
else:
    df_filtrado["valor"] = (
        pd.to_numeric(df_filtrado["valor"], errors="coerce").fillna(0.0)
    )

    receitas_total = (
        df_filtrado[df_filtrado["tipo"].str.lower() == "receita"]["valor"].sum()
    )
    despesas_total = (
        df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"]["valor"].sum()
    )

    total_aportes = 0.0
    if not df_aportes.empty and "valor" in df_aportes.columns:
        total_aportes = (
            pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0).sum()
        )

    saldo_atual = receitas_total - despesas_total - total_aportes

    st.subheader(f"📊 Panorama Atual ({competencia_selecionada})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Atual", f"R$ {receitas_total:,.2f}")
    col2.metric("Despesa Atual", f"R$ {despesas_total:,.2f}")
    col3.metric(
        "Reserva Atual (Aportes)",
        f"R$ {total_aportes:,.2f}",
        delta="Acumulado 💰",
    )
    col4.metric(
        "Resultado Líquido Atual",
        f"R$ {saldo_atual:,.2f}",
        delta=(
            f"{(saldo_atual/receitas_total)*100:.1f}% da Receita"
            if receitas_total > 0
            else "0%"
        ),
        delta_color="normal" if saldo_atual >= 0 else "inverse",
    )

    st.divider()

    df_despesas = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"]

    # Mapeamento de Gargalos Clássico
    st.subheader("🔍 Mapeamento Detalhado de Saídas Atuais")
    if not df_despesas.empty:
        gargalos = (
            df_despesas.groupby("categoria")["valor"]
            .sum()
            .reset_index()
            .sort_values(by="valor", ascending=False)
        )
        gargalos["% do Total"] = (
            (gargalos["valor"] / despesas_total) * 100
            if despesas_total > 0
            else 0
        )

        st.dataframe(
            gargalos.style.format(
                {"valor": "R$ {:,.2f}", "% do Total": "{:.1f}%"}
            ),
            use_container_width=True,
        )

    st.divider()

    # Plano de Ação Estratégico (Focado em autonomia, juventude e aprendizado)
    st.subheader("🛡️ Diretrizes de Educação e Construção Financeira")
    st.markdown("""
    1. **Construção de Hábito Cedo:** Aos 24 anos, cada real guardado e investido com consistência ganha um efeito exponencial do tempo a seu favor. O foco agora é dominar os gastos supérfluos e automatizar os aportes mensais.
    2. **Blindagem de Ganhos Extras:** Ganhos eventuais ou variáveis (como plantões ou extras profissionais) devem ser tratados como dinheiro voltado exclusivamente para o seu futuro patrimônio, evitando que sejam absorvidos pelo custo de vida corrente.
    3. **Independência e Flexibilidade:** Mantenha um controle rigoroso sobre os maiores gargalos de despesa identificados acima para garantir que seu dinheiro sirva aos seus objetivos de médio e longo prazo com total tranquilidade.
    """)