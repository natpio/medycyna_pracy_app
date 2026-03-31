import streamlit as st
import pandas as pd
import os
import urllib.request
from fpdf import FPDF
from db_service import get_data_as_df, apply_pro_style

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="wide")
apply_pro_style()

# --- POBIERANIE CZCIONEK ---
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
        pass
    return font_reg, font_bold

font_regular, font_bold = load_fonts()

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
    # Wyłączamy automatyczne łamanie strony, aby wymusić stopkę prawną na dole
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    if os.path.exists(font_regular) and os.path.exists(font_bold):
        pdf.add_font("Roboto", style="", fname=font_regular)
        pdf.add_font("Roboto", style="B", fname=font_bold)
        pdf.set_font("Roboto", size=10)
    else:
        pdf.set_font("Arial", size=10)
    return pdf

# --- GŁÓWNY GENERATOR SZABLONU (Wzór z pliku orzeczenie.pdf) ---
def create_orzeczenie_pdf(orz_data, wizyta, pacjent, firma):
    pdf = init_pdf()
    
    # --- NAGŁÓWEK (Lewa strona - Dane lekarza) ---
    pdf.set_font("Roboto", style="B", size=8)
    pdf.set_xy(10, 10)
    pdf.multi_cell(100, 4, "INDYWIDUALNA SPECJALISTYCZNA PRAKTYKA LEKARSKA\nMEDYCYNA PRACY lek. med. Jarosław Tarkowski 62-065 Grodzisk Wlkp. Ul. Chopina 18/1\nNIP 788-142-01-53; Regon 631003518; tel. 602 465 777, tel. 794626400, e-mail: jaroslaw.tarkowski@wp.pl", align="L")
    pdf.set_font("Roboto", size=7)
    pdf.cell(100, 4, "(oznaczenie podmiotu przeprowadzającego badanie)", ln=1)
    
    # --- NAGŁÓWEK (Prawa strona - Typ badania) ---
    pdf.set_xy(130, 10)
    pdf.set_font("Roboto", size=10)
    typ_bad = str(wizyta.get('TypBadania', 'okresowe')).lower()
    pdf.multi_cell(70, 5, f"Rodzaj badania lekarskiego: {typ_bad}\n(wstępne, okresowe, kontrolne)")
    
    # --- TYTUŁ DOKUMENTU ---
    pdf.ln(10)
    pdf.set_y(35)
    pdf.set_font("Roboto", style="B", size=14)
    pdf.cell(0, 8, f"ORZECZENIE LEKARSKIE NR {orz_data.get('ID_Orzeczenia', '')}", align="C", ln=1)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 5, f"wydane na podstawie skierowania na badania lekarskie z dnia: {wizyta.get('DataWizyty', '')}", align="C", ln=1)
    
    # --- PREAMBUŁA PRAWNA ---
    pdf.ln(5)
    pdf.set_font("Roboto", size=10)
    preamble = "W wyniku badania lekarskiego i oceny narażeń występujących na stanowisku pracy, stosownie do art. 43 pkt 2 i art. 229 § 4 ustawy z dnia 26 czerwca 1974 r. - Kodeks pracy (t.j.Dz. U. z 2018 r. poz. 108) oraz art.39j Ustawy o transporcie drogowym, orzeka się, że:"
    pdf.multi_cell(0, 5, preamble)
    
    # --- DANE PACJENTA ---
    pdf.ln(5)
    pdf.cell(15, 6, "Pan(i): ")
    pdf.set_font("Roboto", style="B", size=12)
    pdf.cell(100, 6, f"{pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')}")
    
    # Podpis pod nazwiskiem
    pdf.set_font("Roboto", size=7)
    pdf.set_xy(25, pdf.get_y() + 5)
    pdf.cell(100, 4, "(nazwisko i imię)")
    
    # Numer PESEL (z odstępami dla czytelności)
    pdf.set_xy(130, pdf.get_y() - 5)
    pdf.set_font("Roboto", size=10)
    pdf.cell(20, 6, "Nr PESEL:")
    pdf.set_font("Roboto", style="B", size=12)
    pesel_str = str(pacjent.get('PESEL', ''))
    formatted_pesel = " ".join(list(pesel_str)) if pesel_str else ""
    pdf.cell(50, 6, formatted_pesel)
    
    # Adres zamieszkania
    pdf.ln(8)
    pdf.set_font("Roboto", size=10)
    pdf.cell(35, 6, "zamieszkały(-ła) w: ")
    pdf.set_font("Roboto", style="B", size=11)
    adres_pacjenta = pacjent.get('Adres', '......................................................................................')
    pdf.cell(0, 6, adres_pacjenta, ln=1)
    pdf.set_font("Roboto", size=7)
    pdf.cell(0, 4, "(miejscowość, ulica, nr domu, nr lokalu)", ln=1)
    
    # --- DANE PRACODAWCY ---
    pdf.ln(4)
    pdf.set_font("Roboto", size=10)
    pdf.cell(85, 6, "zatrudniony(-na) / przyjmowany(-na)*) do pracy w: ")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.multi_cell(0, 6, f"{firma.get('NazwaFirmy', '')}, {firma.get('Adres', '')}")
    
    # --- STANOWISKO ---
    pdf.ln(2)
    pdf.set_font("Roboto", size=10)
    pdf.cell(80, 6, "na stanowisku / stanowiskach/ stanowisko / stanowiska*): ")
    pdf.set_font("Roboto", style="B", size=11)
    notatki = str(wizyta.get('Notatki', '')).replace('Stanowisko: ', '').split('\n')[0]
    pdf.multi_cell(0, 6, notatki)
    
    # --- DECYZJA (CHECKBOXY) ---
    pdf.ln(6)
    decyzja_z_bazy = str(orz_data.get('Decyzja', '')).upper()
    jest_zdolny = "NIEZDOLNY" not in decyzja_z_bazy
    
    pdf.set_font("Roboto", size=10)
    
    # CHECKBOX 1: Zdolny (21)
    pdf.rect(10, pdf.get_y() + 1, 4, 4)
    if jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.text(10.5, pdf.get_y() + 4.5, "X") # Krzyżyk
    pdf.set_font("Roboto", size=10)
    pdf.set_xy(16, pdf.get_y())
    pdf.multi_cell(0, 5, "wobec braku przeciwwskazań zdrowotnych jest zdolny(-na) do wykonywania/podjęcia*) pracy na określonym stanowisku (symbol 21)*)")
    
    pdf.ln(3)
    
    # CHECKBOX 2: Niezdolny (22)
    pdf.rect(10, pdf.get_y() + 1, 4, 4)
    if not jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.text(10.5, pdf.get_y() + 4.5, "X") # Krzyżyk
    pdf.set_font("Roboto", size=10)
    pdf.set_xy(16, pdf.get_y())
    pdf.multi_cell(0, 5, "wobec istnienia przeciwwskazań zdrowotnych jest niezdolny(-na) do wykonywania/podjęcia*) pracy na określonym stanowisku (symbol 22)*)")
    
    pdf.ln(3)
    
    # CHECKBOX 3: Utracił zdolność (23)
    pdf.rect(10, pdf.get_y() + 1, 4, 4)
    pdf.set_xy(16, pdf.get_y())
    pdf.multi_cell(0, 5, "wobec istnienia przeciwwskazań zdrowotnych utracił(a) zdolność do wykonywania dotychczasowej pracy z dniem .................................. (symbol 23)*).")
    
    # --- STOPKA: DATA NASTĘPNEGO BADANIA I PODPISY ---
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
    
    # Pieczątka lekarza (tekstowa, faksymile możemy dodać później w to miejsce)
    pdf.set_xy(120, y_signatures - 5)
    pdf.set_font("Roboto", style="B", size=9)
    pdf.multi_cell(70, 4, "Badanie profilaktyczne przeprowadził:\nJarosław Tarkowski\nspecjalista medycyny pracy\n30/1JT/370\n8776405", align="C")
    pdf.set_font("Roboto", size=7)
    pdf.set_xy(120, pdf.get_y() + 10)
    pdf.cell(70, 4, "(pieczątka i podpis lekarza przeprowadzającego badanie lekarskie)", align="C")
    
    # --- BLOK PRAWNY: SYMBOLE I POUCZENIE (Dół strony) ---
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

# --- KONTROLER / ROUTER SZABLONÓW ---
def generate_pdf_router(orz_data, wizyta, pacjent, firma):
    # Domyślny, zaawansowany szablon z załącznika orzeczenie.pdf
    return create_orzeczenie_pdf(orz_data, wizyta, pacjent, firma), "Zgodne ze Wzorem (KP 43.2)"

# --- INTERFEJS UI (STREAMLIT) ---
st.markdown("# 🖨️ Generator Orzeczeń")

df_orz = get_data_as_df("Orzeczenia")
df_wiz = get_data_as_df("Wizyty")
df_pac = get_data_as_df("Pacjenci")
df_fir = get_data_as_df("Firmy")

if not df_orz.empty:
    st.subheader("Lista najnowszych dokumentów do wydruku")
    for _, orz in df_orz.sort_values("ID_Orzeczenia", ascending=False).head(10).iterrows():
        
        # Ochrona przed brakującymi relacjami
        id_wiz = str(orz.get('ID_Wizyty', ''))
        wiz = df_wiz[df_wiz['ID_Wizyty'].astype(str) == id_wiz].iloc[0] if not df_wiz.empty and id_wiz in df_wiz['ID_Wizyty'].astype(str).values else {}
        
        pesel = str(orz.get('PESEL_Pacjenta', ''))
        pac = df_pac[df_pac['PESEL'].astype(str) == pesel].iloc[0] if not df_pac.empty and pesel in df_pac['PESEL'].astype(str).values else {"Imie": "Brak", "Nazwisko": "Danych", "PESEL": pesel}
        
        nip = str(wiz.get('NIP_Firmy', '0'))
        fir = df_fir[df_fir['NIP'].astype(str) == nip].iloc[0] if not df_fir.empty and nip in df_fir['NIP'].astype(str).values else {"NazwaFirmy": "Prywatnie / Brak Firmy", "Adres": "-", "NIP": nip}

        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1])
            
            try:
                # Generowanie na żywo
                pdf_bytes, typ_szablonu = generate_pdf_router(orz, wiz, pac, fir)
                
                with col_info:
                    st.markdown(f"📄 **{pac.get('Nazwisko', '')} {pac.get('Imie', '')}** (PESEL: {pac.get('PESEL', '')})")
                    st.caption(f"Firma: {fir.get('NazwaFirmy', '')} | Zastosowany układ: **{typ_szablonu}**")
                
                with col_btn:
                    st.download_button(
                        label="📥 Pobierz PDF",
                        data=pdf_bytes,
                        file_name=f"Orzeczenie_{pac.get('Nazwisko', '')}.pdf",
                        mime="application/pdf",
                        key=f"dl_{orz.get('ID_Orzeczenia', '')}",
                        use_container_width=True
                    )
            except Exception as e:
                with col_info:
                    st.error(f"Błąd kompilacji pliku PDF: {e}")
else:
    st.info("Brak wystawionych orzeczeń w bazie systemu.")
