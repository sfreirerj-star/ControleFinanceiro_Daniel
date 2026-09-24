from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Raio-X de Dívidas - Daniel", page_icon="⚠️", layout="wide")

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

# Garantir que a tabela e todas as colunas necessárias existam
def atualizar_tabela_dividas():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        
        # Cria a tabela se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dividas (
                id SERIAL PRIMARY KEY,
                credor TEXT,
                valor_total REAL,
                status TEXT
            )
        """)
        
        # Adiciona colunas novas caso a tabela seja antiga
        cursor.execute("ALTER TABLE dividas ADD COLUMN IF NOT EXISTS total_parcelas INTEGER;")
        cursor.execute("ALTER TABLE dividas ADD COLUMN IF NOT EXISTS valor_parcela REAL;")
        cursor.execute("ALTER TABLE dividas ADD COLUMN IF NOT EXISTS dia_vencimento INTEGER;")
        
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception as e:
        st.error(f"Erro ao atualizar estrutura da tabela: {e}")

atualizar_tabela_dividas()

st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("⚠️ Gerenciamento de Dívidas e Parcelamentos")

# Formulário de Cadastro de Nova Dívida
with st.form("form_divida", clear_on_submit=True):
    st.markdown("### Cadastrar Novo Parcelamento / Dívida")
    credor = st.text_input("Credor / Nome da Dívida (Ex: Carnê Casas Bahia)")
    
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f", value=0.0)
    with col_d2:
        total_parcelas = st.number_input("Total de Parcelas", min_value=1, step=1, value=1)
    with col_d3:
        valor_parcela = st.number_input("Valor da Parcela (R$)", min_value=0.0, format="%.2f", value=0.0)
    with col_d4:
        dia_vencimento = st.number_input("Dia de Vencimento", min_value=1, max_value=31, step=1, value=15)

    status = st.selectbox("Status", ["Pendente", "Quitada"])

    cadastrar = st.form_submit_button("Cadastrar Dívida")

    if cadastrar:
        if credor and valor_total > 0:
            try:
                conexao = obter_conexao()
                cursor = conexao.cursor()
                cursor.execute(
                    """
                    INSERT INTO dividas (credor, valor_total, total_parcelas, valor_parcela, dia_vencimento, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (credor, valor_total, int(total_parcelas), valor_parcela, int(dia_vencimento), status)
                )
                conexao.commit()
                cursor.close()
                conexao.close()
                st.success("Dívida cadastrada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar dívida: {e}")
        else:
            st.warning("Preencha o credor e um valor total válido.")

st.divider()

# Listagem e Gerenciamento de Dívidas Existentes
try:
    conexao = obter_conexao()
    df_dividas = pd.read_sql_query("SELECT * FROM dividas ORDER BY id DESC", conexao)
    conexao.close()
except Exception:
    df_dividas = pd.DataFrame()

if not df_dividas.empty:
    # --- INDICADORES: SOMA TOTAL E PRAZO DE ENCERRAMENTO ---
    st.markdown("### 📊 Indicadores Gerais das Dívidas")
    
    # Filtra apenas dívidas pendentes para os cálculos
    df_pendentes = df_dividas[df_dividas["status"] == "Pendente"].copy()
    
    col_m1, col_m2 = st.columns(2)
    
    # 1. Somatório do valor total das dívidas pendentes
    soma_dividas = pd.to_numeric(df_pendentes["valor_total"], errors="coerce").sum() if not df_pendentes.empty else 0.0
    soma_fmt = f"R$ {soma_dividas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    with col_m1:
        st.metric(label="💰 Valor Total das Dívidas Pendentes", value=soma_fmt)
        
    # 2. Prazo estimado para encerramento (baseado na dívida com maior número de parcelas pendentes)
    prazo_texto = "Sem dívidas pendentes"
    if not df_pendentes.empty:
        max_parcelas = pd.to_numeric(df_pendentes["total_parcelas"], errors="coerce").max()
        if pd.isna(max_parcelas) or max_parcelas < 1:
            max_parcelas = 1
            
        hoje = datetime.now()
        mes_futuro = hoje.month + int(max_parcelas)
        ano_futuro = hoje.year + (mes_futuro // 12)
        mes_futuro = mes_futuro % 12
        if mes_futuro == 0:
            mes_futuro = 12
            ano_futuro -= 1
            
        prazo_texto = f"Aprox. {int(max_parcelas)} meses ({mes_futuro:02d}/{ano_futuro})"
        
    with col_m2:
        st.metric(label="⏳ Prazo Estimado para Quitação Total", value=prazo_texto)

    st.divider()

    st.markdown("### Suas Dívidas Ativas e Parcelamentos")

    def fmt_moeda(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    df_exibicao = df_dividas.copy()
    
    # Preencher valores nulos caso existam registros antigos sem essas colunas
    if "valor_total" in df_exibicao.columns:
        df_exibicao["valor_total"] = pd.to_numeric(df_exibicao["valor_total"], errors="coerce").fillna(0.0).apply(fmt_moeda)
    if "valor_parcela" in df_exibicao.columns:
        df_exibicao["valor_parcela"] = pd.to_numeric(df_exibicao["valor_parcela"], errors="coerce").fillna(0.0).apply(fmt_moeda)
    if "total_parcelas" in df_exibicao.columns:
        df_exibicao["total_parcelas"] = pd.to_numeric(df_exibicao["total_parcelas"], errors="coerce").fillna(0)
    if "dia_vencimento" in df_exibicao.columns:
        df_exibicao["dia_vencimento"] = pd.to_numeric(df_exibicao["dia_vencimento"], errors="coerce").fillna(0)

    colunas_disponiveis = [col for col in ["id", "credor", "valor_total", "total_parcelas", "valor_parcela", "dia_vencimento", "status"] if col in df_exibicao.columns]

    st.dataframe(
        df_exibicao[colunas_disponiveis].set_index("id"),
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### ✏️ Editar ou Excluir Dívida")
    
    df_dividas["resumo"] = "ID: " + df_dividas["id"].astype(str) + " | " + df_dividas["credor"].fillna("")
    
    divida_selecionada = st.selectbox("Selecione a dívida para gerenciar:", df_dividas["resumo"].tolist())
    id_divida = int(divida_selecionada.split(" | ")[0].replace("ID: ", ""))
    dado_atual = df_dividas[df_dividas["id"] == id_divida].iloc[0]

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        with st.form("form_edicao_divida"):
            st.markdown("#### Corrigir Dados da Dívida")
            novo_credor = st.text_input("Credor", value=str(dado_atual["credor"]) if pd.notna(dado_atual["credor"]) else "")
            novo_valor_total = st.number_input("Valor Total (R$)", value=float(dado_atual["valor_total"]) if "valor_total" in dado_atual and pd.notna(dado_atual["valor_total"]) else 0.0, format="%.2f")
            novo_total_parcelas = st.number_input("Total de Parcelas", value=int(dado_atual["total_parcelas"]) if "total_parcelas" in dado_atual and pd.notna(dado_atual["total_parcelas"]) else 1, min_value=1, step=1)
            novo_valor_parcela = st.number_input("Valor da Parcela (R$)", value=float(dado_atual["valor_parcela"]) if "valor_parcela" in dado_atual and pd.notna(dado_atual["valor_parcela"]) else 0.0, format="%.2f")
            novo_dia_vencimento = st.number_input("Dia de Vencimento", value=int(dado_atual["dia_vencimento"]) if "dia_vencimento" in dado_atual and pd.notna(dado_atual["dia_vencimento"]) else 15, min_value=1, max_value=31, step=1)
            novo_status = st.selectbox("Status", ["Pendente", "Quitada"], index=0 if dado_atual.get("status") == "Pendente" else 1)

            salvar = st.form_submit_button("Salvar Alterações")

            if salvar:
                try:
                    conexao = obter_conexao()
                    cursor = conexao.cursor()
                    cursor.execute(
                        """
                        UPDATE dividas 
                        SET credor = %s, valor_total = %s, total_parcelas = %s, valor_parcela = %s, dia_vencimento = %s, status = %s
                        WHERE id = %s
                        """,
                        (novo_credor, novo_valor_total, int(novo_total_parcelas), novo_valor_parcela, int(novo_dia_vencimento), novo_status, id_divida)
                    )
                    conexao.commit()
                    cursor.close()
                    conexao.close()
                    st.success("Dívida atualizada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

    with col_e2:
        st.markdown("#### Excluir Dívida")
        st.warning("Cuidado: Essa ação remove o registro do controle de dívidas.")
        if st.button("Excluir esta Dívida", type="primary"):
            try:
                conexao = obter_conexao()
                cursor = conexao.cursor()
                cursor.execute("DELETE FROM dividas WHERE id = %s", (id_divida,))
                conexao.commit()
                cursor.close()
                conexao.close()
                st.success("Dívida excluída com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
else:
    st.info("Nenhuma dívida cadastrada no momento.")