import os
import io
import qrcode
import datetime
from fpdf import FPDF

class SanepidPDF(FPDF):
    def strike_block(self, y_start, y_end, line_h=4, x_start=10, x_end=190):
        curr_y = y_start
        while curr_y < y_end - 1:
            self.line(x_start, curr_y + line_h/2.2, x_end, curr_y + line_h/2.2)
            curr_y += line_h
            
    def write_text(self, w, h, text, align="L"):
        """Nasz własny, bezpieczny silnik łamiący tekst. Zawsze wraca do punktu startu (X)"""
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
    pdf = SanepidPDF()
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

def create_sanepid_pdf(orz_data, wizyta, pacjent, firma, signature_path, fonts):
    font_reg, font_bold, font_italic = fonts
    pdf = init_pdf(font_reg, font_bold, font_italic)
    
    pdf.set_font("Roboto", style="B", size=8)
    pdf.set_xy(10, 10)
    naglowek = "INDYWIDUALNA SPECJALISTYCZNA PRAKTYKA LEKARSKA\nMEDYCYNA PRACY lek. med. Jarosław Tarkowski 62-065 Grodzisk Wlkp. Ul. Chopina 18/1\nNIP 788-142-01-53; Regon 631003518; tel. 602 465 777; e-mail med-pracy@outlook.com"
    pdf.write_text(120, 4, naglowek)
    
    pdf.set_y(30)
    pdf.set_font("Roboto", style="B", size=14)
    pdf.set_x(10)
    pdf.write_text(190, 8, "Orzeczenie lekarskie", align="C")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.set_x(10)
    pdf.write_text(190, 6, "z badania przeprowadzonego do celów sanitarno-epidemiologicznych", align="C")
    
    pdf.ln(5)
    pdf.set_font("Roboto", size=10)
    preambula = "W wyniku badania lekarskiego przeprowadzonego na podstawie art. 6 ustawy z dnia 5 grudnia 2008 r. o zapobieganiu oraz zwalczaniu zakażeń i chorób zakaźnych u ludzi (Dz. U. z 2018 r. poz. 151 z późn. zm.), stwierdzono, że:"
    pdf.set_x(10)
    pdf.write_text(190, 5, preambula)
    
    pdf.ln(5)
    
    pdf.set_x(10)
    pdf.set_font("Roboto", size=10)
    pdf.cell(20, 6, "Pani/Pan:")
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(100, 6, f"{pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')}")
    
    pdf.set_font("Roboto", size=10)
    pdf.cell(25, 6, "Nr PESEL**:")
    pdf.set_font("Roboto", style="B", size=11)
    pesel_str = str(pacjent.get('PESEL', ''))
    formatted_pesel = " ".join(list(pesel_str)) if pesel_str else ""
    pdf.cell(0, 6, formatted_pesel, ln=1)
    
    pdf.ln(2)
    pdf.set_x(10)
    pdf.set_font("Roboto", size=10)
    pdf.cell(30, 6, "zamieszkały/a w:")
    pdf.set_font("Roboto", style="B", size=11)
    adres = pacjent.get('Adres', '.........................................................................................................')
    pdf.cell(0, 6, adres, ln=1)
    
    pdf.ln(2)
    pdf.set_x(10)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 6, "zatrudniony(a) / ubiegający(a) się o zatrudnienie w:", ln=1)
    
    pdf.set_font("Roboto", style="B", size=11)
    firma_dane = f"{firma.get('NazwaFirmy', 'Prywatnie')}, {firma.get('Adres', '')}"
    pdf.set_x(10)
    pdf.write_text(190, 6, firma_dane)
    
    pdf.ln(2)
    pdf.set_x(10)
    pdf.set_font("Roboto", size=10)
    pdf.cell(25, 6, "na stanowisku:")
    pdf.set_font("Roboto", style="B", size=11)
    stanowisko = str(wizyta.get('Notatki', '')).split('\n')[0].replace('Stanowisko: ', '')
    pdf.set_x(35)
    pdf.write_text(165, 6, stanowisko)
    
    # --- DECYZJA SANEPID (Skreślenia zamiast Checkboxów) ---
    pdf.ln(6)
    decyzja_z_bazy = str(orz_data.get('Decyzja', '')).upper()
    jest_zdolny = "NIEZDOLNY" not in decyzja_z_bazy
    
    pdf.set_font("Roboto", size=10)
    
    # Opcja 1
    pdf.set_x(10)
    y_start = pdf.get_y()
    pdf.write_text(190, 5, "1) wobec braku przeciwwskazań zdrowotnych zdolny(a) do podjęcia / wykonania* prac / rozpoczęcia nauki przy których istnieje możliwość przeniesienia zakażenia na inne osoby.")
    
    pdf.set_x(10)
    if jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.cell(0, 6, f"Data następnego badania: {orz_data.get('DataKolejnegoBadania', '')}", ln=1)
        pdf.set_font("Roboto", size=10)
    else:
        pdf.cell(0, 6, "Data następnego badania: ........................................", ln=1)
    if not jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 5)
        
    pdf.ln(4)
    
    # Opcja 2
    pdf.set_x(10)
    y_start = pdf.get_y()
    pdf.write_text(190, 5, "2) wobec przeciwwskazań zdrowotnych - niezdolny(a) do podjęcia / wykonywania* prac/ rozpoczęcia nauki przy których istnieje możliwość przeniesienia zakażenia na inne osoby, w procesie:")
    pdf.set_x(10)
    pdf.cell(0, 5, "a) trwale*", ln=1)
    pdf.set_x(10)
    pdf.cell(0, 5, "b) czasowo na: ........................................... Data następnego badania: ...........................................", ln=1)
    if jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 5)
    
    pdf.ln(12)
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
        pdf.set_x(120)
        pdf.write_text(70, 4, "Badanie profilaktyczne przeprowadził:\nJarosław Tarkowski\nspecjalista medycyny pracy\n30/1JT/370\n8776405", align="C")
        pdf.set_font("Roboto", size=6)
        pdf.set_xy(120, pdf.get_y() + 5)
        pdf.cell(70, 4, "(podpis i pieczęć lekarza przeprowadzającego badania)", align="C")

    data_generowania = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', orz_data.get('PodpisCyfrowy', 'Brak autoryzacji')))
    qr_text = f"SANEPID\nNr: {orz_data.get('ID_Orzeczenia', '')}\nWażne: {orz_data.get('DataKolejnegoBadania', '')}\nSHA-256: {podpis_cyfrowy}"
    qr = qrcode.make(qr_text)
    qr_img_bytes = io.BytesIO()
    qr.save(qr_img_bytes, format='PNG')
    pdf.image(qr_img_bytes, x=15, y=y_signatures + 10, w=25)

    pdf.set_y(245)
    pdf.set_x(10)
    pdf.set_font("Roboto", style="B", size=7)
    pdf.cell(0, 4, "POUCZENIE:", ln=1)
    
    pdf.set_x(10)
    pdf.set_font("Roboto", size=6)
    pouczenie_text = (
        "osoba zainteresowana/przedsiębiorca otrzymujący zaświadczenie lekarskie - w przypadku zastrzeżeń co do treści tego zaświadczenia - może wystąpić z wnioskiem o ponowne badanie lekarskie i wydanie zaświadczenia do wojewódzkiego ośrodka medycyny pracy, a w przypadku gdy zaświadczenie zostało wydane po raz pierwszy w tym ośrodku - do jednostki badawczo-rozwojowej w dziedzinie medycyny pracy. Wniosek składa się za pośrednictwem lekarza, który wydał zaświadczenie.*\n"
        "Zaświadczenie zostało wydane w wyniku ponownego badania.**\n"
        "*Niepotrzebne skreślić\n"
        "** W przypadku osoby, której nie nadano numeru PESEL - nazwa i numer dokumentu stwierdzającego tożsamość."
    )
    pdf.write_text(190, 3, pouczenie_text)
    
    return bytes(pdf.output())
