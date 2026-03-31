import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import hashlib

# --- KONFIGURACJA POŁĄCZENIA ---
@st.cache_resource
def get_db_connection():
    """Nawiązuje połączenie z Google Sheets i zwraca obiekt skoroszytu."""
    try:
        # Pobieramy poświadczenia z secrets
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
    """Pobiera dane z wybranej zakładki i zwraca jako Pandas DataFrame."""
    sh = get_db_connection()
    if not sh: return pd.DataFrame()
    
    worksheet = sh.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def add_patient_to_db(pesel, imie, nazwisko, data_urodzenia, telefon):
    """Dodaje nowego pacjenta po weryfikacji unikalności PESEL."""
    sh = get_db_connection()
    ws = sh.worksheet("Pacjenci")
    
    existing_pesels = ws.col_values(1)
    if str(pesel) in existing_pesels:
        return False, "Pacjent o takim numerze PESEL już istnieje w bazie."

    ws.append_row([str(pesel), imie, nazwisko, str(data_urodzenia), telefon])
    return True, "Pacjent dodany pomyślnie."

def add_company_to_db(nip, nazwa, adres, c_wst, c_okr, c_kon, c_san):
    """Dodaje nową firmę wraz z wynegocjowanym cennikiem badań."""
    sh = get_db_connection()
    ws = sh.worksheet("Firmy")
    
    existing_nips = ws.col_values(1)
    if str(nip) in existing_nips:
        return False, "Firma o takim NIP już istnieje."

    ws.append_row([str(nip), nazwa, adres, c_wst, c_okr, c_kon, c_san])
    return True, "Firma wraz z cennikiem została dodana pomyślnie."

def add_appointment_to_db(pesel, nip_firmy, typ_badania, notatki, data_wizyty):
    """Rejestruje nową wizytę w systemie."""
    sh = get_db_connection()
    ws = sh.worksheet("Wizyty")
    
    id_wizyty = datetime.now().strftime("%Y%m%d%H%M%S")
    status = "Zaplanowana"
    
    ws.append_row([id_wizyty, str(data_wizyty), str(pesel), str(nip_firmy), typ_badania, status, notatki])
    return True, f"Wizyta zaplanowana pomyślnie na dzień {data_wizyty}. ID: {id_wizyty}"

# --- MODUŁ ORZECZNICZY Z PODPISEM CYFROWYM ---

def add_orzeczenie_to_db(id_wizyty, pesel, decyzja, data_kolejnego, uwagi, pin_lekarza):
    """Zapisuje orzeczenie z unikalnym podpisem cyfrowym (SHA-256)."""
    sh = get_db_connection()
    
    # 1. Weryfikacja PIN (Dla bezpieczeństwa PIN powinien być w st.secrets)
    # Na potrzeby testów ustawiliśmy: 1234
    if pin_lekarza != "1234":
        return False, "Błąd autoryzacji: Nieprawidłowy PIN lekarza."

    # 2. Generowanie Cyfrowego Hashu (Pieczęć integralności dokumentu)
    # Hashujemy kluczowe dane, aby uniemożliwić ich późniejszą zmianę w bazie
    data_to_hash = f"{id_wizyty}|{pesel}|{decyzja}|{data_kolejnego}|{pin_lekarza}"
    signature_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()[:16].upper()
    full_signature = f"SIG-{signature_hash}"
    
    # 3. Zapis orzeczenia do tabeli
    ws_orzeczenia = sh.worksheet("Orzeczenia")
    id_orzeczenia = "ORZ/" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Kolumny: ID_Orzeczenia, ID_Wizyty, PESEL, Decyzja, DataKolejnego, Uwagi, Podpis_Cyfrowy
    ws_orzeczenia.append_row([
        id_orzeczenia, 
        str(id_wizyty), 
        str(pesel), 
        decyzja, 
        str(data_kolejnego), 
        uwagi,
        full_signature
    ])
    
    # 4. Automatyczne zamknięcie wizyty (zmiana statusu)
    ws_wizyty = sh.worksheet("Wizyty")
    try:
        cell = ws_wizyty.find(str(id_wizyty), in_column=1)
        if cell:
            # Status znajduje się w 6. kolumnie
            ws_wizyty.update_cell(cell.row, 6, "Zakończona")
    except Exception as e:
        print(f"Błąd podczas aktualizacji statusu wizyty: {e}")
        
    return True, f"Orzeczenie wystawione i podpisane cyfrowo. Kod autoryzacji: {full_signature}"

# --- FUNKCJE DODATKOWE ---

def add_stanowisko_to_db(nip_firmy, nazwa_stanowiska, czynniki):
    """Dodaje nowe stanowisko pracy do profilu konkretnej firmy."""
    sh = get_db_connection()
    ws = sh.worksheet("Stanowiska")
    
    ws.append_row([str(nip_firmy), nazwa_stanowiska, czynniki])
    return True, f"Stanowisko '{nazwa_stanowiska}' zostało pomyślnie dodane."
