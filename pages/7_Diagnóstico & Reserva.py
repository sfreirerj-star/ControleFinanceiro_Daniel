from datetime import datetime
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


def obter_conexao():
  db_url = st.secrets.get("DATABASE_URL")
  if not db_url:
    for k, v in st.secrets.items():
      if isinstance(v, str) and "postgresql://" in v:
        db_url = v
        break
  return psycopg2.connect(db_url)


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


# Carregamento dos dados
df_lancamentos = pd.DataFrame(columns=["data", "tipo", "categoria", "descricao", "valor"])
df_dividas = pd.DataFrame(columns=["credor", "valor_total"])
df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])
df_resgates = pd.DataFrame(columns=["id", "data", "valor", "motivo"])

try:
  conn = obter_conexao()
  df_lancamentos = pd.read_sql("SELECT * FROM lancamentos;", con=conn)
  df_dividas = pd.read_sql("SELECT * FROM dividas;", con=conn)
  try:
    df_aportes = pd.read_sql("SELECT id, data, valor, local_aplicacao FROM desafio_aportes;", con=conn)
  except Exception:
    pass
  try:
    df_resgates = pd.read_sql("SELECT * FROM desafio_resgates;", con=conn)
  except Exception:
    pass
  conn.close()
except Exception as e:
  st.error(f"Erro ao conectar ao banco: {e}")

# Processamento de competências
for df_t in [df_lancamentos, df_aportes, df_resgates]:
  if not df_t.empty and "data" in df_t.columns:
    res = df_t["data"].apply(extrair_competencia)
    df_t["competencia"] = [x[0] for x in res]
    df_t["comp_ordem"] = [x[1] for x in res]

mapeamento_comps = pd.concat([
    df_lancamentos[["competencia", "comp_ordem"]] if not df_lancamentos.empty and "competencia" in df_lancamentos.columns else pd.DataFrame(columns=["competencia", "comp_ordem"]),
    df_aportes[["competencia", "comp_ordem"]] if not df_aportes.empty and "competencia" in df_aportes.columns else pd.DataFrame(columns=["competencia", "comp_ordem"]),
    df_resgates[["competencia", "comp_ordem"]] if not df_resgates.empty and "competencia" in df_resgates.columns else pd.DataFrame(columns=["competencia", "comp_ordem"]),
]).drop_duplicates()

mapeamento_comps = mapeamento_comps[mapeamento_comps["competencia"] != "Indefinido"].sort_values("comp_ordem", ascending=False)
competencias_disponiveis = mapeamento_comps["competencia"].tolist() if not mapeamento_comps.empty else [datetime.now().strftime("%m/%Y")]
mes_atual_sistema = datetime.now().strftime("%m/%Y")

if mes_atual_sistema not in competencias_disponiveis:
  competencias_disponiveis.insert(0, mes_atual_sistema)

# Filtro de Competência na Sidebar (Padrão Unificado)
st.sidebar.markdown("---")
st.sidebar.header("📅 Filtro de Competência")
comp_sel = st.sidebar.selectbox("Mês de Referência", options=competencias_disponiveis, index=0 if mes_atual_sistema in competencias_disponiveis else 0)

ordem_selecionada = (
    mapeamento_comps[mapeamento_comps["competencia"] == comp_sel]["comp_ordem"].values[0]
    if not mapeamento_comps.empty and comp_sel in mapeamento_comps["competencia"].values
    else datetime.now().strftime("%Y-%m")
)

# Tratamento numérico
if not df_lancamentos.empty:
  df_lancamentos["valor"] = pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
  df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].str.strip().str.lower()

if not df_aportes.empty:
  df_aportes["valor_num"] = pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)

if not df_resgates.empty:
  df_resgates["valor_num"] = pd.to_numeric(df_resgates["valor"], errors="coerce").fillna(0.0)

# Isola dados do mês selecionado
df_lanc_mes = (
    df_lancamentos[
        (df_lancamentos["competencia"] == comp_sel)
        & (df_lancamentos["categoria"].str.strip().str.lower() != "resgate")
    ].copy()
    if not df_lancamentos.empty else pd.DataFrame()
)

rec_tot = (
    df_lanc_mes[df_lanc_mes["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"])]["valor"].sum()
    if not df_lanc_mes.empty else 0.0
)

desp_tot = (
    df_lanc_mes[df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])]["valor"].sum()
    if not df_lanc_mes.empty else 0.0
)

df_aportes_mes = (
    df_aportes[
        (df_aportes["competencia"] == comp_sel)
        & (~df_aportes["local_aplicacao"].str.contains("Rendimento", case=False, na=False))
    ].copy()
    if not df_aportes.empty else pd.DataFrame()
)
tot_ap_mes = df_aportes_mes["valor_num"].sum() if not df_aportes_mes.empty else 0.0

df_resgates_mes = (
    df_resgates[df_resgates["competencia"] == comp_sel].copy()
    if not df_resgates.empty else pd.DataFrame()
)
tot_res_mes = df_resgates_mes["valor_num"].sum() if not df_resgates_mes.empty else 0.0


# Função de cálculo de saldo acumulado anterior
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


saldo_anterior = calcular_saldo_ate_competencia(df_lancamentos, df_aportes, df_resgates, ordem_selecionada)

# Saldo Final / Resultado Líquido unificado e real da conta
saldo_atual = (
    saldo_anterior
    + rec_tot
    - desp_tot
    - tot_ap_mes
    + tot_res_mes
)

# Reserva Líquida total acumulada até o mês
reserva_liq = (
    df_aportes[df_aportes["comp_ordem"] <= ordem_selecionada]["valor_num"].sum()
    if not df_aportes.empty and "valor_num" in df_aportes.columns else 0.0
) - (
    df_resgates[df_resgates["comp_ordem"] <= ordem_selecionada]["valor_num"].sum()
    if not df_resgates.empty and "comp_ordem" in df_resgates.columns and "valor_num" in df_resgates.columns else 0.0
)

st.subheader(f"📊 Panorama Atual ({comp_sel})")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Receita Atual", f"R$ {rec_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c2.metric("Despesa Atual", f"R$ {desp_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c3.metric(
    "Reserva Guardada (Aportes)",
    f"R$ {reserva_liq:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    delta="Patrimônio Líquido 💙",
)
c4.metric(
    "Resultado Líquido do Mês",
    f"R$ {saldo_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
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
      f"R$ {saldo_livre_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
      delta="Sobra atual calculada",
  )
  st.metric(
      "Reserva Já Acumulada",
      f"R$ {reserva_liq:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
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
df_despesas = df_lanc_mes[df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])]
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
else:
  st.info("Nenhuma despesa registrada nesta competência.")

st.divider()

# Plano de Ação para o Daniel
st.subheader("🛡️ Plano Diretor de Educação & Formação Patrimonial")
st.markdown("""
1. **Consistência nos Aportes:** Como não há custos pesados de moradia/aluguel, o foco principal nesta fase de vida é transformar o saldo positivo em investimentos diários/mensais antes de gastar o dinheiro.
2. **Separação de Contas:** Mantenha os aportes guardados no *Módulo do Desafio* (Renda Fixa/Liquidez Diária) separados do saldo da conta corrente comum para evitar o consumo por impulso.
3. **Mapeamento das Categoria de Lazer/Acessórios:** Acompanhe a tabela de saídas para garantir que pequenas despesas recorrentes não consumam a capacidade de poupança do mês.
""")