from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(
    page_title="Alocação Milenar - Talmude — Painel do Daniel", page_icon="📜", layout="wide"
)
aplicar_estilo_moderno()  # <-- Mantém o menu opaco e padronizado


def obter_conexao():
  """Abre e retorna a conexão com o banco de dados PostgreSQL na nuvem."""
  return psycopg2.connect(st.secrets["DATABASE_URL"])


def extrair_competencia(data_val):
  if pd.isna(data_val) or data_val is None:
    return "Indefinido", "9999-99"
  try:
    if isinstance(data_val, (pd.Timestamp, datetime)):
      return data_val.strftime("%m/%Y"), data_val.strftime("%Y-%m")
    data_str = str(data_val).strip()
    dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
    if pd.isna(dt):
      dt = pd.to_datetime(data_str, errors="coerce")
    if pd.notna(dt):
      return dt.strftime("%m/%Y"), dt.strftime("%Y-%m")
  except Exception:
    pass
  return "Indefinido", "9999-99"


def configurar_sidebar_competencia(conexao, prefixo_key="milenar"):
  mes_atual_sistema = datetime.now().strftime("%m/%Y")
  competencias_disponiveis = [mes_atual_sistema]
  mapeamento_comps = pd.DataFrame(
      {
          "competencia": [mes_atual_sistema],
          "comp_ordem": [datetime.now().strftime("%Y-%m")],
      }
  )

  try:
    df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
  except Exception:
    df_l = pd.DataFrame(columns=["data"])

  try:
    df_a = pd.read_sql_query("SELECT data FROM desafio_aportes", conexao)
  except Exception:
    df_a = pd.DataFrame(columns=["data"])

  try:
    df_r = pd.read_sql_query("SELECT data FROM desafio_resgates", conexao)
  except Exception:
    df_r = pd.DataFrame(columns=["data"])

  for df in [df_l, df_a, df_r]:
    if not df.empty and "data" in df.columns:
      res = df["data"].apply(extrair_competencia)
      df["competencia"] = [x[0] for x in res]
      df["comp_ordem"] = [x[1] for x in res]

  if not df_l.empty or not df_a.empty or not df_r.empty:
    mapeamento_comps = pd.concat([
        df_l[["competencia", "comp_ordem"]] if not df_l.empty else pd.DataFrame(columns=["competencia", "comp_ordem"]),
        df_a[["competencia", "comp_ordem"]] if not df_a.empty else pd.DataFrame(columns=["competencia", "comp_ordem"]),
        df_r[["competencia", "comp_ordem"]] if not df_r.empty else pd.DataFrame(columns=["competencia", "comp_ordem"]),
    ]).drop_duplicates()

    mapeamento_comps = mapeamento_comps[
        mapeamento_comps["competencia"] != "Indefinido"
    ].sort_values("comp_ordem", ascending=False)

    if not mapeamento_comps.empty:
      competencias_disponiveis = mapeamento_comps["competencia"].tolist()

  if mes_atual_sistema not in competencias_disponiveis:
    competencias_disponiveis.insert(0, mes_atual_sistema)

  key_selectbox = f"selectbox_competencia_{prefixo_key}"
  if key_selectbox not in st.session_state:
    st.session_state[key_selectbox] = mes_atual_sistema

  try:
    index_atual = competencias_disponiveis.index(st.session_state[key_selectbox])
  except ValueError:
    index_atual = 0

  st.sidebar.markdown("---")
  st.sidebar.header("📅 Competência (Mês/Ano)")
  competencia_selecionada = st.sidebar.selectbox(
      "Selecione o Mês de Referência",
      options=competencias_disponiveis,
      index=index_atual,
      key=key_selectbox,
  )

  ordem_sel = (
      mapeamento_comps[
          mapeamento_comps["competencia"] == competencia_selecionada
      ]["comp_ordem"].values[0]
      if not mapeamento_comps.empty
      and competencia_selecionada in mapeamento_comps["competencia"].values
      else datetime.now().strftime("%Y-%m")
  )

  return competencia_selecionada, ordem_sel


# Carregando a competência selecionada na sidebar
try:
  conn_temp = obter_conexao()
  competencia_alvo, ordem_alvo = configurar_sidebar_competencia(
      conn_temp, prefixo_key="milenar_daniel"
  )
  conn_temp.close()
except Exception:
  competencia_alvo = datetime.now().strftime("%m/%Y")
  ordem_alvo = datetime.now().strftime("%Y-%m")


st.title("📜 Estratégia de Alocação Milenar (Talmude) — Painel do Daniel")
st.markdown(
    "Aplicação prática dos conceitos de **Tsedacá** e da **Regra dos Três"
    f" Terços** usando seus dados reais na nuvem (Competência: **{competencia_alvo}**)."
)

# --- SEÇÃO EDUCATIVA E CONCEITUAL ---
with st.expander(
    "📖 Clique aqui para entender a Origem e a Filosofia da Riqueza Milenar",
    expanded=False,
):
  st.markdown("""
        ### A Regra dos Três Terços do Talmude
        Para aprofundar seus conhecimentos, o ponto de partida ideal é a **Regra dos Três Terços do Talmude**, uma das diretrizes financeiras mais antigas e eficazes do mundo sobre gestão e diversificação de patrimônio.
        Há mais de 1.500 anos, o tratado **Baba Metzia (42a)** determinou a seguinte estratégia de alocação de recursos:
        > *"Uma pessoa deve sempre dividir seu dinheiro em três partes: um terço em terras, um terço em negócios e um terço mantido em mãos."*
    """)

st.divider()


# --- CARREGAMENTO COMPLETO DOS DADOS PARA O CÁLCULO ACUMULADO CORRETO ---
df_lancamentos = pd.DataFrame(columns=["data", "tipo", "categoria", "descricao", "valor"])
df_aportes = pd.DataFrame(columns=["data", "valor", "local_aplicacao"])
df_resgates = pd.DataFrame(columns=["data", "valor", "local_origem"])

try:
  conn = obter_conexao()
  try:
    df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conn)
  except Exception:
    conn.rollback()

  try:
    df_aportes = pd.read_sql_query("SELECT id, data, valor, local_aplicacao FROM desafio_aportes", conn)
  except Exception:
    conn.rollback()

  try:
    df_resgates = pd.read_sql_query("SELECT id, data, valor, local_origem, motivo FROM desafio_resgates", conn)
  except Exception:
    conn.rollback()
  conn.close()
except Exception as e:
  st.sidebar.error(f"Erro ao carregar banco: {e}")

# Tratamentos numéricos e competências
for df_target in [df_lancamentos, df_aportes, df_resgates]:
  if not df_target.empty and "data" in df_target.columns:
    res = df_target["data"].apply(extrair_competencia)
    df_target["competencia"] = [x[0] for x in res]
    df_target["comp_ordem"] = [x[1] for x in res]

if not df_lancamentos.empty:
  df_lancamentos["valor"] = pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
  df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].str.strip().str.lower()

if not df_aportes.empty:
  df_aportes["valor_num"] = pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)

if not df_resgates.empty:
  df_resgates["valor_num"] = pd.to_numeric(df_resgates["valor"], errors="coerce").fillna(0.0)

# Isola os dados do mês selecionado
df_lanc_mes = (
    df_lancamentos[
        (df_lancamentos["competencia"] == competencia_alvo)
        & (df_lancamentos["categoria"].str.strip().str.lower() != "resgate")
    ].copy()
    if not df_lancamentos.empty
    else pd.DataFrame()
)

total_receitas_mes = (
    df_lanc_mes[df_lanc_mes["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"])]["valor"].sum()
    if not df_lanc_mes.empty else 0.0
)

total_gastos_mes = (
    df_lanc_mes[df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])]["valor"].sum()
    if not df_lanc_mes.empty else 0.0
)

df_aportes_mes = (
    df_aportes[
        (df_aportes["competencia"] == competencia_alvo)
        & (~df_aportes["local_aplicacao"].str.contains("Rendimento", case=False, na=False))
    ].copy()
    if not df_aportes.empty else pd.DataFrame()
)
total_aportes_mes = df_aportes_mes["valor_num"].sum() if not df_aportes_mes.empty else 0.0

df_resgates_mes = (
    df_resgates[df_resgates["competencia"] == competencia_alvo].copy()
    if not df_resgates.empty else pd.DataFrame()
)
total_resgates_mes = df_resgates_mes["valor_num"].sum() if not df_resgates_mes.empty else 0.0


# Função para calcular o saldo acumulado dos meses anteriores (Saldo Anterior)
def calcular_saldo_ate_competencia(df_lan, df_ap, df_res, ordem_alvo):
  try:
    todas_ordens = sorted(
        list(
            set(
                df_lan[df_lan["comp_ordem"] != "9999-99"]["comp_ordem"].unique().tolist()
                + df_ap[df_ap["comp_ordem"] != "9999-99"]["comp_ordem"].unique().tolist()
                + (df_res[df_res["comp_ordem"] != "9999-99"]["comp_ordem"].unique().tolist() if not df_res.empty and "comp_ordem" in df_res.columns else [])
            )
        )
    )
    saldo_acumulado = 0.0
    for ord_comp in todas_ordens:
      if ord_comp < ordem_alvo:
        rec = df_lan[
            (df_lan["comp_ordem"] == ord_comp)
            & (df_lan["categoria"].str.strip().str.lower() != "resgate")
            & (df_lan["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"]))
        ]["valor"].sum()
        gas = df_lan[
            (df_lan["comp_ordem"] == ord_comp)
            & (df_lan["tipo_clean"].isin(["despesa", "débito", "debito", "saida"]))
        ]["valor"].sum()

        apo_c = (
            df_ap[(df_ap["comp_ordem"] == ord_comp) & (~df_ap["local_aplicacao"].str.contains("Rendimento", case=False, na=False))]["valor_num"].sum()
            if not df_ap.empty and "valor_num" in df_ap.columns else 0.0
        )
        res_c = (
            df_res[df_res["comp_ordem"] == ord_comp]["valor_num"].sum()
            if not df_res.empty and "valor_num" in df_res.columns else 0.0
        )

        saldo_acumulado += (rec - gas - (apo_c - res_c))
    return saldo_acumulado
  except Exception:
    return 0.0


saldo_remanescente_anterior = calcular_saldo_ate_competencia(
    df_lancamentos, df_aportes, df_resgates, ordem_alvo
)

# Saldo Livre real considerando o acumulado anterior + entradas do mês - gastos - aportes líquidos
saldo_livre = (
    saldo_remanescente_anterior
    + total_receitas_mes
    - total_gastos_mes
    - total_aportes_mes
    + total_resgates_mes
)

# Painel de métricas do sistema
st.markdown(f"### 📱 Resumo da Competência: {competencia_alvo}")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Saldo Anterior", f"R$ {saldo_remanescente_anterior:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col_m2.metric("Entradas", f"R$ {total_receitas_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col_m3.metric("Gastos Comuns", f"R$ {total_gastos_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col_m4.metric(
    "Saldo Livre",
    f"R$ {saldo_livre:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    delta="No Azul 💙" if saldo_livre >= 0 else "No Vermelho 🔴",
    delta_color="normal" if saldo_livre >= 0 else "inverse"
)

st.divider()

if saldo_livre > 0:
  # --- MATEMÁTICA MILENAR APLICADA AOS SEUS DADOS ---
  tsedaca = saldo_livre * 0.10
  saldo_investivel = saldo_livre - tsedaca
  um_terco = saldo_investivel / 3

  # --- RENDERIZAÇÃO DA INTERFACE ---
  st.warning(
      "🕊️ **Tsedacá (Justiça Social - 10%): R$"
      f" {tsedaca:,.2f}**".replace(",", "X")
      .replace(".", ",")
      .replace("X", ".")
  )
  st.caption(
      "Destine este valor para fazer o bem, apoiar projetos sociais ou ajudar"
      " na capacitação profissional de terceiros."
  )

  st.write("")
  st.markdown("### 🎯 Divisão Estratégica dos Três Terços (Talmude)")

  col1, col2, col3 = st.columns(3)

  with col1:
    st.info("🛡️ **1/3 em Terras**")
    st.subheader(
        f"R$ {um_terco:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    st.markdown(
        "**Foco:** Segurança e Preservação\n\n*Sugestão:* Fundos Imobiliários"
        " de Tijolo, Imóveis ou Renda Fixa IPCA+."
    )

  with col2:
    st.success("📈 **1/3 em Negócios**")
    st.subheader(
        f"R$ {um_terco:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    st.markdown(
        "**Foco:** Multiplicação e Crescimento\n\n*Sugestão:* Ações, novos"
        " projetos geradores de receita ou capacitação pessoal."
    )

  with col3:
    st.error("💰 **1/3 em Mãos**")
    st.subheader(
        f"R$ {um_terco:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    st.markdown(
        "**Foco:** Liquidez e Oportunidade\n\n*Sugestão:* Tesouro Selic ou CDB"
        " 100% CDI com liquidez diária."
    )

  # Elemento Gráfico Complementar
  st.write("")
  st.markdown("### 📊 Visão Geral do Repasse")
  df_grafico = pd.DataFrame({
      "Destino": [
          "Tsedacá",
          "Terras (Segurança)",
          "Negócios (Crescimento)",
          "Em Mãos (Liquidez)",
      ],
      "Valores": [tsedaca, um_terco, um_terco, um_terco],
  })
  st.bar_chart(data=df_grafico, x="Destino", y="Valores")

else:
  st.error(
      "O saldo livre em conta precisa ser positivo para aplicar o"
      " modelo milenar de investimentos."
  )