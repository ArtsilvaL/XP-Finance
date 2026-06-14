import streamlit as st
import pandas as pd

def show_ranking(ranking_df: pd.DataFrame, current_user: str):
    """Exibe o ranking, destacando o usuário atual."""

    html = '<div style="background: #1e293b; padding: 15px; border-radius: 15px; border: 1px solid #334155; display: flex; flex-direction: column; gap: 10px;">'
    
    for idx, row in ranking_df.iterrows():
        is_current = row['Usuário'] == current_user
        
        if is_current:
            style = "background: #3b0764; border: 2px solid #a855f7; box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);"
        else:
            style = "background: #0f172a; border: 1px solid #334155;"
            
        medal = row.name if isinstance(row.name, str) else f"{idx+1}º"
        
        html += (
            f'<div style="{style} padding: 12px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">'
            f'<div style="display: flex; align-items: center; gap: 15px;">'
            f'<span style="font-size: 1.2rem; font-weight: bold; color: #fbbf24;">{medal}</span>'
            f'<span style="font-size: 1.5rem;">👤</span>'
            f'<span style="font-weight: bold; color: white;">{row["Usuário"]}</span>'
            f'</div>'
            f'<span style="color: #10b981; font-weight: bold; font-size: 1.1rem;">R$ {row["Economia (R$)"]:,.2f}</span>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)