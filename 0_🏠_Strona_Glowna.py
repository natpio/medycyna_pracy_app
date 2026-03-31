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

# Wstrzyknięcie stylów CSS z pliku style.css oraz ukrycie standardowych pasków
apply_pro_style()

# --- KOMPONENTY UI (PREMIUM HTML) ---

def render_premium_card(title, value, icon, badge_text, badge_color, badge_bg):
    """Generuje kartę statystyk w stylu Apple/SaaS."""
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
    """Generuje luksusową tabelę z pigułkami statusu."""
    if df.empty:
        st.info("Brak ostatnich aktywności.")
        return

    table_header = """
    <div class="custom-table-container">
        <table style="width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif;">
            <thead>
                <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Pacjent / Badanie</th>
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Data</th>
                    <th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;">Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    rows = ""
    for _, row in df.iterrows():
        # Kolory dla statusów
        status = row['Status']
        is_done = status == "Zakończona"
        bg = "#d1fae5" if is_done else "#fef3c7"
        txt = "#059669" if is_done else "#d97706"
        icon_bg = "#eff6ff" if is_done else "#fff7ed"
        icon_color = "#3b82f6" if is_done else "#f97316"
        
        rows += f"""
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
    
    footer = "</tbody></table></div>"
    st.markdown(table_header + rows + footer, unsafe_allow_html=True)

# --- LOGIKA DANYCH ---
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

# --- LAYOUT STRONY ---

# Nagłówek powitalny
st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-weight: 800; color: #0f172a; letter-spacing: -1.5px; margin-bottom: 0px;">Dashboard</h1>
        <p style="color: #64748b; font-size: 1.1rem; font-weight: 500;">Witaj w panelu dowodzenia systemem Medycyny Pracy.</p>
    </div>
""", unsafe_allow_html=True)

# GÓRNE KARTY (KPI)
col1, col2, col3 = st.columns(3)

with col1:
    render_premium_card("Pacjenci", str(len(df_pacjenci)), "👥", "Aktywni", "#059669", "#d1fae5")
with col2:
    render_premium_card("Firmy", str(len(df_firmy)), "🏢", "Kontrakty", "#2563eb", "#dbeafe")
with col3:
    # Obliczamy wizyty na dziś
    dzis = str(pd.Timestamp.today().date())
    wizyty_dzis = len(df_wizyty[df_wizyty['DataWizyty'] == dzis]) if not df_wizyty.empty else 0
    render_premium_card("Wizyty na dziś", str(wizyty_dzis), "📅", "Oczekujące", "#ea580c", "#ffedd5")

st.markdown("<br>", unsafe_allow_html=True)

# SEKCJA DOLNA: TABELA I KALENDARZ (SZYBKI PODGLĄD)
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1rem;'>Ostatnio zarejestrowane wizyty</h4>", unsafe_allow_html=True)
    if not df_wizyty.empty:
        # Pokazujemy 6 ostatnich wizyt
        latest_viz = df_wizyty.tail(6).iloc[::-1]
        render_activity_table(latest_viz)
    else:
        st.info("Baza wizyt jest pusta.")

with col_right:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1rem;'>Szybkie akcje</h4>", unsafe_allow_html=True)
    
    # Eleganckie przyciski nawigacyjne w kolumnie
    if st.button("➕ Nowy Pacjent", use_container_width=True):
        st.switch_page("pages/1_👤_Rejestracja_Pacjenta.py")
    
    if st.button("📅 Zaplanuj Wizytę", use_container_width=True):
        st.switch_page("pages/2_📅_Nowa_Wizyta.py")
        
    st.markdown("---")
    st.caption("MedycynaPracy OS v2.1 | Wersja Autoryzowana")
