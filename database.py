import os
import sqlite3

# Define o caminho absoluto exato para o banco de dados na raiz do projeto
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIRETORIO_ATUAL, "financas.db")


def obter_conexao():
  """Retorna a conexão com o banco de dados unificado na raiz."""
  return sqlite3.connect(DB_PATH)


def inicializar_banco():
  """Garante que todas as tabelas existem."""
  conexao = obter_conexao()
  cursor = conexao.cursor()

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

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS aportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            local_aplicacao TEXT,
            descricao TEXT,
            valor REAL
        )
    """)

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
  cursor.close()
  conexao.close()
