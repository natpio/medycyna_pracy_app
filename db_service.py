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

# --- FUNKCJE ODCZYTU (Z PAMIĘCIĄ PODRĘCZNĄ) ---

@st.cache_data(ttl=60, show_spinner=False)
def get_data_as_df(worksheet_name):
    """Pobiera dane z Google Sheets i zapisuje w RAM (ochrona API)."""
    sh = get_db_connection()
    if not sh: return pd.DataFrame()
    
    try:
        worksheet = sh.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"⚠️ Chwilowy błąd komunikacji z arkuszem: {worksheet_name}. Spróbuj odświeżyć stronę za chwilę.")
        return pd.DataFrame()

# --- FUNKCJE ZAPISU (CRUD) ---

def add_patient_to_db(pesel, imie, nazwisko, data_urodzenia, telefon):
    """Dodaje nowego pacjenta do bazy."""
    sh = get_db_connection()
    ws = sh.worksheet("Pacjenci")
    
    existing_pesels = ws.col_values(1)
    if str(pesel) in existing_pesels:
        return False, "Pacjent o takim numerze PESEL już istnieje w bazie."

    ws.append_row([str(pesel), imie, nazwisko, str(data_urodzenia), telefon])
    st.cache_data.clear() 
    return True, "Pacjent dodany pomyślnie."

def add_company_to_db(nip, nazwa, adres, c_wst, c_okr, c_kon, c_san):
    """Dodaje firmę wraz z cennikiem."""
    sh = get_db_connection()
    ws = sh.worksheet("Firmy")
    
    existing_nips = ws.col_values(1)
    if str(nip) in existing_nips:
        return False, "Firma o takim NIP już istnieje."

    ws.append_row([str(nip), nazwa, adres, c_wst, c_okr, c_kon, c_san])
    st.cache_data.clear()
    return True, "Firma wraz z cennikiem została dodana pomyślnie."

def add_appointment_to_db(pesel, nip_firmy, typ_badania, notatki, data_wizyty, godzina):
    """Planuje wizytę, uwzględniając konkretną godzinę (slot)."""
    sh = get_db_connection()
    ws = sh.worksheet("Wizyty")
    
    id_wizyty = datetime.now().strftime("%Y%m%d%H%M%S")
    status = "Zaplanowana"
    
    # Zapisujemy dane do 8 kolumn (A-H)
    ws.append_row([
        id_wizyty, 
        str(data_wizyty), 
        str(pesel), 
        str(nip_firmy), 
        typ_badania, 
        status, 
        notatki, 
        str(godzina)
    ])
    st.cache_data.clear()
    return True, f"Wizyta zaplanowana pomyślnie na godz. {godzina}."

def add_stanowisko_to_db(nip_firmy, nazwa_stanowiska, czynniki):
    """Dodaje stanowisko do katalogu danej firmy."""
    sh = get_db_connection()
    ws = sh.worksheet("Stanowiska")
    ws.append_row([str(nip_firmy), nazwa_stanowiska, czynniki])
    st.cache_data.clear()
    return True, f"Stanowisko '{nazwa_stanowiska}' zostało pomyślnie dodane."

# --- MODUŁ ORZECZNICZY Z PODPISEM CYFROWYM ---

def add_orzeczenie_to_db(id_wizyty, pesel, decyzja, data_kolejnego, uwagi, pin_lekarza):
    """Wystawia orzeczenie i generuje bezpieczny podpis SHA-256."""
    sh = get_db_connection()
    
    try:
        correct_pin = st.secrets["doctor"]["pin"]
    except KeyError:
        return False, "Błąd konfiguracji: Nie znaleziono PINu lekarza w systemie Secrets!"

    if str(pin_lekarza) != str(correct_pin):
        return False, "Błąd autoryzacji: Nieprawidłowy PIN lekarza."

    # Generowanie podpisu cyfrowego
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
    
    # Aktualizacja statusu wizyty na Zakończona
    ws_wizyty = sh.worksheet("Wizyty")
    try:
        cell = ws_wizyty.find(str(id_wizyty), in_column=1)
        if cell:
            ws_wizyty.update_cell(cell.row, 6, "Zakończona")
    except Exception as e:
        print(f"Błąd aktualizacji statusu: {e}")
        
    st.cache_data.clear()
    return True, f"Orzeczenie wystawione. Kod autoryzacji: {full_signature}"

# --- MODUŁ WYGLĄDU ---

def apply_pro_style():
    """Wczytuje styl CSS z pliku style.css."""
    css_file = "style.css"
    if os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            css = f.read()
        st.markdown(f'<style>\n{css}\n</style>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Nie znaleziono pliku style.css.")
