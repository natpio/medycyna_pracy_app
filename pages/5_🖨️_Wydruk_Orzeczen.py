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
apply_pro_style()

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

# --- POBIERANIE CZCIONEK (POPRAWIONE: DODANO ITALIC) ---
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

# --- KLASA GŁÓWNA PDF ---
class OrzeczeniePDF(FPDF):
    def draw_form_box(self, x, y, w, h, label, value, is_bold=False):
        """Pomocnicza funkcja rysująca komórki w stylu Excela"""
        self.set_xy(x, y)
        self.set_font("Roboto", size=7)
        self.cell(w, 4, label, ln=1)
        self.set_xy(x, y + 4)
        self.set_font("Roboto", style="B" if is_bold else "", size=10)
        self.multi_cell(w, h - 4, str(value), border=1, align='L')

def init_pdf():
    pdf = OrzeczeniePDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    if os.path.exists(font_regular) and os.path.exists(font_bold) and os.path.exists(font_italic):
        pdf.add_font("Roboto", style="", fname=font_regular)
        pdf.add_font("Roboto", style="B", fname=font_bold)
        pdf.add_font("Roboto", style="I", fname=font_italic) # Rejestracja czcionki pochylonej
        pdf.set_font("Roboto", size=10)
    else:
        pdf.set_font("Arial", size=10)
    return pdf

# --- 1. GENERATOR: ORZECZENIE LEKARSKIE ---
def create_orzeczenie_pdf(orz_data, wizyta, pacjent, firma, signature_path):
    pdf = init_pdf()
    
    pdf.set_font("Roboto", style="B", size=8)
    pdf.set_xy(10, 10)
    pdf.multi_cell(100, 4, "INDYWIDUALNA SPECJALISTYCZNA PRAKTYKA LEKARSKA\nMEDYCYNA PRACY lek. med. Jarosław Tarkowski 62-065 Grodzisk Wlkp. Ul. Chopina 18/1\nNIP 788-142-01-53; Regon 631003518; tel. 602 465 777, tel. 794626400, e-mail: jaroslaw.tarkowski@wp.pl", align="L")
    pdf.set_font("Roboto", size=7)
    pdf.cell(100, 4, "(oznaczenie podmiotu przeprowadzającego badanie)", ln=1)
    
    pdf.set_xy(130, 10)
    pdf.set_font("Roboto", size=10)
    typ_bad = str(wizyta.get('TypBadania', 'okresowe')).lower()
    pdf.multi_cell(70, 5, f"Rodzaj badania lekarskiego: {typ_bad}\n(wstępne, okresowe, kontrolne)")
    
    pdf.ln(10)
    pdf.set_y(35)
    pdf.set_font("Roboto", style="B", size=14)
    pdf.cell(0, 8, f"ORZECZENIE LEKARSKIE NR {orz_data.get('ID_Orzeczenia', '')}", align="C", ln=1)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 5, f"wydane na podstawie skierowania na badania lekarskie z dnia: {wizyta.get('DataWizyty', '')}", align="C", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Roboto", size=10)
    preamble = "W wyniku badania lekarskiego i oceny narażeń występujących na stanowisku pracy, stosownie do art. 43 pkt 2 i art. 229 § 4 ustawy z dnia 26 czerwca 1974 r. - Kodeks pracy (t.j.Dz. U. z 2018 r. poz. 108) oraz art.39j Ustawy o transporcie drogowym, orzeka się, że:"
    pdf.multi_cell(0, 5, preamble)
    
    pdf.ln(5)
    pdf.cell(15, 6, "Pan(i): ")
    pdf.set_font("Roboto", style="B", size=12)
    pdf.cell(100, 6, f"{pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')}")
    
    pdf.set_font("Roboto", size=7)
    pdf.set_xy(25, pdf.get_y() + 5)
    pdf.cell(100, 4, "(nazwisko i imię)")
    
    pdf.set_xy(130, pdf.get_y() - 5)
    pdf.set_font("Roboto", size=10)
    pdf.cell(20, 6, "Nr PESEL:")
    pdf.set_font("Roboto", style="B", size=12)
    pesel_str = str(pacjent.get('PESEL', ''))
    formatted_pesel = " ".join(list(pesel_str)) if pesel_str else ""
    pdf.cell(50, 6, formatted_pesel)
    
    pdf.ln(8)
    pdf.set_font("Roboto", size=10)
    pdf.cell(35, 6, "zamieszkały(-ła) w: ")
    pdf.set_font("Roboto", style="B", size=11)
    adres_pacjenta = pacjent.get('Adres', '......................................................................................')
    pdf.cell(0, 6, adres_pacjenta, ln=1)
    pdf.set_font("Roboto", size=7)
    pdf.cell(0, 4, "(miejscowość, ulica, nr domu, nr lokalu)", ln=1)
    
    pdf.ln(4)
    pdf.set_font("Roboto", size=10)
    pdf.cell(85, 6, "zatrudniony(-na) / przyjmowany(-na)*) do pracy w: ")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.multi_cell(0, 6, f"{firma.get('NazwaFirmy', '')}, {firma.get('Adres', '')}")
    
    pdf.ln(2)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 6, "na stanowisku / stanowiskach/ stanowisko / stanowiska*): ", ln=1)
    
    pdf.set_font("Roboto", style="B", size=11)
    notatki = str(wizyta.get('Notatki', '')).replace('Stanowisko: ', '').split('\n')[0]
    pdf.set_x(15) 
    pdf.multi_cell(0, 6, notatki)
    
    pdf.ln(6)
    decyzja_z_bazy = str(orz_data.get('Decyzja', '')).upper()
    jest_zdolny = "NIEZDOLNY" not in decyzja_z_bazy
    
    pdf.set_font("Roboto", size=10)
    
    pdf.rect(10, pdf.get_y() + 1, 4, 4)
    if jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.text(10.5, pdf.get_y() + 4.5, "X")
    pdf.set_font("Roboto", size=10)
    pdf.set_xy(16, pdf.get_y())
    pdf.multi_cell(0, 5, "wobec braku przeciwwskazań zdrowotnych jest zdolny(-na) do wykonywania/podjęcia*) pracy na określonym stanowisku (symbol 21)*)")
    
    pdf.ln(3)
    pdf.rect(10, pdf.get_y() + 1, 4, 4)
    if not jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.text(10.5, pdf.get_y() + 4.5, "X")
    pdf.set_font("Roboto", size=10)
    pdf.set_xy(16, pdf.get_y())
    pdf.multi_cell(0, 5, "wobec istnienia przeciwwskazań zdrowotnych jest niezdolny(-na) do wykonywania/podjęcia*) pracy na określonym stanowisku (symbol 22)*)")
    
    pdf.ln(3)
    pdf.rect(10, pdf.get_y() + 1, 4, 4)
    pdf.set_xy(16, pdf.get_y())
    pdf.multi_cell(0, 5, "wobec istnienia przeciwwskazań zdrowotnych utracił(a) zdolność do wykonywania dotychczasowej pracy z dniem .................................. (symbol 23)*).")
    
    pdf.ln(8)
    pdf.set_font("Roboto", size=10)
    pdf.cell(100, 6, f"Data następnego badania okresowego: {orz_data.get('DataKolejnegoBadania', '')}")
    
    y_signatures = pdf.get_y() + 15
    pdf.set_xy(10, y_signatures)
    
    try:
        data_wyst = f"{orz_data['ID_Orzeczenia'].split('/')[1][:4]}-{orz_data['ID_Orzeczenia'].split('/')[1][4:6]}-{orz_data['ID_Orzeczenia'].split('/')[1][6:8]}"
    except:
        data_wyst = "...................."
        
    pdf.cell(100, 5, f"Luboń, data {data_wyst}")
    pdf.set_font("Roboto", size=7)
    pdf.set_xy(10, y_signatures + 5)
    pdf.cell(100, 4, "(miejscowość, data)")
    
    data_generowania = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', orz_data.get('PodpisCyfrowy', 'Brak autoryzacji')))
    
    qr_text = (
        f"WERYFIKACJA ORZECZENIA LEKARSKIEGO\n"
        f"Nr orzeczenia: {orz_data.get('ID_Orzeczenia', '')}\n"
        f"Wygenerowano: {data_generowania}\n\n"
        f"DANE LEKARZA:\nlek. Jarosław Tarkowski\n"
        f"CERTYFIKAT AUTENTYCZNOŚCI:\n{podpis_cyfrowy}"
    )
    qr = qrcode.make(qr_text)
    qr_img_bytes = io.BytesIO()
    qr.save(qr_img_bytes, format='PNG')
    
    pdf.image(qr_img_bytes, x=12, y=y_signatures + 10, w=22)
    pdf.set_xy(36, y_signatures + 15)
    pdf.set_font("Roboto", size=6)
    pdf.multi_cell(60, 3, f"Zatwierdzono Elektronicznie\nlek. Jarosław Tarkowski\nCertyfikat (SHA-256):\n{podpis_cyfrowy}", align="L")
    
    if signature_path and os.path.exists(signature_path):
        pdf.image(signature_path, x=130, y=y_signatures - 10, w=55)
    else:
        pdf.set_xy(120, y_signatures - 5)
        pdf.set_font("Roboto", style="B", size=9)
        pdf.multi_cell(70, 4, "Badanie profilaktyczne przeprowadził:\nJarosław Tarkowski\nspecjalista medycyny pracy\n30/1JT/370\n8776405", align="C")
        pdf.set_font("Roboto", size=7)
        pdf.set_xy(120, pdf.get_y() + 10)
        pdf.cell(70, 4, "(pieczątka i podpis lekarza przeprowadzającego badanie lekarskie)", align="C")
    
    pdf.set_y(220)
    pdf.set_font("Roboto", size=6)
    pouczenie_text = (
        "POUCZENIE:\n"
        "1.***) Osoba badana lub pracodawca może w terminie 7 dni od dnia otrzymania orzeczenia lekarskiego wnieść odwołanie wraz z jego uzasadnieniem za pośrednictwem lekarza, który je wydał, do jednego z podmiotów odwoławczych, którymi są:\n"
        "1) wojewódzkie ośrodki medycyny pracy właściwe ze względu na miejsce świadczenia pracy lub siedzibę jednostki organizacyjnej, w której jest zatrudniony pracownik;\n"
        "2) instytuty badawcze w dziedzinie medycyny pracy lub Uniwersyteckie Centrum Medycyny Morskiej i Tropikalnej w Gdyni, w przypadku orzeczenia lekarskiego wydanego przez lekarza zatrudnionego w wojewódzkim ośrodku medycyny pracy;\n"
        "3) Centrum Naukowe Medycyny Kolejowej, w przypadku orzeczenia lekarskiego wydanego przez Kolejowy Zakład Medycyny Pracy;\n"
        "4) podmioty lecznicze utworzone i wyznaczone przez Ministra Obrony Narodowej.\n"
        "2. Orzeczenie lekarskie wydane w trybie odwołania jest ostateczne.\n"
        "3. Orzeczenie lekarskie jest wydawane w dwóch egzemplarzach, z których jeden otrzymuje osoba badana, a drugi pracodawca.\n\n"
        "SYMBOLE RODZAJU ORZECZENIA:\n"
        "21 - wobec braku przeciwwskazań zdrowotnych zdolny do wykonywania pracy na wskazanym (dotychczasowym) stanowisku pracy\n"
        "22 - wobec przeciwwskazań zdrowotnych niezdolny do wykonywania pracy na wskazanym (dotychczasowym) stanowisku pracy\n"
        "23 - wobec przeciwwskazań zdrowotnych utracił zdolność do wykonywania dotychczasowej pracy\n\n"
        "OBJAŚNIENIA: *) Niepotrzebne skreślić. **) W przypadku osoby nieposiadającej numeru PESEL - seria, numer i nazwa dokumentu potwierdzającego tożsamość. ***) Skreślić w przypadku orzeczenia lekarskiego wydanego w trybie odwoławczym."
    )
    pdf.multi_cell(0, 3, pouczenie_text)
    
    return bytes(pdf.output())


# --- 2. GENERATOR: KARTA BADANIA PROFILAKTYCZNEGO (KBP) - 3 STRONY ---
def create_kbp_pdf(orz_data, wizyta, pacjent, firma, signature_path):
    pdf = init_pdf() 
    
    # ------------------ STRONA 1: DANE OGÓLNE ------------------
    pdf.set_font("Roboto", style="B", size=14)
    pdf.cell(0, 8, f"{pacjent.get('Nazwisko', '').upper()} {pacjent.get('Imie', '').upper()}", align="L", ln=1)
    
    pdf.set_font("Roboto", style="B", size=16)
    pdf.cell(0, 10, "Karta badania profilaktycznego", align="C", ln=1)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 5, "(nr kolejny badania ....................................................)", align="C", ln=1)
    
    pdf.ln(5)
    
    pdf.set_font("Roboto", size=8)
    pdf.cell(60, 6, "Rodzaj badania profilaktycznego", border=1)
    typ_bad = str(wizyta.get('TypBadania', '')).lower()
    oznaczenie = "wstępne (W)" if "wstępne" in typ_bad else ("okresowe (O)" if "okresowe" in typ_bad else "kontrolne (K)")
    pdf.cell(0, 6, f"wstępne (W); okresowe (O); kontrolne (K)    =>   Zaznaczono: {oznaczenie}", border=1, ln=1)
    
    pdf.cell(60, 6, "Pozostała działalność profilaktyczna", border=1)
    pdf.cell(0, 6, "monitoring stanu zdrowia (M); badania celowane (C); czynne poradnictwo (D); inne (I)", border=1, ln=1)
    
    pdf.cell(60, 6, "Objęty opieką jako", border=1)
    pdf.cell(0, 6, "pracownik (P); praca nakładcza (N); pobierający naukę (U); na własny wniosek (W)", border=1, ln=1)
    
    pdf.ln(8)
    
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(0, 6, "1. DANE OSOBY BADANEJ", ln=1)
    
    y_start = pdf.get_y() + 2
    pdf.draw_form_box(10, y_start, 95, 12, "Nazwisko i imię", f"{pacjent.get('Nazwisko', '')} {pacjent.get('Imie', '')}", is_bold=True)
    pesel_str = str(pacjent.get('PESEL', ''))
    pdf.draw_form_box(105, y_start, 95, 12, "PESEL", pesel_str, is_bold=True)
    
    pdf.set_y(y_start + 15)
    pdf.draw_form_box(10, pdf.get_y(), 190, 12, "Adres zamieszkania", pacjent.get('Adres', '......................................................................................'))
    
    pdf.set_y(pdf.get_y() + 15)
    pdf.draw_form_box(10, pdf.get_y(), 140, 12, "Zawód wyuczony / wykonywany", ".......................................................................")
    pdf.draw_form_box(150, pdf.get_y()-12, 50, 12, "Płeć (K / M)", "......................")
    
    pdf.ln(18)
    
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(0, 6, "2. DANE IDENTYFIKACYJNE MIEJSCA PRACY / POBIERANIA NAUKI", ln=1)
    
    y_start2 = pdf.get_y() + 2
    pdf.draw_form_box(10, y_start2, 190, 12, "Nazwa zakładu pracy", firma.get('NazwaFirmy', ''))
    pdf.set_y(y_start2 + 15)
    pdf.draw_form_box(10, pdf.get_y(), 190, 12, "Adres zakładu pracy", firma.get('Adres', ''))
    
    pdf.set_y(pdf.get_y() + 15)
    stanowisko_pelne = str(wizyta.get('Notatki', ''))
    stanowisko = stanowisko_pelne.split('\n')[0].replace('Stanowisko: ', '') if 'Stanowisko: ' in stanowisko_pelne else stanowisko_pelne
    czynniki = stanowisko_pelne.replace(stanowisko, '').replace('Stanowisko: ', '').replace('Zagrożenia: ', '').strip()
    
    pdf.draw_form_box(10, pdf.get_y(), 190, 12, "Stanowisko pracy / kierunek nauki", stanowisko)
    
    pdf.set_y(pdf.get_y() + 15)
    pdf.set_font("Roboto", size=9)
    pdf.cell(0, 6, "Skierowanie od pracodawcy / placówki dydaktycznej:   [ X ] TAK     [   ] NIE", ln=1)
    
    pdf.ln(2)
    pdf.draw_form_box(10, pdf.get_y(), 190, 30, "Informacja o czynnikach szkodliwych i uciążliwych (z bazy danych)", czynniki)
    
    # ------------------ STRONA 2: WYWIAD ------------------
    pdf.add_page()
    pdf.set_font("Roboto", style="B", size=12)
    pdf.cell(0, 10, "3. BADANIE PODMIOTOWE (WYWIAD LEKARSKI)", ln=1)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 6, "Skargi badanego(ej): .............................................................................................................................................................", ln=1)
    pdf.cell(0, 6, ".......................................................................................................................................................................................................", ln=1)
    
    pdf.ln(8)
    
    pdf.set_font("Roboto", style="B", size=9)
    pdf.cell(110, 8, "Czy badany(a) choruje lub chorował(a) na:", border=1, align="C")
    pdf.cell(15, 8, "TAK", border=1, align="C")
    pdf.cell(15, 8, "NIE", border=1, align="C")
    pdf.cell(50, 8, "Zaburzenia / Opis", border=1, align="C", ln=1)
    
    pdf.set_font("Roboto", size=9)
    pytania = [
        "Choroby układu krążenia (nadciśnienie, wady serca)",
        "Choroby układu oddechowego (astma, POChP)",
        "Choroby układu pokarmowego",
        "Choroby układu moczowo-płciowego",
        "Choroby układu nerwowego (padaczka, omdlenia)",
        "Choroby psychiczne",
        "Choroby narządu wzroku",
        "Choroby narządu słuchu",
        "Choroby narządu ruchu (kręgosłup, stawy)",
        "Choroby skóry",
        "Choroby zakaźne / choroby zawodowe",
        "Cukrzyca / Inne choroby metaboliczne",
        "Nałogi (palenie tytoniu, alkohol, inne)"
    ]
    
    for p in pytania:
        pdf.cell(110, 7, p, border=1)
        pdf.cell(15, 7, "", border=1)
        pdf.cell(15, 7, "", border=1)
        pdf.cell(50, 7, "", border=1, ln=1)
        
    pdf.ln(15)
    pdf.set_font("Roboto", style="I", size=10)
    pdf.cell(0, 6, "Oświadczam, że zrozumiałem(am) treść zadawanych pytań i odpowiedziałem(am) zgodnie z prawdą.", ln=1)
    
    pdf.ln(10)
    pdf.cell(0, 5, "....................................................................", ln=1, align="R")
    pdf.set_font("Roboto", size=8)
    pdf.cell(0, 4, "(własnoręczny podpis badanego)", ln=1, align="R")
    
    # ------------------ STRONA 3: BADANIE PRZEDMIOTOWE I ORZECZENIE ------------------
    pdf.add_page()
    pdf.set_font("Roboto", style="B", size=12)
    pdf.cell(0, 10, "4. BADANIE PRZEDMIOTOWE (OBIEKTYWNE)", ln=1)
    
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 8, "Wzrost: ............ cm, Ciężar ciała: ............ kg, RR: ............ mmHg, Tętno: ............ /min", ln=1)
    pdf.cell(0, 8, "Ostrość wzroku: OP: ........................ OL: ........................ W okularach OP: ........................ OL: ........................", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "Stan narządów i układów (opisać ewentualne odchylenia):", ln=1)
    pdf.set_font("Roboto", size=10)
    for i in range(4):
        pdf.cell(0, 7, ".......................................................................................................................................................................................................", ln=1)
        
    pdf.ln(5)
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "Wyniki badań dodatkowych / Konsultacje specjalistyczne:", ln=1)
    pdf.set_font("Roboto", size=10)
    for i in range(3):
        pdf.cell(0, 7, ".......................................................................................................................................................................................................", ln=1)
        
    pdf.ln(10)
    pdf.set_font("Roboto", style="B", size=12)
    pdf.cell(0, 10, "5. DECYZJA ORZECZNICZA I UWAGI", ln=1)
    
    pdf.set_font("Roboto", size=9)
    pdf.cell(0, 6, "[   ] przeniesienie pracownicy w ciąży / karmiącej dziecko piersią na inne stanowisko pracy", ln=1)
    pdf.cell(0, 6, "[   ] niezdolność do wykonywania dotychczasowej pracy ze względu na stwierdzoną chorobę zawodową", ln=1)
    pdf.cell(0, 6, "[   ] potrzeba stosowania okularów korygujących wzrok podczas pracy przy obsłudze monitora ekranowego", ln=1)
    
    pdf.ln(5)
    uwagi = str(orz_data.get('UwagiLekarza', ''))
    if not uwagi: uwagi = "..................................................................................................................................."
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(20, 6, "UWAGI: ")
    pdf.set_font("Roboto", size=10)
    pdf.multi_cell(0, 6, uwagi)
    
    pdf.ln(8)
    data_wystawienia = orz_data.get('DataWystawienia', datetime.datetime.now().strftime('%Y-%m-%d'))
    data_kolejnego = orz_data.get('DataKolejnegoBadania', '........................')
    pdf.cell(0, 6, f"Data wydania orzeczenia: {data_wystawienia}", ln=1)
    pdf.cell(0, 6, f"Data następnego badania: {data_kolejnego}", ln=1)
    
    pdf.ln(15)
    y_signatures = pdf.get_y()
    
    pdf.set_xy(10, y_signatures)
    pdf.cell(100, 6, f"Dokumentację medyczną wydano osobie badanej w dniu: {data_wystawienia}")
    
    if signature_path and os.path.exists(signature_path):
        pdf.image(signature_path, x=130, y=y_signatures - 15, w=55)
    else:
        pdf.set_xy(120, y_signatures)
        pdf.set_font("Roboto", style="B", size=9)
        pdf.multi_cell(70, 4, "Badanie profilaktyczne przeprowadził:\nJarosław Tarkowski\nspecjalista medycyny pracy\n30/1JT/370\n8776405", align="C")
        pdf.set_font("Roboto", size=7)
        pdf.set_xy(120, pdf.get_y() + 5)
        pdf.cell(70, 4, "(pieczęć i podpis lekarza)", align="C")
        
    return bytes(pdf.output())


# --- KONTROLER / ROUTER SZABLONÓW ---
def generate_pdf_router(typ_dokumentu, orz_data, wizyta, pacjent, firma, pieczatka_path):
    if typ_dokumentu == "Orzeczenie Lekarskie":
        return create_orzeczenie_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path)
    elif typ_dokumentu == "Karta Badania (KBP)":
        return create_kbp_pdf(orz_data, wizyta, pacjent, firma, pieczatka_path)
    else:
        raise ValueError("Nieznany typ dokumentu")

# --- INTERFEJS UI (STREAMLIT) ---
st.markdown("# 🖨️ Generator Dokumentów Medycznych")
st.write("Wybierz odpowiedni typ dokumentu do wygenerowania dla pacjenta.")

df_orz = get_data_as_df("Orzeczenia")
df_wiz = get_data_as_df("Wizyty")
df_pac = get_data_as_df("Pacjenci")
df_fir = get_data_as_df("Firmy")

if not df_orz.empty:
    st.subheader("Lista dokumentów do wydruku")
    for _, orz in df_orz.sort_values("ID_Orzeczenia", ascending=False).head(10).iterrows():
        
        id_wiz = str(orz.get('ID_Wizyty', ''))
        wiz = df_wiz[df_wiz['ID_Wizyty'].astype(str) == id_wiz].iloc[0] if not df_wiz.empty and id_wiz in df_wiz['ID_Wizyty'].astype(str).values else {}
        
        pesel = str(orz.get('PESEL_Pacjenta', ''))
        pac = df_pac[df_pac['PESEL'].astype(str) == pesel].iloc[0] if not df_pac.empty and pesel in df_pac['PESEL'].astype(str).values else {"Imie": "Brak", "Nazwisko": "Danych", "PESEL": pesel}
        
        nip = str(wiz.get('NIP_Firmy', '0'))
        fir = df_fir[df_fir['NIP'].astype(str) == nip].iloc[0] if not df_fir.empty and nip in df_fir['NIP'].astype(str).values else {"NazwaFirmy": "Prywatnie / Brak Firmy", "Adres": "-", "NIP": nip}

        with st.container(border=True):
            col_info, col_doc, col_btn = st.columns([2.5, 1.5, 1])
            
            with col_info:
                st.markdown(f"📄 **{pac.get('Nazwisko', '')} {pac.get('Imie', '')}**")
                st.caption(f"PESEL: {pac.get('PESEL', '')} | Firma: {fir.get('NazwaFirmy', '')}")
            
            with col_doc:
                typ_dokumentu = st.selectbox(
                    "Wybierz dokument:",
                    ["Orzeczenie Lekarskie", "Karta Badania (KBP)"],
                    key=f"sel_{orz.get('ID_Orzeczenia', '')}",
                    label_visibility="collapsed"
                )
            
            with col_btn:
                try:
                    pdf_bytes = generate_pdf_router(typ_dokumentu, orz, wiz, pac, fir, pieczatka_path)
                    st.download_button(
                        label="📥 Pobierz",
                        data=pdf_bytes,
                        file_name=f"{typ_dokumentu.replace(' ', '_')}_{pac.get('Nazwisko', '')}.pdf",
                        mime="application/pdf",
                        key=f"dl_{typ_dokumentu}_{orz.get('ID_Orzeczenia', '')}",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Błąd kompilacji: {e}")
else:
    st.info("Brak wystawionych orzeczeń w bazie systemu.")
