from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Controle Financeiro Pro", page_icon="💰", layout="centered"
)

st.title("💰 Controle Financeiro - Sair do Vermelho")
st.write("Aplicativo de controle total de créditos, débitos e investimentos.")


# Conexão com o Banco de Dados PostgreSQL no Supabase via Secrets
def obter_conexao():
  url_conexao = st.secrets["DATABASE_URL"]
  return psycopg2.connect(url_conexao)


# Inicializar as tabelas no Supabase caso não existam
def inicializar_banco():
  try:
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                data TEXT,
                tipo TEXT,
                categoria TEXT,
                descricao TEXT,
                valor REAL
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS dividas (
                id SERIAL PRIMARY KEY,
                credor TEXT,
                valor_total REAL,
                juros_mensal REAL,
                status TEXT
            )
        """)
    conexao.commit()
    cursor.close()
    conexao.close()
  except Exception as e:
    st.error(
        f"Erro ao conectar com o banco de dados no Supabase: {e}. Verifique a"
        " URL nos Secrets."
    )
    st.stop()


inicializar_banco()

menu = st.sidebar.selectbox(
    "Menu Principal",
    [
        "📊 Painel & Gráficos",
        "➕ Novo Lançamento",
        "⚠️ Raio-X de Dívidas",
        "💡 Orientação & Investimentos",
    ],
)

# Carregar dados do Supabase para DataFrames do Pandas
try:
  conexao = obter_conexao()
  df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
  df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
  conexao.close()
except Exception:
  df_lancamentos = pd.DataFrame(
      columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
  )
  df_dividas = pd.DataFrame(
      columns=["id", "credor", "valor_total", "juros_mensal", "status"]
  )


if menu == "📊 Painel & Gráficos":
  st.subheader("Resumo do Mês e Visualização Gráfica")

  if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
    df_lancamentos["valor"] = pd.to_numeric(
        df_lancamentos["valor"], errors="coerce"
    )
    total_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"][
        "valor"
    ].sum()
    total_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"][
        "valor"
    ].sum()
    saldo = total_receitas - total_despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Entradas", f"R$ {total_receitas:.2f}")
    col2.metric("Saídas", f"R$ {total_despesas:.2f}")

    if saldo >= 0:
      col3.metric("Saldo Atual", f"R$ {saldo:.2f}", delta="No Azul 💙")
    else:
      col3.metric(
          "Saldo Atual",
          f"R$ {saldo:.2f}",
          delta="No Vermelho 🔴",
          delta_color="inverse",
      )

    st.divider()

    # Gráficos se houver despesas
    df_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"]
    if not df_despesas.empty:
      st.write("### Distribuição dos Gastos por Categoria")
      gasto_por_cat = df_despesas.groupby("categoria")["valor"].sum()

      # Gráfico de Pizza e Barras lado a lado
      col_g1, col_g2 = st.columns(2)

      with col_g1:
        st.write("**Gráfico de Pizza**")
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(
            gasto_por_cat, labels=gasto_por_cat.index, autopct="%1.1f%%", startangle=90
        )
        ax1.axis("equal")
        st.pyplot(fig1)

      with col_g2:
        st.write("**Gráfico de Barras**")
        fig2, ax2 = plt.subplots(figsize=(4, 4))
        gasto_por_cat.plot(kind="bar", ax=ax2, color="#1a73e8")
        ax2.set_ylabel("Valor (R$)")
        plt.xticks(rotation=45)
        st.pyplot(fig2)
    else:
      st.info(
          "Cadastre algumas despesas na aba ao lado para visualizar os gráficos"
          " de pizza e barras."
      )

    st.subheader("Histórico de Lançamentos")
    st.dataframe(df_lancamentos.tail(10), use_container_width=True)
  else:
    st.info(
        "Nenhum lançamento registrado ainda. Utilize a aba 'Novo Lançamento' para"
        " começar."
    )

elif menu == "➕ Novo Lançamento":
  st.subheader("Registrar Gasto ou Receita")

  with st.form("form_lancamento", clear_on_submit=True):
    tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
    categoria = st.text_input(
        "Categoria (Ex: Alimentação, Moradia, Transporte, Cartão)"
    )
    descricao = st.text_input("Descrição / Estabelecimento")
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    data = datetime.now().strftime("%d/%m/%Y")

    enviar = st.form_submit_button("Salvar Lançamento")

    if enviar:
      if categoria and valor > 0:
        try:
          conexao = obter_conexao()
          cursor = conexao.cursor()
          cursor.execute(
              """
                        INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)
                        VALUES (%s, %s, %s, %s, %s)
                    """,
              (data, tipo, categoria, descricao, valor),
          )
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Lançamento salvo com sucesso no banco em nuvem!")
          st.rerun()
        except Exception as e:
          st.error(f"Erro ao salvar: {e}")
      else:
        st.error("Preencha a categoria e um valor válido.")

elif menu == "⚠️ Raio-X de Dívidas":
  st.subheader("Gerenciar Dívidas e Juros")

  with st.form("form_divida", clear_on_submit=True):
    credor = st.text_input("Credor / Nome da Dívida (Ex: Cartão de Crédito)")
    valor_total = st.number_input(
        "Valor Total Devido (R$)", min_value=0.0, format="%.2f"
    )
    juros_mensal = st.number_input(
        "Taxa de Juros Mensal (%)", min_value=0.0, format="%.2f"
    )

    salvar_divida = st.form_submit_button("Cadastrar Dívida")

    if salvar_divida:
      if credor and valor_total > 0:
        try:
          conexao = obter_conexao()
          cursor = conexao.cursor()
          cursor.execute(
              """
                        INSERT INTO dividas (credor, valor_total, juros_mensal, status)
                        VALUES (%s, %s, %s, %s)
                    """,
              (credor, valor_total, juros_mensal, "Pendente"),
          )
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Dívida cadastrada com sucesso!")
          st.rerun()
        except Exception as e:
          st.error(f"Erro ao salvar dívida: {e}")
      else:
        st.error("Preencha o credor e o valor total.")

  if not df_dividas.empty:
    st.write("### Suas Dívidas Ativas")
    st.dataframe(df_dividas, use_container_width=True)

elif menu == "💡 Orientação & Investimentos":
  st.subheader("💡 Consultoria Inteligente de Bolso")

  st.markdown("""
    > **Estratégia para Sair do Vermelho e Retomar o Azul:**
    > 1. **Estanque o Sangramento:** O juro do cartão de crédito e do cheque especial destrói qualquer orçamento. Se houver dívidas caras cadastradas, priorize fazer um acordo ou portabilidade antes de investir em ativos de renda variável.
    > 2. **Corte Cirúrgico (Gráficos):** Olhe na aba de painel para onde está indo o maior volume de recursos nos gráficos de pizza e barras. Reduza 20% dos supérfluos imediatamente.
    > 3. **A Metodologia do Centavo:** Anotar cada movimentação evita o efeito "goteira" (pequenos gastos diários que somados consomem metade do salário).
    """)

  st.markdown("---")
  st.subheader(
      "📈 Primeiros Passos nos Investimentos (Assim que zerar o déficit)"
  )

  st.info("""
    * **Reserva de Emergência:** Assim que o saldo ficar positivo, o primeiro destino do dinheiro deve ser a Renda Fixa com liquidez diária (Tesouro Selic ou CDBs de bancos sólidos que pagem 100% do CDI). O objetivo é juntar de 3 a 6 meses do seu custo de vida.
    * **Segurança e Rendimento:** Diferente da caderneta de poupança tradicional, essas opções rendem todos os dias úteis e possuem a proteção do FGC (Fundo Garantidor de Créditos) até R$ 250 mil por instituição.
    """)