import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(
    page_title="Diagnóstico & Reserva - Painel do Daniel",
    page_icon="🎯",
    layout="wide",
)
aplicar_estilo_moderno()

st.title("💰 Controle Financeiro — Painel do Daniel")
st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")
st.markdown(
    "Esta aba analisa os seus lançamentos diários, identifica os principais gargalos"
    " de despesas e traça a rota para construir e acelerar a sua reserva de segurança."
)


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
      return (
          pd.DataFrame(),
          pd.DataFrame(),
          pd.DataFrame(),
          pd.DataFrame(),
      )

    conn = psycopg2.connect(db_url)
    df_l = pd.read_sql("SELECT * FROM lancamentos;", con=conn)
    df_d = pd.read_sql("SELECT * FROM dividas;", con=conn)

    try:
      df_a = pd.read_sql(
          "SELECT id, data, valor, local_aplicacao FROM desafio_aportes;",
          con=conn,
      )
    except Exception:
      df_a = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])

    try:
      df_r = pd.read_sql("SELECT * FROM desafio_resgates;", con=conn)
    except Exception:
      df_r = pd.DataFrame(columns=["id", "data", "valor", "motivo"])

    conn.close()
    return df_l, df_d, df_a, df_r
  except Exception as e:
    st.error(f"Erro ao conectar ao banco: {e}")
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


df_lancamentos, df_dividas, df_aportes, df_resgates = carregar_dados()

# Filtro de Competência
st.sidebar.header("📅 Filtro de Competência")
comps = []
if not df_lancamentos.empty and "data" in df_lancamentos.columns:
  df_lancamentos["data_dt"] = pd.to_datetime(
      df_lancamentos["data"], errors="coerce", dayfirst=True
  )
  df_lancamentos["competencia"] = df_lancamentos["data_dt"].dt.strftime(
      "%m/%Y"
  )
  comps = sorted(
      df_lancamentos["competencia"].dropna().unique().tolist(),
      key=lambda c: f"{c.split('/')[1]}{c.split('/')[0]}",
  )

opcoes = ["Todos os Meses"] + comps
comp_sel = st.sidebar.selectbox("Mês de Referência", options=opcoes, index=0)

df_filtrado = (
    df_lancamentos[df_lancamentos["competencia"] == comp_sel]
    if comp_sel != "Todos os Meses" and not df_lancamentos.empty
    else df_lancamentos.copy()
)

if df_filtrado.empty:
  st.info(f"Nenhum lançamento encontrado para {comp_sel}.")
else:
  df_filtrado["valor"] = pd.to_numeric(
      df_filtrado["valor"], errors="coerce"
  ).fillna(0.0)

  # Filtro de receitas de trabalho/ganhos (exclui a categoria 'resgate')
  rec_tot = df_filtrado[
      (df_filtrado["tipo"].str.lower() == "receita")
      & (df_filtrado["categoria"].str.strip().str.lower() != "resgate")
  ]["valor"].sum()

  desp_tot = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"][
      "valor"
  ].sum()

  tot_ap = (
      pd.to_numeric(
          df_aportes[
              ~df_aportes["local_aplicacao"].str.contains(
                  "Rendimento", case=False, na=False
              )
          ]["valor"],
          errors="coerce",
      )
      .fillna(0.0)
      .sum()
      if not df_aportes.empty
      else 0.0
  )
  tot_res = (
      pd.to_numeric(df_resgates["valor"], errors="coerce").fillna(0.0).sum()
      if not df_resgates.empty
      else 0.0
  )
  reserva_liq = tot_ap - tot_res
  saldo_atual = rec_tot - desp_tot

  st.subheader(f"📊 Panorama Atual ({comp_sel})")
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("Receita Atual", f"R$ {rec_tot:,.2f}")
  c2.metric("Despesa Atual", f"R$ {desp_tot:,.2f}")
  c3.metric(
      "Reserva Guardada (Aportes)",
      f"R$ {reserva_liq:,.2f}",
      delta="Patrimônio Líquido 💙",
  )
  c4.metric(
      "Resultado Líquido do Mês",
      f"R$ {saldo_atual:,.2f}",
      delta=(
          f"{(saldo_atual/rec_tot)*100:.1f}% da Receita"
          if rec_tot > 0
          else "0%"
      ),
      delta_color="normal" if saldo_atual >= 0 else "inverse",
  )

  st.divider()
  st.subheader("🚀 Simulador Estratégico de Reserva e Aportes Extra")

  col1, col2 = st.columns(2)
  with col1:
    meta_alvo = st.number_input(
        "Meta de Reserva Desejada (R$)",
        min_value=500.0,
        value=3000.0,
        step=500.0,
        format="%.2f",
    )
    incluir_extra = st.checkbox(
        "Considerar Injeção / Aporte Extra Inicial (R$ 500,00)", value=False
    )
    val_extra = 500.0 if incluir_extra else 0.0

    saldo_livre_mensal = max(0.0, saldo_atual)

  with col2:
    st.metric(
        "Capacidade de Aporte Mensal (Saldo Livre)",
        f"R$ {saldo_livre_mensal:,.2f}",
        delta="Sobra atual calculada",
    )
    st.metric(
        "Reserva Já Acumulada",
        f"R$ {reserva_liq:,.2f}",
    )
    if incluir_extra:
      st.success(
          f"💰 **Aporte Extra:** R$ {val_extra:,.2f} considerados no cálculo inicial."
      )

  quanto_falta = max(0.0, meta_alvo - val_extra - reserva_liq)
  if saldo_livre_mensal > 1.0:
    meses_est = quanto_falta / saldo_livre_mensal
    st.info(
        f"🎯 **Previsão de Sucesso:** Guardando a sua sobra mensal de **R$ {saldo_livre_mensal:,.2f}**, você atingirá a sua meta de **R$ {meta_alvo:,.2f}** em aproximadamente **{meses_est:.1f} meses**!"
    )
  else:
    st.warning(
        "💡 **Atenção:** Seu saldo livre mensal está baixo ou zerado. Ajuste os seus lançamentos ou controle os gastos diários para liberar margem para aportes na reserva."
    )

  st.divider()
  st.subheader("🔍 Mapeamento Detalhado de Gastos e Despesas")
  df_despesas = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"]
  if not df_despesas.empty:
    gargalos = (
        df_despesas.groupby("categoria")["valor"]
        .sum()
        .reset_index()
        .sort_values(by="valor", ascending=False)
    )
    gargalos["% do Total"] = (
        (gargalos["valor"] / desp_tot) * 100 if desp_tot > 0 else 0
    )
    st.dataframe(
        gargalos.style.format({"valor": "R$ {:,.2f}", "% do Total": "{:.1f}%"}),
        use_container_width=True,
    )

  st.divider()

  # Plano de Ação para o Daniel
  st.subheader("🛡️ Plano Diretor de Educação & Formação Patrimonial")
  st.markdown("""
1. **Consistência nos Aportes:** Como não há custos pesados de moradia/aluguel, o foco principal nesta fase de vida é transformar o saldo positivo em investimentos diários/mensais antes de gastar o dinheiro.
2. **Separação de Contas:** Mantenha os aportes guardados no *Módulo do Desafio* (Renda Fixa/Liquidez Diária) separados do saldo da conta corrente comum para evitar o consumo por impulso.
3. **Mapeamento das Categoria de Lazer/Acessórios:** Acompanhe a tabela de saídas para garantir que pequenas despesas recorrentes não consumam a capacidade de poupança do mês.
""")