import streamlit as st
import pandas as pd
import os
import urllib.request
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from db_service import get_data_as_df, apply_pro_style

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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="wide")
apply_pro_style()

# --- FUNKCJA ARCHIWIZACJI ---
def zmien_status_archiwum(id_orzeczenia, nowy_status):
    """
    Funkcja zarządzająca statusem archiwum. 
    Wymaga kolumny 'Archiwum' w bazie danych (tabela Orzeczenia).
    """
    try:
        # Próba importu Twojej funkcji aktualizującej bazę z db_service.py
        from db_service import update_record 
        update_record("Orzeczenia", "ID_Orzeczenia", id_orzeczenia, {"Archiwum": nowy_status})
        st.toast(f"Zapisano w bazie: {id_orzeczenia} -> {nowy_status}")
    except ImportError:
        # Fallback (działanie w pamięci RAM), jeśli nie masz jeszcze funkcji update_record
        st.session_state[f"arch_status_{id_orzeczenia}"] = nowy_status
        st.toast("Przeniesiono (Działa w trybie pamięci sesji).")

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

# --- KONTROLER / ROUTER SZABLONÓW ---
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
        raise ValueError("Nieznany typ dokumentu")

# --- FUNKCJA RYSOWANIA WIERSZA Z DOKUMENTEM ---
def render_orzeczenie_row(orz, is_archived):
    id_wiz = str(orz.get('ID_Wizyty', ''))
    wiz = df_wiz[df_wiz['ID_Wizyty'].astype(str) == id_wiz].iloc[0] if not df_wiz.empty and id_wiz in df_wiz['ID_Wizyty'].astype(str).values else {}
    
    pesel = str(orz.get('PESEL_Pacjenta', ''))
    pac = df_pac[df_pac['PESEL'].astype(str) == pesel].iloc[0] if not df_pac.empty and pesel in df_pac['PESEL'].astype(str).values else {"Imie": "Brak", "Nazwisko": "Danych", "PESEL": pesel}
    
    nip = str(wiz.get('NIP_Firmy', '0'))
    fir = df_firmy[df_firmy['NIP'].astype(str) == nip].iloc[0] if not df_firmy.empty and nip in df_firmy['NIP'].astype(str).values else {"NazwaFirmy": "Prywatnie / Brak Firmy", "Adres": "-", "NIP": nip}

    with st.container(border=True):
        col_info, col_doc, col_dl, col_arch = st.columns([2.5, 1.5, 1, 1])
        
        with col_info:
            st.markdown(f"📄 **{pac.get('Nazwisko', '')} {pac.get('Imie', '')}**")
            st.caption(f"PESEL: {pac.get('PESEL', '')} | Firma: {fir.get('NazwaFirmy', '')}")
        
        with col_doc:
            typ_dokumentu = st.selectbox(
                "Wybierz dokument:",
                ["Orzeczenie Lekarskie", "Karta Badania (KBP)", "Orzeczenie Sanepid", "Oświadczenie Kierowcy", "Zaświadczenie Uczeń/Student", "Skierowanie WCMP"],
                key=f"sel_{orz.get('ID_Orzeczenia', '')}",
                label_visibility="collapsed"
            )
        
        with col_dl:
            try:
                pdf_bytes = generate_pdf_router(typ_dokumentu, orz, wiz, pac, fir, pieczatka_path)
                st.download_button(
                    label="📥 Pobierz",
                    data=pdf_bytes,
                    file_name=f"{typ_dokumentu.replace(' ', '_').replace('/', '_')}_{pac.get('Nazwisko', '')}.pdf",
                    mime="application/pdf",
                    key=f"dl_{typ_dokumentu}_{orz.get('ID_Orzeczenia', '')}",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Błąd kompilacji: {e}")
                
        with col_arch:
            if is_archived:
                if st.button("↩️ Przywróć", key=f"restore_{orz.get('ID_Orzeczenia', '')}", use_container_width=True):
                    zmien_status_archiwum(orz.get('ID_Orzeczenia', ''), "NIE")
                    st.rerun()
            else:
                if st.button("📦 Archiwizuj", type="primary", key=f"arch_{orz.get('ID_Orzeczenia', '')}", use_container_width=True):
                    zmien_status_archiwum(orz.get('ID_Orzeczenia', ''), "TAK")
                    st.rerun()

# --- INTERFEJS UI (STREAMLIT) ---
st.markdown("# 🖨️ Generator Dokumentów Medycznych")
st.write("Wybierz odpowiedni typ dokumentu do wygenerowania dla pacjenta.")

df_orz = get_data_as_df("Orzeczenia")
df_wiz = get_data_as_df("Wizyty")
df_pac = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if not df_orz.empty:
    # Wypełnij braki w kolumnie Archiwum domyślnym "NIE"
    if 'Archiwum' not in df_orz.columns:
        df_orz['Archiwum'] = 'NIE'
        
    # Nałożenie nadpisań z pamięci sesji (fallback UI, zanim zrobisz zapis w db_service)
    for index, row in df_orz.iterrows():
        orz_id = row['ID_Orzeczenia']
        if f"arch_status_{orz_id}" in st.session_state:
            df_orz.at[index, 'Archiwum'] = st.session_state[f"arch_status_{orz_id}"]

    # Podział na dwa widoki (DataFrame'y)
    df_aktualne = df_orz[df_orz['Archiwum'] != 'TAK']
    df_archiwum = df_orz[df_orz['Archiwum'] == 'TAK']

    tab_biezace, tab_archiwum = st.tabs([f"📄 Bieżące Orzeczenia ({len(df_aktualne)})", f"📦 Archiwum ({len(df_archiwum)})"])

    # ZAKŁADKA 1: BIEŻĄCE
    with tab_biezace:
        if not df_aktualne.empty:
            for _, orz in df_aktualne.sort_values("ID_Orzeczenia", ascending=False).head(20).iterrows():
                render_orzeczenie_row(orz, is_archived=False)
        else:
            st.info("Wszystkie orzeczenia zostały zarchiwizowane.")

    # ZAKŁADKA 2: ARCHIWUM
    with tab_archiwum:
        if not df_archiwum.empty:
            for _, orz in df_archiwum.sort_values("ID_Orzeczenia", ascending=False).head(20).iterrows():
                render_orzeczenie_row(orz, is_archived=True)
        else:
            st.info("Archiwum jest puste.")
            
else:
    st.info("Brak wystawionych orzeczeń w bazie systemu.")
