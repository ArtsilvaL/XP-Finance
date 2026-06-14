import streamlit as st

def show_missions(missions: list):
    """Exibe os cards de missões com barras de progresso."""
    semanais = [m for m in missions if m['tipo'] == 'Semanal']
    mensais = [m for m in missions if m['tipo'] == 'Mensal']
    
    st.markdown("#### 📅 Semanais")
    for m in semanais:
        render_mission(m)
        
    st.markdown("#### 🗓️ Mensais")
    for m in mensais:
        render_mission(m)

def render_mission(mission):
    current_progress_value = max(0, mission["progresso"])
    progresso_percent = min(1.0, current_progress_value / mission["objetivo"]) if mission["objetivo"] > 0 else 1.0
    
    st.write(f"{mission['icone']} **{mission['nome']}**")
    st.caption(f"Recompensa: 🪙 {mission['moedas']} moedas | ⭐ {mission['xp']} XP")
    
    if mission['concluida']:
        st.success("Missão Concluída! 🎉")
    else:
        if "delivery" in mission['nome'].lower():
            text = "Sem gastos com delivery!" if current_progress_value == 1 else "Gasto registrado com delivery."
            st.progress(progresso_percent, text=text)
        else:
            text = f"R$ {mission['progresso']:.2f} / R$ {mission['objetivo']:.2f}" if "R$" in mission['nome'] else f"{int(mission['progresso'])} / {mission['objetivo']}"
            st.progress(progresso_percent, text=text)
            
    st.empty()