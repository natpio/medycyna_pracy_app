import os
import io
import qrcode
import datetime
from fpdf import FPDF

class SkierowanieWcmpPDF(FPDF):
    def strike_text(self, text, h=4):
        x, y = self.get_x(), self.get_y()
        w = self.get_string_width(text)
        self.cell(w, h, text)
        self.line(x, y + h/2.2, x + w, y + h/2.2)

    def print_options(self, options, selected_idx, h=4, spacer=" ", max_x=195):
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
                
    def write_text(self, w, h, text, align="L"):
        """Kuloodporne pisanie tekstu z łamaniem"""
        x = self.get_x()
        lines = str(text).split("\n")
        for text_line in lines:
            words = text_line.replace("\r", "").split(" ")
            line = ""
            for word in words:
                while self.get_string_width(word) > w - 2:
                    cut_idx = int(len(word) / 2)
                    words.insert(words.index(word)+1, word[cut_idx:])
                    word = word[:cut_idx] + "-"
                if self.get_string_width(line + word + " ") < w - 2:
                    line += word + " "
                else:
                    self.set_x(x)
                    self.cell(w, h, line.strip(), align=align, ln=1)
                    line = word + " "
            if line:
                self.set_x(x)
                self.cell(w, h, line.strip(), align=align, ln=1)

def init_pdf(font_reg, font_bold, font_italic):
    pdf = SkierowanieWcmpPDF()
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

def create_skierowanie_wcmp_pdf(orz_data, wizyta, pacjent, firma, signature_path, fonts):
    font_reg, font_bold, font_italic = fonts
    pdf = init_pdf(font_reg, font_bold, font_italic)
    
    # --- NAGŁÓWEK ---
    pdf.set_font("Roboto", size=9)
    pdf.set_xy(130, 10)
    data_wyst = datetime.datetime.now().strftime('%Y-%m-%d')
    pdf.cell(60, 5, f"Data skierowania: {data_wyst}", ln=1)
    
    pdf.set_xy(130, 15)
    pdf.cell(15, 5, "Płatne: ")
    
    # Logika płatności: jeśli to firma, to Przelew. Jeśli "Prywatnie", to Gotówka.
    is_firma = firma.get('NazwaFirmy') and "prywatnie" not in firma.get('NazwaFirmy', '').lower()
    idx_platne = 1 if is_firma else 0
    pdf.print_options(["Gotówką w kasie*", "Przelew (płatnik - pieczęć)*"], idx_platne, 5, spacer="   ")
    
    # Ramka "Potwierdzenie zarejestrowania"
    pdf.rect(130, 25, 70, 20)
    pdf.set_font("Roboto", size=7)
    pdf.set_xy(130, 26)
    pdf.cell(70, 4, "Potwierdzenie zarejestrowania w WCMP", align="C")
    
    # Pieczątka Lekarza (Tekstowa Lewa Strona)
    pdf.set_xy(10, 15)
    pdf.set_font("Roboto", style="B", size=8)
    naglowek = "PRYWATNA PRAKTYKA LEKARSKA\nJarosław Tarkowski\n62-065 Grodzisk Wlkp., ul. Chopina 18/1\nNIP 788-142-01-53 REGON 631003518"
    pdf.write_text(110, 4, naglowek)
    
    # --- TYTUŁ ---
    pdf.ln(12)
    pdf.set_font("Roboto", style="B", size=14)
    pdf.set_x(10)
    pdf.cell(190, 8, "Skierowanie na badania dodatkowe - uzupełniające", align="C", ln=1)
    pdf.set_font("Roboto", style="B", size=11)
    pdf.set_x(10)
    pdf.cell(190, 6, "Do Wielkopolskiego Centrum Medycyny Pracy w Poznaniu ul. Poznańska 55a", align="C", ln=1)
    
    # --- DANE PACJENTA ---
    pdf.ln(5)
    pdf.set_font("Roboto", size=10)
    pdf.set_x(10)
    pdf.cell(30, 6, "Nazwisko i imię: ")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(100, 6, f"{pacjent.get('Nazwisko', '')} {pacjent.get('Imie', '')}")
    
    pdf.set_font("Roboto", size=10)
    pdf.cell(25, 6, "Data badania: ")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(0, 6, f"{wizyta.get('DataWizyty', '')}", ln=1)
    
    # --- INSTRUKCJA (RAMKA) ---
    pdf.ln(3)
    pdf.set_x(10)
    pdf.set_font("Roboto", style="B", size=8)
    instrukcja = "W dniu badania należy zgłosić się w rejestracji WCMP z dowodem tożsamości, następnie załatwić\nzaznaczone badania, po potwierdzeniu podpisem przez pracownika wykonującego badania\nskierowanie zwrócić w rejestracji!"
    pdf.write_text(190, 4, instrukcja, align="C")
    
    # --- NARAŻENIA ---
    pdf.ln(5)
    pdf.set_x(10)
    pdf.set_font("Roboto", size=9)
    pdf.cell(28, 5, "Rodzaj narażenia: ")
    
    notatki = str(wizyta.get('Notatki', '')).lower()
    
    # Skreślanie poszczególnych narażeń
    idx_wys = 0 if "wysokoś" in notatki else -1
    idx_kier = 1 if "kierowc" in notatki else -1
    idx_woz = 2 if "wózk" in notatki else -1
    idx_komp = 3 if "komputer" in notatki or "ekran" in notatki else -1
    
    x_opt = pdf.get_x()
    if idx_wys == -1: pdf.strike_text("praca na wysokości", 5) 
    else: pdf.cell(pdf.get_string_width("praca na wysokości"), 5, "praca na wysokości")
    pdf.cell(3, 5, ", ")
    
    if idx_kier == -1: pdf.strike_text("kierowca", 5) 
    else: pdf.cell(pdf.get_string_width("kierowca"), 5, "kierowca")
    pdf.cell(3, 5, ", ")
    
    if idx_woz == -1: pdf.strike_text("operator wózka", 5) 
    else: pdf.cell(pdf.get_string_width("operator wózka"), 5, "operator wózka")
    pdf.cell(3, 5, ", ")
    
    if idx_komp == -1: pdf.strike_text("obsługa komputera", 5) 
    else: pdf.cell(pdf.get_string_width("obsługa komputera"), 5, "obsługa komputera")
    pdf.cell(3, 5, ", ")
    
    pdf.cell(0, 5, "inne (jakie?) ......................................", ln=1)
    
    # --- TABELA WCMP (MANUALNE RYSOWANIE LINI PO LINI) ---
    pdf.ln(3)
    y_tbl = pdf.get_y()
    
    cols = [10, 20, 60, 75, 95, 200]
    row_heights = [6, 22, 6, 10, 10, 6, 6, 10, 10, 6, 6, 12]
    
    curr_y = y_tbl
    for h in row_heights:
        pdf.line(cols[0], curr_y, cols[-1], curr_y)
        curr_y += h
    pdf.line(cols[0], curr_y, cols[-1], curr_y) 
    
    for col_x in cols:
        pdf.line(col_x, y_tbl, col_x, curr_y)
        
    # --- WYPEŁNIANIE TABELI TEKSTEM ---
    pdf.set_font("Roboto", style="B", size=8)
    
    r_y = y_tbl
    pdf.set_xy(10, r_y + 1); pdf.cell(10, 4, "LP", align="C")
    pdf.set_xy(20, r_y + 1); pdf.cell(40, 4, "Gabinet / Pracownia", align="C")
    pdf.set_xy(60, r_y + 1); pdf.cell(15, 4, "Piętro", align="C")
    pdf.set_xy(75, r_y + 1); pdf.cell(20, 4, "Nr.pokoju", align="C")
    pdf.set_xy(95, r_y + 1); pdf.cell(105, 4, "Podpis", align="C")
    
    pdf.set_font("Roboto", size=8)
    
    # 1. Laboratorium
    r_y += row_heights[0]
    pdf.set_xy(10, r_y + 9); pdf.cell(10, 4, "1", align="C")
    pdf.set_xy(20, r_y + 9); pdf.cell(40, 4, "Laboratorium", align="C")
    pdf.set_xy(60, r_y + 9); pdf.cell(15, 4, "II", align="C")
    pdf.set_xy(75, r_y + 9); pdf.cell(20, 4, "208", align="C")
    
    pdf.set_xy(97, r_y + 1)
    pdf.cell(100, 4, "OB., Morfologia, płytki, rozmaz, retikulocyty", ln=1)
    pdf.set_x(97); pdf.cell(100, 4, "cholesterol, HDL, LDL, Trójglicerydy", ln=1)
    pdf.set_x(97); pdf.cell(100, 4, "glukoza, bilirubina, AspAT, AlAT, GGTP", ln=1)
    pdf.set_x(97); pdf.cell(100, 4, "kreatynina, mocznik, Mocz badanie ogólne", ln=1)
    pdf.set_x(97); pdf.cell(100, 4, "inne ..............................................................", ln=1)

    # 2. Wibracja
    r_y += row_heights[1]
    pdf.set_xy(10, r_y + 1); pdf.cell(10, 4, "2", align="C")
    pdf.set_xy(20, r_y + 1); pdf.cell(40, 4, "Wibracja", align="C")
    pdf.set_xy(60, r_y + 1); pdf.cell(15, 4, "I", align="C")
    pdf.set_xy(75, r_y + 1); pdf.cell(20, 4, "106", align="C")
    
    # 3. EKG
    r_y += row_heights[2]
    pdf.set_xy(10, r_y + 3); pdf.cell(10, 4, "3", align="C")
    pdf.set_xy(20, r_y + 1); pdf.cell(40, 4, "spoczynkowe", align="C")
    pdf.set_xy(20, r_y + 5); pdf.cell(40, 4, "EKG wysiłkowe", align="C")
    pdf.set_xy(60, r_y + 3); pdf.cell(15, 4, "I", align="C")
    pdf.set_xy(75, r_y + 3); pdf.cell(20, 4, "107", align="C")
    pdf.set_xy(97, r_y + 3); pdf.cell(100, 4, "RR: ..............................", ln=1)

    # 4. Spirometria
    r_y += row_heights[3]
    pdf.set_xy(10, r_y + 3); pdf.cell(10, 4, "4", align="C")
    pdf.set_xy(20, r_y + 3); pdf.cell(40, 4, "Spirometria", align="C")
    pdf.set_xy(60, r_y + 3); pdf.cell(15, 4, "I", align="C")
    pdf.set_xy(75, r_y + 3); pdf.cell(20, 4, "106", align="C")
    pdf.set_xy(97, r_y + 1); pdf.cell(100, 4, "Wzrost: ..............................", ln=1)
    pdf.set_xy(97, r_y + 5); pdf.cell(100, 4, "Waga: ..............................", ln=1)

    # 5. Kardiolog
    r_y += row_heights[4]
    pdf.set_xy(10, r_y + 1); pdf.cell(10, 4, "5", align="C")
    pdf.set_xy(20, r_y + 1); pdf.cell(40, 4, "Kardiolog", align="C")
    pdf.set_xy(60, r_y + 1); pdf.cell(15, 4, "I", align="C")
    pdf.set_xy(75, r_y + 1); pdf.cell(20, 4, "112", align="C")

    # 6. Neurolog
    r_y += row_heights[5]
    pdf.set_xy(10, r_y + 1); pdf.cell(10, 4, "6", align="C")
    pdf.set_xy(20, r_y + 1); pdf.cell(40, 4, "Neurolog", align="C")
    pdf.set_xy(60, r_y + 1); pdf.cell(15, 4, "II", align="C")
    pdf.set_xy(75, r_y + 1); pdf.cell(20, 4, "203", align="C")

    # 7. Laryngolog
    r_y += row_heights[6]
    pdf.set_xy(10, r_y + 3); pdf.cell(10, 4, "7", align="C")
    pdf.set_xy(20, r_y + 3); pdf.cell(40, 4, "Laryngolog", align="C")
    pdf.set_xy(60, r_y + 3); pdf.cell(15, 4, "I", align="C")
    pdf.set_xy(75, r_y + 3); pdf.cell(20, 4, "105, 105A", align="C")
    pdf.set_xy(97, r_y + 1); pdf.cell(100, 4, "Audiometria tonalna", ln=1)
    pdf.set_xy(97, r_y + 5); pdf.cell(100, 4, "Audiometria impedancyjna", ln=1)

    # 8. Okulista
    r_y += row_heights[7]
    pdf.set_xy(10, r_y + 3); pdf.cell(10, 4, "8", align="C")
    pdf.set_xy(20, r_y + 3); pdf.cell(40, 4, "Okulista", align="C")
    pdf.set_xy(60, r_y + 3); pdf.cell(15, 4, "I", align="C")
    pdf.set_xy(75, r_y + 3); pdf.cell(20, 4, "101, 103", align="C")
    pdf.set_xy(97, r_y + 1); pdf.cell(100, 4, "badanie komputerowe", ln=1)
    pdf.set_xy(97, r_y + 5); pdf.cell(100, 4, "dno oka", ln=1)

    # 9. Psycholog
    r_y += row_heights[8]
    pdf.set_xy(10, r_y + 1); pdf.cell(10, 4, "9", align="C")
    pdf.set_xy(20, r_y + 1); pdf.cell(40, 4, "Psycholog", align="C")
    pdf.set_xy(60, r_y + 1); pdf.cell(15, 4, "I", align="C")
    pdf.set_xy(75, r_y + 1); pdf.cell(20, 4, "104, 108", align="C")

    # 10. Dermatolog
    r_y += row_heights[9]
    pdf.set_xy(10, r_y + 1); pdf.cell(10, 4, "10", align="C")
    pdf.set_xy(20, r_y + 1); pdf.cell(40, 4, "Dermatolog", align="C")
    pdf.set_xy(60, r_y + 1); pdf.cell(15, 4, "III", align="C")
    pdf.set_xy(75, r_y + 1); pdf.cell(20, 4, "307", align="C")

    # 11. RTG
    r_y += row_heights[10]
    pdf.set_xy(10, r_y + 4); pdf.cell(10, 4, "11", align="C")
    pdf.set_xy(20, r_y + 2); pdf.cell(40, 4, "Rtg - dołączyć osobne", align="C")
    pdf.set_xy(20, r_y + 6); pdf.cell(40, 4, "skierowanie z uwagami", align="C")
    pdf.set_xy(60, r_y + 4); pdf.cell(15, 4, "Szpital", align="C")
    pdf.set_xy(75, r_y + 2); pdf.cell(20, 4, "Mickiewicza 2", align="C")
    pdf.set_xy(75, r_y + 6); pdf.cell(20, 4, "biuro", align="C")
    pdf.set_xy(97, r_y + 1); pdf.cell(100, 4, "płuc AP, boczne lewe", ln=1)
    pdf.set_xy(97, r_y + 7); pdf.cell(100, 4, "inne (jakie?) ..............................................................", ln=1)
    
    # --- STOPKA DOKUMENTU ---
    pdf.set_y(curr_y + 5)
    pdf.set_font("Roboto", size=9)
    pdf.set_x(10)
    pdf.cell(50, 5, "Wyniki wydać: ")
    
    # Zaznaczamy/skreślamy wynik wydania
    idx_wyniki = 0 # Domyślnie pacjentowi
    pdf.print_options(["pacjentowi", "odbiór w rejestracji", f"wysłać na adres: {firma.get('Adres', '')}"], idx_wyniki, 5, spacer=" / ", max_x=195)
    
    pdf.ln(8)
    pdf.set_font("Roboto", style="I", size=7)
    pdf.set_x(10)
    pdf.cell(0, 4, "właściwe zakreślić / * niepotrzebne skreślić", ln=1)
    
    # --- MIEJSCA NA PIECZĄTKI I QR KOD ---
    pdf.ln(5)
    y_signatures = pdf.get_y()
    
    # Kod QR (Certyfikat z lewej strony)
    data_generowania = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', orz_data.get('PodpisCyfrowy', 'Brak autoryzacji')))
    qr_text = f"SKIEROWANIE WCMP\nNr: {orz_data.get('ID_Orzeczenia', '')}\nWygenerowano: {data_generowania}\nSHA-256: {podpis_cyfrowy}"
    qr = qrcode.make(qr_text)
    qr_img_bytes = io.BytesIO()
    qr.save(qr_img_bytes, format='PNG')
    
    pdf.image(qr_img_bytes, x=15, y=y_signatures, w=22)
    pdf.set_xy(40, y_signatures + 5)
    pdf.set_font("Roboto", size=6)
    pdf.multi_cell(60, 3, f"Zatwierdzono Elektronicznie\nlek. Jarosław Tarkowski\nCertyfikat (SHA-256):\n{podpis_cyfrowy}", align="L")
    
    # Pieczątka lekarza (prawa strona)
    pdf.set_font("Roboto", size=8)
    pdf.set_xy(130, y_signatures)
    pdf.cell(60, 4, "podpis osoby kierującej:", align="C", ln=1)
    
    if signature_path and os.path.exists(signature_path):
        pdf.image(signature_path, x=135, y=pdf.get_y(), w=50)

    return bytes(pdf.output())
