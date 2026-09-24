import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Diagnóstico & Reserva - Painel do Daniel", page_icon="🎯", layout="wide"
)
st.title("💰 Controle Financeiro — Painel do Daniel")
st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")
st.markdown(
    "Esta aba analisa os seus lançamentos, simula o impacto da transição de"
    " moradia em dezembro, a entrada do extra do PROEIS e traça a rota para"
    " construir sua reserva de segurança."
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

    # ==========================================================
    # SIMULADOR DE TRANSIÇÃO (DEZEMBRO + PROEIS + CORTES)
    # ==========================================================
    st.subheader("🚀 Simulador Estratégico: Cenário Dezembro em Diante")
    st.markdown(
        "Simule o impacto da sua mudança para o apartamento próprio (eliminando"
        " o aluguel) e a injeção do extra do PROEIS na formação da sua reserva."
    )

    df_despesas = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"]
    aluguel_atual = 0.0
    if not df_despesas.empty:
        aluguel_match = df_despesas[
            df_despesas["categoria"].str.contains("Aluguel", case=False, na=False)
        ]
        if not aluguel_match.empty:
            aluguel_atual = aluguel_match["valor"].sum()

    col_tr1, col_tr2 = st.columns(2)

    with col_tr1:
        st.markdown("#### Premissas da Virada")
        entregar_aluguel = st.checkbox(
            "Entregar imóvel alugado em Dezembro (Zera o Aluguel de R$"
            f" {aluguel_atual:,.2f})",
            value=True,
        )
        incluir_proeis = st.checkbox(
            "Considerar valor extra do PROEIS (R$ 5.320,00)", value=True
        )

        valor_proeis = 5320.0 if incluir_proeis else 0.0
        economia_aluguel = aluguel_atual if entregar_aluguel else 0.0

        nova_despesa_total = despesas_total - economia_aluguel
        novo_saldo_mensal = receitas_total - nova_despesa_total - total_aportes
        meta_reserva_futura = (nova_despesa_total / 30) * 180

    with col_tr2:
        st.markdown("#### 🎯 Projeção de Caixa (A partir de Dezembro)")
        st.metric(
            "Nova Despesa Mensal",
            f"R$ {nova_despesa_total:,.2f}",
            delta=f"- R$ {economia_aluguel:,.2f} (Aluguel Eliminado)",
            delta_color="inverse",
        )
        st.metric(
            "Novo Saldo Líquido Mensal",
            f"R$ {novo_saldo_mensal:,.2f}",
            delta="Folga real garantida por mês!",
        )
        if incluir_proeis:
            st.success(
                f"💰 **Injeção PROEIS:** Os R$ {valor_proeis:,.2f} extras entram"
                f" direto como o **pontapé inicial absoluto** da sua reserva de"
                f" segurança!"
            )

    if novo_saldo_mensal > 1.0:
        quanto_falta = max(
            0.0, meta_reserva_futura - valor_proeis - total_aportes
        )
        meses_reserva = quanto_falta / novo_saldo_mensal

        st.markdown(
            f"""
            <div style="padding: 15px; border-radius: 8px; background-color: rgba(0, 150, 255, 0.1); border-left: 5px solid #0096ff; margin-top: 15px;">
                <b>Previsão de Sucesso:</b> Com a economia gerando <b>R$ {novo_saldo_mensal:,.2f}</b> livres por mês e aplicando o extra do PROEIS logo no início, você atinge a sua meta completa de reserva de segurança (<b>R$ {meta_reserva_futura:,.2f}</b>) em aproximadamente <b>{meses_reserva:.1f} meses</b> após a mudança em dezembro!
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="padding: 15px; border-radius: 8px; background-color: rgba(255, 165, 0, 0.1); border-left: 5px solid #ffa500; margin-top: 15px;">
                <b>Atenção:</b> O saldo mensal projetado está zerado ou negativo. Para calcular o tempo estimado da reserva, marque a opção acima para <b>Entregar o imóvel alugado em Dezembro</b>, liberando assim a folga financeira necessária.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

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

    # Plano de Ação Estratégico
    st.subheader("🛡️ Plano Diretor de Transição Patrimonial")
    st.markdown(f"""
    1. **Foco na Data de Dezembro:** Mantenha a disciplina financeira atual até completar o prazo contratual do Quinto Andar. A própria inércia do contrato resolve o problema estrutural do aluguel sem multas rescisórias abusivas.
    2. **Blindagem do PROEIS (R$ {valor_proeis:,.2f}):** Quando esse valor for creditado, **não o misture com a conta corrente comum**. Destine-o imediatamente para uma aplicação de renda fixa com liquidez diária (criando a fundação da sua reserva).
    3. **Aproveitamento do Imóvel Próprio:** A mudança para o seu apartamento em dezembro converterá um custo perdido (aluguel a terceiros) em permanência no seu próprio patrimônio, reduzindo drasticamente o escoamento de caixa.
    """)