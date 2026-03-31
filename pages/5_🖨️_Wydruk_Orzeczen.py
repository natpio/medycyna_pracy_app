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

# Uruchomienie stylu wizualnego zdefiniowanego w systemie [cite: 1, 3]
apply_pro_style() [cite: 1, 3]

st.markdown("# 🖨️ Generator Certyfikatów PDF")
st.write("Wygeneruj nienaruszalny dokument PDF z kodem QR i bezpiecznym faksymile podpisu.")

# --- 2. BEZPIECZNE POBIERANIE PIECZĄTKI Z GOOGLE DRIVE ---
@st.cache_resource
def get_secure_signature():
    """Pobiera pieczątkę z Dysku Google przez autoryzowany Service Account."""
    file_id = st.secrets.get("doctor", {}).get("signature_file_id")
    if not file_id or file_id == "TUTAJ_WKLEJ_SWOJE_ID_PLIKU_Z_LINKU":
        return None
        
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=creds)
        
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        path = "temp_signature.png"
        with open(path, "wb") as f:
            f.write(fh.getvalue())
        return path
    except Exception as e:
        st.error(f"Błąd pobierania pieczątki: {e}")
        return None

# --- 3. LOGIKA GENEROWANIA PDF ---
def generate_pdf(pacjent, wizyta, orzeczenie, pieczatka_path):
    """Tworzy finalny dokument PDF z pełną weryfikacją cyfrową."""
    pdf = FPDF()
    pdf.add_page()
    
    # Próba załadowania czcionki Roboto dla zachowania Twojego designu
    try:
        pdf.add_font('Roboto', '', 'Roboto-Regular.ttf', uni=True)
        pdf.set_font('Roboto', size=12)
    except:
        pdf.set_font("Arial", size=12)

    # Nagłówek i Tytuł
    pdf.cell(200, 10, txt="ORZECZENIE LEKARSKIE", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"nr {orzeczenie['ID_Orzeczenia']}", ln=True, align='C')
    pdf.ln(10)

    # Dane Pacjenta
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, txt=f"Imię i Nazwisko: {pacjent['Imie']} {pacjent['Nazwisko']}", ln=True)
    pdf.cell(200, 8, txt=f"PESEL: {pacjent['PESEL']}", ln=True)
    pdf.ln(5)

    # Treść merytoryczna
    pdf.set_font("Arial", 'B', 11)
    pdf.multi_cell(0, 8, txt=f"DECYZJA: {orzeczenie['Decyzja']}")
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, txt=f"Uwagi: {orzeczenie['UwagiLekarza']}")
    pdf.ln(5)
    pdf.cell(200, 8, txt=f"Termin kolejnego badania: {orzeczenie['DataKolejnegoBadania']}", ln=True)
    
    # --- KOD QR I CERTYFIKAT (Pełna Twoja wersja) ---
    podpis_cyfrowy = orzeczenie['PodpisCyfrowy']
    qr_text = (
        f"WERYFIKACJA DOKUMENTU\\n"
        f"ID: {orzeczenie['ID_Orzeczenia']}\\n"
        f"Pacjent: {pacjent['Imie']} {pacjent['Nazwisko']}\\n"
        f"Lekarz: Jarosław Tarkowski\\n"
        f"Nr rejestru: 30/1JT/370\\n"
        f"PWZ: 8776405\\n\\n"
        f"CERTYFIKAT AUTENTYCZNOŚCI:\\n"
        f"{podpis_cyfrowy}"
    )
    
    qr = qrcode.make(qr_text)
    qr_img_bytes = io.BytesIO()
    qr.save(qr_img_bytes, format='PNG')
    
    y_bottom = 220
    pdf.image(qr_img_bytes, x=15, y=y_bottom, w=35)
    
    # Opis obok kodu QR
    pdf.set_xy(55, y_bottom + 5)
    pdf.set_font("Arial", size=8)
    pdf.multi_cell(60, 4, f"Zatwierdzono Elektronicznie\\nlek. Jarosław Tarkowski\\nCertyfikat (SHA-256):\\n{podpis_cyfrowy}", align="L")
    
    # Wstawianie pieczątki z prawej strony
    if pieczatka_path and os.path.exists(pieczatka_path):
        pdf.image(pieczatka_path, x=130, y=y_bottom - 5, w=60)
    else:
        pdf.set_xy(140, y_bottom + 10)
        pdf.cell(40, 10, "PODPIS ELEKTRONICZNY", border=1, align='C')

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- KROK 3: FRAGMENT LIVE - AUTOMATYCZNA LISTA (All-in-One) ---
@st.fragment(run_every="30s")
def render_printable_list():
    """Odświeża listę orzeczeń co 30 sekund bez przeładowania strony."""
    # Pobranie świeżych danych
    df_orzeczenia = get_data_as_df("Orzeczenia") [cite: 1, 2, 3]
    df_wizyty = get_data_as_df("Wizyty") [cite: 1, 2, 3]
    df_pacjenci = get_data_as_df("Pacjenci") [cite: 1, 2, 3]

    if df_orzeczenia.empty:
        st.info("System czeka na wystawienie orzeczeń przez lekarza...")
        return

    st.subheader("Orzeczenia gotowe do wydania")
    
    # Łączenie danych pacjenta z orzeczeniami
    df_print = df_orzeczenia.merge(
        df_pacjenci[['PESEL', 'Imie', 'Nazwisko']], 
        left_on='PESEL_Pacjenta', 
        right_on='PESEL', 
        how='left'
    )
    
    # Iteracja po 10 najnowszych rekordach
    for idx, row in df_print.tail(10).iloc[::-1].iterrows():
        with st.container(border=True):
            c_info, c_btn = st.columns([3, 1])
            with c_info:
                st.markdown(f"📄 **{row['Nazwisko']} {row['Imie']}**")
                st.caption(f"ID: {row['ID_Orzeczenia']} | Ważne do: {row['DataKolejnegoBadania']}")
            
            with c_btn:
                try:
                    # Szukamy wizyty dla notatek
                    wiz_row = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(row['ID_Wizyty'])].iloc[0]
                    
                    # Przygotowanie PDF
                    path_sig = get_secure_signature()
                    pdf_data = generate_pdf(row, wiz_row, row, path_sig)
                    
                    st.download_button(
                        label="Pobierz PDF",
                        data=pdf_data,
                        file_name=f"Orzeczenie_{row['Nazwisko']}_{row['ID_Orzeczenia'].replace('/', '_')}.pdf",
                        mime="application/pdf",
                        key=f"btn_{row['ID_Orzeczenia']}",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error("Błąd generowania")

# Uruchomienie fragmentu
render_printable_list()
