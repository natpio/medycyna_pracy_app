import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import hashlib
import os
import base64
import time

# --- WYMUSZENIE POLSKIEJ STREFY CZASOWEJ W CHMURZE ---
os.environ['TZ'] = 'Europe/Warsaw'
try:
    time.tzset()  # Aktualizuje czas systemowy dla tego skryptu
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
    """Pobiera dane i zapisuje w pamięci podręcznej RAM (chroni przed zablokowaniem API Google)."""
    sh = get_db_connection()
    if not sh: return pd.DataFrame()
    
    try:
        worksheet = sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Chwilowy błąd komunikacji z chmurą Google (arkusz: {worksheet_name}). Odczekaj 10 sekund i odśwież stronę.")
        return pd.DataFrame()

def add_patient_to_db(pesel, imie, nazwisko, data_urodzenia, telefon):
    sh = get_db_connection()
    ws = sh.worksheet("Pacjenci")
    
    existing_pesels = ws.col_values(1)
    if str(pesel) in existing_pesels:
        return False, "Pacjent o takim numerze PESEL już istnieje w bazie."

    ws.append_row([str(pesel), imie, nazwisko, str(data_urodzenia), telefon])
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
    return True, f"Wizyta zaplanowana pomyślnie na dzień {data_wizyty}. ID: {id_wizyty}"

# --- MODUŁ ORZECZNICZY Z BEZPIECZNYM PODPISEM CYFROWYM ---

def add_orzeczenie_to_db(id_wizyty, pesel, decyzja, data_kolejnego, uwagi, pin_lekarza):
    sh = get_db_connection()
    
    try:
        correct_pin = st.secrets["doctor"]["pin"]
    except KeyError:
        return False, "Błąd konfiguracji: Nie znaleziono autoryzacji w systemie Secrets!"

    if str(pin_lekarza) != str(correct_pin):
        return False, "Błąd autoryzacji: Nieprawidłowy PIN lekarza."

    data_to_hash = f"{id_wizyty}|{pesel}|{decyzja}|{data_kolejnego}|{correct_pin}"
    signature_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()[:16].upper()
    full_signature = f"SIG-{signature_hash}"
    
    ws_orzeczenia = sh.worksheet("Orzeczenia")
    id_orzeczenia = "ORZ/" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    ws_orzeczenia.append_row([
        id_orzeczenia, 
        str(id_wizyty), 
        str(pesel), 
        decyzja, 
        str(data_kolejnego), 
        uwagi,
        full_signature
    ])
    
    ws_wizyty = sh.worksheet("Wizyty")
    try:
        cell = ws_wizyty.find(str(id_wizyty), in_column=1)
        if cell:
            ws_wizyty.update_cell(cell.row, 6, "Zakończona")
    except Exception as e:
        print(f"Błąd podczas aktualizacji statusu wizyty: {e}")
        
    st.cache_data.clear()
    return True, f"Orzeczenie podpisane i wystawione. Kod autoryzacji: {full_signature}"

# --- FUNKCJE DODATKOWE ---

def add_stanowisko_to_db(nip_firmy, nazwa_stanowiska, czynniki):
    sh = get_db_connection()
    ws = sh.worksheet("Stanowiska")
    ws.append_row([str(nip_firmy), nazwa_stanowiska, czynniki])
    st.cache_data.clear()
    return True, f"Stanowisko '{nazwa_stanowiska}' zostało pomyślnie dodane."

# --- MODUŁ WYGLĄDU PRO (Zarządzanie CSS i LIVE UPDATES) ---

@st.fragment(run_every="10s")
def render_live_badge():
    """Automatycznie odświeżany skrypt sprawdzający kolejkę (uruchamia się co 10 sek w tle)."""
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
                box-shadow: 0 0 5px rgba(59, 130, 246, 0.5);
            }}
            </style>
            """
            st.markdown(css, unsafe_allow_html=True)
        else:
            st.markdown('<style>[data-testid="stSidebarNav"] a[href*="Panel_Lekarza"] span::after { content: none; }</style>', unsafe_allow_html=True)

def apply_pro_style():
    """Wczytuje profesjonalny plik CSS, logo i uruchamia nasłuch kolejki."""
    # 1. Główny logotyp gabinetu na górze
    logo_file = "logo_jarek2.png"
    if os.path.exists(logo_file):
        with open(logo_file, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        st.markdown(
            f"""
            <style>
            [data-testid="stSidebarNav"] {{
                background-image: url(data:image/png;base64,{encoded_string});
                background-repeat: no-repeat;
                background-position: center 20px;
                background-size: 80%;
                padding-top: 150px !important; 
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
    # 2. Wczytanie stylów CSS
    css_file = "style.css"
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            css = f.read()
        st.markdown(f'<style>\n{css}\n</style>', unsafe_allow_html=True)
    
    # 3. Licznik poczekalni (Live)
    render_live_badge()

    # 4. Stopka twórców (Zawsze na dole paska bocznego)
    # Rozpoznaje logo z rozszerzeniem .png lub .jpg
    creator_logo = None
    if os.path.exists("logo_firma.png"):
        creator_logo = "logo_firma.png"
        mime = "image/png"
    elif os.path.exists("logo_firma.jpg"):
        creator_logo = "logo_firma.jpg"
        mime = "image/jpeg"
        
    if creator_logo:
        with open(creator_logo, "rb") as image_file:
            encoded_creator = base64.b64encode(image_file.read()).decode()
        
        footer_html = f"""
        <div style="position: fixed; bottom: 20px; left: 15px; width: 230px; padding: 12px 15px; background: rgba(0, 0, 0, 0.15); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); z-index: 100;">
            <div style="font-size: 0.55rem; color: rgba(255,255,255,0.4); letter-spacing: 1px; margin-bottom: 8px; font-weight: 700;">
                TECHNOLOGIA I WDROŻENIE:
            </div>
            <div style="display: flex; align-items: center; gap: 12px;">
                <img src="data:{mime};base64,{encoded_creator}" width=\"36\" style="border-radius: 6px;">
                <div style="color: #ffffff; font-size: 0.85rem; font-weight: 700; letter-spacing: 0.5px; line-height: 1.2;">
                    VORTEZA<br><span style="font-weight: 500; font-size: 0.65rem; color: #94a3b8;">SYSTEMS</span>
                </div>
            </div>
        </div>
        """
        st.sidebar.markdown(footer_html, unsafe_allow_html=True)
