import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulador & Melhores Ações - Painel do Daniel",
    page_icon="📈",
    layout="wide",
)

st.title("💰 Controle Financeiro — Painel do Daniel")
st.header("📈 Melhores Ações Globais, Simulador DCA & Inteligência de Mercado")
st.markdown(
    "Esta ferramenta combina projeções de aportes mensais, orientações"
    " operacionais e um painel gráfico com as melhores sugestões de ativos"
    " defensivos e pagadores de dividendos no mercado americano."
)

st.divider()

# ==========================================================
# 1. SUGESTÃO DE ATIVOS SEGUROS (BASEADO EM GRANDES PORTAIS)
# ==========================================================
st.subheader(
    "🌟 1. Painel de Sugestão: Ativos de Referência no Mercado Americano"
)
st.markdown(
    "Com base nos principais portais de investimentos do mundo (como Seeking"
    " Alpha, Yahoo Finance e relatórios institucionais), selecionamos os ativos"
    " mais resilientes para formação de renda passiva com segurança:"
)

# Dados consolidados dos melhores ativos globais de dividendos
dados_melhores_acoes = [
    {
        "Ativo / Ticker": "Realty Income (O)",
        "Classe": "REIT (Imobiliário)",
        "Frequência": "Mensal",
        "Dividend Yield (DY)": "5.3%",
        "Perfil de Risco": "Baixo (Histórico consolidado)",
    },
    {
        "Ativo / Ticker": "SCHD (Schwab ETF)",
        "Classe": "ETF de Dividendos Qualitativos",
        "Frequência": "Trimestral",
        "Dividend Yield (DY)": "3.5%",
        "Perfil de Risco": "Muito Baixo (Diversificado)",
    },
    {
        "Ativo / Ticker": "VYM (Vanguard ETF)",
        "Classe": "ETF de Alto Rendimento",
        "Frequência": "Trimestral",
        "Dividend Yield (DY)": "3.0%",
        "Perfil de Risco": "Baixo (Ampla diversificação)",
    },
    {
        "Ativo / Ticker": "Coca-Cola (KO)",
        "Classe": "Ação (Dividend King)",
        "Frequência": "Trimestral",
        "Dividend Yield (DY)": "3.1%",
        "Perfil de Risco": "Baixo (Resiliência em crises)",
    },
    {
        "Ativo / Ticker": "Johnson & Johnson (JNJ)",
        "Classe": "Ação (Dividend King)",
        "Frequência": "Trimestral",
        "Dividend Yield (DY)": "3.0%",
        "Perfil de Risco": "Baixo (Setor de saúde defensivo)",
    },
]

df_sugestoes = pd.DataFrame(dados_melhores_acoes)
st.dataframe(df_sugestoes, use_container_width=True, hide_index=True)

st.divider()

# ==========================================================
# 2. ONDE OS GRANDES INVESTIDORES BUSCAM INFORMAÇÕES
# ==========================================================
st.subheader(
    "🌍 2. Fontes Oficiais e Termômetros do Mercado Global (Smart Money)"
)
st.markdown(
    "Para investir com segurança e sem especulação, os grandes gestores"
    " acompanham indicadores macroeconômicos e relatórios em plataformas"
    " consolidadas:"
)

col_f1, col_f2 = st.columns(2)

with col_f1:
  st.markdown("""
    #### 📊 Portais de Dados e Cotações Globais
    * **[TradingView](https://br.tradingview.com/):** Principal ferramenta gráfica do mundo para monitorar ativos e índices (S&P 500, NASDAQ).
    * **[Yahoo Finance](https://finance.yahoo.com/):** Essencial para verificar balanços trimestrais e o *Dividend Yield* histórico.
    * **[Seeking Alpha](https://seekingalpha.com/):** Plataforma global com teses detalhadas sobre ações de dividendos e REITs.
    """)

with col_f2:
  st.markdown("""
    #### 🏛️ Indicadores Macroeconômicos (O que move a Bolsa)
    * **Taxa de Juros do FED (FOMC):** O custo do dinheiro nos EUA dita o fluxo de capital para renda fixa e variável.
    * **Índice de Inflação (CPI e PCE):** Medem o ritmo do custo de vida americano e direcionam as políticas do Banco Central.
    * **Relatórios 10-K e 13-F:** Documentos oficiais na SEC onde grandes fundos revelam suas movimentações.
    """)

st.divider()

# ==========================================================
# 3. SELEÇÃO DE ATIVOS E SIMULAÇÃO DE APORTES (DCA)
# ==========================================================
st.subheader("🎯 3. Simulador de Projeção de Renda (Estratégia DCA)")

ativo_escolhido = st.selectbox(
    "Selecione o Ativo para Simular:",
    [
        "Realty Income (O)",
        "SCHD (Schwab ETF)",
        "VYM (Vanguard ETF)",
        "Coca-Cola (KO)",
        "Johnson & Johnson (JNJ)",
    ],
)

# Parâmetros de referência estáveis para simulação segura
tabela_parametros = {
    "Realty Income (O)": {"preco": 55.00, "dy": 0.053},
    "SCHD (Schwab ETF)": {"preco": 28.50, "dy": 0.035},
    "VYM (Vanguard ETF)": {"preco": 125.00, "dy": 0.030},
    "Coca-Cola (KO)": {"preco": 68.00, "dy": 0.031},
    "Johnson & Johnson (JNJ)": {"preco": 160.00, "dy": 0.030},
}

preco_atual = tabela_parametros[ativo_escolhido]["preco"]
dividend_yield = tabela_parametros[ativo_escolhido]["dy"]

st.success(
    f"🌐 Parâmetros de referência para **{ativo_escolhido}** | Cotação Média"
    f" Base: **US$ {preco_atual:,.2f}** | Dividend Yield Anual Estimado:"
    f" **{dividend_yield * 100:.1f}%**"
)

col_s1, col_s2 = st.columns(2)

with col_s1:
  aporte_mensal_usd = st.number_input(
      "Aporte Mensal Planejado (US$)",
      min_value=10.0,
      max_value=5000.0,
      value=100.0,
      step=10.0,
  )
  meses_projecao = st.slider(
      "Horizonte de Projeção (Meses)", min_value=12, max_value=120, value=36, step=12
  )

with col_s2:
  st.markdown(f"""
    * **Valor do Aporte:** US$ {aporte_mensal_usd:,.2f} por mês.
    * **Estratégia DCA:** Aportes regulares reduzem o impacto da volatilidade cambial e dos ciclos de mercado.
    * **Foco:** Acumulação disciplinada de ativos geradores de fluxo passivo.
    """)

if preco_atual > 0:
  cotas_por_mes = aporte_mensal_usd / preco_atual
  total_cotas_acumuladas = cotas_por_mes * meses_projecao
  renda_anual_projetada = total_cotas_acumuladas * preco_atual * dividend_yield
  renda_mensal_projetada = renda_anual_projetada / 12

  st.subheader("📊 Resultados Projetados para o seu Perfil")

  res1, res2, res3 = st.columns(3)
  res1.metric("Cotas Acumuladas Estimadas", f"{total_cotas_acumuladas:.1f} cotas")
  res2.metric(
      "Renda Passiva Anual", f"US$ {renda_anual_projetada:,.2f} por ano"
  )
  res3.metric(
      "Complemento de Renda Mensal",
      f"US$ {renda_mensal_projetada:,.2f} / mês",
      delta="Renda Passiva Gerada 💵",
  )

st.divider()

# ==========================================================
# 4. GUIA PRÁTICO: COMO EXECUTAR A OPERAÇÃO NA CORRETORA
# ==========================================================
st.subheader(
    "🛠️ 4. Guia Prático: Como Executar a Operação na Prática (Avenue ou Nomad)"
)
st.markdown(
    "Com base nas informações globais e no seu planejamento, execute suas"
    " ordens de forma segura seguindo o fluxo nas corretoras internacionais:"
)

with st.expander(
    "📘 Passo 1: Transferência de Recursos e Câmbio", expanded=True
):
  st.markdown("""
    1. **Envio de Reais:** Acesse o aplicativo da sua corretora (Avenue ou Nomad).
    2. **Conversão Cambial:** Faça uma TED/PIX para a conta da corretora e converta para Dólares aplicando a cotação comercial e o IOF.
    3. **Saldo Disponível:** Confirme que o poder de compra em dólares já está liberado em sua conta internacional.
    """)

with st.expander("📘 Passo 2: Localização do Ativo no Home Broker"):
  st.markdown("""
    1. **Horário de Negociação:** Abra a aba de investimentos durante o horário de funcionamento da Bolsa de Nova York (NYSE / NASDAQ).
    2. **Busca pelo Ticker:** Digite o código oficial do ativo na barra de pesquisa (ex: **`O`** para a *Realty Income* ou **`SCHD`** para o ETF).
    3. **Análise de Conjuntura:** Confira o comportamento recente do preço antes de prosseguir.
    """)

with st.expander("📘 Passo 3: Envio da Ordem de Compra (Execução Segura)"):
  st.markdown("""
    1. **Tipo de Ordem:** 
       * *Ordem a Mercado:* Executa imediatamente pelo preço atual.
       * *Ordem Limitada (Recomendada):* Define o teto de preço máximo que você aceita pagar por cota, evitando oscilações bruscas do momento.
    2. **Fracionamento:** Utilize o recurso de compra fracionada caso o valor do aporte não atinja o preço integral de uma cota inteira.
    3. **Confirmação:** Revise os parâmetros e finalize a ordem.
    """)

with st.expander(
    "📘 Passo 4: Custódia, Dividendos e Retenção de Impostos"
):
  st.markdown("""
    * **Custódia Vitalícia:** As cotas adquiridas ficam armazenadas de forma segura na sua conta internacional.
    * **Tributação Automática:** Os dividendos entram líquidos na sua conta após a retenção automática de 30% de imposto na fonte pelo governo americano.
    * **Utilização do Caixa:** Acumule para gerar efeito bola de neve ou solicite remessas futuras para o Brasil conforme sua necessidade.
    """)

st.markdown(
    "<br><hr><p style='text-align: center; color: gray; font-size: 0.85em;'>"
    "<i>Módulo integrado de inteligência global, simulação de aportes e orientação"
    " operacional. Conteúdo de caráter educacional.</i></p>",
    unsafe_allow_html=True,
)
