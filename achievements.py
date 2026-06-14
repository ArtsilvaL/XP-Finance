import streamlit as st

def show_achievements(achievements: list):
    """Exibe as conquistas em formato de grade."""
    
    unlocked = [a for a in achievements if a['desbloqueada']]
    locked = [a for a in achievements if not a['desbloqueada']]

    html_content = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
    for a in unlocked:
        html_content += (
            f'<div class="achievement-badge rarity-{a["raridade"]}">'
            f'<div style="font-size: 1.5rem;">{a["icone"]}</div>'
            f'<div style="font-size: 0.85rem; font-weight: bold; margin-top: 8px;">{a["nome"]}</div>'
            f'<div style="font-size: 0.65rem; margin-top: 4px; opacity: 0.8; letter-spacing: 1px;">{str(a["raridade"]).upper()}</div>'
            '</div>'
        )
    html_content += '</div>'
    st.markdown(html_content, unsafe_allow_html=True)

    with st.expander("Ver conquistas bloqueadas"):
        for a in locked:
            st.write(f"❓ {a['nome']}")