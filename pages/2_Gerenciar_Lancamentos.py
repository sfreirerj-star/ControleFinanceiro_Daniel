from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Gerenciar Lançamentos - Daniel", page_icon="✏️", layout="wide")

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("✏️ Gerenciar, Editar ou Excluir Lançamentos")

try:
    conexao = obter_conexao()
    # Busca lançamentos manuais
    df = pd.read_sql_query(
        "SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC",
        conexao,
    )
    # Busca dívidas cadastradas para cruzar os parcelamentos ativos
    df_div = pd.read_sql_query(
        "SELECT id, credor, valor_parcela, dia_vencimento, status FROM dividas WHERE status = 'Pendente'",
        conexao,
    )
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    df = pd.DataFrame()
    df_div = pd.DataFrame()

if not df.empty:
    # Converte a coluna de data para data real do Python para filtrar passado/futuro
    df["data_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    hoje = pd.Timestamp(datetime.now().date())

    # Separa os lançamentos futuros manuais
    df_futuros = (
        df[df["data_dt"] > hoje]
        .sort_values(by="data_dt", ascending=True)
        .copy()
    )

    # SEÇÃO INTELIGENTE: Puxa as parcelas ativas das dívidas para o mês atual/futuro
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

    # Seção Visual Fixa para Lançamentos Futuros
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
        "Selecione um lançamento abaixo para alterar os dados (exceto o tipo)"
        " ou excluí-lo."
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
        
        st.info(
            f"💡 **Tipo Fixo:** Este registro é uma **{dados_atuais['tipo']}**. "
            "Para alterar entre Receita e Despesa, exclua o registro e crie um novo."
        )

        with st.form("form_edicao"):
            nova_categoria = st.text_input("Categoria", value=dados_atuais["categoria"])
            nova_descricao = st.text_input("Descrição", value=dados_atuais["descricao"])
            novo_valor = st.number_input(
                "Valor (R$)",
                min_value=0.0,
                format="%.2f",
                value=float(dados_atuais["valor"]),
            )
            nova_data = st.text_input("Data (DD/MM/AAAA)", value=dados_atuais["data"])

            salvar_alteracao = st.form_submit_button("Salvar Alterações")

            if salvar_alteracao:
                try:
                    datetime.strptime(nova_data.strip(), "%d/%m/%Y")

                    conexao = obter_conexao()
                    cursor = conexao.cursor()
                    valor_limpo = abs(float(novo_valor))

                    cursor.execute(
                        """
                        UPDATE lancamentos 
                        SET data = %s, categoria = %s, descricao = %s, valor = %s
                        WHERE id = %s
                        """,
                        (
                            nova_data.strip(),
                            nova_categoria.strip(),
                            nova_descricao.strip(),
                            valor_limpo,
                            id_selecionado,
                        ),
                    )
                    conexao.commit()
                    cursor.close()
                    conexao.close()
                    st.success("Lançamento atualizado com sucesso!")
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
                cursor.execute("DELETE FROM lancamentos WHERE id = %s", (id_selecionado,))
                conexao.commit()
                cursor.close()
                conexao.close()
                st.success("Lançamento excluído com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
else:
    st.info("Nenhum lançamento encontrado para gerenciar.")