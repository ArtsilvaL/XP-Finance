import pandas as pd
from database import get_db_connection
from datetime import datetime

def get_movimentacoes_df(user_id: int) -> pd.DataFrame:
    """Busca todas as movimentações de um usuário e retorna como DataFrame."""
    conn = get_db_connection()
    query = "SELECT * FROM movimentacoes WHERE user_id = ?"
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['mes_ano'] = df['data'].dt.to_period('M')
    return df

def get_resumo_financeiro(df: pd.DataFrame) -> dict:
    """Calcula o resumo financeiro (total e mensal) a partir de um DataFrame."""
    if df.empty:
        return {"receita_total": 0, "despesa_total": 0, "economia_total": 0,
                "receita_mes": 0, "despesa_mes": 0, "economia_mes": 0,
                "receita_mes_anterior": 0, "despesa_mes_anterior": 0, "economia_mes_anterior": 0,
                "taxa_economia": 0}

    # Resumo total
    receita_total = df[df['tipo'] == 'Receita']['valor'].sum()
    despesa_total = df[df['tipo'] == 'Despesa']['valor'].sum()
    economia_total = receita_total - despesa_total

    # Resumo do mês atual e anterior
    mes_atual = pd.Timestamp.now().to_period('M')
    mes_anterior = (pd.Timestamp.now() - pd.DateOffset(months=1)).to_period('M')
    
    df_mes_atual = df[df['mes_ano'] == mes_atual]
    df_mes_anterior = df[df['mes_ano'] == mes_anterior]
    
    receita_mes = df_mes_atual[df_mes_atual['tipo'] == 'Receita']['valor'].sum()
    despesa_mes = df_mes_atual[df_mes_atual['tipo'] == 'Despesa']['valor'].sum()
    economia_mes = receita_mes - despesa_mes

    receita_mes_anterior = df_mes_anterior[df_mes_anterior['tipo'] == 'Receita']['valor'].sum()
    despesa_mes_anterior = df_mes_anterior[df_mes_anterior['tipo'] == 'Despesa']['valor'].sum()
    economia_mes_anterior = receita_mes_anterior - despesa_mes_anterior
    
    taxa_economia = (economia_mes / receita_mes * 100) if receita_mes > 0 else 0

    return {
        "receita_total": receita_total,
        "despesa_total": despesa_total,
        "economia_total": economia_total,
        "receita_mes": receita_mes,
        "despesa_mes": despesa_mes,
        "economia_mes": economia_mes,
        "receita_mes_anterior": receita_mes_anterior,
        "despesa_mes_anterior": despesa_mes_anterior,
        "economia_mes_anterior": economia_mes_anterior,
        "taxa_economia": taxa_economia
    }

def get_gastos_por_categoria(df: pd.DataFrame) -> pd.Series:
    """Retorna uma série do Pandas com o total de gastos por categoria."""
    despesas_df = df[df['tipo'] == 'Despesa']
    return despesas_df.groupby('categoria')['valor'].sum().sort_values(ascending=False)

def get_evolucao_economias(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna um DataFrame com a evolução das economias mensais."""
    if df.empty:
        return pd.DataFrame()
    df['economia'] = df.apply(lambda row: row['valor'] if row['tipo'] == 'Receita' else -row['valor'], axis=1)
    evolucao = df.groupby('mes_ano')['economia'].sum().cumsum().reset_index()
    evolucao['mes_ano'] = evolucao['mes_ano'].astype(str)
    return evolucao.set_index('mes_ano')

def get_receitas_vs_despesas(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna dados de Receitas vs Despesas agrupados por mês."""
    if df.empty:
        return pd.DataFrame()
    mensal = df.groupby(['mes_ano', 'tipo'])['valor'].sum().reset_index()
    mensal['mes_ano'] = mensal['mes_ano'].astype(str)
    pivot_df = mensal.pivot(index='mes_ano', columns='tipo', values='valor').fillna(0)
    if 'Receita' not in pivot_df.columns: pivot_df['Receita'] = 0
    if 'Despesa' not in pivot_df.columns: pivot_df['Despesa'] = 0
    return pivot_df

def get_dashboard_insights(df_mov: pd.DataFrame, resumo: dict, metas_df: pd.DataFrame) -> dict:
    """Gera insights avançados, identifica vilão/herói e impacto nas metas."""
    insights = []
    vilao = {"nome": "Nenhum", "valor": 0, "pct": 0, "dica": "Continue assim!"}
    heroi = {"nome": "Nenhum", "desc": "Registre mais dados para descobrirmos seu ponto forte."}
    impacto_metas = []
    
    if df_mov.empty:
        return {"insights": ["Comece a registrar suas finanças para receber dicas!"], "vilao": vilao, "heroi": heroi, "impacto_metas": impacto_metas}
        
    mes_atual = pd.Timestamp.now().to_period('M')
    df_mes = df_mov[df_mov['mes_ano'] == mes_atual]
    despesas_mes = df_mes[df_mes['tipo'] == 'Despesa']
    total_despesas_mes = despesas_mes['valor'].sum()
    
    # Vilão do Mês
    if not despesas_mes.empty and total_despesas_mes > 0:
        gastos_cat = despesas_mes.groupby('categoria')['valor'].sum().sort_values(ascending=False)
        maior_cat = gastos_cat.index[0]
        maior_valor = gastos_cat.iloc[0]
        pct_maior = (maior_valor / total_despesas_mes) * 100
        
        vilao = {
            "nome": maior_cat, 
            "valor": maior_valor, 
            "pct": pct_maior,
            "dica": f"Reduzir gastos com {maior_cat} em 10% aceleraria muito suas metas."
        }
        
        if "Delivery" in gastos_cat and (gastos_cat["Delivery"] / total_despesas_mes) > 0.2:
            insights.append(f"⚠️ Delivery representa {(gastos_cat['Delivery'] / total_despesas_mes)*100:.1f}% dos seus gastos deste mês.")
            
    # MoM Comparison Insights
    if resumo['despesa_mes'] > resumo['despesa_mes_anterior'] and resumo['despesa_mes_anterior'] > 0:
        aumento = ((resumo['despesa_mes'] - resumo['despesa_mes_anterior']) / resumo['despesa_mes_anterior']) * 100
        insights.append(f"⚠️ Atenção! Seus gastos aumentaram {aumento:.1f}% em relação ao mês passado.")
        
    if resumo['economia_mes'] > resumo['economia_mes_anterior']:
        insights.append(f"🎯 Excelente! Você economizou mais do que no mês passado.")
        heroi = {"nome": "Economia Crescente", "desc": f"Sua economia aumentou em R$ {resumo['economia_mes'] - resumo['economia_mes_anterior']:,.2f}!"}
        
    if resumo['taxa_economia'] > 20:
        insights.append(f"🏆 Sua taxa de economia está acima da média ({resumo['taxa_economia']:.1f}% guardados).")
        
    # Herói Alternativo
    educacao = df_mes[df_mes['categoria'] == 'Educação']['valor'].sum()
    if educacao > 0 and heroi["nome"] == "Nenhum":
        heroi = {"nome": "Educação", "desc": f"Você investiu R$ {educacao:,.2f} no seu aprendizado."}
        
    # Impacto nas Metas
    if not metas_df.empty and resumo['economia_mes'] > 0:
        for _, row in metas_df.iterrows():
            falta = row['valor_alvo'] - row['valor_acumulado']
            if falta > 0:
                meses = falta / resumo['economia_mes']
                impacto_metas.append({"nome": row['nome'], "meses": max(1, int(meses))})
                
    if len(insights) == 0:
        insights.append("💡 Registre mais atividades diárias para obter análises do seu padrão de gastos.")
        
    return {
        "insights": insights,
        "vilao": vilao,
        "heroi": heroi,
        "impacto_metas": impacto_metas
    }

def adicionar_movimentacao(user_id: int, tipo: str, categoria: str, valor: float, data, descricao: str):
    """Insere uma nova atividade financeira no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO movimentacoes (user_id, tipo, categoria, valor, data, descricao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, tipo, categoria, valor, data, descricao))
    conn.commit()
    conn.close()

def adicionar_meta(user_id: int, nome: str, valor_alvo: float, prazo):
    """Insere uma nova meta financeira no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO metas (user_id, nome, valor_alvo, prazo)
        VALUES (?, ?, ?, ?)
    """, (user_id, nome, valor_alvo, prazo))
    conn.commit()
    conn.close()

def get_metas_df(user_id: int) -> pd.DataFrame:
    """Busca as metas cadastradas do usuário, somando os valores aportados."""
    conn = get_db_connection()
    query = """
        SELECT m.*, COALESCE(SUM(a.valor), 0) as valor_acumulado
        FROM metas m
        LEFT JOIN aportes_meta a ON m.id = a.meta_id
        WHERE m.user_id = ?
        GROUP BY m.id
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def adicionar_aporte(meta_id: int, valor: float, observacao: str, data: str):
    """Insere um novo aporte para uma meta específica."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO aportes_meta (meta_id, valor, observacao, data) VALUES (?, ?, ?, ?)", 
                   (meta_id, valor, observacao, data))
    conn.commit()
    conn.close()

def get_aportes_df(user_id: int) -> pd.DataFrame:
    """Busca todos os aportes realizados pelo usuário em todas as suas metas."""
    conn = get_db_connection()
    query = """
        SELECT a.* FROM aportes_meta a
        JOIN metas m ON a.meta_id = m.id
        WHERE m.user_id = ?
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def deletar_meta(meta_id: int):
    """Apaga uma meta e todo o seu histórico de aportes associado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM aportes_meta WHERE meta_id = ?", (meta_id,))
    cursor.execute("DELETE FROM metas WHERE id = ?", (meta_id,))
    conn.commit()
    conn.close()