import streamlit as st

st.set_page_config(
    page_title="Estratégia de Dividendos em Dólar - Painel do Daniel",
    page_icon="🌐",
    layout="wide",
)

st.title("💰 Controle Financeiro — Painel do Daniel")
st.header("🌐 Estratégia de Dividendos Globais em Dólar")
st.markdown(
    "Esta página integra o seu objetivo de **geração de renda passiva em moeda"
    " forte** ao seu planejamento financeiro atual, respeitando a sua fase de"
    " consolidação da Reserva de Emergência."
)

st.divider()

# ==========================================================
# 1. PRÉ-REQUISITOS DO PROJETO
# ==========================================================
st.subheader("🚦 1. Pré-Requisitos do Projeto (Sinal Verde)")
st.markdown(
    "Antes de aportar o primeiro dólar focado em dividendos, valide os"
    " seguintes marcos no seu controle principal:"
)

col_req1, col_req2 = st.columns(2)
with col_req1:
  st.info(
      "**1. Reserva de Emergência Concluída:**\nMínimo de 3 a 6 meses dos seus"
      " custos mensais totais guardados em ativos de liquidez imediata no"
      " Brasil (CDB 100% CDI ou Tesouro Selic)."
  )
with col_req2:
  st.warning(
      "**2. Capital de Risco Isolado:**\nO dinheiro enviado para plataformas"
      " globais (como Avenue ou Nomad) deve ser aquele que você **não**"
      " precisará resgatar nos próximos 3 a 5 anos."
  )

st.divider()

# ==========================================================
# 2. COMO FUNCIONA A RENDA PASSIVA NOS EUA
# ==========================================================
st.subheader("🇺🇸 2. Como Funciona a Renda Passiva nos EUA?")
st.markdown(
    "Diferente do Brasil, onde a maioria das ações paga dividendos semestrais"
    " ou anuais, o mercado americano possui características únicas que"
    " facilitam a previsibilidade da renda:"
)

col_eua1, col_eua2 = st.columns(2)
with col_eua1:
  st.markdown("""
        * **Pagamentos Trimestrais ou Mensais:** A maioria das empresas americanas divide seus dividendos em 4 pagamentos ao ano. Existem também ativos específicos que pagam **todos os meses**.
        """)
with col_eua2:
  st.markdown("""
        * **Tributação Direta na Fonte:** Os EUA retêm automaticamente **30% de imposto de renda** sobre o dividendo distribuído a estrangeiros. O valor líquido já cai pronto para uso ou reinvestimento na sua conta internacional.
        """)

st.divider()

# ==========================================================
# 3. PILARES DE ATIVOS PARA RENDA EM DÓLAR
# ==========================================================
st.subheader("🏗️ 3. Pilares de Ativos para Renda em Dólar")
st.markdown(
    "Para montar uma carteira focada em renda com a segurança necessária, o"
    " estudo deve focar em três classes de ativos:"
)

tab1, tab2, tab3 = st.tabs([
    "👑 Dividend Aristocrats & Kings",
    "🏢 REITs (Fundos Imobiliários)",
    "📦 ETFs de Dividendos",
])

with tab1:
  st.markdown("""
    #### Ações Individuais Sólidas
    São empresas listadas no índice *S&P 500* que aumentam o pagamento de dividendos consecutivamente há pelo menos **25 anos** (Aristocratas) ou **50 anos** (Reis).
    * **Exemplos clássicos:** Coca-Cola (KO), Johnson & Johnson (JNJ), Procter & Gamble (PG).
    * **Vantagem:** Extrema resiliência econômica e histórico sólido de manutenção de proventos mesmo em crises globais.
    """)

with tab2:
  st.markdown("""
    #### REITs (Real Estate Investment Trusts)
    O equivalente americano aos Fundos Imobiliários (FIIs). São empresas que possuem, operam ou financiam imóveis geradores de caixa (galpões logísticos, shoppings, data centers).
    * **Exemplo clássico:** *Realty Income (O)* – Conhecido como *"The Monthly Dividend Company"* por pagar proventos **mensalmente** há décadas.
    * **Vantagem:** A legislação americana obriga os REITs a distribuírem pelo menos 90% do lucro tributável aos acionistas.
    """)

with tab3:
  st.markdown("""
    #### ETFs de Dividendos (Maior Segurança)
    Em vez de escolher ações sozinhas, você adquire um pacote diversificado com centenas de empresas pagadoras de dividendos. É a forma mais recomendada para mitigar o risco de concentração.
    * **SCHD (Schwab U.S. Dividend Equity ETF):** Focado em empresas americanas de altíssima qualidade e crescimento sustentável de dividendos.
    * **VYM (Vanguard High Dividend Yield ETF):** Focado em empresas com rendimentos (yields) acima da média do mercado.
    """)

st.divider()

# ==========================================================
# 4. TABELA DE FLUXO E CALENDÁRIO DE DIVIDENDOS
# ==========================================================
st.subheader("📉 4. Tabela de Simulação de Fluxo de Dividendos")
st.markdown(
    "Organize o cronograma de estudos combinando ativos com diferentes"
    " frequências de pagamento para preencher o seu calendário:"
)

import pandas as pd

dados_tabela = [
    {
        "Ativo / ETF": "SCHD",
        "Tipo de Ativo": "ETF de Dividendos Qualitativos",
        "Frequência": "Trimestral",
        "Meses de Pagamento Padrão": "Março, Junho, Setembro, Dezembro",
    },
    {
        "Ativo / ETF": "VYM",
        "Tipo de Ativo": "ETF de Alto Rendimento (Yield)",
        "Frequência": "Trimestral",
        "Meses de Pagamento Padrão": "Março, Junho, Setembro, Dezembro",
    },
    {
        "Ativo / ETF": "Realty Income (O)",
        "Tipo de Ativo": "REIT (Imobiliário Americano)",
        "Frequência": "Mensal",
        "Meses de Pagamento Padrão": "Todos os meses do ano",
    },
    {
        "Ativo / ETF": "Coca-Cola (KO)",
        "Tipo de Ativo": "Ação (Dividend King)",
        "Frequência": "Trimestral",
        "Meses de Pagamento Padrão": "Abril, Julho, Outubro, Dezembro",
    },
]

df_estrategia = pd.DataFrame(dados_tabela)
st.dataframe(df_estrategia, use_container_width=True, hide_index=True)

st.divider()

# ==========================================================
# 5. PRÓXIMOS PASSOS
# ==========================================================
st.subheader("📝 5. Próximos Passos para o seu Planejamento")
st.markdown("""
1. **Defina a sua Meta de Renda Passiva:** Estabeleça o primeiro marco inicial (ex: *Receber US$ 10 por mês*, evoluindo progressivamente).
2. **Método de Aporte Constante:** Separe um percentual planejado do orçamento após a consolidação da sua base no Brasil para iniciar a internacionalização.
3. **Reinvestimento em Bola de Neve:** Utilize os primeiros dólares recebidos de dividendos para comprar novas frações de ETFs, acelerando o crescimento exponencial da renda passiva.
""")

st.markdown(
    "<br><hr><p style='text-align: center; color: gray; font-size: 0.85em;'>"
    "<i>Este documento é de caráter exclusivamente educativo para guiar os"
    " seus estudos de planejamento financeiro. Investimentos em renda"
    " variável possuem riscos inerentes de mercado.</i></p>",
    unsafe_allow_html=True,
)
