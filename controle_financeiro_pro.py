import os
import sqlite3
import pandas as pd
from datetime import datetime

# Nome do banco de dados local
DB_NAME = "financas.db"

def inicializar_banco():
    """Cria o banco de dados e as tabelas se elas não existirem."""
    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()
    
    # Tabela de Lançamentos Diários (Créditos e Débitos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL
        )
    """)
    
    # Tabela de Dívidas (Raio-X)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dividas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credor TEXT,
            valor_total REAL,
            juros_mensal REAL,
            status TEXT
        )
    """)
    
    conexao.commit()
    conexao.close()

def adicionar_lancamento():
    print("\n--- NOVO LANÇAMENTO (CADA CENTAVO) ---")
    data = datetime.now().strftime("%d/%m/%Y")
    
    print("Tipo:")
    print("1 - Receita (Entrada)")
    print("2 - Despesa (Saída/Gasto)")
    tipo_op = input("Escolha (1 ou 2): ")
    tipo = "Receita" if tipo_op == "1" else "Despesa"
    
    categoria = input("Categoria (Ex: Alimentação, Moradia, Cartão): ")
    descricao = input("Descrição / Estabelecimento: ")
    try:
        valor = float(input("Valor (R$): ").replace(",", "."))
    except ValueError:
        print("Valor inválido! Operação cancelada.")
        return

    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (?, ?, ?, ?, ?)",
        (data, tipo, categoria, descricao, valor)
    )
    conexao.commit()
    conexao.close()
    print("Lançamento registrado com sucesso!")

def adicionar_divida():
    print("\n--- CADASTRAR / MAPEAR DÍVIDA ---")
    credor = input("Credor / Nome da Dívida (Ex: Cartão de Crédito X): ")
    try:
        valor_total = float(input("Valor Total Devido (R$): ").replace(",", "."))
        juros_mensal = float(input("Taxa de Juros Mensal (%): ").replace(",", "."))
    except ValueError:
        print("Valores inválidos! Operação cancelada.")
        return
    status = "Pendente"

    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()
    cursor.execute(
        "INSERT INTO dividas (credor, valor_total, juros_mensal, status) VALUES (?, ?, ?, ?)",
        (credor, valor_total, juros_mensal, status)
    )
    conexao.commit()
    conexao.close()
    print("Dívida cadastrada com sucesso para foco de renegociação!")

def ver_resumo():
    conexao = sqlite3.connect(DB_NAME)
    
    # Lendo lançamentos com pandas
    df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
    df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
    
    conexao.close()
    
    print("\n" + "="*40)
    print("       PAINEL DE CONTROLE FINANCEIRO")
    print("="*40)
    
    if not df_lancamentos.empty:
        total_receitas = df_lancamentos[df_lancamentos['tipo'] == 'Receita']['valor'].sum()
        total_despesas = df_lancamentos[df_lancamentos['tipo'] == 'Despesa']['valor'].sum()
        saldo = total_receitas - total_despesas
        
        print(f"Total de Entradas (Créditos): R$ {total_receitas:.2f}")
        print(f"Total de Saídas (Débitos):    R$ {total_despesas:.2f}")
        print(f"Saldo Atual do Mês:           R$ {saldo:.2f}")
    else:
        print("Nenhum lançamento registrado ainda.")
        
    print("\n--- DÍVIDAS MAPEADAS ---")
    if not df_dividas.empty:
        print(df_dividas.to_string(index=False))
    else:
        print("Nenhuma dívida cadastrada.")
    print("="*40)

def exportar_excel():
    conexao = sqlite3.connect(DB_NAME)
    df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
    df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
    conexao.close()
    
    nome_arquivo = "relatorio_financeiro.xlsx"
    with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
        df_lancamentos.to_excel(writer, sheet_name='Lancamentos', index=False)
        df_dividas.to_excel(writer, sheet_name='Dividas', index=False)
        
    print(f"\nRelatório exportado com sucesso para '{nome_arquivo}' na pasta do projeto!")

def main():
    inicializar_banco()
    while True:
        print("\n--- MENU PRINCIPAL ---")
        print("1. Adicionar Lançamento (Gasto ou Receita)")
        print("2. Cadastrar Dívida (Raio-X)")
        print("3. Ver Resumo e Saldo Atual")
        print("4. Exportar para Planilha Excel (.xlsx)")
        print("5. Sair")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            adicionar_lancamento()
        elif opcao == "2":
            adicionar_divida()
        elif opcao == "3":
            ver_resumo()
        elif opcao == "4":
            exportar_excel()
        elif opcao == "5":
            print("Saindo... Foco no objetivo de voltar ao azul!")
            break
        else:
            print("Opção inválida, tente novamente.")

if __name__ == "__main__":
    main()
