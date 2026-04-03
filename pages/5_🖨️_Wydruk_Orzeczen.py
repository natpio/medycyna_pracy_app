import streamlit as st
import pandas as pd
import os
import urllib.request
import io
import time
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from db_service import get_data_as_df, apply_pro_style, upload_to_google_drive, update_record

# --- IMPORTY ZEWNĘTRZNYCH SZABLONÓW ---
try:
    from pdf_templates.pdf_orzeczenie import create_orzeczenie_pdf
    from pdf_templates.pdf_kbp import create_kbp_pdf
    from pdf_templates.pdf_sanepid import create_sanepid_pdf
    from pdf_templates.pdf_kierowca_wywiad import create_kierowca_wywiad_pdf
    from pdf_templates.pdf_uczen import create_uczen_pdf
    from pdf_templates.pdf_skierowanie_wcmp import create_skierowanie_wcmp_pdf
except ImportError as e:
    st.error(f"Błąd importu szablonów: {e}. Upewnij się, że przeniosłeś wszystkie pliki do folderu pdf_templates.")

# --- TWOJE ID FOLDERU KARTOTEKI NA GOOGLE DRIVE ---
FOLDER_KARTOTEKI_ID = "1zU0GawxmZN-LtvL6YTw3Y3tra7Ms7tgW"

st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="wide")
apply_pro_style()

def zmien_status_archiwum(id_orzeczenia, nowy_status):
    sukces = update_record("Orzeczenia", "ID_Orzeczenia", id_orzeczenia, {"Archiwum": nowy_status})
    if sukces:
        st.session_state[f"arch_status_{id_orzeczenia}"] = nowy_status
        st.cache_data.clear()
        st.rerun()

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

@st.cache_resource
def load_fonts():
    font_reg = "Roboto-Regular.ttf"
    font_bold = "Roboto-Bold.ttf"
    font_italic = "Roboto-Italic.ttf"
    try:
        if not os.path.exists(font_reg):
            urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", font_reg)
        if not os.path.exists(font_bold):
            urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", font_bold)
        if not os.path.exists(font_italic):
            urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Italic.ttf", font_italic)
    except:
        pass
    return font_reg, font_bold, font_italic

font_regular, font_bold, font_italic = load_fonts()
pieczatka_path = get_secure_signature()

def generate_pdf_router(typ_dokumentu, orz_data, wizyta, pacjent, firma, pieczatka_path):
    fonts = (font_regular, font_bold, font_italic)
    
    if typ_dokumentu == "Orzeczenie Lekarskie":
        return create_orzeczenie_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path, fonts)
    elif typ_dokumentu == "Karta Badania (KBP)":
        return create_kbp_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path, fonts)
    elif typ_dokumentu == "Orzeczenie Sanepid":
        return create_sanepid_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path, fonts)
    elif typ_dokumentu == "Oświadczenie Kierowcy":
        return create_kierowca_wywiad_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path, fonts)
    elif typ_dokumentu == "Zaświadczenie Uczeń/Student":
        return create_uczen_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path, fonts)
    elif typ_dokumentu == "Skierowanie WCMP":
        return create_skierowanie_wcmp_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path, fonts)
    else:
        return b""

def render_orzeczenie_row(orz, pacjent, wizyta, firma, is_archived):
    orz_id = orz.get('ID_Orzeczenia', '')
    decyzja = orz.get('Decyzja', '')
    typ_badania = wizyta.get('TypBadania', 'Brak danych')
    nazwa_firmy = firma.get('NazwaFirmy', 'Prywatnie / Brak Firmy')
    data_kolejnego = orz.get('DataKolejnegoBadania', '')

    with st.container(border=True):
        # Sekcja górna: Informacje o pacjencie i decyzji
        col_info, col_status = st.columns([4, 1])
        with col_info:
            st.markdown(f"#### 📄 {pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')} - {typ_badania}")
            st.caption(f"**PESEL:** {pacjent.get('PESEL', '')} | **Firma:** {nazwa_firmy} | **Ważne do:** {data_kolejnego} | **Nr:** {orz_id}")
            
            link = orz.get('Link_Drive', "")
            if pd.notna(link) and str(link).startswith("http"):
                st.markdown(f"[📂 Otwórz zapisaną kartotekę na Dysku Google]({link})")
                
        with col_status:
            color = "#059669" if "ZDOLNY" in decyzja.upper() and "NIEZDOLNY" not in decyzja.upper() else "#dc2626"
            st.markdown(f"<div style='text-align:right; font-weight:700; color:{color};'>{decyzja}</div>", unsafe_allow_html=True)
             
        st.divider()
        
        # Sekcja dolna: Wybór dokumentu i operacje
        col_sel, col_btn1, col_btn2, col_arch = st.columns([2.5, 1, 1.5, 1])
        
        # Inteligentne pokazywanie dostępnych dokumentów na podstawie skierowania
        dostepne_dokumenty = ["Orzeczenie Lekarskie", "Karta Badania (KBP)"]
        if "Sanitarno" in str(typ_badania): dostepne_dokumenty.append("Orzeczenie Sanepid")
        if "Kierowca" in str(typ_badania): dostepne_dokumenty.append("Oświadczenie Kierowcy")
        if "Uczeń" in str(typ_badania) or "Student" in str(typ_badania): dostepne_dokumenty.append("Zaświadczenie Uczeń/Student")
        if "Odwołanie" in str(typ_badania) or "WCMP" in str(typ_badania): dostepne_dokumenty.append("Skierowanie WCMP")
            
        with col_sel:
            wybrany_dok = st.selectbox(
                "Wybierz dokument do operacji:",
                options=dostepne_dokumenty,
                key=f"sel_{orz_id}",
                label_visibility="collapsed"
            )
            
        # Generowanie wybranego pliku w locie
        try:
            pdf_bytes = generate_pdf_router(wybrany_dok, orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path)
        except Exception as e:
            pdf_bytes = b""
            st.error(f"Błąd kompilacji PDF: {e}")

        with col_btn1:
            st.download_button(
                label="📥 Pobierz",
                data=pdf_bytes,
                file_name=f"{wybrany_dok.replace(' ', '_').replace('/', '_')}_{pacjent.get('Nazwisko', '')}.pdf",
                mime="application/pdf",
                key=f"dl_{orz_id}",
                use_container_width=True,
                disabled=(not pdf_bytes)
            )
            
        with col_btn2:
            if st.button("☁️ Zapisz na Dysku", key=f"cloud_{orz_id}", use_container_width=True, disabled=(not pdf_bytes)):
                with st.spinner("Wysyłanie do chmury..."):
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
                    safe_name = wybrany_dok.replace(' ', '_').replace('/', '_')
                    filename = f"{safe_name}_{pacjent.get('Nazwisko', '')}_{timestamp}.pdf"
                    
                    up_sukces, drive_id = upload_to_google_drive(pdf_bytes, filename, FOLDER_KARTOTEKI_ID)
                    
                    if up_sukces:
                        drive_link = f"https://drive.google.com/file/d/{drive_id}/view"
                        update_record("Orzeczenia", "ID_Orzeczenia", orz_id, {"Link_Drive": drive_link})
                        st.success("Zapisano!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Błąd wysyłania.")
        
        with col_arch:
            if is_archived:
                if st.button("⏪ Przywróć", key=f"restore_{orz_id}", use_container_width=True):
                    zmien_status_archiwum(orz_id, "NIE")
            else:
                if st.button("📦 Do archiwum", type="primary", key=f"arch_{orz_id}", use_container_width=True):
                    zmien_status_archiwum(orz_id, "TAK")


st.markdown("# 🖨️ Wydruki i Archiwizacja (Chmura)")
st.write("Wybierz dokument z listy, a następnie pobierz go lokalnie lub zapisz bezpośrednio w Kartotece Pacjenta na Dysku Google.")

df_orz = get_data_as_df("Orzeczenia")
df_wiz = get_data_as_df("Wizyty")
df_pac = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if not df_orz.empty:
    if 'Archiwum' not in df_orz.columns:
        df_orz['Archiwum'] = 'NIE'
        
    for index, row in df_orz.iterrows():
        orz_id = row['ID_Orzeczenia']
        if f"arch_status_{orz_id}" in st.session_state:
            df_orz.at[index, 'Archiwum'] = st.session_state[f"arch_status_{orz_id}"]

    df_aktualne = df_orz[df_orz['Archiwum'] != 'TAK']
    df_archiwum = df_orz[df_orz['Archiwum'] == 'TAK']

    tab_biezace, tab_archiwum = st.tabs([f"📄 Bieżące ({len(df_aktualne)})", f"📦 Archiwum ({len(df_archiwum)})"])

    with tab_biezace:
        if not df_aktualne.empty:
            for _, orz in df_aktualne.sort_values("ID_Orzeczenia", ascending=False).head(20).iterrows():
                wiz_id = str(orz.get('ID_Wizyty', ''))
                wiz = df_wiz[df_wiz['ID_Wizyty'].astype(str) == wiz_id].iloc[0] if not df_wiz.empty and wiz_id in df_wiz['ID_Wizyty'].astype(str).values else pd.Series()
                pac_pesel = str(orz.get('PESEL_Pacjenta', ''))
                pac = df_pac[df_pac['PESEL'].astype(str) == pac_pesel].iloc[0] if not df_pac.empty and pac_pesel in df_pac['PESEL'].astype(str).values else pd.Series()
                nip = str(wiz.get('NIP_Firmy', '0'))
                fir = df_firmy[df_firmy['NIP'].astype(str) == nip].iloc[0] if not df_firmy.empty and nip in df_firmy['NIP'].astype(str).values else pd.Series()
                
                render_orzeczenie_row(orz, pac, wiz, fir, is_archived=False)
        else:
            st.info("Brak bieżących orzeczeń do wydruku.")

    with tab_archiwum:
        if not df_archiwum.empty:
            for _, orz in df_archiwum.sort_values("ID_Orzeczenia", ascending=False).head(20).iterrows():
                wiz_id = str(orz.get('ID_Wizyty', ''))
                wiz = df_wiz[df_wiz['ID_Wizyty'].astype(str) == wiz_id].iloc[0] if not df_wiz.empty and wiz_id in df_wiz['ID_Wizyty'].astype(str).values else pd.Series()
                pac_pesel = str(orz.get('PESEL_Pacjenta', ''))
                pac = df_pac[df_pac['PESEL'].astype(str) == pac_pesel].iloc[0] if not df_pac.empty and pac_pesel in df_pac['PESEL'].astype(str).values else pd.Series()
                nip = str(wiz.get('NIP_Firmy', '0'))
                fir = df_firmy[df_firmy['NIP'].astype(str) == nip].iloc[0] if not df_firmy.empty and nip in df_firmy['NIP'].astype(str).values else pd.Series()
                
                render_orzeczenie_row(orz, pac, wiz, fir, is_archived=True)
        else:
            st.info("Archiwum jest puste.")
else:
    st.warning("Brak wystawionych orzeczeń w systemie.")
