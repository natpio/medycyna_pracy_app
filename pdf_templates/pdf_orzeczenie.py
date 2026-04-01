import os
import io
import qrcode
import datetime
from fpdf import FPDF

class OrzeczeniePDF(FPDF):
    def strike_text(self, text, h=4):
        """Rysuje przekreślony pojedynczy tekst"""
        x, y = self.get_x(), self.get_y()
        w = self.get_string_width(text)
        self.cell(w, h, text)
        self.line(x, y + h/2.2, x + w, y + h/2.2)

    def print_options(self, options, selected_idx, h=4, spacer=" / ", max_x=195):
        """Inteligentne rysowanie opcji z automatycznym łamaniem linii"""
        start_x = self.get_x()
        for i, opt in enumerate(options):
            opt_w = self.get_string_width(opt)
            spacer_w = self.get_string_width(spacer) if i < len(options)-1 else 0
            
            # Bezpiecznik: jeśli tekst wychodzi poza stronę, przenieś do nowej linii
            if self.get_x() + opt_w + spacer_w > max_x:
                self.ln(h)
                self.set_x(start_x)
                
            if i == selected_idx:
                self.set_font("Roboto", style="B")
                self.cell(opt_w, h, opt)
                self.set_font("Roboto", style="")
            else:
                self.strike_text(opt, h)
                
            if i < len(options) - 1:
                self.cell(spacer_w, h, spacer)

    def strike_block(self, y_start, y_end, line_h=5, x_start=10, x_end=190):
        """Rysuje precyzyjne przekreślenia na blokach tekstu (linijka po linijce)"""
        curr_y = y_start
        while curr_y < y_end - 1:
            self.line(x_start, curr_y + line_h/2.2, x_end, curr_y + line_h/2.2)
            curr_y += line_h

    def draw_form_box(self, x, y, w, h, label, value, is_bold=False):
        self.set_xy(x, y)
        self.set_font("Roboto", size=6)
        self.cell(w, 3, label, ln=1)
        self.set_xy(x, y + 3)
        self.set_font("Roboto", style="B" if is_bold else "", size=9)
        self.multi_cell(w, h - 3, str(value), border=1, align='L')

def init_pdf(font_reg, font_bold, font_italic):
    pdf = OrzeczeniePDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    if os.path.exists(font_reg) and os.path.exists(font_bold) and os.path.exists(font_italic):
        pdf.add_font("Roboto", style="", fname=font_reg)
        pdf.add_font("Roboto", style="B", fname=font_bold)
        pdf.add_font("Roboto", style="I", fname=font_italic)
        pdf.set_font("Roboto", size=10)
    else:
        pdf.set_font("Arial", size=10)
    return pdf

def create_orzeczenie_pdf(orz_data, wizyta, pacjent, firma, signature_path, fonts):
    font_reg, font_bold, font_italic = fonts
    pdf = init_pdf(font_reg, font_bold, font_italic)
    
    pdf.set_font("Roboto", style="B", size=8)
    pdf.set_xy(10, 10)
    pdf.multi_cell(100, 4, "INDYWIDUALNA SPECJALISTYCZNA PRAKTYKA LEKARSKA\nMEDYCYNA PRACY lek. med. Jarosław Tarkowski 62-065 Grodzisk Wlkp. Ul. Chopina 18/1\nNIP 788-142-01-53; Regon 631003518; tel. 602 465 777, tel. 794626400, e-mail: jaroslaw.tarkowski@wp.pl", align="L")
    pdf.set_font("Roboto", size=7)
    pdf.cell(100, 4, "(oznaczenie podmiotu przeprowadzającego badanie)", ln=1)
    
    pdf.set_xy(130, 10)
    pdf.set_font("Roboto", size=10)
    typ_bad = str(wizyta.get('TypBadania', 'okresowe')).lower()
    
    pdf.cell(70, 5, f"Rodzaj badania lekarskiego:", ln=1)
    pdf.set_x(130)
    pdf.set_font("Roboto", size=10)
    idx_bad = 0 if "wstępne" in typ_bad else (1 if "okresowe" in typ_bad else 2)
    pdf.print_options(["wstępne", "okresowe", "kontrolne"], idx_bad, 5, ", ")
    
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
    
    # Skreślanie dla zatrudnienia
    idx_zatr = 1 if "wstępne" in typ_bad else 0
    pdf.print_options(["Zatrudniony(-na)", "Przyjmowany(-na)"], idx_zatr, 6, " / ")
    pdf.cell(pdf.get_string_width(" do pracy w: "), 6, " do pracy w: ")
    
    pdf.set_font("Roboto", style="B", size=11)
    pdf.multi_cell(0, 6, f"{firma.get('NazwaFirmy', '')}, {firma.get('Adres', '')}")
    
    pdf.ln(2)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 6, "na stanowisku / stanowiskach / stanowisko / stanowiska*): ", ln=1)
    
    pdf.set_font("Roboto", style="B", size=11)
    notatki = str(wizyta.get('Notatki', '')).replace('Stanowisko: ', '').split('\n')[0]
    pdf.set_x(15) 
    pdf.multi_cell(0, 6, notatki)
    
    pdf.ln(6)
    decyzja_z_bazy = str(orz_data.get('Decyzja', '')).upper()
    jest_zdolny = "NIEZDOLNY" not in decyzja_z_bazy
    
    pdf.set_font("Roboto", size=10)
    
    # Bezpieczne skreślanie akapitów decyzji (linia po linii)
    y_start = pdf.get_y()
    pdf.multi_cell(0, 5, "wobec braku przeciwwskazań zdrowotnych jest zdolny(-na) do wykonywania pracy na określonym stanowisku (symbol 21)*)")
    if not jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 5)
    pdf.ln(3)
    
    y_start = pdf.get_y()
    pdf.multi_cell(0, 5, "wobec istnienia przeciwwskazań zdrowotnych jest niezdolny(-na) do wykonywania pracy na określonym stanowisku (symbol 22)*)")
    if jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 5)
    pdf.ln(3)
    
    y_start = pdf.get_y()
    pdf.multi_cell(0, 5, "wobec istnienia przeciwwskazań zdrowotnych utracił(a) zdolność do wykonywania dotychczasowej pracy z dniem .................................. (symbol 23)*).")
    pdf.strike_block(y_start, pdf.get_y(), 5) # Zawsze skreślone
    
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
        "1. Osoba badana lub pracodawca może w terminie 7 dni od dnia otrzymania orzeczenia lekarskiego wnieść odwołanie wraz z jego uzasadnieniem za pośrednictwem lekarza, który je wydał, do jednego z podmiotów odwoławczych, którymi są:\n"
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
        "OBJAŚNIENIA: *) Niewłaściwe skreślić. **) W przypadku osoby nieposiadającej numeru PESEL - seria, numer i nazwa dokumentu potwierdzającego tożsamość."
    )
    pdf.multi_cell(0, 3, pouczenie_text)
    
    return bytes(pdf.output())
