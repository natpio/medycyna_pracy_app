import streamlit as st
import pandas as pd
from datetime import datetime
from db_service import get_data_as_df, apply_pro_style

# --- 1. KONFIGURACJA ---
st.set_page_config(
    page_title="Gabinet Medycyny Pracy", 
    page_icon="🏥", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Wstrzyknięcie stylów CSS oraz automatyczne ładowanie Logo i Stopki VORTEZA
apply_pro_style()

# --- 2. KOMPONENTY PREMIUM UI ---

def render_premium_card(title, value, icon, badge_text, badge_color, badge_bg):
    """Renderuje karty statystyk (KPI)."""
    card_html = f"""
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
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 500;">Baza Live</span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_activity_table(df):
    """Renderuje tabelę aktywności - wersja 'Bulletproof'."""
    if df is None or df.empty:
        st.markdown("<p style='color: #64748b; padding: 20px;'>Brak nadchodzących wizyt.</p>", unsafe_allow_html=True)
        return

    # Nagłówek tabeli
    html = '<div class="custom-table-container"><table style="width: 100%; border-collapse: collapse; background: white;">'
    html += '<thead><tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">'
    html += '<th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase;">Badanie / Status</th>'
    html += '<th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase;">Termin</th>'
    html += '<th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase;">Status</th>'
    html += '</tr></thead><tbody>'

    # Wiersze
    for _, row in df.iterrows():
        status = str(row['Status'])
        is_done = (status == "Zakończona")
        bg, txt = ("#d1fae5", "#059669") if is_done else ("#fef3c7", "#d97706")
        icon_bg, icon_color = ("#eff6ff", "#3b82f6") if is_done else ("#fff7ed", "#f97316")
        
        typ = str(row['TypBadania'])
        litera = typ[0] if typ else "?"
        
        row_html = f"""
        <tr class="table-row" style="border-bottom: 1px solid #f1f5f9; {'opacity: 0.6;' if is_done else ''}">
            <td style="padding: 16px; display: flex; align-items: center; gap: 12px;">
                <div style="width: 38px; height: 38px; background: {icon_bg}; color: {icon_color}; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem;">{litera}</div>
                <div>
                    <div style="color: #0f172a; font-weight: 600; font-size: 0.9rem;">{typ}</div>
                    <div style="color: #94a3b8; font-size: 0.72rem;">ID: {str(row.get('ID_Wizyty', '---'))[-6:]}</div>
                </div>
            </td>
            <td style="padding: 16px; color: #475569; font-size: 0.85rem; font-weight: 600;">{row['DataWizyty']}</td>
            <td style="padding: 16px;">
                <span style="background: {bg}; color: {txt}; padding: 5px 14px; border-radius: 8px; font-size: 0.72rem; font-weight: 700; display: inline-block;">{status}</span>
            </td>
        </tr>
        """
        html += row_html.replace('\n', '').strip()

    html += '</tbody></table></div>'
    st.write(html, unsafe_allow_html=True)

# --- 3. LOGIKA POBIERANIA DANYCH I INTELIGENTNE FILTROWANIE ---
try:
    df_wizyty = get_data_as_df("Wizyty")
    df_pacjenci = get_data_as_df("Pacjenci")
    df_firmy = get_data_as_df("Firmy")
except:
    df_wizyty = pd.DataFrame(columns=['DataWizyty', 'TypBadania', 'Status'])
    df_pacjenci = df_firmy = pd.DataFrame()

# Ustalenie dzisiejszej daty z uwzględnieniem strefy czasowej w chmurze
dzis = pd.Timestamp.today(tz='Europe/Warsaw').date()
wiz_dzis = 0
df_do_tabeli = pd.DataFrame()

if not df_wizyty.empty:
    # Bezpieczna konwersja dat wizyt do formatu pozwalającego na matematykę (porównania)
    df_wizyty['DataWizyty_dt'] = pd.to_datetime(df_wizyty['DataWizyty'], errors='coerce').dt.date

    # KPI: Obliczamy ile wizyt jest zaplanowanych na dzisiaj (wszystkie statusy)
    wiz_dzis = len(df_wizyty[df_wizyty['DataWizyty_dt'] == dzis])

    # FILTROWANIE OPERACYJNE (Inteligentny Radar)
    # Warunek 1: Pokaż Zaplanowane na dzisiaj i w przyszłości
    mask_zaplanowane = (df_wizyty['Status'] == 'Zaplanowana') & (df_wizyty['DataWizyty_dt'] >= dzis)
    # Warunek 2: Pokaż Zakończone, ale TYLKO z dzisiaj
    mask_zakonczone_dzis = (df_wizyty['Status'] == 'Zakończona') & (df_wizyty['DataWizyty_dt'] == dzis)

    df_do_tabeli = df_wizyty[mask_zaplanowane | mask_zakonczone_dzis].copy()

    if not df_do_tabeli.empty:
        # Sortowanie: najpierw data, potem status odwrotnie alfabetycznie (Z-aplanowana wyżej niż Z-akończona)
        df_do_tabeli = df_do_tabeli.sort_values(by=['DataWizyty_dt', 'Status'], ascending=[True, False]).head(8)

# --- 4. WIDOK GŁÓWNY ---

# Nagłówek Dashboardu
st.markdown("""
    <div style="margin-bottom: 2.5rem;">
        <h1 style="font-weight: 800; color: #0f172a; letter-spacing: -1.8px; margin-bottom: 4px; font-size: 2.8rem;">Dashboard</h1>
        <p style="color: #64748b; font-size: 1.15rem; font-weight: 500;">Medycyna Pracy | Panel Zarządzania</p>
    </div>
""", unsafe_allow_html=True)

# Górne karty KPI
c1, c2, c3 = st.columns(3)
with c1:
    render_premium_card("Pacjenci", str(len(df_pacjenci)), "👥", "Aktywni", "#059669", "#d1fae5")
with c2:
    render_premium_card("Firmy", str(len(df_firmy)), "🏢", "Kontrakty", "#2563eb", "#dbeafe")
with c3:
    render_premium_card("Wizyty na dziś", str(wiz_dzis), "📅", "Dzisiaj", "#ea580c", "#ffedd5")

st.markdown("<br>", unsafe_allow_html=True)

# Dolna sekcja: Tabela i Szybkie Akcje
col_l, col_r = st.columns([2.2, 1])

with col_l:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Wizyty operacyjne (od dziś)</h4>", unsafe_allow_html=True)
    if not df_do_tabeli.empty:
        render_activity_table(df_do_tabeli)
    else:
        st.info("Brak aktywnych wizyt na dziś i nadchodzące dni. Mamy wolne!")

with col_r:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Szybkie akcje</h4>", unsafe_allow_html=True)
    if st.button("➕ Nowy Pacjent", use_container_width=True):
        st.switch_page("pages/1_👤_Rejestracja_Pacjenta.py")
    if st.button("📅 Zaplanuj Wizytę", use_container_width=True):
        st.switch_page("pages/2_📅_Nowa_Wizyta.py")
    if st.button("💰 Raport Miesięczny", use_container_width=True):
        st.switch_page("pages/6_💰_Raporty_i_Finanse.py")
    
    st.markdown("---")
    st.markdown("""
        <div style="background: #eff6ff; padding: 20px; border-radius: 16px; border: 1px solid #dbeafe;">
            <p style="margin: 0; font-size: 0.82rem; color: #1e40af; line-height: 1.5;">
                💡 <b>System zautoryzowany:</b><br>Zabezpieczone połączenie z bazą i modułem orzeczeń.
            </p>
        </div>
    """, unsafe_allow_html=True)
