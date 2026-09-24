from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Consultoria e Saúde Financeira - Daniel",
    page_icon="💡",
    layout="wide",
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
st.subheader("💡 Consultoria Inteligente de Bolso - Diagnóstico Financeiro")
st.write(
    f"Análise automática da sua saúde financeira para a competência:"
    f" **{competencia_selecionada}**, com base nos seus ganhos, compromissos"
    " mensais e dívidas ativas."
)

# Carrega os dados do banco (Lançamentos e Dívidas)
try:
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query(
        "SELECT data, tipo, valor FROM lancamentos", conexao
    )
    df_dividas = pd.read_sql_query(
        "SELECT valor_parcela, status FROM dividas WHERE status = 'Pendente'",
        conexao,
    )
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar dados para o diagnóstico: {e}")
    df_lancamentos = pd.DataFrame()
    df_dividas = pd.DataFrame()


# Função auxiliar para filtrar lançamentos pela competência selecionada da barra lateral
def filtrar_por_competencia(df):
    if df.empty or "data" not in df.columns:
        return pd.DataFrame()

    def extrair_mes_ano(data_str):
        try:
            dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
            if pd.isna(dt):
                dt = pd.to_datetime(data_str, errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%m/%Y")
        except Exception:
            pass
        return ""

    df = df.copy()
    df["competencia"] = df["data"].apply(extrair_mes_ano)
    return df[df["competencia"] == competencia_selecionada]


# Aplica o filtro de competência nos lançamentos
df_lancamentos_filtrado = filtrar_por_competencia(df_lancamentos)

# Cálculos financeiros base (filtrados pelo mês selecionado)
total_receitas = (
    df_lancamentos_filtrado[df_lancamentos_filtrado["tipo"] == "Receita"][
        "valor"
    ].sum()
    if not df_lancamentos_filtrado.empty
    else 0.0
)
total_despesas_manuais = (
    df_lancamentos_filtrado[df_lancamentos_filtrado["tipo"] == "Despesa"][
        "valor"
    ].sum()
    if not df_lancamentos_filtrado.empty
    else 0.0
)

# Soma apenas as parcelas ativas das dívidas pendentes que possuem valor de parcela cadastrado
total_parcelas_dividas = (
    df_dividas[df_dividas["valor_parcela"] > 0]["valor_parcela"].sum()
    if not df_dividas.empty
    else 0.0
)

# Despesa Total Real (Despesas Manuais do Mês + Parcelas de Dívidas Ativas)
despesa_total_real = total_despesas_manuais + total_parcelas_dividas

# Saldo Livre / Comprometimento
saldo_livre = total_receitas - despesa_total_real


def fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.divider()

# --- PAINEL DE MÉTRICAS DA SAÚDE FINANCEIRA ---
st.markdown(f"### 📊 Seus Indicadores Atuais ({competencia_selecionada})")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric(
        label="🟢 Total de Ganhos (Receitas)", value=fmt_moeda(total_receitas)
    )

with col_m2:
    st.metric(
        label="🔴 Total de Compromissos",
        value=fmt_moeda(despesa_total_real),
        help=(
            "Inclui despesas manuais do mês + parcelas mensais de dívidas"
            " ativas"
        ),
    )

with col_m3:
    st.metric(label="⚖️ Saldo Livre / Resultado", value=fmt_moeda(saldo_livre))

with col_m4:
    # Diagnóstico rápido de status
    if total_receitas == 0 and despesa_total_real == 0:
        status_saude = "Sem Dados"
    elif saldo_livre < 0:
        status_saude = "🚨 Em Déficit (Vermelho)"
    elif saldo_livre == 0:
        status_saude = "⚠️ No Zero a Zero"
    else:
        status_saude = "✅ Com Sobra (Azul)"
    st.metric(label="🩺 Status da Saúde Financeira", value=status_saude)

st.divider()

# --- DIAGNÓSTICO E ORIENTAÇÃO PERSONALIZADA ---
st.markdown("### 🧭 Roteiro Estratégico Personalizado para o seu Momento")

if total_receitas == 0 and despesa_total_real == 0:
    st.info(
        f"⚠️ Você ainda não possui lançamentos cadastrados para o mês de"
        f" **{competencia_selecionada}** suficientes para gerarmos uma análise"
        " profunda. Comece cadastrando suas receitas e despesas na aba 'Novo"
        " Lançamento' ou selecione outro mês na barra lateral."
    )
else:
    if saldo_livre < 0:
        # Cenário 1: Vermelho / Endividado
        st.error(
            "🚨 **Diagnóstico:** Suas despesas e compromissos mensais estão"
            " superando os seus ganhos nesta competência. No momento, o foco"
            " principal **não é investir**, e sim estancar o sangramento do"
            " orçamento."
        )

        st.markdown("""
            #### 🛠️ Plano de Ação Imediato para Sair do Vermelho:
            1. **Estancar o Sangramento:** O juro do rotativo de cartão de crédito e cheque especial destrói qualquer orçamento. Priorize negociar as dívidas que possuem juros altos antes de pensar em guardar dinheiro.
            2. **Corte Cirúrgico de Custos:** Olhe nos seus lançamentos para onde está indo o maior volume de recursos em supérfluos. Reduza custos imediatamente para equilibrar o mês e zerar o déficit.
            3. **A Metodologia do Centavo:** Evite pequenos gastos diários invisíveis ("efeito goteira") que somados consomem boa parte do seu ganho mensal.
            """)

    elif saldo_livre == 0:
        # Cenário 2: Equilibrado mas sem folga
        st.warning(
            "⚠️ **Diagnóstico:** Suas contas estão empatadas com os seus ganhos"
            " neste mês. Você não está acumulando dívidas novas, mas também não está"
            " conseguindo construir uma gordura financeira."
        )

        st.markdown("""
            #### 🛠️ Plano de Ação para Criar Folga:
            1. **Encontrar Margem:** Tente espremer pelo menos 5% a 10% dos seus gastos mensais para começar a transformá-los em sobra livre.
            2. **Foco no Acordo das Dívidas:** Se você possui dívidas sem parcelamento ativo (aquelas pendentes paradas), use qualquer sobra eventual para propor acordos à vista com desconto agressivo.
            """)

    else:
        # Cenário 3: Saudável / Com Sobra
        st.success(
            "✅ **Diagnóstico:** Parabéns! Seus ganhos estão superiores aos seus"
            " compromissos mensais nesta competência. Você possui uma sobra de"
            " caixa livre para direcionar ao seu futuro."
        )

        st.markdown("""
            #### 🚀 Plano de Ação Rumo à Reserva de Emergência:
            1. **Destino da Soberania (Reserva de Emergência):** Todo o seu saldo livre atual deve ter como destino primário a **Renda Fixa com liquidez diária** (Tesouro Selic ou CDBs de bancos sólidos que pagem 100% do CDI). O objetivo ideal é acumular o equivalente a **3 a 6 meses do seu custo de vida**.
            2. **Segurança e Rendimento:** Diferente da caderneta de poupança tradicional, essas opções rendem todos os dias úteis e possuem a proteção do FGC (Fundo Garantidor de Créditos) até R$ 250 mil por instituição.
            3. **Aceleração de Quitação:** Se ainda restam dívidas parceladas ativas, você pode usar parte do excedente para amortizar parcelas antecipadamente e economizar nos juros.
            """)