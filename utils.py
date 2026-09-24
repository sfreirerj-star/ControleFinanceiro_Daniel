from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st


def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


# --- FUNÇÃO PARA GERENCIAR A COMPETÊNCIA GLOBALMENTE ---
def configurar_sidebar_competencia():
  # Carrega dados básicos apenas para listar as competências disponíveis
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

  # Processar ordenação das competências
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

  # Inicializar session_state se não existir
  if "competencia_selecionada" not in st.session_state:
    st.session_state["competencia_selecionada"] = (
        mes_atual_sistema
        if mes_atual_sistema in competencias_disponiveis
        else competencias_disponiveis[0]
    )

  # Garantir índice válido para o selectbox
  try:
    index_atual = competencias_disponiveis.index(
        st.session_state["competencia_selecionada"]
    )
  except ValueError:
    index_atual = 0

  # Seletor na Barra Lateral (Comportamento Global via session_state)
  st.sidebar.header("📅 Competência (Mês/Ano)")
  st.session_state["competencia_selecionada"] = st.sidebar.selectbox(
      "Selecione o Mês de Referência",
      options=competencias_disponiveis,
      index=index_atual,
      key="selectbox_competencia",
  )

  # Retorna a competência e a ordem para filtros nas páginas
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
