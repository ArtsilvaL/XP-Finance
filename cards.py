import streamlit as st

def show_gamified_stats(receitas, despesas, economia, moedas, xp):
    """Exibe os cards de estatísticas gamificadas do jogador."""
    col1, col2, col3, col4, col5 = st.columns(5)

    def make_card(icon, title, value, desc):
        return f"""
        <div class="stat-card" style="padding: 15px;">
            <div style="font-size: 1.8rem;">{icon}</div>
            <div style="font-size: 1.2rem; font-weight: bold; margin: 5px 0;">{value}</div>
            <div style="color: #94a3b8; font-size: 0.8rem;">{title}</div>
            <div style="color: #fbbf24; font-size: 0.75rem; margin-top: 5px;">{desc}</div>
        </div>
        """

    economia_str = f"R$ {economia:,.2f}" if economia >= 0 else "Sem economia"

    col1.markdown(make_card("💰", "Receitas", f"R$ {receitas:,.0f}", "Entradas"), unsafe_allow_html=True)
    col2.markdown(make_card("💸", "Despesas", f"R$ {despesas:,.0f}", "Saídas"), unsafe_allow_html=True)
    col3.markdown(make_card("📈", "Economia Real", economia_str, "O que sobrou"), unsafe_allow_html=True)
    col4.markdown(make_card("🪙", "Moedas", moedas, "Saldo na loja"), unsafe_allow_html=True)
    col5.markdown(make_card("⭐", "XP Total", xp, "Experiência"), unsafe_allow_html=True)