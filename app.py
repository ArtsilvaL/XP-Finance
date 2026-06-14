import sys
import os
import streamlit as st
import pandas as pd
import altair as alt

# Adiciona o diretório raiz do projeto ao path do Python para resolver problemas de importação
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from database import setup_database, reset_database

try:
    # Tenta importar usando a estrutura de pastas modular (services/ e components/)
    from services import finance_service, gamification_service
    from components import cards, ranking, missions, achievements
except ModuleNotFoundError:
    # Fallback: importa diretamente se os arquivos estiverem todos soltos na mesma pasta
    import finance_service
    import gamification_service
    import cards
    import ranking
    import missions
    import achievements

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="XP Finance",
    page_icon="🎮",
    layout="wide"
)

# --- CSS CUSTOMIZADO PARA GAMIFICAÇÃO ---
st.markdown("""
<style>
    /* Cores e Fundos */
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* Player Card */
    .player-card { background: linear-gradient(135deg, #1e1b4b, #4c1d95); border-radius: 20px; padding: 25px; color: white; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); border: 1px solid #7c3aed; }
    .player-title { color: #fbbf24; font-weight: bold; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Cards Genéricos */
    .stat-card { background: #1e293b; border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #334155; transition: transform 0.2s; }
    .stat-card:hover { transform: translateY(-5px); border-color: #6366f1; }
    
    /* Conquistas / Raridade */
    .achievement-badge { padding: 12px; border-radius: 12px; text-align: center; width: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.3s;}
    .achievement-badge:hover { transform: scale(1.1); }
    .rarity-comum { background: #334155; color: #cbd5e1; border: 2px solid #475569; }
    .rarity-raro { background: #1e3a8a; color: #bfdbfe; border: 2px solid #3b82f6; }
    .rarity-epico { background: #4c1d95; color: #e9d5ff; border: 2px solid #8b5cf6; }
    .rarity-lendario { background: #78350f; color: #fef3c7; border: 2px solid #f59e0b; box-shadow: 0 0 15px rgba(245,158,11,0.5); }
    
    /* Cards Vilão / Metas Concluídas */
    .villain-card { background: linear-gradient(45deg, #7f1d1d, #450a0a); border-radius: 15px; padding: 25px; text-align: center; color: white; border: 2px solid #ef4444; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);}
    .hero-card { background: linear-gradient(45deg, #064e3b, #14532d); border-radius: 15px; padding: 25px; text-align: center; color: white; border: 2px solid #10b981; box-shadow: 0 0 15px rgba(16, 185, 129, 0.4);}
    .exec-card { background: #1e293b; border-radius: 15px; padding: 20px; border: 1px solid #334155; transition: transform 0.2s; }
    .exec-card:hover { transform: translateY(-5px); border-color: #6366f1; }
    .exec-icon { font-size: 2.5rem; margin-bottom: 10px; }
    .exec-value { font-size: 1.8rem; font-weight: bold; color: #f8fafc; }
    .exec-label { font-size: 1rem; color: #94a3b8; font-weight: bold; }
    .exec-desc { font-size: 0.8rem; color: #64748b; margin-top: 5px; }
    .goal-card-done { border: 2px solid #10b981 !important; background: rgba(16, 185, 129, 0.1) !important; }
    
    /* Loja */
    .shop-item { background: #1e293b; border: 1px solid #334155; border-radius: 15px; padding: 15px; text-align: center; }
    .shop-price { color: #fbbf24; font-weight: bold; margin: 10px 0; font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
# Garante que o banco de dados e os dados de exemplo existam
setup_database()
USER_ID = 1  # ID do usuário fixo para o protótipo

# --- CARREGAMENTO DOS DADOS ---
# Financeiro
movimentacoes_df = finance_service.get_movimentacoes_df(USER_ID)
resumo = finance_service.get_resumo_financeiro(movimentacoes_df)
gastos_categoria = finance_service.get_gastos_por_categoria(movimentacoes_df)
evolucao_economias = finance_service.get_evolucao_economias(movimentacoes_df)
receitas_vs_despesas = finance_service.get_receitas_vs_despesas(movimentacoes_df)

# Gamificação
user_data = gamification_service.get_user(USER_ID)
metas_df = finance_service.get_metas_df(USER_ID)
aportes_df = finance_service.get_aportes_df(USER_ID)

intel = finance_service.get_dashboard_insights(movimentacoes_df, resumo, metas_df)

missoes_estado, recompensas_recentes = gamification_service.process_missoes(USER_ID, movimentacoes_df, metas_df)

if recompensas_recentes:
    st.balloons()
    for r in recompensas_recentes:
        st.toast(f"🎉 Missão concluída: {r['nome']}! \n🪙 +{r['moedas']} moedas \n⭐ +{r['xp']} XP", icon="🏆")
    user_data = gamification_service.get_user(USER_ID) # Recarrega moedas atualizadas

level_info = gamification_service.get_xp_level(USER_ID, movimentacoes_df, metas_df, aportes_df)

user_achievements = gamification_service.get_conquistas(resumo["economia_total"], level_info["level"], metas_df, aportes_df)
ranking_data = gamification_service.get_ranking(user_data["nome"], resumo["economia_total"])

# --- SEÇÃO 1: CABEÇALHO DO PERFIL GAMIFICADO ---
st.markdown(f"""
<div class="player-card">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="font-size: 4rem; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 50%;">👾</div>
            <div>
                <h1 style="margin: 0; padding: 0; font-size: 2.5rem;">{user_data['nome']}</h1>
                <div class="player-title">🏆 {user_data['titulo']}</div>
            </div>
        </div>
        <div style="text-align: right;">
            <h2 style="margin: 0; color: #10b981;">⭐ Nível {level_info['level']}</h2>
            <div style="color: #fbbf24; font-size: 1.5rem; font-weight: bold;">🪙 {user_data['moedas']} moedas</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.progress(level_info['progress_percent'], text=f"✨ Experiência (XP): {level_info['xp_atual_nivel']} / {level_info['xp_para_prox_nivel']}")

st.divider()

# --- SEÇÃO 2: ESTATÍSTICAS GAMIFICADAS ---
cards.show_gamified_stats(
    resumo["receita_total"],
    resumo["despesa_total"],
    resumo["economia_total"],
    user_data["moedas"],
    level_info["xp_total"]
)

st.divider()

# --- SEÇÃO 3: DESAFIOS E METAS ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("🎯 Suas Missões")
    with st.container(border=True):
        missions.show_missions(missoes_estado)

with col2:
    st.subheader("🌟 Suas Metas (Quests)")
    with st.expander("➕ Criar Nova Meta"):
        m_nome = st.text_input("Nome da Meta (ex: Comprar notebook)")
        m_valor = st.number_input("Valor Alvo (R$)", min_value=1.0, format="%.2f", step=100.0)
        m_prazo = st.date_input("Prazo da Meta")
        if st.button("Salvar Meta", type="primary"):
            finance_service.adicionar_meta(USER_ID, m_nome, m_valor, m_prazo)
            st.success("🎯 Meta cadastrada com sucesso!")
            st.rerun()
            
    if st.session_state.get('show_balloons', False):
        st.balloons()
        st.success("🎉 Meta Concluída! Você ganhou bônus de XP e Moedas!")
        st.session_state.show_balloons = False
            
    if not metas_df.empty:
        for _, row in metas_df.iterrows():
            valor_alvo = row['valor_alvo']
            valor_acumulado = row['valor_acumulado']
            progresso = min(1.0, valor_acumulado / valor_alvo) if valor_alvo > 0 else 1.0
            is_done = progresso >= 1.0
            
            css_class = "goal-card-done" if is_done else ""
            
            with st.container(border=True):
                if is_done:
                    st.markdown("### ✅ " + row['nome'] + " <span style='color:#10b981;'>(Concluída!)</span>", unsafe_allow_html=True)
                else:
                    st.write(f"### {row['nome']}")
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Acumulado", f"R$ {valor_acumulado:,.2f}")
                col_m2.metric("Alvo", f"R$ {valor_alvo:,.2f}")
                col_m3.metric("Progresso", f"{progresso*100:.1f}%")
                
                st.progress(progresso, text=f"Data final: {row['prazo']}")
                
                c_btn1, c_btn2, c_btn3 = st.columns(3)
                with c_btn1:
                    with st.popover("➕ Adicionar Valor", use_container_width=True):
                        aporte_val = st.number_input("Valor (R$)", min_value=0.01, step=50.0, key=f"val_{row['id']}")
                        aporte_obs = st.text_input("Observação", key=f"obs_{row['id']}", placeholder="Ex: Do 13º salário")
                        if st.button("Salvar Aporte", key=f"btn_{row['id']}", type="primary"):
                            finance_service.adicionar_aporte(row['id'], aporte_val, aporte_obs, pd.Timestamp.now().strftime('%Y-%m-%d'))
                            if (valor_acumulado + aporte_val) >= valor_alvo and valor_acumulado < valor_alvo:
                                st.session_state.show_balloons = True
                            st.rerun()
                with c_btn2:
                    with st.popover("📜 Histórico", use_container_width=True):
                        hist_df = aportes_df[aportes_df['meta_id'] == row['id']]
                        if not hist_df.empty:
                            for _, h_row in hist_df.iterrows():
                                st.write(f"**{h_row['data']}** - R$ {h_row['valor']:,.2f}")
                                if h_row['observacao']:
                                    st.caption(f'"{h_row["observacao"]}"')
                                st.divider()
                        else:
                            st.info("Nenhum aporte realizado.")
                with c_btn3:
                    with st.popover("✏️ Editar", use_container_width=True):
                        st.info("A edição será disponibilizada na próxima versão.")
                        if st.button("❌ Excluir Meta", key=f"del_{row['id']}", type="secondary", use_container_width=True):
                            finance_service.deletar_meta(row['id'])
                            st.rerun()

st.divider()

# --- SEÇÃO 4: CENTRAL FINANCEIRA ---
st.subheader("📊 Central Financeira")
st.write("Acompanhe o destino do seu dinheiro e entenda seus hábitos.")

# Resumo Executivo
c_exec1, c_exec2, c_exec3, c_exec4, c_exec5 = st.columns(5)

def render_exec(icon, label, value, desc):
    return f"""
    <div class="exec-card">
        <div class="exec-icon">{icon}</div>
        <div class="exec-value">{value}</div>
        <div class="exec-label">{label}</div>
        <div class="exec-desc">{desc}</div>
    </div>
    """

c_exec1.markdown(render_exec("💰", "Receita Total", f"R$ {resumo['receita_mes']:,.2f}", "Entradas no mês"), unsafe_allow_html=True)
c_exec2.markdown(render_exec("💸", "Despesa Total", f"R$ {resumo['despesa_mes']:,.2f}", "Saídas no mês"), unsafe_allow_html=True)

economia_fmt = f"R$ {resumo['economia_mes']:,.2f}" if resumo['economia_mes'] >= 0 else "-R$ " + f"{abs(resumo['economia_mes']):,.2f}"
c_exec3.markdown(render_exec("📈", "Economia Real", economia_fmt, "O que sobrou"), unsafe_allow_html=True)
c_exec4.markdown(render_exec("🎯", "Taxa de Economia", f"{resumo['taxa_economia']:.1f}%", "Da renda foi poupada"), unsafe_allow_html=True)
c_exec5.markdown(render_exec("🔥", "Sequência Positiva", f"{level_info['streak']} Dias", "Registrando finanças"), unsafe_allow_html=True)

st.write("")

# Comparação com Mês Anterior
st.markdown("#### ⚖️ Comparação com Mês Anterior")
col_mom1, col_mom2, col_mom3 = st.columns(3)

def get_mom_delta(atual, anterior):
    if anterior > 0: return ((atual - anterior) / anterior) * 100
    return 0.0

pct_rec = get_mom_delta(resumo['receita_mes'], resumo['receita_mes_anterior'])
pct_desp = get_mom_delta(resumo['despesa_mes'], resumo['despesa_mes_anterior'])
pct_eco = get_mom_delta(resumo['economia_mes'], resumo['economia_mes_anterior'])

col_mom1.metric("Receitas", f"R$ {resumo['receita_mes']:,.2f}", f"{pct_rec:.1f}%", delta_color="normal")
col_mom2.metric("Despesas", f"R$ {resumo['despesa_mes']:,.2f}", f"{pct_desp:.1f}%", delta_color="inverse")
col_mom3.metric("Economia", f"R$ {resumo['economia_mes']:,.2f}", f"{pct_eco:.1f}%", delta_color="normal")

st.write("")

# Gráficos e Distribuição
col_g1, col_g2 = st.columns([1, 1])

with col_g1:
    with st.container(border=True):
        st.markdown("### 🍕 Distribuição de Gastos")
        if len(gastos_categoria) > 0:
            df_pie = gastos_categoria.reset_index()
            df_pie.columns = ['Categoria', 'Valor']
            pie_chart = alt.Chart(df_pie).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Valor", type="quantitative"),
                color=alt.Color(field="Categoria", type="nominal", scale=alt.Scale(scheme='category20b')),
                tooltip=['Categoria', 'Valor']
            ).properties(height=350)
            st.altair_chart(pie_chart, use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada no período.")

with col_g2:
    with st.container(border=True):
        st.markdown("### ⚔️ Receitas vs Despesas")
        if not receitas_vs_despesas.empty:
            st.bar_chart(receitas_vs_despesas, height=350)
        else:
            st.info("Nenhum dado financeiro para comparar.")

with st.container(border=True):
    st.markdown("### 📈 Evolução da Economia")
    if not evolucao_economias.empty:
        st.line_chart(evolucao_economias, height=250)
    else:
        st.info("Continue economizando para ver sua evolução!")
        
st.write("")

# Insights e Cards Dinâmicos
col_ins1, col_ins2, col_ins3 = st.columns(3)

with col_ins1:
    v = intel['vilao']
    st.markdown(f"""
    <div class="villain-card">
        <div style="font-size: 3rem;">💀</div>
        <h3 style="margin: 10px 0;">Vilão do Mês</h3>
        <h2 style="color: #fbbf24; margin: 0;">{v['nome']}</h2>
        <h4 style="margin-top: 5px;">R$ {v['valor']:,.2f} ({v['pct']:.1f}%)</h4>
        <p style="font-size: 0.8rem; margin-top: 10px;">{v['dica']}</p>
    </div>
    """, unsafe_allow_html=True)

with col_ins2:
    h = intel['heroi']
    st.markdown(f"""
    <div class="hero-card">
        <div style="font-size: 3rem;">🦸</div>
        <h3 style="margin: 10px 0;">Herói do Mês</h3>
        <h2 style="color: #fbbf24; margin: 0;">{h['nome']}</h2>
        <p style="font-size: 0.9rem; margin-top: 15px;">{h['desc']}</p>
    </div>
    """, unsafe_allow_html=True)

with col_ins3:
    with st.container(border=True):
        st.markdown("### 🎯 Impacto nas Metas")
        if len(intel['impacto_metas']) > 0:
            st.write("Neste ritmo de economia:")
            for imp in intel['impacto_metas']:
                st.write(f"- **{imp['nome']}**: em ~{imp['meses']} meses.")
        else:
            st.info("Economize mais para ver projeções de suas metas!")
            
st.markdown("### 🧠 Insights Financeiros")
for ins in intel['insights']:
    st.info(ins)

st.divider()

# --- SEÇÃO 5: CONQUISTAS E RANKING ---
col_ach, col_rank = st.columns(2)
with col_ach:
    st.subheader("🏆 Conquistas")
    achievements.show_achievements(user_achievements)

with col_rank:
    st.subheader("🌍 Ranking Global")
    ranking.show_ranking(ranking_data, user_data["nome"])

st.divider()

# --- SEÇÃO 6: LOJA DE ITENS (Demonstrativo) ---
st.subheader("🛍️ Loja de Aventureiros")
st.write("Gaste suas moedas conquistadas em itens de personalização!")

c_loja1, c_loja2, c_loja3, c_loja4 = st.columns(4)

def render_shop_item(col, emoji, name, price):
    col.markdown(f"""
    <div class="shop-item">
        <div style="font-size: 3rem;">{emoji}</div>
        <div style="font-weight: bold; margin-top: 10px;">{name}</div>
        <div class="shop-price">🪙 {price}</div>
    </div>
    """, unsafe_allow_html=True)
    if col.button("Comprar", key=f"buy_{name}", use_container_width=True):
        if gamification_service.comprar_item(USER_ID, name, price):
            st.success(f"Você comprou: {name}!")
            st.rerun()
        else:
            st.error("Moedas insuficientes!")

render_shop_item(c_loja1, "👑", "Moldura Ouro", 1000)
render_shop_item(c_loja2, "🎩", "Chapéu Premium", 500)
render_shop_item(c_loja3, "⚡", "Avatar Neon", 800)
render_shop_item(c_loja4, "🔥", "Título Exclusivo", 1500)

st.divider()

# --- SEÇÃO 7: HISTÓRICO DE RECOMPENSAS ---
st.subheader("📜 Histórico de Recompensas")
hist_df = gamification_service.get_historico_recompensas(USER_ID)
if not hist_df.empty:
    for _, row in hist_df.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['data']}** - {row['missao_nome']}")
            st.markdown(f"<span style='color: #fbbf24; font-weight: bold;'>🪙 +{row['moedas']} moedas</span> &nbsp;|&nbsp; <span style='color: #10b981; font-weight: bold;'>⭐ +{row['xp']} XP</span>", unsafe_allow_html=True)
else:
    st.info("Complete missões para começar a ganhar recompensas!")

st.divider()

# --- SEÇÃO DE REGISTRO DE ATIVIDADE FINANCEIRA (Input) ---
with st.expander("📝 Registrar Nova Atividade Financeira", expanded=False):
    col_tipo, col_cat, col_val = st.columns(3)
    with col_tipo:
        tipo_mov = st.selectbox("Tipo", ["Receita", "Despesa"])
    with col_cat:
        if tipo_mov == "Receita":
            categorias = ["Salário", "Freelancer", "Investimentos", "Vendas", "Outros"]
        else:
            categorias = ["Alimentação", "Transporte", "Moradia", "Lazer", "Educação", "Saúde", "Delivery", "Compras", "Outros"]
        categoria = st.selectbox("Categoria", categorias)
    with col_val:
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f", step=10.0)

    col_data, col_desc = st.columns([1, 2])
    with col_data:
        data_mov = st.date_input("Data da Ocorrência")
    with col_desc:
        descricao = st.text_input("Descrição (Opcional)", placeholder="Ex: Conta de luz do mês")

    if st.button("Salvar Movimentação", type="primary", use_container_width=True):
        finance_service.adicionar_movimentacao(USER_ID, tipo_mov, categoria, valor, data_mov, descricao)
        st.success("✅ Movimentação salva com sucesso!")
        st.rerun()

st.divider()

# --- SEÇÃO 10: ADMINISTRAÇÃO E RESET ---
if 'confirm_reset' not in st.session_state:
    st.session_state.confirm_reset = False

if not st.session_state.confirm_reset:
    if st.button("🔄 Reiniciar Dados", type="secondary"):
        st.session_state.confirm_reset = True
        st.rerun()
    st.caption("Utilizado apenas para testes e demonstrações.")
else:
    with st.container(border=True):
        st.warning("⚠️ **TEM CERTEZA QUE DESEJA REINICIAR TODOS OS DADOS?**")
        col_cancel, col_confirm = st.columns(2)
        with col_cancel:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.confirm_reset = False
                st.rerun()
        with col_confirm:
            if st.button("Confirmar Reinicialização", type="primary", use_container_width=True):
                logs = reset_database()
                
                # Limpar toda a persistência do Streamlit
                chaves_removidas = list(st.session_state.keys())
                st.cache_data.clear()
                st.cache_resource.clear()
                st.session_state.clear()
                
                st.session_state.reset_success = True
                st.session_state.debug_logs = {**logs, "session_keys": len(chaves_removidas)}
                st.rerun()

if st.session_state.get('reset_success', False):
    st.success("✅ Dados reiniciados com sucesso.")
    if 'debug_logs' in st.session_state:
        logs = st.session_state.debug_logs
        st.info(f"🐛 **Logs de Depuração (Reset):**\n"
                f"- Tabelas de progresso limpas: {logs['tabelas_limpas']}\n"
                f"- Registros apagados: {logs['movs_removidas']} movimentações e {logs['metas_removidas']} metas\n"
                f"- Aportes de metas removidos: {logs['aportes_removidos']}\n"
                f"- Limpeza de Memória: cache_data, cache_resource\n"
                f"- Variáveis do session_state deletadas: {logs['session_keys']}")
        del st.session_state['debug_logs']
    st.session_state.reset_success = False
