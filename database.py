import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = "data/financeiro.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn):
    """Cria as tabelas do banco de dados se não existirem."""
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        titulo TEXT,
        avatar_url TEXT
    )
    """)

    # Tabela de movimentações financeiras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tipo TEXT NOT NULL, -- 'Receita' ou 'Despesa'
        categoria TEXT NOT NULL,
        valor REAL NOT NULL,
        data DATE NOT NULL,
        descricao TEXT,
        FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
    """)

    # Tratativa de segurança: Adiciona a coluna descricao se a tabela antiga já existir
    try:
        cursor.execute("ALTER TABLE movimentacoes ADD COLUMN descricao TEXT")
    except sqlite3.OperationalError:
        pass # A coluna já existe, ignorar erro

    # Tabela de metas financeiras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        nome TEXT NOT NULL,
        valor_alvo REAL NOT NULL,
        prazo DATE NOT NULL,
        FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
    """)

    # Tabela de histórico de aportes para as metas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aportes_meta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meta_id INTEGER,
        valor REAL NOT NULL,
        observacao TEXT,
        data DATE NOT NULL,
        FOREIGN KEY (meta_id) REFERENCES metas (id)
    )
    """)

    # Tabela de histórico de recompensas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico_recompensas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        missao_id TEXT NOT NULL,
        missao_nome TEXT NOT NULL,
        xp INTEGER NOT NULL,
        moedas INTEGER NOT NULL,
        data DATE NOT NULL
    )
    """)

    # Tabela de itens comprados na loja
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras_loja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_nome TEXT NOT NULL,
        preco INTEGER NOT NULL,
        data DATE NOT NULL
    )
    """)

    # Outras tabelas para gamificação (podem ser expandidas no futuro)
    cursor.execute("CREATE TABLE IF NOT EXISTS conquistas (id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT, icone TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS missoes (id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT, xp_recompensa INTEGER)")

    conn.commit()

def seed_data_if_empty(conn):
    """Popula o banco de dados com dados de exemplo se estiver vazio."""
    cursor = conn.cursor()
    
    # Verifica se já existem usuários
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        print("Banco de dados vazio. Populando com dados de exemplo...")
        
        # Inserir usuário de exemplo
        cursor.execute("INSERT INTO usuarios (id, nome, titulo) VALUES (?, ?, ?)", 
                       (1, 'Arthur', 'Mestre da Economia'))

        # Inserir movimentações de exemplo para o usuário 1
        today = datetime.today()
        movimentacoes_exemplo = [
            (1, 'Receita', 'Salário', 3500.00, (today - timedelta(days=15)).strftime('%Y-%m-%d')),
            (1, 'Receita', 'Freelance', 850.00, (today - timedelta(days=10)).strftime('%Y-%m-%d')),
            (1, 'Despesa', 'Aluguel', 1200.00, (today - timedelta(days=14)).strftime('%Y-%m-%d')),
            (1, 'Despesa', 'Supermercado', 650.00, (today - timedelta(days=12)).strftime('%Y-%m-%d')),
            (1, 'Despesa', 'Internet', 100.00, (today - timedelta(days=10)).strftime('%Y-%m-%d')),
            (1, 'Despesa', 'Transporte', 150.00, (today - timedelta(days=8)).strftime('%Y-%m-%d')),
            (1, 'Despesa', 'Delivery', 250.00, (today - timedelta(days=5)).strftime('%Y-%m-%d')),
            (1, 'Despesa', 'Lazer', 300.00, (today - timedelta(days=3)).strftime('%Y-%m-%d')),
             # Movimentação do mês anterior
            (1, 'Receita', 'Salário', 3500.00, (today - timedelta(days=45)).strftime('%Y-%m-%d')),
            (1, 'Despesa', 'Aluguel', 1200.00, (today - timedelta(days=44)).strftime('%Y-%m-%d')),
        ]
        
        cursor.executemany(
            "INSERT INTO movimentacoes (user_id, tipo, categoria, valor, data) VALUES (?, ?, ?, ?, ?)",
            movimentacoes_exemplo
        )
        
        conn.commit()
        print("Dados de exemplo inseridos com sucesso.")

def setup_database():
    """Função principal para configurar o banco de dados."""
    conn = get_db_connection()
    create_tables(conn)
    seed_data_if_empty(conn)
    conn.close()

def reset_database():
    """Limpa todas as tabelas e reinicia os dados de demonstração."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Coletar contagem para logs de depuração
    cursor.execute("SELECT COUNT(*) FROM movimentacoes")
    movs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM metas")
    metas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM aportes_meta")
    aportes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM historico_recompensas")
    hist = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM compras_loja")
    compras = cursor.fetchone()[0]

    # Limpar APENAS as tabelas de progresso do usuário
    cursor.execute("DELETE FROM compras_loja")
    cursor.execute("DELETE FROM historico_recompensas")
    cursor.execute("DELETE FROM aportes_meta")
    cursor.execute("DELETE FROM movimentacoes")
    cursor.execute("DELETE FROM metas")
    cursor.execute("DELETE FROM conquistas")
    cursor.execute("DELETE FROM missoes")
    
    conn.commit()
    
    conn.close()
    
    return {
        "tabelas_limpas": 7,
        "movs_removidas": movs,
        "metas_removidas": metas,
        "aportes_removidos": aportes,
        "historico_removidos": hist,
        "compras_removidas": compras
    }