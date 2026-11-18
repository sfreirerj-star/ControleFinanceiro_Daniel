from datetime import datetime
import os
import sys
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(
    page_title="Desafio Reserva & Simulador - Painel do Daniel",
    page_icon="🎯",
    layout="wide",
)
aplicar_estilo_moderno()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from database import inicializar_banco, obter_conexao
    inicializar_banco()
except ImportError:
    def inicializar_banco():
        pass

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def garantir_tabelas():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS desafio_aportes (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                valor NUMERIC(10,2) NOT NULL,
                local_aplicacao TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS desafio_resgates (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                valor NUMERIC(10,2) NOT NULL,
                local_origem TEXT NOT NULL,
                motivo TEXT
            )
        """)
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
    except Exception as e:
        print(f"Erro ao garantir tabelas: {e}")

garantir_tabelas()

st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("🎯 Desafio Personalizado & Simulador de Antecipação")
st.write(
    "Controle seus aportes mensais, gerencie resgates, diversifique suas"
    " instituições financeiras e simule o impacto de ganhos extras nas suas"
    " metas."
)

def fmt_moeda(v):
    return (
        f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

aba_desafio, aba_resgate, aba_simulador, aba_orientacao = st.tabs([
    "🎯 Meu Desafio & Aportes",
    "💸 Módulo de Resgates",
    "🎯 Simulador de Antecipação",
    "📈 Consultoria Diária de Investimentos (Moderado)",
])

with aba_desafio:
    with st.expander(
        "⚙️ Configurar / Selecionar Meta Mensal", expanded=True
    ):
        opcoes_meta_mensal = {
            "Personalizado (Definir manual)": 0.0,
            "Conservador (R$ 100,00 / mês)": 100.00,
            "Intermediário (R$ 300,00 / mês)": 300.00,
            "Agressivo (R$ 500,00 / mês)": 500.00,
        }

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            escolha_perfil = st.selectbox(
                "Escolha o Perfil / Valor Mensal", list(opcoes_meta_mensal.keys())
            )
        with col_m2:
            meses_totais = st.number_input(
                "Prazo do Desafio (Meses)", min_value=1, max_value=60, value=12, step=1
            )

        if escolha_perfil != "Personalizado (Definir manual)":
            meta_mensal_base = opcoes_meta_mensal[escolha_perfil]
        else:
            meta_mensal_base = st.number_input(
                "Valor Desejado por Mês (R$)",
                min_value=10.0,
                value=100.00,
                step=10.0,
                format="%.2f",
            )

        meta_total = meta_mensal_base * meses_totais

    try:
        conexao = obter_conexao()
        df_aportes = pd.read_sql_query(
            "SELECT id, data, valor, local_aplicacao FROM desafio_aportes",
            conexao,
        )
        df_resgates = pd.read_sql_query(
            "SELECT id, data, valor, local_origem, motivo FROM desafio_resgates ORDER BY id DESC",
            conexao,
        )
        conexao.close()
        
        # Ordenação cronológica automática dos aportes por data (do mais recente para o mais antigo)
        if not df_aportes.empty:
            df_aportes['data_dt'] = pd.to_datetime(df_aportes['data'], format='%d/%m/%Y', errors='coerce')
            df_aportes = df_aportes.sort_values(by=['data_dt', 'id'], ascending=[False, False]).drop(columns=['data_dt'])
    except Exception:
        df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])
        df_resgates = pd.DataFrame(
            columns=["id", "data", "valor", "local_origem", "motivo"]
        )

    if not df_aportes.empty:
        df_aportes["valor_num"] = pd.to_numeric(
            df_aportes["valor"], errors="coerce"
        ).fillna(0.0)
        total_aportado = df_aportes["valor_num"].sum()
    else:
        total_aportado = 0.0

    if not df_resgates.empty:
        df_resgates["valor_num"] = pd.to_numeric(
            df_resgates["valor"], errors="coerce"
        ).fillna(0.0)
        total_resgatado = df_resgates["valor_num"].sum()
    else:
        total_resgatado = 0.0

    total_guardado = total_aportado - total_resgatado
    progresso_perc = (
        min(total_guardado / meta_total, 1.0) if meta_total > 0 else 0.0
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Meta Total Calculada", fmt_moeda(meta_total))
    with col2:
        st.metric("Total Aportado", fmt_moeda(total_aportado))
    with col3:
        st.metric("Total Resgatado", fmt_moeda(total_resgatado))
    with col4:
        st.metric("Patrimônio Líquido Guardado", fmt_moeda(total_guardado))

    st.write("")
    st.progress(
        progresso_perc,
        text=f"Progresso Atual do Desafio: {progresso_perc * 100:.1f}% alcançado",
    )

    st.divider()

    st.markdown("### 📥 Registrar Novo Depósito / Aporte")
    with st.form("form_novo_aporte_daniel"):
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            data_aporte = st.text_input(
                "Data do Depósito (DD/MM/AAAA)",
                value=datetime.now().strftime("%d/%m/%Y"),
            )
        with col_a2:
            valor_aporte = st.number_input(
                "Valor Depositado (R$)",
                min_value=1.0,
                value=meta_mensal_base if meta_mensal_base > 0 else 100.00,
                step=10.0,
                format="%.2f",
            )
        with col_a3:
            locais_disponiveis = [
                "Banco Itaú",
                "Nomad (Investimentos em Dólar)",
                "Sofisa Direto (CDB 105% CDI)",
                "Banco Inter (CDB Liquidez Diária)",
                "Nubank (Caixinha / RDB 100% CDI)",
                "Tesouro Selic (Tesouro Direto)",
                "Outro (Personalizado)",
            ]
            local_selecionado = st.selectbox(
                "Local da Aplicação", locais_disponiveis, key="novo_local_daniel"
            )

        local_personalizado = st.text_input(
            "Se selecionou 'Outro (Personalizado)' acima, digite o nome do Banco ou Corretora:",
            key="novo_outro_daniel",
        )

        if st.form_submit_button("💾 Salvar Aporte no Desafio"):
            if local_selecionado == "Outro (Personalizado)":
                local_aporte = (
                    local_personalizado.strip()
                    if local_personalizado.strip()
                    else "Outro"
                )
            else:
                local_aporte = local_selecionado

            try:
                datetime.strptime(data_aporte.strip(), "%d/%m/%Y")
                conexao = obter_conexao()
                cursor = conexao.cursor()
                
                # 1. Salva na tabela oficial de aportes do desafio
                cursor.execute(
                    "INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES (%s, %s, %s)",
                    (data_aporte.strip(), valor_aporte, local_aporte),
                )
                
                # 2. Salva na tabela geral de lançamentos para abater do caixa do mês
                cursor.execute(
                    "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (%s, %s, %s, %s, %s)",
                    (data_aporte.strip(), "Aporte", "Investimento", f"Aporte Desafio - {local_aporte}", float(valor_aporte))
                )
                
                conexao.commit()
                cursor.close()
                conexao.close()
                st.success("Aporte registrado com sucesso no Desafio e integrado ao fluxo de caixa!")
                st.rerun()
            except ValueError:
                st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    st.divider()

    st.markdown("### 🏦 Saldo e Distribuição por Banco / Corretora (Líquido)")
    if not df_aportes.empty:
        df_resumo_aportes = (
            df_aportes.groupby("local_aplicacao")["valor_num"].sum().reset_index()
        )

        if not df_resgates.empty:
            df_resumo_resgates = (
                df_resgates.groupby("local_origem")["valor_num"].sum().reset_index()
            )
            df_resumo_bancos = pd.merge(
                df_resumo_aportes,
                df_resumo_resgates,
                left_on="local_aplicacao",
                right_on="local_origem",
                how="left",
            ).fillna(0)
            df_resumo_bancos["valor_liquido"] = (
                df_resumo_bancos["valor_num_x"] - df_resumo_bancos["valor_num_y"]
            )
            df_resumo_bancos = df_resumo_bancos[
                ["local_aplicacao", "valor_liquido"]
            ].rename(columns={"valor_liquido": "valor_num"})
        else:
            df_resumo_bancos = df_resumo_aportes

        df_resumo_bancos = df_resumo_bancos[df_resumo_bancos["valor_num"] > 0]

        if not df_resumo_bancos.empty and total_guardado > 0:
            df_resumo_bancos["Valor Acumulado"] = df_resumo_bancos["valor_num"].apply(
                fmt_moeda
            )
            df_resumo_bancos["% do Total"] = (
                (df_resumo_bancos["valor_num"] / total_guardado) * 100
            ).apply(lambda x: f"{x:.1f}%")

            df_tabela_bancos = df_resumo_bancos[
                ["local_aplicacao", "Valor Acumulado", "% do Total"]
            ].rename(columns={"local_aplicacao": "Instituição / Local"})
            st.dataframe(df_tabela_bancos, use_container_width=True, hide_index=True)
        else:
            st.info("Saldo líquido distribuído zerado ou indisponível.")
    else:
        st.info("Nenhuma aplicação registrada para calcular a distribuição ainda.")

    st.divider()

    st.markdown("### 📊 Extrato de Aportes Realizados")
    if not df_aportes.empty:
        df_tabela_final = df_aportes[
            ["id", "data", "local_aplicacao", "valor_num"]
        ].rename(
            columns={"local_aplicacao": "Local da Aplicação", "valor_num": "Valor"}
        )
        df_tabela_final["Valor"] = df_tabela_final["Valor"].apply(fmt_moeda)
        st.dataframe(
            df_tabela_final.set_index("id"), use_container_width=True, height=180
        )
    else:
        st.info("Nenhum aporte registrado ainda.")

with aba_resgate:
    st.markdown("### 💸 Módulo de Resgates & Ajuste de Rendimentos")
    st.write(
        "Registre resgates ou adicione correções monetárias/rendimentos para"
        " alinhar o saldo com o extrato da corretora."
    )

    tipo_operacao = st.radio(
        "Escolha a Operação:",
        ["Registrar Resgate", "Registrar Rendimento / Correção Monetária"],
        horizontal=True,
    )

    if tipo_operacao == "Registrar Resgate":
        with st.form("form_novo_resgate_daniel"):
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                data_resgate = st.text_input(
                    "Data do Resgate (DD/MM/AAAA)",
                    value=datetime.now().strftime("%d/%m/%Y"),
                    key="resgate_data_daniel",
                )
            with col_r2:
                valor_resgate = st.number_input(
                    "Valor Resgatado (R$)",
                    min_value=1.0,
                    value=50.00,
                    step=10.0,
                    format="%.2f",
                    key="resgate_valor_daniel",
                )
            with col_r3:
                locais_resgate = [
                    "Selecione...",
                    "Banco Itaú",
                    "Nomad (Investimentos em Dólar)",
                    "Sofisa Direto (CDB 105% CDI)",
                    "Banco Inter (CDB Liquidez Diária)",
                    "Nubank (Caixinha / RDB 100% CDI)",
                    "Tesouro Selic (Tesouro Direto)",
                    "Outro (Personalizado)",
                ]
                local_origem_sel = st.selectbox(
                    "Instituição de Origem do Resgate",
                    locais_resgate,
                    key="resgate_local_daniel",
                )

            origem_personalizada = st.text_input(
                "Se 'Outro (Personalizado)', digite o nome:",
                key="resgate_outro_local_daniel",
            )

            motivo_resgate = st.text_input(
                "Motivo do Resgate / Destino (Ex: Emergência, Oportunidade, etc.)",
                key="resgate_motivo_daniel",
            )

            if st.form_submit_button("📤 Registrar Resgate"):
                if local_origem_sel == "Selecione...":
                    st.error("Por favor, selecione uma instituição de origem válida.")
                else:
                    origem_final = (
                        origem_personalizada.strip()
                        if local_origem_sel == "Outro (Personalizado)"
                        and origem_personalizada.strip()
                        else local_origem_sel
                    )
                    try:
                        datetime.strptime(data_resgate.strip(), "%d/%m/%Y")
                        conexao = obter_conexao()
                        cursor = conexao.cursor()

                        cursor.execute(
                            "INSERT INTO desafio_resgates (data, valor, local_origem, motivo) VALUES (%s, %s, %s, %s)",
                            (
                                data_resgate.strip(),
                                valor_resgate,
                                origem_final,
                                motivo_resgate.strip(),
                            ),
                        )

                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Resgate registrado com sucesso!")
                        st.rerun()
                    except ValueError:
                        st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
                    except Exception as e:
                        st.error(f"Erro ao salvar resgate: {e}")
    else:
        with st.form("form_novo_rendimento_daniel"):
            st.info(
                "💡 **Orientação de Uso:** Utilize este formulário para registrar rendimentos de liquidez diária que caíram "
                "efetivamente na sua conta corrente (lançando-os como Receita para alinhar o saldo do banco), preservando o saldo da aplicação."
            )
            col_rend1, col_rend2, col_rend3 = st.columns(3)
            with col_rend1:
                data_rend = st.text_input(
                    "Data do Rendimento (DD/MM/AAAA)",
                    value=datetime.now().strftime("%d/%m/%Y"),
                )
            with col_rend2:
                valor_rend = st.number_input(
                    "Valor da Correção / Juros (R$)",
                    min_value=0.0,
                    value=0.00,
                    step=0.10,
                    format="%.2f",
                )
            with col_rend3:
                locais_rendimento = [
                    "Selecione...",
                    "Banco Itaú",
                    "Nomad (Investimentos em Dólar)",
                    "Sofisa Direto (CDB 105% CDI)",
                    "Banco Inter (CDB Liquidez Diária)",
                    "Nubank (Caixinha / RDB 100% CDI)",
                    "Tesouro Selic (Tesouro Direto)",
                ]
                local_rend = st.selectbox(
                    "Instituição",
                    locais_rendimento,
                    key="sel_inst_rend_daniel"
                )

            if st.form_submit_button("📈 Registrar Apenas como Receita de Rendimento"):
                if local_rend == "Selecione...":
                    st.error("Por favor, selecione uma instituição válida.")
                elif valor_rend <= 0:
                    st.error("O valor do rendimento deve ser maior que zero.")
                else:
                    try:
                        datetime.strptime(data_rend.strip(), "%d/%m/%Y")
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        
                        cursor.execute(
                            "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (%s, %s, %s, %s, %s)",
                            (data_rend.strip(), "Receita", "Rendimento", f"Rendimento / Juros {local_rend}", float(valor_rend))
                        )
                          
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success(f"Rendimento de R$ {valor_rend:,.2f} lançado como Receita no caixa com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao aplicar rendimento: {e}")

    st.divider()

    st.markdown("### 📋 Histórico de Resgates Realizados")
    if not df_resgates.empty:
        df_tabela_resgates = df_resgates[
            ["id", "data", "local_origem", "valor_num", "motivo"]
        ].rename(
            columns={
                "local_origem": "Instituição de Origem",
                "valor_num": "Valor Resgatado",
                "motivo": "Motivo / Destino",
            }
        )
        df_tabela_resgates["Valor Resgatado"] = df_tabela_resgates[
            "Valor Resgatado"
        ].apply(fmt_moeda)
        st.dataframe(
            df_tabela_resgates.set_index("id"), use_container_width=True, height=200
        )

        st.markdown("#### 🗑️ Excluir Lançamento de Resgate")
        id_resgate_excluir = st.selectbox(
            "Selecione o ID do resgate que deseja excluir:",
            df_resgates["id"].tolist(),
            key="excluir_resg_id_daniel",
        )
        if st.button("Excluir Resgate Selecionado"):
            try:
                conexao = obter_conexao()
                cursor = conexao.cursor()

                cursor.execute(
                    "DELETE FROM desafio_resgates WHERE id = %s",
                    (int(id_resgate_excluir),),
                )
                conexao.commit()
                cursor.close()
                conexao.close()
                st.warning(f"Resgate ID {id_resgate_excluir} excluído com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir resgate: {e}")
    else:
        st.info("Nenhum resgate registrado até o momento.")

with aba_simulador:
    st.markdown("### 🎯 Simulador de Antecipação de Metas")
    st.write(
        "Descubra o impacto de um ganho extra no alcance da sua meta de reserva."
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        meta_alvo_sim = st.number_input(
            "Meta Alvo Total Desejada (R$)",
            min_value=100.0,
            value=max(meta_total, 1200.0),
            step=500.0,
            format="%.2f",
        )
        aporte_mensal_sim = st.number_input(
            "Sua média de aporte mensal atual (R$)",
            min_value=10.0,
            value=meta_mensal_base if meta_mensal_base > 0 else 100.00,
            step=50.0,
            format="%.2f",
        )
    with col_s2:
        ganho_extra_simulado = st.number_input(
            "Valor do Ganho Extra Pontual (R$)",
            min_value=10.0,
            value=100.00,
            step=10.0,
            format="%.2f",
        )
        quantidade_extras = st.number_input(
            "Quantos extras desses você faria no mês?",
            min_value=1,
            value=1,
            step=1,
        )

    st.divider()

    falta_para_meta = max(0.0, meta_alvo_sim - total_guardado)

    meses_sem_extra = (
        (falta_para_meta / aporte_mensal_sim) if aporte_mensal_sim > 0 else 0.0
    )
    aporte_mensal_com_extra = aporte_mensal_sim + (
        ganho_extra_simulado * quantidade_extras
    )
    meses_com_extra = (
        (falta_para_meta / aporte_mensal_com_extra)
        if aporte_mensal_com_extra > 0
        else 0.0
    )
    economia_meses = meses_sem_extra - meses_com_extra

    st.markdown("### 📊 Resultado da Simulação")
    c_res1, c_res2, c_res3 = st.columns(3)
    with c_res1:
        st.metric(
            "Tempo estimado sem o extra",
            f"{meses_sem_extra:.1f} meses",
            help="Considerando apenas o seu aporte mensal atual.",
        )
    with c_res2:
        st.metric(
            "Tempo estimado COM o extra",
            f"{meses_com_extra:.1f} meses",
            delta=f"-{economia_meses:.1f} meses",
            delta_color="inverse",
            help="Considerando o aporte mensal + os ganhos extras mensais.",
        )
    with c_res3:
        st.metric(
            "Reforço Mensal Injetado",
            fmt_moeda(ganho_extra_simulado * quantidade_extras),
        )

    if total_guardado >= meta_alvo_sim:
        st.success(
            "Parabéns! O seu patrimônio atual já atingiu ou ultrapassou essa meta alvo!"
        )
    else:
        st.info(
            f"💡 **Visão Inspiradora:** Adicionar esse reforço encurta a sua jornada"
            f" rumo à liberdade financeira em **{economia_meses * 30:.0f} dias**"
            f" (quase **{economia_meses:.1f} meses** a menos de espera)!"
        )

    st.divider()

    st.markdown(
        "### 🧮 Simulador Avançado de Prazo e Juros Compostos (Reserva de Emergência)"
    )
    st.write(
        "Projete o crescimento do seu capital ao longo dos meses considerando"
        " uma taxa média de rendimento (ex: 100% a 105% do CDI)."
    )

    col_sim_av1, col_sim_av2, col_sim_av3 = st.columns(3)
    with col_sim_av1:
        patrimonio_inicial_sim = st.number_input(
            "Patrimônio Inicial Guardado (R$)",
            min_value=0.0,
            value=float(total_guardado),
            step=100.0,
            format="%.2f",
        )
    with col_sim_av2:
        aporte_mensal_proj = st.number_input(
            "Aporte Mensal Previsto (R$)",
            min_value=0.0,
            value=float(meta_mensal_base),
            step=50.0,
            format="%.2f",
        )
    with col_sim_av3:
        taxa_cdi_anual = st.number_input(
            "Taxa CDI Anual Estimada (%)",
            min_value=1.0,
            max_value=30.0,
            value=11.25,
            step=0.25,
            format="%.2f",
        )

    meses_projecao = st.slider(
        "Horizonte de Projeção (Meses)",
        min_value=6,
        max_value=120,
        value=24,
        step=6,
    )

    taxa_mensal = (1 + (taxa_cdi_anual / 100.0)) ** (1 / 12) - 1

    lista_projecao = []
    patrimonio_atual_loop = patrimonio_inicial_sim
    total_aportado_loop = patrimonio_inicial_sim

    for m in range(1, meses_projecao + 1):
        rendimento_mes = patrimonio_atual_loop * taxa_mensal
        patrimonio_atual_loop = (
            patrimonio_atual_loop + rendimento_mes + aporte_mensal_proj
        )
        total_aportado_loop += aporte_mensal_proj

        lista_projecao.append({
            "Mês": f"Mês {m}",
            "Patrimônio Total (R$)": round(patrimonio_atual_loop, 2),
            "Total Aportado (R$)": round(total_aportado_loop, 2),
            "Rendimento Acumulado (R$)": round(
                patrimonio_atual_loop - total_aportado_loop, 2
            ),
        })

    df_proj = pd.DataFrame(lista_projecao)

    col_pr1, col_pr2 = st.columns(2)
    with col_pr1:
        st.metric(
            "Patrimônio Projetado ao Final", fmt_moeda(patrimonio_atual_loop)
        )
    with col_pr2:
        st.metric(
            "Rendimento Total Gerado (Juros)",
            fmt_moeda(patrimonio_atual_loop - total_aportado_loop),
            delta="Trabalho do Dinheiro",
        )

    st.write("")
    st.line_chart(
        df_proj.set_index("Mês")[
            ["Patrimônio Total (R$)", "Total Aportado (R$)"]
        ]
    )

with aba_orientacao:
    st.markdown("### 📈 Painel Diário de Alocação & Mercado (Perfil Moderado)")
    st.write(
        "Opções recomendadas no mercado financeiro para diversificação segura e"
        " rentável:"
    )

    col_inf1, col_inf2, col_inf3 = st.columns(3)
    with col_inf1:
        st.metric("Retorno Médio Esperado", "105% a 110% CDI", delta="Pós-fixado")
    with col_inf2:
        st.metric("Segurança Coberta", "FGC & Tesouro Nacional", delta="Garantido")
    with col_inf3:
        st.metric("Liquidez Principal", "Diária (D+0)", delta="Resgate Imediato")

    st.markdown("#### 🏦 Melhores Opções de Bancos e Corretoras no Mercado")

    data_instituicoes = {
        "Instituição / Corretora": [
            "Banco Itaú",
            "Nomad (Investimentos em Dólar)",
            "Sofisa Direto",
            "Banco Inter",
            "Tesouro Direto",
        ],
        "Produto Recomendado": [
            "CDBs e Fundos DI",
            "Investimento Internacional em Dólar",
            "CDB Liquidez Diária (105% CDI)",
            "CDB Mais Limite / Liquidez Diária",
            "Tesouro Selic 2029 / 2031",
        ],
        "Vantagem para Reserva": [
            "Solidez do maior banco privado do Brasil",
            "Diversificação cambial geográfica",
            "Excelente taxa para pós-fixado com FGC",
            "Praticidade e solidez de banco múltiplo",
            "Tesouro Selic com liquidez e segurança soberana",
        ],
    }
    st.dataframe(
        pd.DataFrame(data_instituicoes), use_container_width=True, hide_index=True
    )

    st.markdown("#### 💡 Estratégia de Diversificação (Regra dos Ovos)")
    st.info(
        "📌 **Dica de Ouro:** Dividir os aportes entre 2 ou 3 instituições"
        " diferentes (por exemplo, Banco Itaú, Nomad e Sofisa) protege seu"
        " patrimônio, garante taxas competitivas e mantém o valor protegido."
    )

    st.divider()

    st.markdown("### 📋 Checklist de Saúde Financeira e Governança")
    st.write(
        "Garanta que sua estrutura patrimonial e de documentos esteja"
        " perfeitamente organizada:"
    )

    check_1 = st.checkbox(
        "Possuo ao menos 6 meses do meu custo de vida guardados em ativos de"
        " liquidez diária."
    )
    check_2 = st.checkbox(
        "Meus investimentos estão divididos em pelo menos duas instituições"
        " diferentes para mitigar risco sistêmico."
    )
    check_3 = st.checkbox(
        "Acompanho periodicamente minhas despesas e receitas mensais para"
        " garantir constância nos aportes."
    )
    check_4 = st.checkbox(
        "Mantenho meus registros administrativos e comprovações de transparência"
        " organizados e auditáveis."
    )

if check_1 and check_2 and check_3 and check_4:
    st.balloons()
    st.success(
        "🌟 Parabéns! Sua governança financeira e seus critérios de segurança"
        " patrimonial estão em nível de excelência!"
    )