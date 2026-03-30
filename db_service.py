import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource
def get_db_connection():
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open(st.secrets["gsheets"]["sheet_name"])
        return sh
    except Exception as e:
        st.error(f"Błąd krytyczny połączenia z bazą danych: {e}")
        return None

# --- FUNKCJE POMOCNICZE (CRUD) ---
def get_data_as_df(worksheet_name):
    sh = get_db_connection()
    if not sh: return pd.DataFrame()
    worksheet = sh.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def add_patient_to_db(pesel, imie, nazwisko, data_urodzenia, telefon):
    sh = get_db_connection()
    ws = sh.worksheet("Pacjenci")
    existing_pesels = ws.col_values(1)
    if pesel in existing_pesels:
        return False, "Pacjent o takim numerze PESEL już istnieje w bazie."
    ws.append_row([pesel, imie, nazwisko, str(data_urodzenia), telefon])
    return True, "Pacjent dodany pomyślnie."

def add_company_to_db(nip, nazwa, adres):
    sh = get_db_connection()
    ws = sh.worksheet("Firmy")
    existing_nips = ws.col_values(1)
    if nip in existing_nips:
        return False, "Firma o takim NIP już istnieje."
    ws.append_row([nip, nazwa, adres])
    return True, "Firma dodana pomyślnie."

def add_appointment_to_db(pesel, nip_firmy, typ_badania, notatki):
    sh = get_db_connection()
    ws = sh.worksheet("Wizyty")
    id_wizyty = datetime.now().strftime("%Y%m%d%H%M%S")
    data_wizyty = datetime.now().strftime("%Y-%m-%d")
    status = "Zaplanowana"
    ws.append_row([id_wizyty, data_wizyty, pesel, nip_firmy, typ_badania, status, notatki])
    return True, f"Wizyta zaplanowana pomyślnie. ID: {id_wizyty}"

# --- NOWE FUNKCJE DLA LEKARZA ---
def add_orzeczenie_to_db(id_wizyty, pesel, decyzja, data_kolejnego, uwagi):
    """Zapisuje decyzję lekarza i oznacza wizytę jako zakończoną."""
    sh = get_db_connection()
    
    # 1. Zapis orzeczenia do nowej zakładki
    ws_orzeczenia = sh.worksheet("Orzeczenia")
    id_orzeczenia = "ORZ/" + datetime.now().strftime("%Y%m%d%H%M%S")
    ws_orzeczenia.append_row([id_orzeczenia, str(id_wizyty), pesel, decyzja, str(data_kolejnego), uwagi])
    
    # 2. Aktualizacja statusu wizyty na "Zakończona" w starej zakładce
    ws_wizyty = sh.worksheet("Wizyty")
    try:
        # Szukamy wiersza z tym ID wizyty (w 1 kolumnie)
        cell = ws_wizyty.find(str(id_wizyty), in_column=1)
        if cell:
            # Kolumna 6 to Status. Nadpisujemy z "Zaplanowana" na "Zakończona"
            ws_wizyty.update_cell(cell.row, 6, "Zakończona")
    except Exception as e:
        print(f"Błąd aktualizacji statusu: {e}")
        
    return True, "Orzeczenie wystawione pomyślnie. Wizyta zakończona!"
