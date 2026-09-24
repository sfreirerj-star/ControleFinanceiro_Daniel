from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Novo Lançamento - Daniel", page_icon="📝", layout="wide"
)

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def garantir_tabelas():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor NUMERIC(10,2) NOT NULL
            )
        """)
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception:
        pass

garantir_tabelas()

st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("📝 Novo Lançamento & Registo de Caixa")
st.write("Registe as suas receitas e despesas do dia a dia com abatimento automático dos aportes de investimentos.")

# Formulário de Novo Lançamento organizado com valores limpos e zerados
with st.form("form_novo_lancamento", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        data_lancamento = st.text_input("Data do Lançamento (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y"))
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
    with col2:
        categoria = st.text_input("Categoria (Ex: Alimentação, Transporte...)", value="")
        valor = st.number_input("Valor (R$)", min_value=0.0, value=0.0, step=10.0, format="%.2f")
    with col3:
        descricao = st.text_input("Descrição / Estabelecimento", value="")
        
    submitted = st.form_submit_button("Salvar Lançamento")
    if submitted:
        try:
            datetime.strptime(data_lancamento.strip(), "%d/%m/%Y")
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (%s, %s, %s, %s, %s)",
                (data_lancamento.strip(), tipo, categoria, descricao, valor)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.success("Lançamento guardado com sucesso!")
            st.rerun()
        except ValueError:
            st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

st.divider()

# Carregamento robusto dos dados (Lançamentos e Aportes)
df_lancamentos = pd.DataFrame(columns=["id", "data", "tipo", "categoria", "descricao", "valor"])
df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])

try:
    conexao = obter_conexao()
    try:
        df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos ORDER BY id DESC", conexao)
    except Exception:
        conexao.rollback()
        
    try:
        df_aportes = pd.read_sql_query("SELECT id, data, valor, local_aplicacao FROM desafio_aportes", conexao)
    except Exception:
        conexao.rollback()
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar dados do banco: {e}")

# Tratamento e limpeza dos dados
if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
    df_lancamentos["valor_num"] = pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
    df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].str.strip().str.lower()
else:
    df_lancamentos["tipo_clean"] = ""

if not df_aportes.empty and "valor" in df_aportes.columns:
    df_aportes["valor_num"] = pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
    total_aportes = df_aportes["valor_num"].sum()
else:
    total_aportes = 0.0

total_receitas = (
    df_lancamentos[df_lancamentos["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"])]["valor_num"].sum()
    if not df_lancamentos.empty else 0.0
)

total_gastos = (
    df_lancamentos[df_lancamentos["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])]["valor_num"].sum()
    if not df_lancamentos.empty else 0.0
)

# Saldo Real Atualizado: Entradas - Gastos Comuns - Total em Aportes
saldo_atual = total_receitas - total_gastos - total_aportes

def fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.subheader("📊 Resumo Consolidado de Créditos, Débitos e Aportes")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Créditos", fmt_moeda(total_receitas))
c2.metric("Total Débitos", fmt_moeda(total_gastos))
c3.metric("Total em Aportes", fmt_moeda(total_aportes))

if saldo_atual >= 0:
    c4.metric("Saldo Atual", fmt_moeda(saldo_atual), delta="No Azul 💙")
else:
    c4.metric("Saldo Atual", fmt_moeda(saldo_atual), delta="No Vermelho 🔴", delta_color="inverse")

st.divider()

st.subheader("Histórico de Lançamentos")
if not df_lancamentos.empty:
    df_exibicao = df_lancamentos.drop(columns=["tipo_clean", "valor_num"], errors="ignore")
    df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
    st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
else:
    st.info("Nenhum lançamento registado.")