import streamlit as st
import pandas as pd
import os
import urllib.request
import io
import qrcode
import datetime
from fpdf import FPDF
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from db_service import get_data_as_df, apply_pro_style

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="centered")

# Uruchomienie profesjonalnego stylu CSS zdefiniowanego w db_service.py
apply_pro_style()

st.markdown("# 🖨️ Generator Orzeczeń PDF")
st.write("Pobierz gotowe dokumenty. Lista odświeża się automatycznie co 30 sekund.")

# --- 2. BEZPIECZNE POBIERANIE PIECZĄTKI Z GOOGLE DRIVE ---
@st.cache_resource
def get_secure_signature():
    """Pobiera pieczątkę z Dysku Google przez autoryzowany Service Account."""
    # Pobranie ID pliku z sekcji secrets
    file_id = st.secrets.get("doctor", {}).get("signature_file_id")
    if not file_id or file_id == "TUTAJ_WKLEJ_SWOJE_ID_PLIKU_Z_LINKU":
        return None
        
    try:
        # Autoryzacja dostępu do Google Drive API
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        
        # Pobieranie mediów (obrazu pieczątki)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Zapis tymczasowy dla biblioteki FPDF
        path = "temp_signature.png"
        with open(path, "wb") as f:
            f.write(fh.getvalue())
        return path
    except Exception as e:
        st.error(f"Błąd pobierania pieczątki: {e}")
        return None

# --- 3. LOGIKA GENEROWANIA PLIKU PDF ---
def generate_pdf(pacjent, wizyta, orzeczenie, pieczatka_path):
    """Tworzy dokument PDF z danymi orzeczenia, kodem QR i pieczątką."""
    pdf = FPDF()
    pdf.add_page()
    
    # Ustawienie czcionki podstawowej
    pdf.set_font("Arial", size=12)

    # Nagłówek dokumentu
    pdf.cell(200, 10, txt="ORZECZENIE LEKARSKIE", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"nr {orzeczenie['ID_Orzeczenia']}", ln=True, align='C')
    pdf.ln(10)

    # Dane identyfikacyjne pacjenta
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, txt=f"Imię i Nazwisko: {pacjent['Imie']} {pacjent['Nazwisko']}", ln=True)
    pdf.cell(200, 8, txt=f"PESEL: {pacjent['PESEL']}", ln=True)
    pdf.ln(5)

    # Treść orzeczenia i decyzja lekarska
    pdf.set_font("Arial", 'B', 11)
    pdf.multi_cell(0, 8, txt=f"DECYZJA: {orzeczenie['Decyzja']}")
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, txt=f"Uwagi i zalecenia: {orzeczenie['UwagiLekarza']}")
    pdf.ln(5)
    pdf.cell(200, 8, txt=f"Termin kolejnego badania profilaktycznego: {orzeczenie['DataKolejnegoBadania']}", ln=True)
    
    # --- KOD QR I PODPIS CYFROWY ---
    # Generowanie kodu QR z sumą kontrolną SHA-256 dla weryfikacji autentyczności
    podpis_cyfrowy = orzeczenie['PodpisCyfrowy']
    qr_text = (
        f"Weryfikacja autentycznosci dokumentu\n"
        f"ID: {orzeczenie['ID_Orzeczenia']}\n"
        f"Pacjent: {pacjent['Nazwisko']}\n"
        f"Kod SHA-256: {podpis_cyfrowy}"
    )
    
    qr = qrcode.make(qr_text)
    qr_img_bytes = io.BytesIO()
    qr.save(qr_img_bytes, format='PNG')
    
    # Pozycjonowanie elementów na dole strony
    y_pos = 220
    pdf.image(qr_img_bytes, x=15, y=y_pos, w=35)
    
    pdf.set_xy(55, y_pos + 5)
    pdf.set_font("Arial", size=8)
    pdf.multi_cell(70, 4, f"Zatwierdzono Elektronicznie\nCertyfikat Autentycznosci (SHA-256):\n{podpis_cyfrowy}")

    # Wstawienie grafiki pieczątki/podpisu lekarza
    if pieczatka_path and os.path.exists(pieczatka_path):
        pdf.image(pieczatka_path, x=130, y=y_pos - 5, w=60)

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- KROK 3: FRAGMENT LIVE - AUTOMATYCZNA LISTA DO WYDRUKU ---
@st.fragment(run_every="30s")
def render_printable_list():
    """Automatycznie odświeżana lista orzeczeń gotowych do wydania pacjentowi."""
    # Pobieranie najświeższych danych z Google Sheets
    df_orzeczenia = get_data_as_df("Orzeczenia")
    df_wizyty = get_data_as_df("Wizyty")
    df_pacjenci = get_data_as_df("Pacjenci")

    if df_orzeczenia.empty:
        st.info("System oczekuje na wystawienie pierwszych orzeczeń przez lekarza...")
        return

    st.subheader("Ostatnio wystawione dokumenty ( gotowe do druku )")
    
    # Łączenie danych orzeczeń z danymi osobowymi pacjentów
    df_print = df_orzeczenia.merge(
        df_pacjenci[['PESEL', 'Imie', 'Nazwisko']], 
        left_on='PESEL_Pacjenta', 
        right_on='PESEL', 
        how='left'
    )
    
    # Wyświetlanie 10 najnowszych rekordów (najnowsze na górze)
    for idx, row in df_print.tail(10).iloc[::-1].iterrows():
        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"📄 **{row['Imie']} {row['Nazwisko']}**")
                st.caption(f"ID Orzeczenia: {row['ID_Orzeczenia']} | Status: {row['Decyzja']}")
            
            with col_btn:
                # Pobieranie powiązanej wizyty dla celów generowania notatek
                try:
                    wizyta_row = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(row['ID_Wizyty'])].iloc[0]
                    
                    # Generowanie pliku PDF w locie do pobrania
                    pieczatka = get_secure_signature()
                    pdf_bytes = generate_pdf(row, wizyta_row, row, pieczatka)
                    
                    st.download_button(
                        label="Drukuj PDF",
                        data=pdf_bytes,
                        file_name=f"Orzeczenie_{row['Nazwisko']}_{row['ID_Orzeczenia'].replace('/', '_')}.pdf",
                        mime="application/pdf",
                        key=f"btn_pdf_{row['ID_Orzeczenia']}",
                        use_container_width=True
                    )
                except Exception:
                    st.error("Błąd danych")

# Aktywacja automatycznego fragmentu na stronie
render_printable_list()
