from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(
    page_title="Gerenciar Lançamentos — Painel do Daniel",
    page_icon="✏️",
    layout="wide",
)
aplicar_estilo_moderno()


def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


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
st.subheader("✏️ Gerenciar, Editar ou Excluir Lançamentos")
st.write(
    "Gerencie, edite ou exclua seus lançamentos manuais e acompanhe seus"
    " compromissos."
)

try:
  conexao = obter_conexao()

  competencia_selecionada, ordem_selecionada = configurar_sidebar_competencia(
      conexao, prefixo_key="gerenciar_lancamentos_daniel"
  )

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
  competencia_selecionada = datetime.now().strftime("%m/%Y")

if not df.empty:
  res_lanc = df["data"].apply(extrair_competencia)
  df["competencia"] = [x[0] for x in res_lanc]
  df["comp_ordem"] = [x[1] for x in res_lanc]

  df_mes = df[df["competencia"] == competencia_selecionada].copy()

  df["data_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
  hoje = pd.Timestamp(datetime.now().date())

  df_futuros = (
      df[df["data_dt"] > hoje]
      .sort_values(by="data_dt", ascending=True)
      .copy()
  )

  if not df_div.empty:
    df_div_ativas = df_div[df_div["valor_parcela"] > 0].copy()

    if not df_div_ativas.empty:
      mes_atual = hoje.month
      ano_atual = hoje.year

      lista_parcelas_mes = []
      for _, row in df_div_ativas.iterrows():
        dia_v = (
            int(row["dia_vencimento"])
            if pd.notna(row["dia_vencimento"]) and row["dia_vencimento"] > 0
            else 10
        )
        try:
          data_venc_obj = datetime(ano_atual, mes_atual, dia_v)
        except ValueError:
          data_venc_obj = datetime(ano_atual, mes_atual, 28)

        if data_venc_obj < datetime.now():
          if mes_atual == 12:
            data_venc_obj = datetime(ano_atual + 1, 1, dia_v)
          else:
            data_venc_obj = datetime(ano_atual, mes_atual + 1, dia_v)

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

  st.write(
      f"### 🔄 Editar ou Excluir Registros ({competencia_selecionada})"
  )


  def fmt_moeda(v):
    return (
        f"R$ {v:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


  if not df_mes.empty:
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

    id_str = lancamento_selecionado.split(" | ")[0].replace("ID: ", "")
    dados_atuais = df_mes[df_mes["id"].astype(str) == id_str].iloc[0]

    st.divider()

    col_edit1, col_edit2 = st.columns(2)

    with col_edit1:
      st.markdown("### 🔄 Atualizar Lançamento")

      opcoes_tipo = [
          "Receita (crédito)",
          "Despesa (débito)",
          "Aporte (investimento)",
      ]
      tipo_atual_raw = str(dados_atuais["tipo"]).strip().lower()

      if "rec" in tipo_atual_raw or "cred" in tipo_atual_raw:
        idx_padrao = 0
      elif "apo" in tipo_atual_raw or "inv" in tipo_atual_raw:
        idx_padrao = 2
      else:
        idx_padrao = 1

      with st.form("form_edicao_daniel"):
        novo_tipo_sel = st.selectbox(
            "Tipo de Lançamento", opcoes_tipo, index=idx_padrao
        )
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
        nova_data = st.text_input(
            "Data (DD/MM/AAAA)", value=dados_atuais["data"]
        )

        salvar_alteracao = st.form_submit_button("Salvar Alterações")

        if salvar_alteracao:
          if "Receita" in novo_tipo_sel:
            tipo_banco = "Receita"
          elif "Despesa" in novo_tipo_sel:
            tipo_banco = "Despesa"
          else:
            tipo_banco = "Aporte"

          try:
            datetime.strptime(nova_data.strip(), "%d/%m/%Y")
            conexao = obter_conexao()
            cursor = conexao.cursor()
            valor_limpo = abs(float(novo_valor))

            cursor.execute(
                """
                UPDATE lancamentos 
                SET data = %s, tipo = %s, categoria = %s, descricao = %s, valor = %s
                WHERE id = %s
                """,
                (
                    nova_data.strip(),
                    tipo_banco,
                    nova_categoria.strip(),
                    nova_descricao.strip(),
                    valor_limpo,
                    int(id_str),
                ),
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.success(f"Lançamento ID {id_str} atualizado para {tipo_banco} com sucesso!")
            st.rerun()
          except ValueError:
            st.error("A data digitada é inválida. Utilize o formato DD/MM/AAAA.")
          except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

    with col_edit2:
      st.markdown("### 🗑️ Excluir Lançamento")
      st.warning(
          "Atenção: Essa operação apagará permanentemente este registro."
      )

      if st.button("Excluir este Lançamento", type="primary"):
        try:
          conexao = obter_conexao()
          cursor = conexao.cursor()
          
          val_item = float(dados_atuais["valor"])
          
          cursor.execute("DELETE FROM desafio_resgates WHERE valor = %s", (val_item,))
          cursor.execute("DELETE FROM lancamentos WHERE id = %s", (int(id_str),))
          
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Lançamento excluído com sucesso!")
          st.rerun()
        except Exception as e:
          st.error(f"Erro ao excluir: {e}")
  else:
    st.info(
        f"Nenhum lançamento encontrado na competência {competencia_selecionada}."
    )

  st.divider()
  st.markdown("### ⏳ Lançamentos Futuros e Parcelamentos a Pagar")

  if not df_futuros.empty:
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
  else:
    st.info("Não há lançamentos futuros ou parcelamentos ativos cadastrados.")
else:
  st.info("Nenhum lançamento cadastrado no banco de dados.")