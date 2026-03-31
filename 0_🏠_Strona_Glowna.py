import streamlit as st
import pandas as pd
from db_service import get_data_as_df, apply_pro_style

# --- 1. KONFIGURACJA ---
st.set_page_config(
    page_title="Gabinet Medycyny Pracy", 
    page_icon="🏥", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Wstrzyknięcie CSS (style.css musi być w głównym katalogu)
apply_pro_style()

# --- 2. SIDEBAR (LOGO GÓRA I DÓŁ) ---
with st.sidebar:
    # LOGO JAREK2 - GÓRA
    st.markdown('''
    <div class="logo-top-container">
        <img src="https://raw.githubusercontent.com/natpio/medycyna_pracy_app/main/logo_jarek2.png" width="200">
    </div>
    ''', unsafe_allow_html=True)
    
    # Przekładka, by menu zaczęło się w dobrym miejscu
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # LOGO TWÓRCÓW - DÓŁ
    st.markdown('''
    <div class="sidebar-footer">
        <img src="https://raw.githubusercontent.com/natpio/medycyna_pracy_app/main/logo_firma.png" width="35" style="border-radius: 6px;">
        <div style="color: white; font-size: 0.75rem; line-height: 1.2;">
            <b style="letter-spacing: 0.5px;">MedycynaPracy OS</b><br>
            <span style="opacity: 0.6;">v2.1 | Premium Edition</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- 3. KOMPONENTY RENDERUJĄCE (HTML) ---

def render_premium_card(title, value, icon, badge_text, badge_color, badge_bg):
    """Generuje luksusową kartę KPI."""
    st.markdown(f'''
    <div class="premium-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span class="card-label">{title}</span>
            <div style="background: #f1f5f9; padding: 10px; border-radius: 12px; font-size: 1.25rem;">{icon}</div>
        </div>
        <div style="color: #0f172a; font-size: 2.5rem; font-weight: 800; margin: 12px 0; letter-spacing: -1px;">{value}</div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: {badge_color}; background: {badge_bg}; padding: 4px 12px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase;">
                {badge_text}
            </span>
            <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 500;">Synchronizacja OK</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def render_activity_table(df):
    """Renderuje luksusową tabelę. WAŻNE: Płaski HTML bez wcięć zapobiega błędom Streamlit."""
    if df is None or df.empty:
        st.info("Brak aktywności do wyświetlenia.")
        return

    html = '<div class="custom-table-container"><table style="width:100%;border-collapse:collapse;background:white;">'
    html += '<thead><tr style="background:#f8fafc;border-bottom:1px solid #e2e8f0;">'
    html += '<th style="padding:18px;text-align:left;color:#64748b;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Usługa / Pacjent</th>'
    html += '<th style="padding:18px;text-align:left;color:#64748b;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Termin</th>'
    html += '<th style="padding:18px;text-align:left;color:#64748b;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;">Status</th>'
    html += '</tr></thead><tbody>'

    for _, row in df.iterrows():
        status = str(row['Status'])
        is_done = (status == "Zakończona")
        bg, txt = ("#d1fae5", "#059669") if is_done else ("#fef3c7", "#d97706")
        icon_bg, icon_color = ("#eff6ff", "#3b82f6") if is_done else ("#fff7ed", "#f97316")
        typ = str(row['TypBadania'])
        litera = typ[0] if typ else "?"
        
        html += f'<tr class="table-row" style="border-bottom:1px solid #f1f5f9;">'
        html += f'<td style="padding:16px;display:flex;align-items:center;gap:12px;">'
        html += f'<div style="width:38px;height:38px;background:{icon_bg};color:{icon_color};border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;">{litera}</div>'
        html += f'<div><div style="color:#0f172a;font-weight:600;font-size:0.9rem;">{typ}</div><div style="color:#94a3b8;font-size:0.72rem;">ID: {row.get("ID_Wizyty", "---")}</div></div></td>'
        html += f'<td style="padding:16px;color:#475569;font-size:0.85rem;font-weight:500;">{row["DataWizyty"]}</td>'
        html += f'<td style="padding:16px;"><span style="background:{bg};color:{txt};padding:5px 14px;border-radius:8px;font-size:0.72rem;font-weight:700;display:inline-block;">{status}</span></td></tr>'

    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 4. LOGIKA DANYCH ---
try:
    df_wizyty = get_data_as_df("Wizyty")
    df_pacjenci = get_data_as_df("Pacjenci")
    df_firmy = get_data_as_df("Firmy")
except Exception as e:
    st.error(f"Problem z połączeniem: {e}")
    df_wizyty = df_pacjenci = df_firmy = pd.DataFrame()

# --- 5. GŁÓWNY LAYOUT ---

# Nagłówek
st.markdown('''
<div style="margin-bottom: 2.5rem;">
    <h1 style="font-weight: 800; color: #0f172a; letter-spacing: -1.8px; margin-bottom: 4px; font-size: 2.8rem;">Dashboard</h1>
    <p style="color: #64748b; font-size: 1.15rem; font-weight: 500;">System Operacyjny Gabinetu Medycyny Pracy</p>
</div>
''', unsafe_allow_html=True)

# Karty statystyk
c1, c2, c3 = st.columns(3)

with c1:
    render_premium_card("Baza Pacjentów", str(len(df_pacjenci)), "👥", "Aktywni", "#059669", "#d1fae5")

with c2:
    render_premium_card("Kontrakty", str(len(df_firmy)), "🏢", "Firmy", "#2563eb", "#dbeafe")

with c3:
    dzis = str(pd.Timestamp.today().date())
    wiz_dzis = len(df_wizyty[df_wizyty['DataWizyty'].astype(str) == dzis]) if not df_wizyty.empty else 0
    render_premium_card("Wizyty na dziś", str(wiz_dzis), "📅", "Oczekujące", "#ea580c", "#ffedd5")

st.markdown("<br>", unsafe_allow_html=True)

# Sekcja aktywności i akcji
col_main, col_side = st.columns([2.3, 1])

with col_main:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Ostatnie zdarzenia w systemie</h4>", unsafe_allow_html=True)
    if not df_wizyty.empty:
        # Pokaż 6 ostatnich wizyt
        render_activity_table(df_wizyty.tail(6).iloc[::-1])
    else:
        st.info("System jest gotowy. Brak zarejestrowanych wizyt w bazie.")

with col_side:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Szybka nawigacja</h4>", unsafe_allow_html=True)
    
    # Przyciski akcji
    if st.button("➕ Zarejestruj Pacjenta", use_container_width=True):
        st.switch_page("pages/1_👤_Rejestracja_Pacjenta.py")
        
    if st.button("📅 Zaplanuj Nową Wizytę", use_container_width=True):
        st.switch_page("pages/2_📅_Nowa_Wizyta.py")
        
    if st.button("📊 Finanse i Raporty", use_container_width=True):
        st.switch_page("pages/6_💰_Raporty_i_Finanse.py")
        
    st.markdown("---")
    
    # Widget statusu
    st.markdown('''
    <div style="background: #eff6ff; padding: 20px; border-radius: 16px; border: 1px solid #dbeafe;">
        <p style="margin: 0; font-size: 0.85rem; color: #1e40af; line-height: 1.6;">
            💡 <b>Wskazówka:</b><br>
            Panel Lekarza oraz Historia Pacjenta zostały przeniesione do sekcji medycznej na dole menu bocznego.
        </p>
    </div>
    ''', unsafe_allow_html=True)
