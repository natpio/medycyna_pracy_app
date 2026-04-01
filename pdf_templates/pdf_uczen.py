import os
import io
import qrcode
import datetime
from fpdf import FPDF

class UczenPDF(FPDF):
    def strike_text(self, text, h=4):
        x, y = self.get_x(), self.get_y()
        w = self.get_string_width(text)
        self.cell(w, h, text)
        self.line(x, y + h/2.2, x + w, y + h/2.2)

    def print_options(self, options, selected_idx, h=4, spacer=", ", max_x=195):
        start_x = self.get_x()
        for i, opt in enumerate(options):
            opt_w = self.get_string_width(opt)
            spacer_w = self.get_string_width(spacer) if i < len(options)-1 else 0
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

    def strike_block(self, y_start, y_end, line_h=4, x_start=10, x_end=190):
        curr_y = y_start
        while curr_y < y_end - 1:
            self.line(x_start, curr_y + line_h/2.2, x_end, curr_y + line_h/2.2)
            curr_y += line_h
            
    def safe_text(self, x, y, w, h, text):
        """Kuloodporne łamanie tekstu"""
        self.set_xy(x, y)
        safe_value = str(text).replace("\r", "").replace("\n", " ")
        words = safe_value.split(" ")
        line = ""
        for word in words:
            while self.get_string_width(word) > w - 2:
                cut_idx = int(len(word) / 2)
                words.insert(words.index(word)+1, word[cut_idx:])
                word = word[:cut_idx] + "-"
            if self.get_string_width(line + word + " ") < w - 2:
                line += word + " "
            else:
                self.cell(w, h, line, ln=1)
                self.set_x(x)
                line = word + " "
        if line:
            self.cell(w, h, line, ln=1)

def init_pdf(font_reg, font_bold, font_italic):
    pdf = UczenPDF()
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

def create_uczen_pdf(orz_data, wizyta, pacjent, firma, signature_path, fonts):
    font_reg, font_bold, font_italic = fonts
    pdf = init_pdf(font_reg, font_bold, font_italic)
    
    pdf.set_font("Roboto", style="B", size=8)
    pdf.set_xy(10, 10)
    naglowek = "INDYWIDUALNA SPECJALISTYCZNA PRAKTYKA LEKARSKA\nMEDYCYNA PRACY lek. med. Jarosław Tarkowski 62-065 Grodzisk Wlkp. Ul. Chopina 18/1\nNIP 788-142-01-53; Regon 631003518; tel. 602 465 777; e-mail med-pracy@outlook.com"
    pdf.multi_cell(130, 4, naglowek, align="L")
    
    pdf.ln(10)
    pdf.set_font("Roboto", style="B", size=15)
    pdf.cell(0, 8, "ZAŚWIADCZENIE LEKARSKIE", align="C", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Roboto", size=9)
    preambula = "W wyniku badania lekarskiego mającego na celu ocenę możliwości pobierania nauki, uwzględniającą stan zdrowia osób badanych i zagrożenia występujące na miejscu wykonywania i odbywania nauki zawodu lub stażu uczniowskiego, studiów, kwalifikacyjnych kursów zawodowych albo kształcenia w szkole doktorskiej, stosownie do przepisu art. 5 ust. 1 pkt 4 i 5 ustawy z dnia 27 czerwca 1997 r. o służbie medycyny pracy (Dz.U. 2022 r. poz. 437)"
    pdf.multi_cell(0, 5, preambula, align="J")
    
    pdf.ln(3)
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(0, 6, "orzeka się, że:", align="C", ln=1)
    
    pdf.ln(2)
    pdf.set_font("Roboto", size=10)
    pdf.cell(10, 6, "u")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(0, 6, f"{pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')}", ln=1)
    
    pdf.set_font("Roboto", size=7)
    pdf.set_x(20)
    pdf.cell(0, 4, "/imię (imiona) i nazwisko/", ln=1)
    
    pdf.ln(2)
    pdf.set_font("Roboto", size=10)
    pdf.cell(35, 6, "urodzonego(ej) dnia")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(40, 6, str(pacjent.get('DataUrodzenia', '..................')))
    pdf.set_font("Roboto", size=10)
    pdf.cell(20, 6, "nr PESEL")
    pdf.set_font("Roboto", style="B", size=11)
    pesel_str = str(pacjent.get('PESEL', ''))
    formatted_pesel = " ".join(list(pesel_str)) if pesel_str else ""
    pdf.cell(0, 6, formatted_pesel, ln=1)
    
    pdf.ln(4)
    pdf.set_font("Roboto", size=10)
    pdf.multi_cell(0, 5, "podejmującego/kontynuującego kształcenie:")
    
    # Skreślenia typu edukacji (domyślnie zostawiamy pierwszą opcję)
    pdf.set_font("Roboto", size=10)
    pdf.set_x(15)
    pdf.print_options(["praktyczna nauka zawodu / szkoła / studia", "kwalifikacyjny kurs zawodowy", "szkoła doktorska"], 0, 5, spacer="\n")
    
    pdf.ln(2)
    pdf.set_font("Roboto", size=10)
    pdf.cell(10, 6, "w")
    pdf.set_font("Roboto", style="B", size=11)
    szkola_dane = f"{firma.get('NazwaFirmy', '')}, {firma.get('Adres', '')}" if firma.get('NazwaFirmy') and firma.get('NazwaFirmy') != "Prywatnie / Brak Firmy" else "...................................................................................................."
    pdf.safe_text(20, pdf.get_y(), 180, 6, szkola_dane)
    
    pdf.ln(2)
    pdf.set_font("Roboto", style="B", size=11)
    stanowisko = str(wizyta.get('Notatki', '')).split('\n')[0].replace('Stanowisko: ', '')
    if not stanowisko or stanowisko.lower() == "brak" or stanowisko.lower() == "uczeń":
        stanowisko = "...................................................................................................."
    pdf.safe_text(20, pdf.get_y(), 180, 6, stanowisko)
    
    # --- DECYZJA (Skreślanie akapitów) ---
    pdf.ln(6)
    decyzja_z_bazy = str(orz_data.get('Decyzja', '')).upper()
    jest_zdolny = "NIEZDOLNY" not in decyzja_z_bazy
    
    pdf.set_font("Roboto", size=10)
    y_start = pdf.get_y()
    pdf.multi_cell(0, 5, "1) brak jest przeciwskazań zdrowotnych do wykonywania i odbywania nauki / studiów")
    if jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.cell(0, 6, f"Data następnego badania: {orz_data.get('DataKolejnegoBadania', '')}", ln=1)
        pdf.set_font("Roboto", size=10)
    else:
        pdf.cell(0, 6, "Data następnego badania: ........................................", ln=1)
    if not jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 5)
    
    pdf.ln(2)
    
    y_start = pdf.get_y()
    pdf.multi_cell(0, 5, "2) istnieją przeciwskazania zdrowotne do wykonywania i odbywania nauki / studiów")
    if jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 5)
    
    pdf.ln(2)
    pdf.set_font("Roboto", size=7)
    pdf.cell(0, 4, "*niewłaściwe skreślić", ln=1)
    
    # --- DATA I PODPIS ---
    pdf.ln(10)
    y_signatures = pdf.get_y()
    
    try:
        data_wyst = f"{orz_data['ID_Orzeczenia'].split('/')[1][:4]}-{orz_data['ID_Orzeczenia'].split('/')[1][4:6]}-{orz_data['ID_Orzeczenia'].split('/')[1][6:8]}"
    except:
        data_wyst = "...................."
        
    pdf.set_xy(10, y_signatures)
    pdf.set_font("Roboto", size=10)
    pdf.cell(100, 5, f"Luboń, dnia {data_wyst} r.")
    
    if signature_path and os.path.exists(signature_path):
        pdf.image(signature_path, x=130, y=y_signatures - 15, w=55)
    else:
        pdf.set_xy(120, y_signatures - 5)
        pdf.set_font("Roboto", style="B", size=9)
        pdf.multi_cell(70, 4, "Badanie profilaktyczne przeprowadził:\nJarosław Tarkowski\nspecjalista medycyny pracy\n30/1JT/370\n8776405", align="C")
        pdf.set_font("Roboto", size=6)
        pdf.set_xy(120, pdf.get_y() + 5)
        pdf.multi_cell(70, 3, "podpis oraz pieczątka lub nadruk zawierające imię i nazwisko", align="C")

    data_generowania = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', orz_data.get('PodpisCyfrowy', 'Brak autoryzacji')))
    qr_text = f"UCZEŃ/STUDENT\nNr: {orz_data.get('ID_Orzeczenia', '')}\nWażne: {orz_data.get('DataKolejnegoBadania', '')}\nSHA-256: {podpis_cyfrowy}"
    qr = qrcode.make(qr_text)
    qr_img_bytes = io.BytesIO()
    qr.save(qr_img_bytes, format='PNG')
    pdf.image(qr_img_bytes, x=15, y=y_signatures + 10, w=25)
    
    pdf.set_y(235)
    pdf.set_x(10)
    pdf.set_font("Roboto", style="B", size=7)
    pdf.cell(0, 4, "POUCZENIE:", ln=1)
    
    pdf.set_x(10)
    pdf.set_font("Roboto", size=6)
    pouczenie_text = (
        "Od zaświadczenia lekarskiego osobie badanej oraz placówce dydaktycznej przysługuje odwołanie wnoszone na piśmie. Odwołanie "
        "wraz z uzasadnieniem wnosi się w terminie 14 dni od dnia otrzymania zaświadczenia lekarskiego, za pośrednictwem lekarza, który "
        "wydał zaświadczenie lekarskie, do wojewódzkiego ośrodka medycyny pracy, właściwego ze względu na siedzibę placówki "
        "dydaktycznej, a w przypadku gdy odwołanie dotyczy zaświadczenia lekarskiego wydanego w wojewódzkim ośrodku medycyny pracy - "
        "do instytutu badawczego w dziedzinie medycyny pracy. W przypadku gdy zaświadczenie lekarskie wydał lekarz kolejowego ośrodka "
        "medycyny pracy, odwołanie od zaświadczenia lekarskiego składa się, za jego pośrednictwem, do Centrum Naukowego Medycyny Kolejowej."
    )
    pdf.multi_cell(0, 3, pouczenie_text)
    
    return bytes(pdf.output())
