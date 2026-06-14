from database import get_db_connection
import pandas as pd

XP_LEVELS = {
    1: 0, 2: 500, 3: 1000, 4: 2000, 5: 3500, 
    6: 5000, 7: 7500, 8: 10000, 9: 15000, 10: 20000
}

def get_user(user_id: int) -> dict:
    """Busca os dados de um usuário no banco."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    user_dict = dict(user) if user else {}
    
    if user_dict:
        # Calcula o saldo real de moedas
        cursor.execute("SELECT SUM(moedas) FROM historico_recompensas WHERE user_id = ?", (user_id,))
        ganhas = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(preco) FROM compras_loja WHERE user_id = ?", (user_id,))
        gastas = cursor.fetchone()[0] or 0
        
        user_dict['moedas'] = ganhas - gastas
        
    conn.close()
    return user_dict

def process_missoes(user_id: int, df_mov: pd.DataFrame, df_metas: pd.DataFrame):
    """Avalia o progresso, conclui missões e gera recompensas de XP e Moedas."""
    hoje = pd.Timestamp.now().normalize()
    inicio_semana = hoje - pd.Timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    
    eco_semana = 0
    eco_mes = 0
    dias_semana = 0
    prog_del = 0
    metas_conc = 0
    
    if not df_mov.empty:
        df = df_mov.copy()
        df['data'] = pd.to_datetime(df['data'])
        
        df_sem = df[df['data'] >= inicio_semana]
        df_mes = df[df['data'] >= inicio_mes]
        
        if not df_sem.empty:
            eco_semana = df_sem[df_sem['tipo']=='Receita']['valor'].sum() - df_sem[df_sem['tipo']=='Despesa']['valor'].sum()
            dias_semana = df_sem['data'].dt.date.nunique()
            gasto_del = df_sem[df_sem['categoria']=='Delivery']['valor'].sum()
            prog_del = 1 if gasto_del == 0 else 0
        
        if not df_mes.empty:
            eco_mes = df_mes[df_mes['tipo']=='Receita']['valor'].sum() - df_mes[df_mes['tipo']=='Despesa']['valor'].sum()
            
    if df_metas is not None and not df_metas.empty:
        metas_conc = len(df_metas[df_metas['valor_acumulado'] >= df_metas['valor_alvo']])

    missoes = [
        {"id": "sem_1", "tipo": "Semanal", "nome": "Economize R$100 na semana", "objetivo": 100, "progresso": eco_semana, "moedas": 100, "xp": 50, "icone": "💰"},
        {"id": "sem_2", "tipo": "Semanal", "nome": "Registrar movimentações por 5 dias", "objetivo": 5, "progresso": dias_semana, "moedas": 50, "xp": 25, "icone": "📅"},
        {"id": "sem_3", "tipo": "Semanal", "nome": "Sem delivery na semana", "objetivo": 1, "progresso": prog_del, "moedas": 150, "xp": 75, "icone": "🍕"},
        {"id": "mes_1", "tipo": "Mensal", "nome": "Economizar R$500 no mês", "objetivo": 500, "progresso": eco_mes, "moedas": 500, "xp": 250, "icone": "🏆"},
        {"id": "mes_2", "tipo": "Mensal", "nome": "Economizar R$1000 no mês", "objetivo": 1000, "progresso": eco_mes, "moedas": 1000, "xp": 500, "icone": "🏆"},
        {"id": "geral_1", "tipo": "Mensal", "nome": "Concluir uma meta financeira", "objetivo": 1, "progresso": metas_conc, "moedas": 300, "xp": 150, "icone": "🎯"},
    ]

    conn = get_db_connection()
    df_hist = pd.read_sql_query("SELECT missao_id FROM historico_recompensas WHERE user_id = ?", conn, params=(user_id,))
    claimed = df_hist['missao_id'].tolist() if not df_hist.empty else []
    
    recentes = []
    for m in missoes:
        if m['progresso'] >= m['objetivo'] and m['id'] not in claimed:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO historico_recompensas (user_id, missao_id, missao_nome, xp, moedas, data) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, m['id'], m['nome'], m['xp'], m['moedas'], pd.Timestamp.now().strftime('%d/%m/%Y')))
            conn.commit()
            recentes.append(m)
            claimed.append(m['id'])
        
        m['concluida'] = m['id'] in claimed

    conn.close()
    return missoes, recentes

def get_xp_level(user_id: int, df_movimentacoes: pd.DataFrame, df_metas: pd.DataFrame = None, df_aportes: pd.DataFrame = None) -> dict:
    """Calcula o nível e XP total (Soma de recompensas e conquistas independentes)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(xp) FROM historico_recompensas WHERE user_id = ?", (user_id,))
    xp_total = cursor.fetchone()[0] or 0
    conn.close()

    economia_total = 0
    streak_final = 0
    
    if not df_movimentacoes.empty:
        df_mov = df_movimentacoes.copy()
        df_mov['data'] = pd.to_datetime(df_mov['data'])
        if 'mes_ano' not in df_mov.columns:
            df_mov['mes_ano'] = df_mov['data'].dt.to_period('M')
            
        mensal = df_mov.groupby(['mes_ano', 'tipo'])['valor'].sum().unstack(fill_value=0)
        if 'Receita' not in mensal.columns: mensal['Receita'] = 0
        if 'Despesa' not in mensal.columns: mensal['Despesa'] = 0
        economia_total = (mensal['Receita'] - mensal['Despesa']).sum()

        datas_unicas = df_mov['data'].dt.date.drop_duplicates().sort_values().tolist()
        streak = 1
        for i in range(1, len(datas_unicas)):
            if (datas_unicas[i] - datas_unicas[i-1]).days == 1:
                streak += 1
            else:
                streak = 1
        streak_final = streak

    # Conquistas Desbloqueadas (+150 XP cada)
    conquistas_count = 0
    if economia_total > 0: conquistas_count += 1
    if economia_total >= 500: conquistas_count += 1
    if economia_total >= 1000: conquistas_count += 1
    
    if df_metas is not None and not df_metas.empty:
        metas_concluidas = len(df_metas[df_metas['valor_acumulado'] >= df_metas['valor_alvo']])
        conquistas_count += 1
        if any(df_metas['valor_acumulado'] >= (df_metas['valor_alvo'] / 2)):
            conquistas_count += 1
        if metas_concluidas > 0:
            conquistas_count += 1
            
        
    xp_total += conquistas_count * 150
    
    # XP retroativo e em cadeia das Conquistas de Nível
    def get_current_level(xp):
        lvl = 1
        for l, xp_req in sorted(XP_LEVELS.items()):
            if xp >= xp_req: lvl = l
            else: break
        return lvl
        
    temp_level = get_current_level(xp_total)
    if temp_level >= 5: xp_total += 150
    temp_level = get_current_level(xp_total)
    if temp_level >= 10: xp_total += 150
    
    level = get_current_level(xp_total)
    
    xp_para_prox_nivel = XP_LEVELS.get(level + 1, XP_LEVELS[10])
    xp_base_nivel_atual = XP_LEVELS[level]

    xp_atual_nivel = xp_total - xp_base_nivel_atual
    xp_necessario = xp_para_prox_nivel - xp_base_nivel_atual
    
    progress_percent = min(1.0, xp_atual_nivel / xp_necessario) if xp_necessario > 0 else 1.0

    return {
        "level": level,
        "xp_total": xp_total,
        "xp_atual_nivel": xp_atual_nivel,
        "xp_para_prox_nivel": xp_necessario,
        "progress_percent": progress_percent,
        "streak": streak_final
    }

def get_conquistas(economia_total: float, level: int, df_metas: pd.DataFrame = None, df_aportes: pd.DataFrame = None) -> list:
    """Verifica e retorna a lista de conquistas do usuário."""
    conquistas = [
        {"nome": "Primeira Economia", "desbloqueada": economia_total > 0, "icone": "🥉", "raridade": "comum"},
        {"nome": "Economizou R$500", "desbloqueada": economia_total >= 500, "icone": "🥈", "raridade": "raro"},
        {"nome": "Economizou R$1000", "desbloqueada": economia_total >= 1000, "icone": "🥇", "raridade": "epico"},
        {"nome": "Alcançou Nível 5", "desbloqueada": level >= 5, "icone": "🚀", "raridade": "epico"},
        {"nome": "Mestre das Finanças", "desbloqueada": level >= 10, "icone": "👑", "raridade": "lendario"},
        
        # Novas Conquistas de Metas
        {"nome": "Primeira Meta Criada", "desbloqueada": df_metas is not None and len(df_metas) > 0, "icone": "🎯", "raridade": "comum"},
        {"nome": "Primeiros R$100 Guardados", "desbloqueada": df_aportes is not None and not df_aportes.empty and df_aportes['valor'].sum() >= 100, "icone": "🐖", "raridade": "comum"},
        {"nome": "Meta 50% Concluída", "desbloqueada": df_metas is not None and not df_metas.empty and any(df_metas['valor_acumulado'] >= df_metas['valor_alvo'] / 2), "icone": "⏳", "raridade": "raro"},
        {"nome": "Primeira Meta Concluída", "desbloqueada": df_metas is not None and not df_metas.empty and any(df_metas['valor_acumulado'] >= df_metas['valor_alvo']), "icone": "💎", "raridade": "lendario"}
    ]
    return conquistas

def comprar_item(user_id: int, item_nome: str, preco: int) -> bool:
    user = get_user(user_id)
    if user.get('moedas', 0) >= preco:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO compras_loja (user_id, item_nome, preco, data) VALUES (?, ?, ?, ?)",
                       (user_id, item_nome, preco, pd.Timestamp.now().strftime('%d/%m/%Y')))
        conn.commit()
        conn.close()
        return True
    return False

def get_historico_recompensas(user_id: int) -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM historico_recompensas WHERE user_id = ? ORDER BY id DESC", conn, params=(user_id,))
    conn.close()
    return df

def get_ranking(current_user_name: str, current_user_economia: float) -> pd.DataFrame:
    """Cria um ranking fictício baseado na economia real para demonstração."""
    dados = {
        'Usuário': ['João', 'Maria', 'Lucas', 'Ana'],
        'Economia (R$)': [1500, 1000, 700, 650]
    }
    ranking_df = pd.DataFrame(dados)
    
    # Adiciona o usuário atual
    current_user_df = pd.DataFrame([{'Usuário': current_user_name, 'Economia (R$)': current_user_economia}])
    ranking_df = pd.concat([ranking_df, current_user_df], ignore_index=True)
    
    ranking_df = ranking_df.sort_values(by='Economia (R$)', ascending=False).reset_index(drop=True)
    ranking_df.index = [f'{"🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f" {i+1}º"} ' for i in ranking_df.index]
    return ranking_df