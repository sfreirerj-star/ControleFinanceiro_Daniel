from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Consultoria e Saúde Financeira - Daniel", page_icon="💡", layout="wide")

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

st.title("💰 Controle Financeiro — Painel do Daniel")
st.subheader("💡 Consultoria Inteligente de Bolso - Diagnóstico Financeiro")
st.write("Análise automática da sua saúde financeira com base nos seus ganhos, compromissos mensais e dívidas ativas.")

# Carrega os dados do banco (Lançamentos e Dívidas)
try:
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query("SELECT tipo, valor FROM lancamentos", conexao)
    df_dividas = pd.read_sql_query("SELECT valor_parcela, status FROM dividas WHERE status = 'Pendente'", conexao)
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar dados para o diagnóstico: {e}")
    df_lancamentos = pd.DataFrame()
    df_dividas = pd.DataFrame()

# Cálculos financeiros base
total_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"]["valor"].sum() if not df_lancamentos.empty else 0.0
total_despesas_manuais = df_lancamentos[df_lancamentos["tipo"] == "Despesa"]["valor"].sum() if not df_lancamentos.empty else 0.0

# Soma apenas as parcelas ativas das dívidas pendentes que possuem valor de parcela cadastrado
total_parcelas_dividas = df_dividas[df_dividas["valor_parcela"] > 0]["valor_parcela"].sum() if not df_dividas.empty else 0.0

# Despesa Total Real (Despesas Manuais + Parcelas de Dívidas Ativas)
despesa_total_real = total_despesas_manuais + total_parcelas_dividas

# Saldo Livre / Comprometimento
saldo_livre = total_receitas - despesa_total_real

def fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.divider()

# --- PAINEL DE MÉTRICAS DA SAÚDE FINANCEIRA ---
st.markdown("### 📊 Seus Indicadores Atuais")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.metric(label="🟢 Total de Ganhos (Receitas)", value=fmt_moeda(total_receitas))

with col_m2:
    st.metric(label="🔴 Total de Compromissos", value=fmt_moeda(despesa_total_real), help="Inclui despesas manuais + parcelas de dívidas ativas")

with col_m3:
    st.metric(label="⚖️ Saldo Livre / Resultado", value=fmt_moeda(saldo_livre))

with col_m4:
    # Diagnóstico rápido de status
    if total_receitas == 0 and despesa_total_real == 0:
        status_saude = "Sem Dados"
    elif saldo_livre < 0:
        status_saude = "🚨 Em Déficit (Vermelho)"
    elif saldo_livre == 0:
        status_saude = "⚠️ No Zero a Zero"
    else:
        status_saude = "✅ Com Sobra (Azul)"
    st.metric(label="🩺 Status da Saúde Financeira", value=status_saude)

st.divider()

# --- DIAGNÓSTICO E ORIENTAÇÃO PERSONALIZADA ---
st.markdown("### 🧭 Roteiro Estratégico Personalizado para o seu Momento")

if total_receitas == 0 and despesa_total_real == 0:
    st.info("⚠️ Você ainda não possui lançamentos cadastrados suficientes para gerarmos uma análise profunda. Comece cadastrando suas receitas e despesas na aba 'Novo Lançamento'.")
else:
    if saldo_livre < 0:
        # Cenário 1: Vermelho / Endividado
        st.error("🚨 **Diagnóstico:** Suas despesas e compromissos mensais estão superando os seus ganhos. No momento, o foco principal **não é investir**, e sim estancar o sangramento do orçamento.")
        
        st.markdown("""
        #### 🛠️ Plano de Ação Imediato para Sair do Vermelho:
        1. **Estancar o Sangramento:** O juro do rotativo de cartão de crédito e cheque especial destrói qualquer orçamento. Priorize negociar as dívidas que possuem juros altos antes de pensar em guardar dinheiro.
        2. **Corte Cirúrgico de Custos:** Olhe nos seus lançamentos para onde está indo o maior volume de recursos em supérfluos. Reduza custos imediatamente para equilibrar o mês e zerar o déficit.
        3. **A Metodologia do Centavo:** Evite pequenos gastos diários invisíveis ("efeito goteira") que somados consomem boa parte do seu ganho mensal.
        """)
        
    elif saldo_livre == 0:
        # Cenário 2: Equilibrado mas sem folga
        st.warning("⚠️ **Diagnóstico:** Suas contas estão empatadas com os seus ganhos. Você não está acumulando dívidas novas, mas também não está conseguindo construir uma gordura financeira.")
        
        st.markdown("""
        #### 🛠️ Plano de Ação para Criar Folga:
        1. **Encontrar Margem:** Tente espremer pelo menos 5% a 10% dos seus gastos mensais para começar a transformá-los em sobra livre.
        2. **Foco no Acordo das Dívidas:** Se você possui dívidas sem parcelamento ativo (aquelas pendentes paradas), use qualquer sobra eventual para propor acordos à vista com desconto agressivo.
        """)
        
    else:
        # Cenário 3: Saudável / Com Sobra
        st.success("✅ **Diagnóstico:** Parabéns! Seus ganhos estão superiores aos seus compromissos mensais. Você possui uma sobra de caixa livre para direcionar ao seu futuro.")
        
        st.markdown("""
        #### 🚀 Plano de Ação Rumo à Reserva de Emergência:
        1. **Destino da Soberania (Reserva de Emergência):** Todo o seu saldo livre atual deve ter como destino primário a **Renda Fixa com liquidez diária** (Tesouro Selic ou CDBs de bancos sólidos que pagem 100% do CDI). O objetivo ideal é acumular o equivalente a **3 a 6 meses do seu custo de vida**.
        2. **Segurança e Rendimento:** Diferente da caderneta de poupança tradicional, essas opções rendem todos os dias úteis e possuem a proteção do FGC (Fundo Garantidor de Créditos) até R$ 250 mil por instituição.
        3. **Aceleração de Quitação:** Se ainda restam dívidas parceladas ativas, você pode usar parte do excedente para amortizar parcelas antecipadamente e economizar nos juros.
        """)