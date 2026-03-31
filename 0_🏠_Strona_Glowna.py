import streamlit as st
import pandas as pd
from db_service import get_data_as_df, apply_pro_style

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Gabinet Medycyny Pracy", page_icon="🏥", layout="wide")
apply_pro_style()

# --- FUNKCJA GENERUJĄCA KARTY PREMIUM ---
def premium_card(title, value, icon, badge_text, badge_color, badge_bg):
    html = f"""
    <div class="premium-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span class="card-label">{title}</span>
            <span class="card-icon">{icon}</span>
        </div>
        <div class="card-value">{value}</div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: {badge_color}; background: {badge_bg}; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">{badge_text}</span>
            <span style="color: #94a3b8; font-size: 0.8rem;">Statystyka bazy</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- FUNKCJA GENERUJĄCA TABELĘ PREMIUM (HTML) ---
def render_custom_table(df):
    if df.empty:
        return "<p style='color: #64748b;'>Brak danych do wyświetlenia.</p>"
    
    table_html = """
    <div style="overflow-x: auto; border-radius: 16px; border: 1px solid #e2e8f0; background: white;">
        <table style="width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif;">
            <thead>
                <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <th style="padding: 16px; text-align: left; color: #64748b; font-size: 0.75rem; text-transform: uppercase;">Pacjent</th>
                    <th style="padding: 16px; text-align: left; color: #64748b; font-size: 0.75rem; text-transform: uppercase;">Rodzaj Badania</th>
                    <th style="padding: 16px; text-align: left; color: #64748b; font-size: 0.75rem; text-transform: uppercase;">Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df.iterrows():
        # Logika kolorów statusu
        status = row['Status']
        status_bg = "#d1fae5" if status == "Zakończona" else "#fef3c7"
        status_color = "#059669" if status == "Zakończona" else "#d97706"
        
        table_html += f"""
        <tr class="table-row" style="border-bottom: 1px solid #f1f5f9; transition: background 0.2s;">
            <td style="padding: 16px; display: flex; align-items: center; gap: 12px;">
                <div style="width: 32px; height: 32px; background: #eff6ff; color: #2563eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem;">
                    {row['TypBadania'][0]}
                </div>
                <span style="color: #0f172a; font-weight: 500;">{row['TypBadania']}</span>
            </td>
            <td style="padding: 16px; color: #64748b; font-size: 0.875rem;">{row['DataWizyty']}</td>
            <td style="padding: 16px;">
                <span style="background: {status_bg}; color: {status_color}; padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">
                    {status}
                </span>
            </td>
        </tr>
        """
    
    table_html += "</tbody></table></div>"
    return table_html

# --- DANE ---
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

# --- UI ---
st.markdown("<h2 style='font-weight: 800; color: #0f172a; margin-bottom: 0;'>Panel Zarządzania</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; margin-bottom: 2rem;'>Przegląd operacyjny gabinetu medycyny pracy.</p>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    premium_card("Pacjenci", str(len(df_pacjenci)), "👥", "Aktywni", "#059669", "#d1fae5")
with c2:
    premium_card("Firmy", str(len(df_firmy)), "🏢", "Kontrakty", "#2563eb", "#dbeafe")
with c3:
    premium_card("Oczekujący", "3", "⏳", "Na dziś", "#d97706", "#fef3c7")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1rem;'>Ostatnie wizyty</h4>", unsafe_allow_html=True)

# Wyświetlamy naszą luksusową tabelę
if not df_wizyty.empty:
    st.markdown(render_custom_table(df_wizyty.tail(5)), unsafe_allow_html=True)
else:
    st.info("Brak aktywności.")
