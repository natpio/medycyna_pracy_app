import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource
def get_db_connection():
    """Nawiązuje połączenie z Google Sheets i zwraca obiekt skoroszytu."""
    try:
        # Pobieramy poświadczenia z secrets.toml
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        
        # Otwieramy arkusz po nazwie zdefiniowanej w secrets
        sh = gc.open(st.secrets["gsheets"]["sheet_name"])
        return sh
    except Exception as e:
        st.error(f"Błąd krytyczny połączenia z bazą danych: {e}")
        return None

# --- FUNKCJE POMOCNICZE (CRUD) ---

def get_data_as_df(worksheet_name):
    """Pobiera dane z zakładki i zwraca jako Pandas DataFrame."""
    sh = get_db_connection()
    if not sh: return pd.DataFrame()
    
    worksheet = sh.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def add_patient_to_db(pesel, imie, nazwisko, data_urodzenia, telefon):
    """Dodaje nowego pacjenta po weryfikacji PESEL."""
    sh = get_db_connection()
    ws = sh.worksheet("Pacjenci")
    
    # Sprawdź czy PESEL już istnieje (prosta walidacja)
    existing_pesels = ws.col_values(1) # Zakładamy, że PESEL to 1. kolumna
    if pesel in existing_pesels:
        return False, "Pacjent o takim numerze PESEL już istnieje w bazie."

    ws.append_row([pesel, imie, nazwisko, str(data_urodzenia), telefon])
    return True, "Pacjent dodany pomyślnie."

def add_company_to_db(nip, nazwa, adres):
    """Dodaje nową firmę."""
    sh = get_db_connection()
    ws = sh.worksheet("Firmy")
    
    # Sprawdź NIP
    existing_nips = ws.col_values(1)
    if nip in existing_nips:
        return False, "Firma o takim NIP już istnieje."

    ws.append_row([nip, nazwa, adres])
    return True, "Firma dodana pomyślnie."

def add_appointment_to_db(pesel, nip_firmy, typ_badania, notatki):
    """Rejestruje nową wizytę."""
    sh = get_db_connection()
    ws = sh.worksheet("Wizyty")
    
    id_wizyty = datetime.now().strftime("%Y%m%d%H%M%S") # Proste unikalne ID
    data_wizyty = datetime.now().strftime("%Y-%m-%d")
    status = "Zaplanowana"
    
    ws.append_row([id_wizyty, data_wizyty, pesel, nip_firmy, typ_badania, status, notatki])
    return True, f"Wizyta zaplanowana pomyślnie. ID: {id_wizyty}"
