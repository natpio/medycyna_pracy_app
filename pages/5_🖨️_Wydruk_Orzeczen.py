import streamlit as st
import pandas as pd
import os
import urllib.request
import io
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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="wide")
apply_pro_style()

# --- FUNKCJA ARCHIWIZACJI ---
def zmien_status_archiwum(id_orzeczenia, nowy_status):
    """Zmienia status archiwum w bazie danych i czyści cache."""
    sukces = update_record("Orzeczenia", "ID_Orzeczenia", id_orzeczenia, {"Archiwum": nowy_status})
    if sukces:
        st.session_state[f"arch_status_{id_orzeczenia}"] = nowy_status
        st.cache_data.clear()
        st.rerun()

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

# --- POBIERANIE CZCIONEK ---
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

st.markdown("# 🖨️ Centrum Wydruków i Archiwum")
st.write("Generuj dokumenty PDF, wysyłaj je na Dysk Google i oznaczaj jako zakończone.")

# Pobieranie danych
df_orz = get_data_as_df("Orzeczenia")
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

def render_orzeczenie_row(orz, pacjent, wizyta, firma):
    orz_id = orz['ID_Orzeczenia']
    decyzja = orz['Decyzja']
    typ_badania = wizyta['TypBadania']
    nazwa_firmy = firma['NazwaFirmy'] if not firma.empty else "Brak powiązanej firmy"
    data_kolejnego = orz['DataKolejnegoBadania']
    
    with st.expander(f"📑 {orz_id} | {pacjent['Imie']} {pacjent['Nazwisko']} | {typ_badania} ({decyzja})"):
        col1, col2, col3 = st.columns([1, 1.5, 1])
        
        with col1:
            st.markdown(f"**Pesel:** {pacjent['PESEL']}<br>**Firma:** {nazwa_firmy}", unsafe_allow_html=True)
            st.markdown(f"**Ważne do:** {data_kolejnego}")
            
            # Link do chmury (jeśli istnieje)
            link = orz.get('Link_Drive', "")
            if pd.notna(link) and str(link).startswith("http"):
                st.link_button("📂 Otwórz z chmury", link, type="primary")

        with col2:
            st.markdown("#### 1. Generowanie PDF (Pobieranie)")
            fonts = (font_regular, font_bold, font_italic)
            # Przycisk 1: Główne Orzeczenie
            pdf_main = create_orzeczenie_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts)
            st.download_button(
                label="📄 Orzeczenie Lekarskie",
                data=pdf_main,
                file_name=f"Orzeczenie_{orz_id.replace('/','_')}.pdf",
                mime="application/pdf",
                key=f"dl_orz_{orz_id}"
            )
            # Przycisk 2: Karta Badania
            pdf_kbp = create_kbp_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts)
            st.download_button(
                label="📋 Karta Badania Profilaktycznego",
                data=pdf_kbp,
                file_name=f"KBP_{orz_id.replace('/','_')}.pdf",
                mime="application/pdf",
                key=f"dl_kbp_{orz_id}"
            )
            
            # Przyciski dla dokumentów dodatkowych w rzędzie
            c_dod1, c_dod2 = st.columns(2)
            if "Sanitarno" in str(typ_badania):
                pdf_san = create_sanepid_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts)
                c_dod1.download_button("🍏 Orzeczenie Sanepid", data=pdf_san, file_name=f"Sanepid_{orz_id.replace('/','_')}.pdf", mime="application/pdf", key=f"dl_san_{orz_id}")
            if "Kierowca" in str(typ_badania):
                pdf_kier = create_kierowca_wywiad_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts)
                c_dod1.download_button("🚗 Oświadczenie Kierowcy", data=pdf_kier, file_name=f"Oswiadczenie_{orz_id.replace('/','_')}.pdf", mime="application/pdf", key=f"dl_kier_{orz_id}")
            if "Uczeń" in str(typ_badania) or "Student" in str(typ_badania):
                pdf_ucz = create_uczen_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts)
                c_dod2.download_button("🎓 Zaświadczenie Uczeń", data=pdf_ucz, file_name=f"Uczen_{orz_id.replace('/','_')}.pdf", mime="application/pdf", key=f"dl_ucz_{orz_id}")
            if "Odwołanie" in str(typ_badania) or "WCMP" in str(typ_badania):
                pdf_wcmp = create_skierowanie_wcmp_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts)
                c_dod2.download_button("🏥 Skierowanie WCMP", data=pdf_wcmp, file_name=f"WCMP_{orz_id.replace('/','_')}.pdf", mime="application/pdf", key=f"dl_wcmp_{orz_id}")

        with col3:
            st.markdown("#### 2. Dysk Google i Archiwum")
            
            # --- SEKCJA ZAPISU DO CHMURY ---
            if st.button("☁️ Zapisz wszystkie PDFy do Kartoteki", type="secondary", key=f"cloud_{orz_id}", use_container_width=True):
                with st.spinner("Wysyłanie plików na Google Drive..."):
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
                    fonts = (font_regular, font_bold, font_italic)
                    
                    # 1. Wysyłanie Głównego Orzeczenia
                    up_sukces, drive_id = upload_to_google_drive(create_orzeczenie_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts), f"Orzeczenie_{pacjent['Nazwisko']}_{timestamp}.pdf", FOLDER_KARTOTEKI_ID)
                    
                    # Zapisywanie linku do bazy, aby był dostępny w historii pacjenta
                    if up_sukces:
                        drive_link = f"https://drive.google.com/file/d/{drive_id}/view"
                        update_record("Orzeczenia", "ID_Orzeczenia", orz_id, {"Link_Drive": drive_link})
                        st.success("Wysłano Główne Orzeczenie!")
                        
                    # 2. Wysyłanie KBP
                    upload_to_google_drive(create_kbp_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts), f"KBP_{pacjent['Nazwisko']}_{timestamp}.pdf", FOLDER_KARTOTEKI_ID)
                    
                    # 3. Wysyłanie dodatkowych dokumentów (jeśli dotyczy)
                    if "Sanitarno" in str(typ_badania):
                        upload_to_google_drive(create_sanepid_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts), f"Sanepid_{pacjent['Nazwisko']}_{timestamp}.pdf", FOLDER_KARTOTEKI_ID)
                    if "Uczeń" in str(typ_badania) or "Student" in str(typ_badania):
                         upload_to_google_drive(create_uczen_pdf(orz.to_dict(), wizyta.to_dict(), pacjent.to_dict(), firma.to_dict() if not firma.empty else {}, pieczatka_path, fonts), f"Uczen_{pacjent['Nazwisko']}_{timestamp}.pdf", FOLDER_KARTOTEKI_ID)
                         
                    st.balloons()
                    st.success("Wszystkie dokumenty zostały bezpiecznie zapisane w kartotece pacjenta!")

            st.markdown("<br>", unsafe_allow_html=True)
            # --- SEKCJA ARCHIWIZACJI ---
            if orz['Archiwum'] == 'TAK':
                if st.button("⏪ Przywróć do Bieżących", key=f"btn_przywroc_{orz_id}"):
                    zmien_status_archiwum(orz_id, "NIE")
            else:
                if st.button("📦 Przenieś do Archiwum", type="primary", key=f"btn_arch_{orz_id}"):
                    zmien_status_archiwum(orz_id, "TAK")


if not df_orz.empty:
    if 'Archiwum' not in df_orz.columns:
        df_orz['Archiwum'] = 'NIE'
        
    for index, row in df_orz.iterrows():
        orz_id = row['ID_Orzeczenia']
        if f"arch_status_{orz_id}" in st.session_state:
            df_orz.at[index, 'Archiwum'] = st.session_state[f"arch_status_{orz_id}"]

    df_aktualne = df_orz[df_orz['Archiwum'] != 'TAK']
    df_archiwum = df_orz[df_orz['Archiwum'] == 'TAK']

    tab_biezace, tab_archiwum = st.tabs([f"📄 Bieżące Orzeczenia ({len(df_aktualne)})", f"📦 Archiwum ({len(df_archiwum)})"])

    with tab_biezace:
        if not df_aktualne.empty:
            for _, orz in df_aktualne.sort_values("ID_Orzeczenia", ascending=False).head(20).iterrows():
                try:
                    wizyta = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(orz['ID_Wizyty'])].iloc[0]
                    pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(orz['PESEL_Pacjenta'])].iloc[0]
                    firma = df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].iloc[0] if not df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].empty else pd.DataFrame()
                    render_orzeczenie_row(orz, pacjent, wizyta, firma)
                except IndexError:
                    st.error(f"Błąd spójności danych dla orzeczenia {orz['ID_Orzeczenia']}")
        else:
            st.info("Brak bieżących orzeczeń do wydruku. Wszystkie zostały zarchiwizowane.")

    with tab_archiwum:
        if not df_archiwum.empty:
            for _, orz in df_archiwum.sort_values("ID_Orzeczenia", ascending=False).head(20).iterrows():
                 try:
                    wizyta = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(orz['ID_Wizyty'])].iloc[0]
                    pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(orz['PESEL_Pacjenta'])].iloc[0]
                    firma = df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].iloc[0] if not df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].empty else pd.DataFrame()
                    render_orzeczenie_row(orz, pacjent, wizyta, firma)
                 except IndexError:
                    pass
        else:
            st.info("Archiwum jest puste.")
else:
    st.warning("Brak wystawionych orzeczeń w systemie.")
