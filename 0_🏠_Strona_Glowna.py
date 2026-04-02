import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import pyotp
import uuid
import time
import extra_streamlit_components as esc
from db_service import (
    get_data_as_df, apply_pro_style, add_note_to_db, 
    check_trusted_device, add_trusted_device
)

# --- 1. KONFIGURACJA ---
st.set_page_config(
    page_title="Gabinet Medycyny Pracy", 
    page_icon="🏥", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Wstrzyknięcie stylów CSS oraz automatyczne ładowanie Logo i Stopki VORTEZA
apply_pro_style()

# --- INICJALIZACJA COOKIE MANAGERA ---
cookie_manager = esc.CookieManager()

# --- SYSTEM LOGOWANIA I WERYFIKACJI URZĄDZENIA ---
def render_login_screen():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h1 style='font-weight: 800; color: #1e3a8a; margin-bottom: 0;'>System Zabezpieczony</h1>
                <p style='color: #64748b; font-size: 0.9rem;'>Zaloguj się przy użyciu Google Authenticator</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            with st.form("login_form"):
                st.markdown("<div style='text-align: center; font-size: 3rem; margin-bottom: 10px;'>🔒</div>", unsafe_allow_html=True)
                
                kod_2fa = st.text_input("Wprowadź 6-cyfrowy kod z aplikacji:", max_chars=6)
                zapamietaj = st.checkbox("Zapamiętaj to urządzenie przez 30 dni", value=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                zaloguj = st.form_submit_button("Odblokuj system", type="primary", use_container_width=True)
                
                if zaloguj:
                    try:
                        secret = st.secrets["doctor"]["totp_secret"]
                        totp = pyotp.TOTP(secret)
                        
                        if totp.verify(kod_2fa):
                            st.success("✅ Autoryzacja pomyślna! Odblokowywanie...")
                            if zapamietaj:
                                new_token = str(uuid.uuid4())
                                add_trusted_device(new_token)
                                cookie_manager.set("vorteza_auth_token", new_token, expires_at=datetime.now() + timedelta(days=30))
                            else:
                                st.session_state['temp_logged_in'] = True
                                
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("❌ Nieprawidłowy kod. Spróbuj ponownie.")
                    except KeyError:
                        st.error("⚠️ Błąd krytyczny: Brak klucza 'totp_secret' w pliku konfiguracji (Secrets)!")

# SPRAWDZENIE STATUSU ZALOGOWANIA
zalogowany = False
if st.session_state.get('temp_logged_in', False):
    zalogowany = True
else:
    # Weryfikacja ciasteczka w bazie
    token = cookie_manager.get("vorteza_auth_token")
    if token and check_trusted_device(token):
        zalogowany = True

if not zalogowany:
    # Użytkownik NIE zautoryzowany -> Pokaż ekran logowania i zatrzymaj renderowanie reszty
    render_login_screen()
    st.stop()


# --- FUNKCJE POMOCNICZE DLA KALENDARZA ---

def czy_to_swieto(d):
    """Sprawdza, czy dana data jest dniem ustawowo wolnym w Polsce."""
    rok = d.year
    # Święta stałe
    stale = [
        (1, 1),   # Nowy Rok
        (1, 6),   # Trzech Króli
        (5, 1),   # Święto Pracy
        (5, 3),   # Święto Konstytucji
        (8, 15),  # Wniebowzięcie NMP
        (11, 1),  # Wszystkich Świętych
        (11, 11), # Święto Niepodległości
        (12, 25), # Boże Narodzenie
        (12, 26)  # Boże Narodzenie (II dzień)
    ]
    if (d.month, d.day) in stale:
        return True
    
    # Obliczanie Wielkanocy (Algorytm Meeusa/Jonesa/Butchera)
    a = rok % 19
    b = rok // 100
    c = rok % 100
    d_q = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d_q - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    miesiac_w = (h + l - 7 * m + 114) // 31
    dzien_w = ((h + l - 7 * m + 114) % 31) + 1
    
    wielkanoc = date(rok, miesiac_w, dzien_w)
    poniedzialek_wielkanocny = wielkanoc + timedelta(days=1)
    boze_cialo = wielkanoc + timedelta(days=60)
    
    if d in [wielkanoc, poniedzialek_wielkanocny, boze_cialo]:
        return True
    return False

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

def render_calendar_grid(df_wizyty):
    """Generuje wizualną siatkę kalendarza z wyróżnieniem weekendów i świąt."""
    dzis = date.today()
    rok, miesiac = dzis.year, dzis.month
    
    miesiace_pl = {1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień", 5: "Maj", 6: "Czerwiec", 
                   7: "Lipiec", 8: "Sierpień", 9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień"}
    
    st.markdown(f"#### 🗓️ Radar Obłożenia: {miesiace_pl[miesiac]} {rok}")
    
    if not df_wizyty.empty:
        df_wizyty['temp_date'] = pd.to_datetime(df_wizyty['DataWizyty'], errors='coerce').dt.date
        counts = df_wizyty['temp_date'].value_counts().to_dict()
    else:
        counts = {}

    days_header = ["Pn", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]
    cols_header = st.columns(7)
    for i, day in enumerate(days_header):
        color = "#ef4444" if i >= 5 else "#64748b"
        cols_header[i].markdown(f"<div style='text-align: center; color: {color}; font-weight: 700; font-size: 0.75rem; margin-bottom: 5px;'>{day}</div>", unsafe_allow_html=True)

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(rok, miesiac)

    for week in month_days:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                week_cols[i].markdown("<div style='height: 65px;'></div>", unsafe_allow_html=True)
            else:
                curr_date = date(rok, miesiac, day)
                wizyty_count = counts.get(curr_date, 0)
                is_weekend = (curr_date.weekday() >= 5)
                is_holiday = czy_to_swieto(curr_date)
                is_today = (curr_date == dzis)
                
                # LOGIKA KOLORÓW
                if is_today:
                    bg_color, text_color, border = "#1e3a8a", "#ffffff", "2px solid #3b82f6"
                elif is_holiday:
                    bg_color, text_color, border = "#fee2e2", "#b91c1c", "1px solid #fca5a5"
                elif is_weekend:
                    bg_color, text_color, border = "#f1f5f9", "#475569", "1px solid #e2e8f0"
                elif wizyty_count > 0:
                    bg_color, text_color, border = "#eff6ff", "#1e40af", "1px solid #bfdbfe"
                else:
                    bg_color, text_color, border = "#ffffff", "#64748b", "1px solid #e2e8f0"
                
                icon_html = f"👤 {wizyty_count}" if wizyty_count > 0 and not is_holiday else ("ZAMKNIĘTE" if is_holiday else "&nbsp;")
                
                cell_html = (
                    f"<div style='background:{bg_color}; color:{text_color}; border:{border}; "
                    f"border-radius:12px; padding:8px; height:65px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.02);'>"
                    f"<div style='font-size:0.75rem; font-weight:800;'>{day}</div>"
                    f"<div style='font-size:0.6rem; font-weight:700; margin-top:4px;'>{icon_html}</div>"
                    f"</div>"
                )
                week_cols[i].markdown(cell_html, unsafe_allow_html=True)

def render_activity_table(df):
    """Renderuje tabelę aktywności."""
    if df is None or df.empty:
        st.markdown("<p style='color: #64748b; padding: 20px;'>Brak nadchodzących wizyt.</p>", unsafe_allow_html=True)
        return

    html = '<div class="custom-table-container"><table style="width: 100%; border-collapse: collapse; background: white;">'
    html += '<thead><tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0;">'
    html += '<th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase;">Badanie / Status</th>'
    html += '<th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase;">Termin</th>'
    html += '<th style="padding: 18px; text-align: left; color: #64748b; font-size: 0.7rem; text-transform: uppercase;">Status</th>'
    html += '</tr></thead><tbody>'

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

# --- 3. LOGIKA POBIERANIA DANYCH ---
try:
    df_wizyty = get_data_as_df("Wizyty")
    df_pacjenci = get_data_as_df("Pacjenci")
    df_firmy = get_data_as_df("Firmy")
except:
    df_wizyty = pd.DataFrame(columns=['DataWizyty', 'TypBadania', 'Status'])
    df_pacjenci = df_firmy = pd.DataFrame()

dzis = pd.Timestamp.today(tz='Europe/Warsaw').date()
wiz_dzis = 0
df_do_tabeli = pd.DataFrame()

if not df_wizyty.empty:
    df_wizyty['DataWizyty_dt'] = pd.to_datetime(df_wizyty['DataWizyty'], errors='coerce').dt.date
    wiz_dzis = len(df_wizyty[df_wizyty['DataWizyty_dt'] == dzis])
    mask_zaplanowane = (df_wizyty['Status'] == 'Zaplanowana') & (df_wizyty['DataWizyty_dt'] >= dzis)
    mask_zakonczone_dzis = (df_wizyty['Status'] == 'Zakończona') & (df_wizyty['DataWizyty_dt'] == dzis)
    df_do_tabeli = df_wizyty[mask_zaplanowane | mask_zakonczone_dzis].copy()
    if not df_do_tabeli.empty:
        df_do_tabeli = df_do_tabeli.sort_values(by=['DataWizyty_dt', 'Status'], ascending=[True, False]).head(5)

# --- 4. WIDOK GŁÓWNY ---

st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-weight: 800; color: #0f172a; letter-spacing: -1.8px; margin-bottom: 4px; font-size: 2.8rem;">Dashboard</h1>
        <p style="color: #64748b; font-size: 1.15rem; font-weight: 500;">Medycyna Pracy | Panel Zarządzania</p>
    </div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    render_premium_card("Pacjenci", str(len(df_pacjenci)), "👥", "Aktywni", "#059669", "#d1fae5")
with c2:
    render_premium_card("Firmy", str(len(df_firmy)), "🏢", "Kontrakty", "#2563eb", "#dbeafe")
with c3:
    render_premium_card("Wizyty na dziś", str(wiz_dzis), "📅", "Dzisiaj", "#ea580c", "#ffedd5")

st.markdown("<br>", unsafe_allow_html=True)

col_main, col_side = st.columns([2.2, 1])

with col_main:
    # Radar Obłożenia
    render_calendar_grid(df_wizyty)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Najbliższe wizyty</h4>", unsafe_allow_html=True)
    if not df_do_tabeli.empty:
        render_activity_table(df_do_tabeli)
    else:
        st.info("Brak aktywnych wizyt.")

with col_side:
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 1.2rem;'>Szybkie akcje</h4>", unsafe_allow_html=True)
    if st.button("➕ Nowy Pacjent", use_container_width=True):
        st.switch_page("pages/1_👤_Rejestracja_Pacjenta.py")
    if st.button("📅 Zaplanuj Wizytę", use_container_width=True):
        st.switch_page("pages/2_📅_Nowa_Wizyta.py")
    
    st.divider()
    
    # --- SEKCJA: SZYBKA NOTATKA ---
    st.markdown("<h4 style='font-weight: 700; color: #1e293b; margin-bottom: 0.8rem;'>📝 Szybka notatka</h4>", unsafe_allow_html=True)
    
    with st.container(border=True):
        nowa_notatka = st.text_area("Wpisz treść...", height=100, label_visibility="collapsed", placeholder="Pamiętaj o...")
        if st.button("💾 Zapisz notatkę", use_container_width=True):
            if nowa_notatka:
                sukces, msg = add_note_to_db(nowa_notatka)
                if sukces:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Wpisz treść notatki.")

    # Podgląd ostatniej notatki
    try:
        df_n = get_data_as_df("Notatki")
        if not df_n.empty:
            ostatnia = df_n.iloc[-1]
            st.markdown(f"""
                <div style="background: #f8fafc; padding: 12px; border-radius: 12px; border-left: 4px solid #3b82f6; margin-top: 10px;">
                    <p style="margin: 0; font-size: 0.7rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Ostatni zapis ({ostatnia['Data']}):</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.85rem; color: #1e293b; line-height: 1.4;">{ostatnia['Tresc']}</p>
                </div>
            """, unsafe_allow_html=True)
    except: pass

    st.markdown("---")
    st.markdown("""
        <div style="background: #eff6ff; padding: 20px; border-radius: 16px; border: 1px solid #dbeafe;">
            <p style="margin: 0; font-size: 0.82rem; color: #1e40af; line-height: 1.5;">
                💡 <b>System zautoryzowany:</b><br>Ochrona Google Authenticator (TOTP) i Cookie.
            </p>
        </div>
    """, unsafe_allow_html=True)
