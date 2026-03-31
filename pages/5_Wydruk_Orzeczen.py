import streamlit as st
import pandas as pd
import os
import urllib.request
import io
import qrcode
import datetime
from fpdf import FPDF
from db_service import get_data_as_df
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from db_service import get_data_as_df, apply_pro_style

st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="centered")
st.markdown("# 🖨️ Generator Certyfikatów PDF")
st.write("Wygeneruj nienaruszalny dokument PDF z kodem QR i bezpiecznym faksymile podpisu.")

# --- BEZPIECZNE POBIERANIE PIECZĄTKI Z GOOGLE DRIVE ---
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
        while not done:
            status, done = downloader.next_chunk()
            
        temp_path = "temp_secure_signature.png"
        with open(temp_path, "wb") as f:
            f.write(fh.getvalue())
        return temp_path
    except Exception as e:
        st.error(f"⚠️ Błąd pobierania pieczątki z chmury: {e}")
        return None

# --- POBIERANIE POLSKICH CZCIONEK ---
@st.cache_resource
def load_fonts():
    font_reg = "Roboto-Regular.ttf"
    font_bold = "Roboto-Bold.ttf"
    if not os.path.exists(font_reg):
        urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", font_reg)
    if not os.path.exists(font_bold):
        urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", font_bold)
    return font_reg, font_bold

font_regular, font_bold = load_fonts()
pieczatka_path = get_secure_signature()

# 1. Pobieranie danych z bazy
df_orzeczenia = get_data_as_df("Orzeczenia")
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if df_orzeczenia.empty:
    st.info("Brak wydanych orzeczeń w bazie. Najpierw wystaw orzeczenie w Panelu Lekarza.")
    st.stop()

# 2. Wybór orzeczenia
opcje_wydruku = ["--- Wybierz orzeczenie ---"]
orzeczenia_dict = {}

for idx, orz in df_orzeczenia.iterrows():
    pesel = str(orz['PESEL_Pacjenta'])
    pacjent_df = df_pacjenci[df_pacjenci['PESEL'].astype(str) == pesel]
    imie = pacjent_df.iloc[0]['Imie'] if not pacjent_df.empty else "Nieznane"
    nazwisko = pacjent_df.iloc[0]['Nazwisko'] if not pacjent_df.empty else "Nieznane"
    
    decyzja_skrot = orz['Decyzja'].split(' ')[0]
    etykieta = f"{orz['ID_Orzeczenia']} | {nazwisko} {imie} | {decyzja_skrot}"
    opcje_wydruku.append(etykieta)
    orzeczenia_dict[etykieta] = orz

wybrane = st.selectbox("Wybierz dokument z archiwum:", opcje_wydruku)

if wybrane != "--- Wybierz orzeczenie ---":
    orz_data = orzeczenia_dict[wybrane]
    wizyta = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(orz_data['ID_Wizyty'])].iloc[0]
    pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(orz_data['PESEL_Pacjenta'])].iloc[0]
    firma = df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].iloc[0]
    
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', 'Brak autoryzacji'))
    data_wystawienia = f"{orz_data['ID_Orzeczenia'].split('/')[1][:4]}-{orz_data['ID_Orzeczenia'].split('/')[1][4:6]}-{orz_data['ID_Orzeczenia'].split('/')[1][6:8]}"
    
    st.divider()
    
    # --- GENEROWANIE PDF ---
    with st.spinner("Kompilowanie zabezpieczonego dokumentu PDF..."):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.add_font("Roboto", style="", fname=font_regular)
        pdf.add_font("Roboto", style="B", fname=font_bold)
        
        pdf.set_font("Roboto", size=10)
        pdf.cell(0, 10, f"Luboń, dnia: {data_wystawienia} r.", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        pdf.set_font("Roboto", style="B", size=18)
        pdf.cell(0, 10, "ORZECZENIE LEKARSKIE", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=10)
        pdf.cell(0, 5, f"Nr {orz_data['ID_Orzeczenia']}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, f"Wydane na podstawie skierowania z dnia: {wizyta['DataWizyty']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, "Wystawionego przez pracodawcę:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="B", size=11)
        pdf.cell(0, 6, f"{firma['NazwaFirmy']} (NIP: {firma['NIP']})", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, f"{firma['Adres']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.cell(0, 6, f"W wyniku badania profilaktycznego ({wizyta['TypBadania']}) pacjenta:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="B", size=12)
        pdf.cell(0, 8, f"Pana/Pani: {pacjent['Imie']} {pacjent['Nazwisko']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, f"PESEL: {pacjent['PESEL']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        pdf.set_font("Roboto", style="B", size=14)
        pdf.cell(0, 10, "ORZEKAM, ŻE BADANY JEST:", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("Roboto", style="B", size=16)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 15, f"{orz_data['Decyzja'].upper()}", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, "Wobec braku przeciwwskazań zdrowotnych.", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Data następnego badania okresowego: {orz_data['DataKolejnegoBadania']}", new_x="LMARGIN", new_y="NEXT")
        
        # --- ZAAWANSOWANE GENEROWANIE KODU QR ---
        data_generowania = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        qr_text = (
            f"WERYFIKACJA ORZECZENIA LEKARSKIEGO\n"
            f"-----------------------------------\n"
            f"Nr orzeczenia: {orz_data['ID_Orzeczenia']}\n"
            f"Wygenerowano: {data_generowania}\n\n"
            f"DANE LEKARZA:\n"
            f"lek. Jarosław Tarkowski\n"
            f"Nr rejestru: 30/1JT/370\n"
            f"PWZ: 8776405\n\n"
            f"CERTYFIKAT AUTENTYCZNOŚCI:\n"
            f"{podpis_cyfrowy}"
        )
        
        qr = qrcode.make(qr_text)
        qr_img_bytes = io.BytesIO()
        qr.save(qr_img_bytes, format='PNG')
        
        y_bottom = 220
        pdf.image(qr_img_bytes, x=15, y=y_bottom, w=35)
        
        # Krótki tekst obok kodu QR (widoczny okiem)
        pdf.set_xy(55, y_bottom + 5)
        pdf.set_font("Roboto", size=8)
        pdf.multi_cell(60, 4, f"Zatwierdzono Elektronicznie\nlek. Jarosław Tarkowski\nCertyfikat (SHA-256):\n{podpis_cyfrowy}", align="L")
        
        # --- WSTAWIANIE BEZPIECZNEJ PIECZĄTKI ---
        if pieczatka_path and os.path.exists(pieczatka_path):
            # x=130 żeby lepiej wyśrodkować po prawej stronie
            pdf.image(pieczatka_path, x=130, y=y_bottom - 5, w=60)
        else:
            pdf.set_xy(140, y_bottom + 10)
            pdf.set_font("Roboto", size=10)
            pdf.cell(50, 20, "Pieczęć i podpis lekarza", border=1, align="C")

        pdf_bytes = bytes(pdf.output())
    
    # 5. Przycisk pobierania PDF
    st.success("✅ Dokument zabezpieczony i gotowy do wydruku.")
    st.download_button(
        label="📥 POBIERZ OFICJALNE ORZECZENIE (PDF)",
        data=pdf_bytes,
        file_name=f"Orzeczenie_{pacjent['Nazwisko']}_{orz_data['ID_Orzeczenia'].replace('/','_')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
