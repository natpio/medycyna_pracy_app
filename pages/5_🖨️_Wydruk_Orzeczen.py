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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="wide")

# --- URUCHOMIENIE STYLU PRO ---
apply_pro_style()

st.markdown("# 🖨️ Generator Certyfikatów PDF")
st.write("Wygeneruj nienaruszalny dokument PDF z kodem QR i bezpiecznym faksymile podpisu.")

# --- BEZPIECZNE POBIERANIE PIECZĄTKI Z GOOGLE DRIVE ---
@st.cache_resource
def get_secure_signature():
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
        return None

# --- POBIERANIE POLSKICH CZCIONEK ---
@st.cache_resource
def load_fonts():
    font_reg = "Roboto-Regular.ttf"
    font_bold = "Roboto-Bold.ttf"
    try:
        if not os.path.exists(font_reg):
            urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", font_reg)
        if not os.path.exists(font_bold):
            urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", font_bold)
    except:
        pass # W razie braku internetu uzyjemy wbudowanych
    return font_reg, font_bold

font_regular, font_bold = load_fonts()
pieczatka_path = get_secure_signature()

# --- FUNKCJA GENERUJĄCA DOKUMENT (BEZPIECZNA) ---
def generate_pdf_bytes(orz_data, wizyta, pacjent, firma, pieczatka_path, font_regular, font_bold):
    pdf = FPDF()
    pdf.add_page()
    
    # Obsługa czcionek (Fallback na Arial jeśli brakuje pliku)
    if os.path.exists(font_regular) and os.path.exists(font_bold):
        pdf.add_font("Roboto", style="", fname=font_regular)
        pdf.add_font("Roboto", style="B", fname=font_bold)
        font_family = "Roboto"
    else:
        font_family = "Arial"
        
    try:
        data_wystawienia = f"{orz_data['ID_Orzeczenia'].split('/')[1][:4]}-{orz_data['ID_Orzeczenia'].split('/')[1][4:6]}-{orz_data['ID_Orzeczenia'].split('/')[1][6:8]}"
    except:
        data_wystawienia = str(datetime.date.today())

    # Bezpieczne wyciąganie danych za pomocą .get()
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', orz_data.get('PodpisCyfrowy', 'Brak autoryzacji')))
    
    pdf.set_font(font_family, size=10)
    pdf.cell(0, 10, f"Luboń, dnia: {data_wystawienia} r.", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font(font_family, style="B", size=18)
    pdf.cell(0, 10, "ORZECZENIE LEKARSKIE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, size=10)
    pdf.cell(0, 5, f"Nr {orz_data.get('ID_Orzeczenia', 'Brak')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font(font_family, size=11)
    pdf.cell(0, 6, f"Wydane na podstawie skierowania z dnia: {wizyta.get('DataWizyty', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Wystawionego przez pracodawcę:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, style="B", size=11)
    pdf.cell(0, 6, f"{firma.get('NazwaFirmy', '')} (NIP: {firma.get('NIP', '')})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, size=11)
    pdf.cell(0, 6, f"{firma.get('Adres', '')}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.cell(0, 6, f"W wyniku badania profilaktycznego ({wizyta.get('TypBadania', '')}) pacjenta:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, style="B", size=12)
    pdf.cell(0, 8, f"Pana/Pani: {pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, size=11)
    pdf.cell(0, 6, f"PESEL: {pacjent.get('PESEL', '')}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_font(font_family, style="B", size=14)
    pdf.cell(0, 10, "ORZEKAM, ŻE BADANY JEST:", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_font(font_family, style="B", size=16)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 15, f"{str(orz_data.get('Decyzja', '')).upper()}", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    pdf.set_font(font_family, size=11)
    pdf.cell(0, 6, "Wobec braku przeciwwskazań zdrowotnych.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Data następnego badania okresowego: {orz_data.get('DataKolejnegoBadania', '')}", new_x="LMARGIN", new_y="NEXT")
    
    # --- ZAAWANSOWANE GENEROWANIE KODU QR ---
    data_generowania = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    qr_text = (
        f"WERYFIKACJA ORZECZENIA LEKARSKIEGO\n"
        f"-----------------------------------\n"
        f"Nr orzeczenia: {orz_data.get('ID_Orzeczenia', '')}\n"
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
    
    pdf.set_xy(55, y_bottom + 5)
    pdf.set_font(font_family, size=8)
    pdf.multi_cell(60, 4, f"Zatwierdzono Elektronicznie\nlek. Jarosław Tarkowski\nCertyfikat (SHA-256):\n{podpis_cyfrowy}", align="L")
    
    if pieczatka_path and os.path.exists(pieczatka_path):
        pdf.image(pieczatka_path, x=130, y=y_bottom - 5, w=60)
    else:
        pdf.set_xy(140, y_bottom + 10)
        pdf.set_font(font_family, size=10)
        pdf.cell(50, 20, "Pieczęć i podpis lekarza", border=1, align="C")

    return bytes(pdf.output())

# --- FRAGMENT LIVE DO LISTY DOKUMENTÓW ---
@st.fragment(run_every="30s")
def render_live_pdf_list():
    df_orzeczenia = get_data_as_df("Orzeczenia")
    df_wizyty = get_data_as_df("Wizyty")
    df_pacjenci = get_data_as_df("Pacjenci")
    df_firmy = get_data_as_df("Firmy")

    if df_orzeczenia.empty:
        st.info("Brak wystawionych orzeczeń w systemie.")
        return

    st.subheader("Orzeczenia gotowe do wydania (Odświeża się co 30 sek)")
    
    # Sortowanie od najnowszego
    df_orzeczenia = df_orzeczenia.sort_values(by="ID_Orzeczenia", ascending=False).head(10)

    for _, orz_data in df_orzeczenia.iterrows():
        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1])
            
            try:
                # Bezpieczne pobieranie powiązanych danych
                pesel = str(orz_data.get('PESEL_Pacjenta', ''))
                
                pacjent_df = df_pacjenci[df_pacjenci['PESEL'].astype(str) == pesel] if not df_pacjenci.empty else pd.DataFrame()
                pacjent = pacjent_df.iloc[0].to_dict() if not pacjent_df.empty else {"Imie": "Nieznane", "Nazwisko": "Nieznane", "PESEL": pesel}
                
                id_wizyty = str(orz_data.get('ID_Wizyty', ''))
                wizyta_df = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == id_wizyty] if not df_wizyty.empty else pd.DataFrame()
                wizyta = wizyta_df.iloc[0].to_dict() if not wizyta_df.empty else {"NIP_Firmy": "0000", "TypBadania": "Nieznany"}
                
                nip = str(wizyta.get('NIP_Firmy', ''))
                firma_df = df_firmy[df_firmy['NIP'].astype(str) == nip] if not df_firmy.empty else pd.DataFrame()
                firma = firma_df.iloc[0].to_dict() if not firma_df.empty else {"NazwaFirmy": "Brak danych firmy", "NIP": nip, "Adres": ""}

                with col_info:
                    st.markdown(f"📄 **{pacjent['Nazwisko']} {pacjent['Imie']}**")
                    st.caption(f"ID: {orz_data.get('ID_Orzeczenia', '')} | Ważne do: {orz_data.get('DataKolejnegoBadania', 'Brak')}")
                
                with col_btn:
                    pdf_bytes = generate_pdf_bytes(orz_data, wizyta, pacjent, firma, pieczatka_path, font_regular, font_bold)
                    st.download_button(
                        label="Pobierz PDF",
                        data=pdf_bytes,
                        file_name=f"Orzeczenie_{pacjent['Nazwisko']}_{str(orz_data.get('ID_Orzeczenia', '')).replace('/', '_')}.pdf",
                        mime="application/pdf",
                        key=f"dl_{orz_data.get('ID_Orzeczenia', '')}",
                        use_container_width=True
                    )
            except Exception as e:
                # Wyświetlamy dokładnie treść błędu, żeby wiedzieć co się zepsuło
                with col_info:
                    st.error(f"Problem techniczny z tym dokumentem: {e}")
                with col_btn:
                    st.button("Błąd", disabled=True, key=f"err_{orz_data.get('ID_Orzeczenia', 'err')}")

# Wywołanie
render_live_pdf_list()
