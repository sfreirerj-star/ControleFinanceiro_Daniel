import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Estratégia de Dividendos em Dólar - Painel do Daniel",
    page_icon="💵",
    layout="wide",
)

st.title("💰 Controle Financeiro — Painel do Daniel")
st.header("💵 Estratégia de Renda Passiva & Dividendos em Dólar")
st.markdown(
    "Esta página consolida os seus estudos para operar no mercado americano"
    " com foco em **gerar fluxo de caixa e dividendos regulares** para"
    " complementar sua renda, utilizando plataformas globais como Avenue ou"
    " Nomad."
)

st.divider()

# ==========================================================
# 1. FILOSOFIA DE CRESCIMENTO VS. RENDA
# ==========================================================
st.subheader("🎯 1. O Foco na Renda: Como Montar a Sua Rota")
st.markdown(
    "Enquanto os índices amplos (como o VTI ou VOO) reinvestem os lucros das"
    " empresas para focar na valorização da cota, a estratégia de"
    " **dividendos** busca selecionar ativos focados na distribuição"
    " recorrente de caixa para o acionista."
)

col_f1, col_f2 = st.columns(2)
with col_f1:
  st.info(
      "**Vantagem do Fluxo de Caixa:**\nO dinheiro cai diretamente na sua"
      " conta internacional (Avenue ou Nomad) em dólares líquidos já"
      " descontados os 30% de imposto retidos na fonte pelo governo"
      " americano."
  )
with col_f2:
  st.warning(
      "**Disciplina de Reinvestimento / Uso:**\nVocê pode optar por usar esses"
      " dólares para complementar suas despesas futuras ou reaplicá-los para"
      " comprar mais cotas, acelerando o efeito bola de neve."
  )

st.divider()

# ==========================================================
# 2. OS TRÊS PILARES DA RENDA PASSIVA EM DÓLAR
# ==========================================================
st.subheader("🏗️ 2. Os Três Pilares da Renda Passiva nos EUA")
st.markdown(
    "Para estruturar uma carteira segura de dividendos no exterior, dividimos o"
    " estudo em três categorias fundamentais:"
)

tab1, tab2, tab3 = st.tabs([
    "👑 Dividend Aristocrats & Kings",
    "🏢 REITs (Fundos Imobiliários)",
    "📦 ETFs de Dividendos Qualitativos",
])

with tab1:
  st.markdown("""
    #### Ações Individuais Sólidas (Dividend Aristocrats/Kings)
    * **O que são:** Empresas do S&P 500 que aumentam o pagamento de dividendos de forma consecutiva há pelo menos 25 anos (Aristocratas) ou 50 anos (Reis).
    * **Exemplos:** Coca-Cola (KO), Johnson & Johnson (JNJ), Procter & Gamble (PG).
    * **Por que investir:** Extrema estabilidade de caixa e histórico impecável de resiliência em crises globais.
    """)

with tab2:
  st.markdown("""
    #### REITs - Real Estate Investment Trusts (FIIs Americanos)
    * **O que são:** Empresas que gerenciam portfólios de imóveis geradores de aluguel (shoppings, galpões logísticos, torres de telecomunicação).
    * **Exemplo clássico:** *Realty Income (O)* – Conhecida como *"The Monthly Dividend Company"* por pagar proventos **todos os meses** aos acionistas há décadas.
    * **Por que investir:** Por lei, os REITs são obrigados a distribuir pelo menos 90% dos seus lucros tributáveis na forma de dividendos.
    """)

with tab3:
  st.markdown("""
    #### ETFs de Dividendos de Alta Qualidade
    * **O que são:** Fundos negociados em bolsa que reúnem centenas de empresas focadas em pagar bons dividendos com balanços financeiros saudáveis.
    * **Exemplos:** *SCHD* (Schwab U.S. Dividend Equity ETF) e *VYM* (Vanguard High Dividend Yield ETF).
    * **Por que investir:** Elimina o risco de depender da saúde de uma única empresa, oferecendo diversificação imediata e pagamentos trimestrais consistentes.
    """)

st.divider()

# ==========================================================
# 3. CALENDÁRIO INTELIGENTE DE FLUXO DE CAIXA
# ==========================================================
st.subheader(
    "📉 3. Calendário de Alinhamento: Criando Fluxo Quase Semanal"
)
st.markdown(
    "Combinando ativos com meses de pagamento diferentes e ativos mensais"
    " (como os REITs), você consegue estruturar um cronograma previsível de"
    " entradas em dólar:"
)

dados_fluxo = [
    {
        "Ativo / ETF": "Realty Income (O)",
        "Classe": "REIT (Imobiliário)",
        "Frequência": "Mensal",
        "Meses de Pagamento": "Todos os meses do ano",
    },
    {
        "Ativo / ETF": "SCHD",
        "Classe": "ETF de Dividendos",
        "Frequência": "Trimestral",
        "Meses de Pagamento": "Março, Junho, Setembro, Dezembro",
    },
    {
        "Ativo / ETF": "Coca-Cola (KO)",
        "Classe": "Ação (Dividend King)",
        "Frequência": "Trimestral",
        "Meses de Pagamento": "Abril, Julho, Outubro, Dezembro",
    },
    {
        "Ativo / ETF": "J&J (JNJ)",
        "Classe": "Ação (Dividend King)",
        "Frequência": "Trimestral",
        "Meses de Pagamento": "Fevereiro, Maio, Agosto, Novembro",
    },
]

df_fluxo = pd.DataFrame(dados_fluxo)
st.dataframe(df_fluxo, use_container_width=True, hide_index=True)

st.divider()

# ==========================================================
# 4. REGRAS DE OURO PARA OPERAR COM SEGURANÇA
# ==========================================================
st.subheader("🛡️ 4. Regras de Ouro para Execução")
st.markdown("""
1. **Preço Médio Constante (DCA):** Não tente adivinhar o melhor momento do dólar ou da bolsa. Defina aportes mensais fixos (ex: US$ 50 ou US$ 100) para comprar suas cotas de forma disciplinada.
2. **Horizonte de Longo Prazo:** A renda variável oscila no curto prazo. Mantenha o foco na solidez das empresas globais e garanta que o capital alocado não fará falta nos próximos 3 a 5 anos.
3. **Consolidação da Base Brasil:** Mantenha o foco em concluir a sua reserva de emergência e estabilizar o seu orçamento doméstico antes de iniciar as transferências internacionais pelas suas contas da Avenue ou Nomad.
""")

st.markdown(
    "<br><hr><p style='text-align: center; color: gray; font-size: 0.85em;'>"
    "<i>Módulo integrado de estudos estratégicos para geração de renda passiva"
    " em moeda forte. Conteúdo de caráter exclusivamente educacional.</i></p>",
    unsafe_allow_html=True,
)
