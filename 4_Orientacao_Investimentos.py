from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(
    page_title="Consultoria e Saúde Financeira — Painel do Daniel",
    page_icon="💡",
    layout="wide",
)
aplicar_estilo_moderno()


def obter_conexao():
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


def configurar_sidebar_competencia(conexao, prefixo_key="global"):
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

  for df_item in [df_l, df_a]:
    if not df_item.empty and "data" in df_item.columns:
      res = df_item["data"].apply(extrair_competencia)
      df_item["competencia"] = [x[0] for x in res]
      df_item["comp_ordem"] = [x[1] for x in res]

  if not df_l.empty or not df_a.empty:
    mapeamento_comps = pd.concat([
        df_l[["competencia", "comp_ordem"]]
        if not df_l.empty
        else pd.DataFrame(columns=["competencia", "comp_ordem"]),
        df_a[["competencia", "comp_ordem"]]
        if not df_a.empty
        else pd.DataFrame(columns=["competencia", "comp_ordem"]),
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
  st.sidebar.header("📅 Filtro de Competência")
  competencia_selecionada = st.sidebar.selectbox(
      "Selecione o Mês/Ano de Referência",
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


st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("💡 Consultoria Inteligente de Bolso - Diagnóstico Financeiro")
st.write(
    "Análise automática da sua saúde financeira com base no saldo acumulado,"
    " ganhos e compromissos mensais."
)

# Configuração da barra lateral
try:
  conexao_sidebar = obter_conexao()
  competencia_selecionada, ordem_selecionada = configurar_sidebar_competencia(
      conexao_sidebar, prefixo_key="diagnostico_financeiro_daniel"
  )
  conexao_sidebar.close()
except Exception:
  competencia_selecionada = datetime.now().strftime("%m/%Y")
  ordem_selecionada = datetime.now().strftime("%Y-%m")

# Carrega os dados do banco
try:
  conexao = obter_conexao()
  df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
  df_aportes = pd.read_sql_query("SELECT data, valor, local_aplicacao FROM desafio_aportes", conexao)
  df_resgates = pd.read_sql_query("SELECT data, valor, local_origem FROM desafio_resgates", conexao)
  conexao.close()
except Exception as e:
  st.error(f"Erro ao carregar dados para o diagnóstico: {e}")
  df_lancamentos = pd.DataFrame()
  df_aportes = pd.DataFrame()
  df_resgates = pd.DataFrame()

# Tratamentos numéricos e de competência
if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
  df_lancamentos["valor"] = pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
  df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].str.strip().str.lower()
else:
  df_lancamentos["tipo_clean"] = ""

if not df_aportes.empty and "valor" in df_aportes.columns:
  df_aportes["valor_num"] = pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
else:
  df_aportes["valor_num"] = 0.0

if not df_resgates.empty and "valor" in df_resgates.columns:
  df_resgates["valor_num"] = pd.to_numeric(df_resgates["valor"], errors="coerce").fillna(0.0)
else:
  df_resgates["valor_num"] = 0.0

for df_item in [df_lancamentos, df_aportes, df_resgates]:
  if not df_item.empty and "data" in df_item.columns:
    res = df_item["data"].apply(extrair_competencia)
    df_item["competencia"] = [x[0] for x in res]
    df_item["comp_ordem"] = [x[1] for x in res]

# Isola os lançamentos comuns do mês (excluindo resgates duplicados no cálculo de receitas comuns)
df_lanc_mes = (
    df_lancamentos[
        (df_lancamentos["competencia"] == competencia_selecionada)
        & (df_lancamentos["categoria"].str.strip().str.lower() != "resgate")
    ].copy()
    if not df_lancamentos.empty
    else pd.DataFrame()
)

total_receitas = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"])
    ]["valor"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

total_despesas = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])
    ]["valor"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

# Aportes e resgates específicos do mês (excluindo rendimentos)
df_aportes_mes = (
    df_aportes[
        (df_aportes["competencia"] == competencia_selecionada)
        & (~df_aportes["local_aplicacao"].str.contains("Rendimento", case=False, na=False))
    ].copy()
    if not df_aportes.empty
    else pd.DataFrame()
)
total_aportes_mes = (
    df_aportes_mes["valor_num"].sum() if not df_aportes_mes.empty and "valor_num" in df_aportes_mes.columns else 0.0
)

df_resgates_mes = (
    df_resgates[df_resgates["competencia"] == competencia_selecionada].copy()
    if not df_resgates.empty and "competencia" in df_resgates.columns
    else pd.DataFrame()
)
total_resgates_mes = (
    df_resgates_mes["valor_num"].sum() if not df_resgates_mes.empty and "valor_num" in df_resgates_mes.columns else 0.0
)

impacto_investimentos_mes = total_aportes_mes - total_resgates_mes

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
            df_ap[
                (df_ap["comp_ordem"] == ord_comp)
                & (~df_ap["local_aplicacao"].str.contains("Rendimento", case=False, na=False))
            ]["valor_num"].sum()
            if not df_ap.empty and "valor_num" in df_ap.columns
            else 0.0
        )
        res_c = (
            df_res[df_res["comp_ordem"] == ord_comp]["valor_num"].sum()
            if not df_res.empty and "valor_num" in df_res.columns
            else 0.0
        )
        saldo_acumulado += (rec - gas - (apo_c - res_c))
    return saldo_acumulado
  except Exception:
    return 0.0

saldo_anterior = calcular_saldo_ate_competencia(
    df_lancamentos, df_aportes, df_resgates, ordem_selecionada
)

# Saldo Livre / Resultado Final da Conta Corrente do Mês
saldo_livre = saldo_anterior + total_receitas - total_despesas - impacto_investimentos_mes

def fmt_moeda(v):
  return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.divider()

st.markdown(f"### 📊 Seus Indicadores Atuais ({competencia_selecionada})")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
  st.metric(label="🟢 Total de Ganhos (Receitas)", value=fmt_moeda(total_receitas))
with col_m2:
  st.metric(label="🔴 Total de Compromissos", value=fmt_moeda(total_despesas))
with col_m3:
  st.metric(label="⚖️ Saldo Livre / Resultado", value=fmt_moeda(saldo_livre))
with col_m4:
  if total_receitas == 0 and total_despesas == 0 and saldo_anterior == 0:
    status_saude = "Sem Dados"
  elif saldo_livre < 0:
    status_saude = "🚨 Em Déficit (Vermelho)"
  elif abs(saldo_livre) < 0.05:
    status_saude = "⚠️ No Zero a Zero"
  else:
    status_saude = "✅ Com Sobra (Azul)"
  st.metric(label="🩺 Status da Saúde Financeira", value=status_saude)

st.divider()

st.markdown("### 🧭 Roteiro Estratégico Personalizado para o seu Momento")

if saldo_livre >= 0:
  st.success(
      "✅ **Diagnóstico:** Parabéns! O seu orçamento possui margem saudável."
      " Mantenha a regra de direcionar a sobra diretamente para a sua Reserva de Emergência!"
  )
  st.markdown("""
      #### 🚀 Plano de Ação para a sua Reserva de Emergência:
      1. **Pague-se Primeiro:** Separe uma porcentagem do valor dos seus ganhos assim que os receber.
      2. **Destino Seguro:** Aplique em **Renda Fixa com liquidez diária** (Tesouro Selic ou CDBs que paguem 100%+ do CDI).
      3. **Consistência:** A constância dos aportes mensais é o fator mais relevante para atingir as suas metas de longo prazo.
      """)
else:
  st.error(
      "🚨 **Diagnóstico:** O seu caixa acumulado atual está negativo."
      " Reorganize as despesas do mês para recuperar a margem de segurança."
  )
  st.markdown("""
      #### 🛠️ Plano de Ação Imediato:
      1. **Mapeamento de Gastos:** Identifique nas categorias de despesas onde estão ocorrendo os maiores vazamentos.
      2. **Controle de Impulsos:** Mantenha os aportes guardados em conta de rendimento e evite resgates para cobrir gastos do dia a dia.
      """)