import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import hashlib
import os
import base64

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

def add_appointment_to_db(pesel, nip_firmy, typ_badania, notatki, data_wizyty, godzina=None):
    sh = get_db_connection()
    ws = sh.worksheet("Wizyty")
    
    id_wizyty = datetime.now().strftime("%Y%m%d%H%M%S")
    status = "Zaplanowana"
    
    # Obsługa opcjonalnej godziny - jeśli została podana, konwertujemy na string, w przeciwnym razie pusty ciąg
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
        # Liczymy tylko wizyty ze statusem "Zaplanowana"
        oczekujacy = len(df_wizyty[df_wizyty['Status'] == 'Zaplanowana'])
        if oczekujacy > 0:
            # Dynamiczny CSS dodający licznik (badge) na pasku bocznym
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
            # Usuwamy licznik, gdy poczekalnia jest pusta
            st.markdown('<style>[data-testid="stSidebarNav"] a[href*="Panel_Lekarza"] span::after { content: none; }</style>', unsafe_allow_html=True)

def apply_pro_style():
    """Wczytuje profesjonalny plik CSS, logo i uruchamia nasłuch kolejki."""
    # 1. Wymuszenie wyświetlenia loga na samej górze paska bocznego (Base64 + CSS)
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
    else:
        st.warning("⚠️ Błąd wyglądu: Nie znaleziono pliku style.css w głównym katalogu.")
    
    # 3. Uruchomienie "żywego" licznika na pasku bocznym
    render_live_badge()
