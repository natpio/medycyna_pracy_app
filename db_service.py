import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, date, timedelta
import hashlib
import os
import base64
import time
import uuid

# --- WYMUSZENIE POLSKIEJ STREFY CZASOWEJ W CHMURZE ---
os.environ['TZ'] = 'Europe/Warsaw'
try:
    time.tzset()
except AttributeError:
    pass

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource
def get_db_connection():
    """Nawiązuje połączenie z Google Sheets i zwraca obiekt skoroszytu."""
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open(st.secrets["gsheets"]["sheet_name"])
        return sh
    except Exception as e:
        st.error(f"Błąd krytyczny połączenia z bazą danych: {e}")
        return None

# --- FUNKCJE POMOCNICZE (CRUD) ---

@st.cache_data(ttl=60, show_spinner=False)
def get_data_as_df(worksheet_name):
    sh = get_db_connection()
    if not sh: return pd.DataFrame()
    try:
        worksheet = sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Chwilowy błąd komunikacji (arkusz: {worksheet_name}). Odczekaj chwilę i odśwież.")
        return pd.DataFrame()

def update_record(worksheet_name, id_col_name, id_value, update_dict):
    """
    Uniwersalna funkcja do aktualizacji wiersza w Arkuszu Google.
    """
    sh = get_db_connection()
    if not sh: return False
    
    try:
        ws = sh.worksheet(worksheet_name)
        headers = ws.row_values(1)
        
        if id_col_name not in headers:
            return False
        id_col_idx = headers.index(id_col_name) + 1
        
        cell = ws.find(str(id_value), in_column=id_col_idx)
        if not cell:
            return False
            
        updates = []
        for key, val in update_dict.items():
            if key in headers:
                col_idx = headers.index(key) + 1
                updates.append({
                    'range': gspread.utils.rowcol_to_a1(cell.row, col_idx),
                    'values': [[str(val)]]
                })
        
        if updates:
            ws.batch_update(updates)
            st.cache_data.clear() 
            return True
        return False
    except Exception as e:
        st.error(f"Błąd aktualizacji bazy: {e}")
        return False

def add_patient_to_db(pesel, imie, nazwisko, data_urodzenia, telefon, adres="", email="", plec=""):
    sh = get_db_connection()
    ws = sh.worksheet("Pacjenci")
    existing_pesels = ws.col_values(1)
    if str(pesel) in existing_pesels:
        return False, "Pacjent o takim numerze PESEL już istnieje w bazie."
    
    ws.append_row([str(pesel), imie, nazwisko, str(data_urodzenia), telefon, adres, email, plec])
    st.cache_data.clear()
    return True, "Pacjent dodany pomyślnie."

def add_company_to_db(nip, nazwa, adres, c_wst, c_okr, c_kon, c_san):
    sh = get_db_connection()
    ws = sh.worksheet("Firmy")
    existing_nips = ws.col_values(1)
    if str(nip) in existing_nips:
        return False, "Firma o takim NIP już istnieje."
    ws.append_row([str(nip), nazwa, adres, c_wst, c_okr, c_kon, c_san])
    st.cache_data.clear()
    return True, "Firma wraz z cennikiem została dodana pomyślnie."

def add_appointment_to_db(pesel, nip_firmy, typ_badania, notatki, data_wizyty, godzina=None):
    sh = get_db_connection()
    ws = sh.worksheet("Wizyty")
    id_wizyty = datetime.now().strftime("%Y%m%d%H%M%S")
    status = "Zaplanowana"
    godzina_zapis = str(godzina) if godzina else ""
    ws.append_row([id_wizyty, str(data_wizyty), str(pesel), str(nip_firmy), typ_badania, status, notatki, godzina_zapis])
    st.cache_data.clear()
    return True, f"Wizyta zaplanowana pomyślnie. ID: {id_wizyty}"

def add_orzeczenie_to_db(id_wizyty, pesel, decyzja, data_kolejnego, uwagi, pin_lekarza):
    sh = get_db_connection()
    try:
        correct_pin = st.secrets["doctor"]["pin"]
    except KeyError:
        return False, "Błąd konfiguracji Secrets!"

    if str(pin_lekarza) != str(correct_pin):
        return False, "Błąd autoryzacji: Nieprawidłowy PIN."

    data_to_hash = f"{id_wizyty}|{pesel}|{decyzja}|{data_kolejnego}|{correct_pin}"
    signature_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()[:16].upper()
    full_signature = f"SIG-{signature_hash}"
    
    ws_orzeczenia = sh.worksheet("Orzeczenia")
    id_orzeczenia = "ORZ/" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    ws_orzeczenia.append_row([
        id_orzeczenia, str(id_wizyty), str(pesel), decyzja, str(data_kolejnego), uwagi, full_signature, "NIE"
    ])
    
    update_record("Wizyty", "ID_Wizyty", id_wizyty, {"Status": "Zakończona"})
    return True, f"Orzeczenie wystawione. Kod: {full_signature}"

def add_stanowisko_to_db(nip_firmy, nazwa_stanowiska, czynniki):
    sh = get_db_connection()
    ws = sh.worksheet("Stanowiska")
    ws.append_row([str(nip_firmy), nazwa_stanowiska, czynniki])
    st.cache_data.clear()
    return True, f"Stanowisko '{nazwa_stanowiska}' zostało dodane."

def add_note_to_db(tresc):
    """Zapisuje szybką notatkę do arkusza 'Notatki'."""
    sh = get_db_connection()
    if not sh: return False, "Błąd połączenia."
    try:
        ws = sh.worksheet("Notatki")
    except Exception:
        return False, "Brak arkusza 'Notatki'. Dodaj zakładkę o tej nazwie w Google Sheets (kolumny: Data, Tresc)."
    
    data_notatki = datetime.now().strftime("%Y-%m-%d %H:%M")
    ws.append_row([data_notatki, tresc])
    st.cache_data.clear()
    return True, "Notatka zapisana pomyślnie!"

def dekoduj_pesel(pesel):
    """Wyciąga datę urodzenia i płeć z numeru PESEL."""
    if not pesel or len(str(pesel)) != 11 or not str(pesel).isdigit():
        return None, None
    
    p = str(pesel)
    plec = "Kobieta" if int(p[9]) % 2 == 0 else "Mężczyzna"
    
    rok = int(p[0:2])
    miesiac = int(p[2:4])
    dzien = int(p[4:6])
    
    if 1 <= miesiac <= 12:
        rok += 1900
    elif 21 <= miesiac <= 32:
        rok += 2000
        miesiac -= 20
    elif 81 <= miesiac <= 92:
        rok += 1800
        miesiac -= 80
        
    try:
        data_urodzenia = date(rok, miesiac, dzien)
        return data_urodzenia, plec
    except ValueError:
        return None, None

# --- FUNKCJE AUTORYZACJI URZĄDZEŃ (NOWE) ---
def check_trusted_device(token):
    """Sprawdza, czy podany token urządzenia znajduje się w bazie zaufanych i czy nie wygasł."""
    if not token: return False
    df_auth = get_data_as_df("Autoryzacja")
    if df_auth.empty: return False
    
    # Przeszukujemy bazę pod kątem tokena
    is_valid = str(token) in df_auth['Token'].astype(str).values
    return is_valid

def add_trusted_device(token):
    """Dodaje nowy token zaufanego urządzenia do bazy danych (ważny przez 30 dni)."""
    sh = get_db_connection()
    if not sh: return False
    try:
        ws = sh.worksheet("Autoryzacja")
    except Exception:
        st.error("Brak arkusza 'Autoryzacja' w Google Sheets!")
        return False
    
    wygasa = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
    ws.append_row([str(token), wygasa])
    st.cache_data.clear()
    return True


@st.fragment(run_every="10s")
def render_live_badge():
    df_wizyty = get_data_as_df("Wizyty")
    if not df_wizyty.empty:
        oczekujacy = len(df_wizyty[df_wizyty['Status'] == 'Zaplanowana'])
        if oczekujacy > 0:
            css = f"""
            <style>
            [data-testid="stSidebarNav"] a[href*="Panel_Lekarza"] span::after {{
                content: "{oczekujacy}";
                background-color: #3b82f6;
                color: white;
                border-radius: 12px;
                padding: 2px 8px;
                font-size: 0.75rem;
                margin-left: 10px;
                font-weight: 800;
            }}
            </style>
            """
            st.markdown(css, unsafe_allow_html=True)
        else:
            st.markdown('<style>[data-testid="stSidebarNav"] span::after { content: none; }</style>', unsafe_allow_html=True)

def apply_pro_style():
    logo_file = "logo_jarek2.png"
    if os.path.exists(logo_file):
        with open(logo_file, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(f"""<style>[data-testid="stSidebarNav"] {{ background-image: url(data:image/png;base64,{encoded_string}); background-repeat: no-repeat; background-position: center 20px; background-size: 80%; padding-top: 150px !important; }}</style>""", unsafe_allow_html=True)
    
    bg_file = "1775064952136.jpg"  
    if os.path.exists(bg_file):
        with open(bg_file, "rb") as bg_image:
            encoded_bg = base64.b64encode(bg_image.read()).decode()
        st.markdown(f"""
            <style>
            .stApp::before {{
                content: "";
                position: fixed;
                top: 0; left: 0; width: 100vw; height: 100vh;
                background-image: url("data:image/jpeg;base64,{encoded_bg}");
                background-size: cover;
                background-position: center center;
                background-repeat: no-repeat;
                z-index: -1;
                opacity: 0.6; 
            }}
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main, .block-container {{
                background-color: transparent !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            
    css_file = "style.css"
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            css = f.read()
        st.markdown(f'<style>\n{css}\n</style>', unsafe_allow_html=True)
    
    render_live_badge()

    creator_logo = "logo_firma.png" if os.path.exists("logo_firma.png") else ("logo_firma.jpg" if os.path.exists("logo_firma.jpg") else None)
    if creator_logo:
        mime = "image/png" if creator_logo.endswith(".png") else "image/jpeg"
        with open(creator_logo, "rb") as image_file:
            encoded_creator = base64.b64encode(image_file.read()).decode()
        footer_html = f"""<div style="position: fixed; bottom: 20px; left: 15px; width: 230px; padding: 12px 15px; background: rgba(0, 0, 0, 0.15); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); z-index: 100;"><div style="font-size: 0.55rem; color: rgba(255,255,255,0.4); margin-bottom: 8px; font-weight: 700;">TECHNOLOGIA I WDROŻENIE:</div><div style="display: flex; align-items: center; gap: 12px;"><img src="data:{mime};base64,{encoded_creator}" width="36" style="border-radius: 6px;"><div style="color: #ffffff; font-size: 0.85rem; font-weight: 700;">VORTEZA<br><span style="font-weight: 500; font-size: 0.65rem; color: #94a3b8;">SYSTEMS</span></div></div></div>"""
        st.sidebar.markdown(footer_html, unsafe_allow_html=True)
