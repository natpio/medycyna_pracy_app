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

# Wstrzyknięcie stylów CSS i usunięcie standardowych elementów Streamlit
apply_pro_style()

# --- PASEK BOCZNY (SIDEBAR) Z LOGOTYPEM ---
with st.sidebar:
    # Przestrzeń na górze (Streamlit sam tu wstawi listę stron)
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # LOGO FIRMY NA DOLE SIDEBARU
    # Link prowadzi do Twojego repozytorium na GitHubie
    st.markdown(f"""
        <div class="sidebar-footer">
            <img src="https://raw.githubusercontent.com/natpio/medycyna_pracy_app/main/logo_firma.png" width="38" style="border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            <div class="footer-text">
                <b>MedycynaPracy OS</b><br>
                v2.1 | Premium Edition
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- KOMPONENTY PREMIUM UI (HTML/CSS) ---

def render_premium_card(title, value, icon, badge_text, badge_color, badge_bg):
    """Renderuje kartę statystyk (KPI) w stylu Apple/SaaS."""
    st.markdown(f"""
    <div class="premium-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span class="card-label">{title}</span>
            <div class="card-icon">{icon}</div>
        </div>
        <div class="card-value">{value}</div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: {badge_color}; background: {badge_bg}; padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;">
                {badge_text}
            </span>
            <span style="color: #94a3b8; font-size: 0.75rem; font-weight: 500;">Baza Live</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_activity_table(df):
    """Renderuje nowoczesną tabelę z pigułkami statusu (Naprawione wyświetlanie)."""
    if df is None or df.empty:
        st.markdown("<p style='color: #64748b; padding: 20px;'>Brak zarejestrowanych aktywności w systemie.</p>", unsafe_allow_html=True)
        return

    # Inicjalizacja HTML tabeli
    table_html = """
    <div class="custom-table-container">
        <table style="width: 100%; border-collapse: collapse; background: white;">
            <thead>
                <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Usługa / Pacjent</th>
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Termin</th>
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Dodawanie wierszy
    for _, row in df.iterrows():
        status = str(row['Status'])
        is_done = status == "Zakończona"
        
        # Kolory statusów
        bg = "#d1fae5" if is_done else "#fef3c7"
        txt = "#059669" if is_done else "#d97706"
        icon_bg = "#eff6ff" if is_done else "#fff7ed"
        icon_color = "#3b82f6" if is_done else "#f97316"
        
        # Pierwsza litera typu badania dla ikonki
        typ_badania = str(row['TypBadania'])
        pierwsza_litera = typ_badania[0] if typ_badania else "?"
        
        table_html += f"""
        <tr class="table-row" style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 16px; display: flex; align-items: center; gap: 12px;">
                <div style="width: 38px; height: 38px; background: {icon_bg}; color: {icon_color}; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem;">
                    {pierwsza_litera}
                </div>
                <div>
                    <div style="color: #0f172a; font-weight: 600; font-size: 0.9rem;">{typ_badania}</div>
                    <div style="color: #94a3b8; font-size: 0.72rem;">ID: {row.get('ID_Wizyty', '---')}</div>
                </div>
            </td>
            <td style="padding: 16px; color: #475569; font-size: 0.85rem; font-weight: 500;">{row['DataWizyty']}</td>
            <td style="padding: 16px;">
                <span style="background: {bg}; color: {txt}; padding: 5px 14px; border-radius: 8px; font-size: 0.72rem; font-weight: 700; display: inline-block;">
                    {status}
                </span>
            </td>
        </tr>
        """
    
    table_html += "</tbody></table></div>"
    
    # KLUCZOWE: Renderowanie HTML
    st.markdown(table_html, unsafe_allow_html=True)

# --- LOGIKA POBIERANIA DANYCH ---
try:
    df_wizyty = get_data_as_df("Wizyty")
    df_pacjenci = get_data_as_df("Pacjenci")
    df_firmy = get_data_as_df("Firmy")
except:
    df_wizyty = df_pacjenci = df_firmy = pd.DataFrame()

# --- GŁÓWNY INTERFEJS (DASHBOARD) ---

# 1. Nagłówek dynamiczny
st.markdown("""
    <div style="margin-bottom: 2.5rem;">
        <h1 style="font-weight: 800; color: #0f172a; letter-spacing: -1.8px; margin-bottom: 4px; font-size: 2.8rem;">Dashboard</h1>
        <p style="color: #64748b; font-size: 1.15rem; font-weight: 500;">System Zarządzania Placówką Medycyny Pracy</p>
    </div>
""", unsafe_allow_html=True)

# 2. Górny rząd: Karty KPI (3 kolumny)
col1, col2, col3 = st.columns(3)

with col1:
    render_premium_card("Baza Pacjentów", str(len(df_pacjenci)), "👥", "Aktywni", "#059669", "#d1fae5")
with col2:
    render_premium_card("Kontrahenci", str(len(df_firmy)), "🏢", "Firmy", "#2563eb", "#dbeafe")
with col3:
    dzis = str(pd.Timestamp.today().date())
    wizyty_dzis = len(df_wizyty[df_wizyty['DataWizyty'].astype(str) == dzis]) if not df_wizyty.empty else 0
    render_premium_card("Dzisiejsze Wizyty", str(wizyty_dzis), "📅", "Oczekujące", "#ea580c", "#ffedd5")

st.markdown("<br>", unsafe_allow_html=True)

# 3. Dolny rząd: Tabela Aktywności i Szybkie Akcje
col_left, col_right = st.columns([2.2, 1])

with col_left:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem; letter-spacing: -0.5px;'>Ostatnio zarejestrowane zdarzenia</h4>", unsafe_allow_html=True)
    if not df_wizyty.empty:
        # Sortujemy od najnowszych i bierzemy 6 rekordów
        render_activity_table(df_wizyty.tail(6).iloc[::-1])
    else:
        st.info("Brak aktywności do wyświetlenia.")

with col_right:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem; letter-spacing: -0.5px;'>Nawigacja ekspresowa</h4>", unsafe_allow_html=True)
    
    # Szybkie skróty do podstron
    if st.button("➕ Zarejestruj Nowego Pacjenta", use_container_width=True):
        st.switch_page("pages/1_👤_Rejestracja_Pacjenta.py")
        
    if st.button("📅 Umów wizytę profilaktyczną", use_container_width=True):
        st.switch_page("pages/2_📅_Nowa_Wizyta.py")
        
    if st.button("💰 Rozliczenia z kontrahentami", use_container_width=True):
        st.switch_page("pages/6_💰_Raporty_i_Finanse.py")

    st.markdown("---")
    
    # Estetyczny box informacyjny
    st.markdown("""
        <div style="background: #eff6ff; padding: 20px; border-radius: 16px; border: 1px solid #dbeafe; box-shadow: 0 2px 4px rgba(37,99,235,0.05);">
            <p style="margin: 0; font-size: 0.82rem; color: #1e40af; line-height: 1.5;">
                💡 <b>System zautoryzowany:</b><br>
                Zabezpieczone połączenie z bazą Google Cloud oraz modułem generowania orzeczeń SHA-256.
            </p>
        </div>
    """, unsafe_allow_html=True)
