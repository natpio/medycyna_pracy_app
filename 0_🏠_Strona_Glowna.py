import streamlit as st
import pandas as pd
from db_service import get_data_as_df, apply_pro_style

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Gabinet Medycyny Pracy", 
    page_icon="🏥", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Wstrzyknięcie stylów CSS i usunięcie standardowych elementów wizualnych
apply_pro_style()

# --- PASEK BOCZNY (SIDEBAR) Z LOGOTYPEM ---
with st.sidebar:
    # Wolna przestrzeń na górze (menu stron wygeneruje się tu automatycznie)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # KONTENER NA LOGO FIRMY (Zaszyty na dole dzięki klasie w CSS)
    # UWAGA: Podmień 'TWOJA_NAZWA_UZYTKOWNIKA' na swoją nazwę na GitHubie
    st.markdown(f"""
        <div class="sidebar-footer">
            <img src="https://raw.githubusercontent.com/natpio/medycyna_pracy_app/main/logo_firma.png" width="35" style="border-radius: 6px;">
            <div class="footer-text">
                <b>MedycynaPracy OS</b><br>
                v2.1 | Premium Edition
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- KOMPONENTY PREMIUM (HTML/CSS INJECTION) ---

def render_premium_card(title, value, icon, badge_text, badge_color, badge_bg):
    """Renderuje nowoczesną kartę statystyk."""
    st.markdown(f"""
    <div class="premium-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span class="card-label">{title}</span>
            <div class="card-icon">{icon}</div>
        </div>
        <div class="card-value">{value}</div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: {badge_color}; background: {badge_bg}; padding: 4px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase;">
                {badge_text}
            </span>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 500;">Baza Live</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_activity_table(df):
    """Renderuje tabelę z 'pigułkami' statusu."""
    if df.empty:
        st.markdown("<p style='color: #64748b;'>Brak danych o wizytach.</p>", unsafe_allow_html=True)
        return

    table_html = """
    <div class="custom-table-container">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Badanie / Pacjent</th>
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Termin</th>
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for _, row in df.iterrows():
        status = row['Status']
        is_done = status == "Zakończona"
        bg = "#d1fae5" if is_done else "#fef3c7"
        txt = "#059669" if is_done else "#d97706"
        icon_bg = "#eff6ff" if is_done else "#fff7ed"
        icon_color = "#3b82f6" if is_done else "#f97316"
        
        table_html += f"""
        <tr class="table-row" style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 16px; display: flex; align-items: center; gap: 12px;">
                <div style="width: 36px; height: 36px; background: {icon_bg}; color: {icon_color}; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.8rem;">
                    {row['TypBadania'][0]}
                </div>
                <div>
                    <div style="color: #0f172a; font-weight: 600; font-size: 0.9rem;">{row['TypBadania']}</div>
                    <div style="color: #94a3b8; font-size: 0.75rem;">ID: {row.get('ID_Wizyty', '---')}</div>
                </div>
            </td>
            <td style="padding: 16px; color: #475569; font-size: 0.85rem; font-weight: 500;">{row['DataWizyty']}</td>
            <td style="padding: 16px;">
                <span style="background: {bg}; color: {txt}; padding: 5px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 700;">
                    {status}
                </span>
            </td>
        </tr>
        """
    
    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)

# --- POBIERANIE DANYCH ---
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

# --- WIDOK GŁÓWNY (DASHBOARD) ---

st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-weight: 800; color: #0f172a; letter-spacing: -1.5px; margin-bottom: 0px;">Dashboard</h1>
        <p style="color: #64748b; font-size: 1.1rem; font-weight: 500;">Zarządzanie operacyjne gabinetem medycyny pracy.</p>
    </div>
""", unsafe_allow_html=True)

# 1. Górny rząd: Karty KPI
c1, c2, c3 = st.columns(3)

with c1:
    render_premium_card("Pacjenci", str(len(df_pacjenci)), "👥", "Aktywni", "#059669", "#d1fae5")
with c2:
    render_premium_card("Firmy", str(len(df_firmy)), "🏢", "Kontrakty", "#2563eb", "#dbeafe")
with c3:
    dzis = str(pd.Timestamp.today().date())
    wizyty_dzis = len(df_wizyty[df_wizyty['DataWizyty'] == dzis]) if not df_wizyty.empty else 0
    render_premium_card("Wizyty na dziś", str(wizyty_dzis), "📅", "Oczekujące", "#ea580c", "#ffedd5")

st.markdown("<br>", unsafe_allow_html=True)

# 2. Dolny rząd: Tabela i Szybkie akcje
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Ostatnie aktywności</h4>", unsafe_allow_html=True)
    if not df_wizyty.empty:
        # Odwracamy kolejność, aby najnowsze były na górze
        render_activity_table(df_wizyty.tail(6).iloc[::-1])
    else:
        st.info("Nie zarejestrowano jeszcze żadnych wizyt.")

with col_right:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Szybkie akcje</h4>", unsafe_allow_html=True)
    
    # Przyciski kierujące do najważniejszych modułów
    if st.button("➕ Nowy Pacjent", use_container_width=True):
        st.switch_page("pages/1_👤_Rejestracja_Pacjenta.py")
        
    if st.button("📅 Zaplanuj Wizytę", use_container_width=True):
        st.switch_page("pages/2_📅_Nowa_Wizyta.py")
        
    if st.button("📊 Raport Miesięczny", use_container_width=True):
        st.switch_page("pages/6_💰_Raporty_i_Finanse.py")

    st.markdown("---")
    st.markdown("""
        <div style="background: #eff6ff; padding: 15px; border-radius: 12px; border: 1px solid #dbeafe;">
            <p style="margin: 0; font-size: 0.8rem; color: #1e40af;">
                💡 <b>Podpowiedź:</b> Panel Lekarza i Historia zostały przeniesione na dół menu bocznego dla Twojej wygody.
            </p>
        </div>
    """, unsafe_allow_html=True)
