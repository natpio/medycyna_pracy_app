import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import hashlib
import os

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
    st.cache_data.clear()  # <-- Zrzuca pamięć podręczną po aktualizacji bazy
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

def add_appointment_to_db(pesel, nip_firmy, typ_badania, notatki, data_wizyty):
    sh = get_db_connection()
    ws = sh.worksheet("Wizyty")
    
    id_wizyty = datetime.now().strftime("%Y%m%d%H%M%S")
    status = "Zaplanowana"
    
    ws.append_row([id_wizyty, str(data_wizyty), str(pesel), str(nip_firmy), typ_badania, status, notatki])
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

# --- MODUŁ WYGLĄDU PRO (Zarządzanie CSS) ---

def apply_pro_style():
    """Wczytuje profesjonalny plik CSS i ukrywa branding Streamlit."""
    # 1. Wymuszenie wyświetlenia loga na samej górze paska bocznego
    if os.path.exists("logo_jarek2.png"):
        st.sidebar.image("logo_jarek2.png", use_container_width=True)
        
    # 2. Wczytanie stylów CSS
    css_file = "style.css"
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            css = f.read()
        st.markdown(f'<style>\n{css}\n</style>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Błąd wyglądu: Nie znaleziono pliku style.css w głównym katalogu.")
