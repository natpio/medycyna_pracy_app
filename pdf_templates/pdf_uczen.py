import os
import io
import qrcode
import datetime
from fpdf import FPDF

class UczenPDF(FPDF):
    pass

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
    
    # --- NAGŁÓWEK ---
    pdf.set_font("Roboto", style="B", size=8)
    pdf.set_xy(10, 10)
    naglowek = "INDYWIDUALNA SPECJALISTYCZNA PRAKTYKA LEKARSKA\nMEDYCYNA PRACY lek. med. Jarosław Tarkowski 62-065 Grodzisk Wlkp. Ul. Chopina 18/1\nNIP 788-142-01-53; Regon 631003518; tel. 602 465 777; e-mail med-pracy@outlook.com"
    pdf.multi_cell(130, 4, naglowek, align="L")
    
    # --- TYTUŁ DOKUMENTU ---
    pdf.ln(10)
    pdf.set_font("Roboto", style="B", size=15)
    pdf.cell(0, 8, "ZAŚWIADCZENIE LEKARSKIE", align="C", ln=1)
    
    # --- PREAMBUŁA ---
    pdf.ln(5)
    pdf.set_font("Roboto", size=9)
    preambula = "W wyniku badania lekarskiego mającego na celu ocenę możliwości pobierania nauki, uwzględniającą stan zdrowia osób badanych i zagrożenia występujące na miejscu wykonywania i odbywania nauki zawodu lub stażu uczniowskiego, studiów, kwalifikacyjnych kursów zawodowych albo kształcenia w szkole doktorskiej, stosownie do przepisu art. 5 ust. 1 pkt 4 i 5 ustawy z dnia 27 czerwca 1997 r. o służbie medycyny pracy (Dz.U. 2022 r. poz. 437)"
    pdf.multi_cell(0, 5, preambula, align="J")
    
    pdf.ln(3)
    pdf.set_font("Roboto", style="B", size=11)
    pdf.cell(0, 6, "orzeka się, że:", align="C", ln=1)
    
    pdf.ln(2)
    
    # --- DANE UCZNIA ---
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
    
    pdf.set_font("Roboto", size=7)
    pdf.set_x(105)
    pdf.multi_cell(0, 3, "a w przypadku osoby, która nie posiada nr PESEL - rodzaj, serię i numer dokumentu\npotwierdzającego tożsamość")
    
    # --- SZKOŁA I KIERUNEK ---
    pdf.ln(4)
    pdf.set_font("Roboto", size=10)
    pdf.multi_cell(0, 5, "podejmującego/kontynuującego praktyczną naukę zawodu*, studia*, kwalifikacyjny kurs zawodowy*, kształcenie w szkole doktorskiej*")
    
    pdf.ln(2)
    pdf.cell(10, 6, "w")
    pdf.set_font("Roboto", style="B", size=11)
    szkola_dane = f"{firma.get('NazwaFirmy', '')}, {firma.get('Adres', '')}" if firma.get('NazwaFirmy') and firma.get('NazwaFirmy') != "Prywatnie / Brak Firmy" else "........................................................................................................................"
    pdf.multi_cell(0, 6, szkola_dane)
    pdf.set_font("Roboto", size=7)
    pdf.set_x(20)
    pdf.cell(0, 4, "/nazwa i adres placówki dydaktycznej/", ln=1)
    
    pdf.ln(2)
    pdf.set_font("Roboto", style="B", size=11)
    stanowisko = str(wizyta.get('Notatki', '')).split('\n')[0].replace('Stanowisko: ', '')
    if not stanowisko or stanowisko.lower() == "brak" or stanowisko.lower() == "uczeń":
        stanowisko = "........................................................................................................................"
    pdf.set_x(20)
    pdf.multi_cell(0, 6, stanowisko)
    pdf.set_font("Roboto", size=7)
    pdf.set_x(20)
    pdf.cell(0, 4, "/zakres praktycznej nauki zawodu albo kształcenia/", ln=1)
    
    # --- DECYZJA ---
    pdf.ln(6)
    decyzja_z_bazy = str(orz_data.get('Decyzja', '')).upper()
    jest_zdolny = "NIEZDOLNY" not in decyzja_z_bazy
    
    # Decyzja Zdolny
    pdf.set_x(10)
    y_box1 = pdf.get_y()
    pdf.rect(10, y_box1 + 1, 4, 4)
    if jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.text(10.5, y_box1 + 4.5, "X")
        
    pdf.set_font("Roboto", size=10)
    pdf.set_xy(16, y_box1)
    pdf.multi_cell(0, 5, "1) brak jest przeciwskazań zdrowotnych do wykonywania i odbywania praktycznej nauki zawodu*, studiów*, kwalifikacyjnego kursu zawodowego*, kształcenia w szkole doktorskiej*")
    
    pdf.set_x(16)
    if jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.cell(0, 6, f"Data następnego badania: {orz_data.get('DataKolejnegoBadania', '')}", ln=1)
    else:
        pdf.cell(0, 6, "Data następnego badania: ........................................", ln=1)
    
    pdf.ln(4)
    
    # Decyzja Niezdolny
    pdf.set_x(10)
    y_box2 = pdf.get_y()
    pdf.rect(10, y_box2 + 1, 4, 4)
    if not jest_zdolny:
        pdf.set_font("Roboto", style="B", size=10)
        pdf.text(10.5, y_box2 + 4.5, "X")
        
    pdf.set_font("Roboto", size=10)
    pdf.set_xy(16, y_box2)
    pdf.multi_cell(0, 5, "2) istnieją przeciwskazania zdrowotne do wykonywania i odbywania praktycznej nauki zawodu*, studiów*, kwalifikacyjnego kursu zawodowego*, kształcenia w szkole doktorskiej*")
    
    pdf.ln(2)
    pdf.set_font("Roboto", size=7)
    pdf.cell(0, 4, "*właściwe zaznaczyć", ln=1)
    
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
        pdf.multi_cell(70, 3, "podpis oraz pieczątka lub nadruk zawierające imię i nazwisko oraz numer prawa wykonywania zawodu lekarza przeprowadzającego badanie", align="C")

    # Kod QR z certyfikatem (bezpieczeństwo)
    data_generowania = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', orz_data.get('PodpisCyfrowy', 'Brak autoryzacji')))
    qr_text = f"UCZEŃ/STUDENT\nNr: {orz_data.get('ID_Orzeczenia', '')}\nWażne: {orz_data.get('DataKolejnegoBadania', '')}\nSHA-256: {podpis_cyfrowy}"
    qr = qrcode.make(qr_text)
    qr_img_bytes = io.BytesIO()
    qr.save(qr_img_bytes, format='PNG')
    pdf.image(qr_img_bytes, x=15, y=y_signatures + 10, w=25)
    
    # --- POUCZENIE PRAWNE (STOPKA) ---
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
