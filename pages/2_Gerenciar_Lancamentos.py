from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Gerenciar Lançamentos - Daniel", page_icon="✏️", layout="wide"
)


def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("✏️ Gerenciar, Editar ou Excluir Lançamentos")

try:
  conexao = obter_conexao()
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

if not df.empty:
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

  st.markdown("### ⏳ Lançamentos Futuros e Parcelamentos a Pagar")

  if not df_futuros.empty:
    st.info(
        "Aqui estão reunidos seus compromissos manuais futuros e as parcelas"
        " ativas das suas dívidas com base nos dias de vencimento."
    )

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

    total_futuro_valor = (
        df_futuros[df_futuros["tipo"] == "Despesa"]["valor"].sum()
        - df_futuros[df_futuros["tipo"] == "Receita"]["valor"].sum()
    )
    total_fut_fmt = (
        f"R$ {abs(total_futuro_valor):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    st.metric(
        label="📉 Impacto Líquido dos Próximos Vencimentos Listados",
        value=total_fut_fmt,
    )
  else:
    st.info("Não há lançamentos futuros ou parcelamentos ativos cadastrados.")

  st.divider()

  st.write("### 🔄 Editar ou Excluir Registros Manuais")
  st.write(
      "Selecione um lançamento abaixo para alterar os dados ou corrigir o tipo."
  )


  def fmt_moeda(v):
    return (
        f"R$ {v:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


  df["valor_fmt"] = (
      pd.to_numeric(df["valor"], errors="coerce")
      .fillna(0.0)
      .apply(fmt_moeda)
  )

  df["resumo_label"] = (
      "ID: "
      + df["id"].astype(str)
      + " | "
      + df["data"]
      + " | "
      + df["tipo"]
      + " | "
      + df["categoria"]
      + " | "
      + df["valor_fmt"]
      + " ("
      + df["descricao"].fillna("")
      + ")"
  )

  lancamento_selecionado = st.selectbox(
      "Escolha o lançamento para gerenciar:", df["resumo_label"].tolist()
  )

  id_selecionado = int(
      lancamento_selecionado.split(" | ")[0].replace("ID: ", "")
  )
  dados_atuais = df[df["id"] == id_selecionado].iloc[0]

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

    with st.form("form_edicao"):
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
      nova_data = st.text_input("Data (DD/MM/AAAA)", value=dados_atuais["data"])

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
                  id_selecionado,
              ),
          )
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success(
              f"Lançamento ID {id_selecionado} atualizado para {tipo_banco} com"
              " sucesso!"
          )
          st.rerun()
        except ValueError:
          st.error("A data digitada é inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
          st.error(f"Erro ao atualizar: {e}")

  with col_edit2:
    st.markdown("### 🗑️ Excluir Lançamento")
    st.warning(
        "Atenção: Essa operação apagará permanentemente este registro e o saldo"
        " retornará imediatamente ao valor real."
    )

    if st.button("Excluir este Lançamento", type="primary"):
      try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "DELETE FROM lancamentos WHERE id = %s", (id_selecionado,)
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        st.success("Lançamento excluído com sucesso!")
        st.rerun()
      except Exception as e:
        st.error(f"Erro ao excluir: {e}")
else:
  st.info("Nenhum lançamento encontrado para gerenciar.")