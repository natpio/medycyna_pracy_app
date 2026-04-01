import os
import datetime
from fpdf import FPDF

# --- KLASA POMOCNICZA PDF ---
class KierowcaWywiadPDF(FPDF):
    def draw_question_row(self, lp, text, is_header=False):
        """Rysuje wiersz tabeli wywiadu z automatycznym dopasowaniem wysokości."""
        x = self.get_x()
        y = self.get_y()
        
        # Ustawienie czcionki
        if is_header:
            self.set_font("Roboto", style="B", size=8)
        else:
            self.set_font("Roboto", size=8)
            
        # Symulacja rysowania tekstu, aby obliczyć wymaganą wysokość wiersza
        self.set_xy(x + 12, y + 2)
        self.multi_cell(136, 4, text)
        h = self.get_y() - y + 2 # Obliczona wysokość + padding
        
        # Wymuszenie minimalnej wysokości wiersza
        if h < 8: h = 8
        
        # Rysowanie kratek (obramowań)
        self.rect(x, y, 10, h)      # Kolumna Lp.
        self.rect(x+10, y, 140, h)  # Kolumna Pytanie
        self.rect(x+150, y, 20, h)  # Kolumna TAK
        self.rect(x+170, y, 20, h)  # Kolumna NIE
        
        # Wpisanie Lp.
        self.set_xy(x, y + (h/2) - 2)
        self.cell(10, 4, lp, align="C")
        
        # Wpisanie właściwego tekstu pytania
        self.set_xy(x + 12, y + 2)
        self.multi_cell(136, 4, text)
        
        # Ustawienie kursora na początek następnego wiersza
        self.set_xy(10, y + h)

def init_pdf(font_reg, font_bold, font_italic):
    pdf = KierowcaWywiadPDF()
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

# --- GŁÓWNY GENERATOR OŚWIADCZENIA KIEROWCY ---
def create_kierowca_wywiad_pdf(orz_data, wizyta, pacjent, firma, signature_path, fonts):
    font_reg, font_bold, font_italic = fonts
    pdf = init_pdf(font_reg, font_bold, font_italic)
    
    # ==================== STRONA 1 ====================
    
    # --- TYTUŁ ---
    pdf.set_font("Roboto", style="B", size=12)
    pdf.cell(0, 10, "OŚWIADCZENIE DOTYCZĄCE STANU ZDROWIA¹)", align="C", ln=1)
    
    # --- I. DANE OSOBY ---
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "I. Dane osoby podlegającej badaniu lekarskiemu", ln=1)
    
    pdf.set_font("Roboto", size=9)
    pdf.cell(35, 6, "Nazwisko i imię:")
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, f"{pacjent.get('Nazwisko', '')} {pacjent.get('Imie', '')}", ln=1)
    
    pdf.set_font("Roboto", size=9)
    pdf.cell(35, 6, "Adres zamieszkania:")
    pdf.set_font("Roboto", style="B", size=10)
    adres = pacjent.get('Adres', '.........................................................................................................')
    pdf.cell(0, 6, adres, ln=1)
    
    pdf.set_font("Roboto", size=9)
    pdf.cell(35, 6, "Data urodzenia:")
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(75, 6, str(pacjent.get('DataUrodzenia', '........................')))
    
    pdf.set_font("Roboto", size=9)
    pdf.cell(35, 6, "Kategoria prawa jazdy:")
    pdf.cell(0, 6, "................................", ln=1)
    
    pdf.set_font("Roboto", size=9)
    pdf.cell(60, 6, "Telefon lub adres e-mail - jeżeli posiada:")
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, str(pacjent.get('Telefon', '........................................')), ln=1)
    
    pdf.set_font("Roboto", size=8)
    pdf.cell(75, 8, "Nr PESEL, a w przypadku osoby, której nie nadano nr")
    pdf.set_font("Roboto", style="B", size=11)
    pesel_str = str(pacjent.get('PESEL', ''))
    formatted_pesel = " ".join(list(pesel_str)) if pesel_str else ""
    pdf.cell(0, 8, formatted_pesel, ln=1)
    pdf.set_font("Roboto", size=8)
    pdf.cell(0, 2, "PESEL - nazwa i numer dokumentu stwierdzającego tożsamość", ln=1)
    
    pdf.ln(4)
    
    # --- II. INSTRUKCJA ---
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "II. Instrukcja wypełniania ankiety", ln=1)
    pdf.set_font("Roboto", size=8)
    pdf.multi_cell(0, 4, "Proszę odpowiedzieć na poniższe pytania przez wstawienie znaku \"X\" w odpowiednią rubrykę. W przypadku gdy pytanie jest niezrozumiałe, należy poprosić o pomoc lekarza, aby udzielić odpowiedzi.")
    
    pdf.ln(4)
    
    # --- III. DANE DOTYCZĄCE STANU ZDROWIA (TABELA - STRONA 1) ---
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "III. Dane dotyczące stanu zdrowia", ln=1)
    
    # Nagłówek Tabeli
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.set_font("Roboto", style="B", size=8)
    pdf.rect(x, y, 10, 6)
    pdf.rect(x+10, y, 140, 6)
    pdf.rect(x+150, y, 20, 6)
    pdf.rect(x+170, y, 20, 6)
    
    pdf.set_xy(x, y+1)
    pdf.cell(10, 4, "Lp.", align="C")
    pdf.set_xy(x+10, y+1)
    pdf.cell(140, 4, "Pytanie dotyczące stanu zdrowia", align="C")
    pdf.set_xy(x+150, y+1)
    pdf.cell(20, 4, "TAK", align="C")
    pdf.set_xy(x+170, y+1)
    pdf.cell(20, 4, "NIE", align="C", ln=1)
    
    pdf.set_xy(10, y+6)
    
    # Wiersze Pytania (Strona 1)
    pytania_p1 = [
        ("1.", "Czy korzysta Pan/Pani z opieki zdrowotnej z powodu jakiejkolwiek choroby, przebytych urazów lub niepełnosprawności?"),
        ("2.", "Czy przyjmuje Pan/Pani leki przepisane na receptę, dostępne bez recepty lub suplementy diety? Jeśli tak - to jakie? ...................................................................................................................................."),
        ("3.", "Czy kiedykolwiek wystąpiły lub stwierdzono w Pana/Pani niżej wymienione choroby, dolegliwości lub został(a) Pan/Pani poinformowany(-na) o nich przez lekarza?"),
        ("3.1.", "wysokie ciśnienie krwi"),
        ("3.2.", "choroby serca"),
        ("3.3.", "ból w klatce piersiowej, choroba wieńcowa"),
        ("3.4.", "zawał serca"),
        ("3.5.", "choroby wymagające operacji serca"),
        ("3.6.", "nieregularne bicie serca"),
        ("3.7.", "zaburzenia oddychania"),
        ("3.8.", "zaburzenia funkcji nerek"),
        ("3.9.", "cukrzyca"),
        ("3.10.", "urazy głowy, urazy kręgosłupa"),
        ("3.11.", "drgawki, padaczka"),
        ("3.12.", "omdlenia"),
        ("3.13.", "udar mózgu/wylew krwi do mózgu"),
        ("3.14.", "nudności, zawroty głowy, problemy z utrzymaniem równowagi"),
        ("3.15.", "utraty pamięci lub trudności z koncentracją"),
        ("3.16.", "inne zaburzenia neurologiczne"),
        ("3.17.", "choroby szyi, pleców lub kończyn"),
        ("3.18.", "podwójne widzenie, kłopoty ze wzrokiem"),
        ("3.19.", "zaburzenia rozpoznawania barw (daltonizm)"),
        ("3.20.", "trudności w widzeniu po zmierzchu i częste uczucie oślepienia prze światła innych pojazdów"),
        ("3.21.", "ubytek słuchu, głuchota lub operacja ucha"),
        ("3.22.", "choroby psychiczne, depresja lub zaburzenia nerwicowe"),
        ("4.", "Czy kiedykolwiek miał(a) Pan/Pani operację lub wypadek, lub był(a) Pan/Pani w szpitalu z jakiegokolwiek powodu? Opisać: ......................................................................................................................")
    ]
    
    for lp, tekst in pytania_p1:
        is_header = True if lp == "3." else False
        pdf.draw_question_row(lp, tekst, is_header)


    # ==================== STRONA 2 ====================
    pdf.add_page()
    pdf.set_y(15)
    
    # Wiersze Pytania (Strona 2)
    pytania_p2 = [
        ("5.", "Czy używa lub kiedykolwiek używał(a) Pan/Pani aparatu słuchowego? Jeżeli tak, to kiedy? ..........................................................................................................................................................."),
        ("6.", "Czy kiedykolwiak był(a) Pan/Pani badany(-na) z powodu zaburzeń snu lub lekarz informował, że ma Pan/Pani zaburzenia snu, zespoły bezdechu nocnego lub narkolepsję?"),
        ("7.", "Czy ktokolwiek mówił Panu/Pani o zaobserwowanych u Pana/Pani epizodach zatrzymania oddechu w czasie snu?"),
        ("8.", "Czy kiedykolwiek potrzebował(a) Pan/Pani pomocy lub wsparcia z powodu nadużycia alkoholu lub środków działających podobnie do alkoholu?"),
        ("9.", "Czy używa Pan/Pani narkotyków lub innych substancji psychoaktywnych? Jeżeli tak, to jakich? ....................................................................................................................................................."),
        ("10.", "Jak często pije Pan/Pani alkohol (piwo, wino, wódkę i inne alkohole)?"),
        ("10.1", "nigdy albo rzadziej niż raz w miesiącu"),
        ("10.2", "raz w miesiącu"),
        ("10.3", "dwa do czterech razy w miesiącu"),
        ("10.4", "dwa do trzech razy w tygodniu"),
        ("10.5", "cztery i więcej razy w tygodniu"),
        ("11.", "Czy był(a) Pan/Pani sprawcą/uczestnikiem wypadku drogowego od dnia zdania egzaminu na prawo jazdy?"),
        ("12.", "Czy pobiera Pan/Pani rentę z tytułu niezdolności do pracy? Jeżeli tak, to z jakiego powodu. ........................................................................................................................................................"),
        ("13.", "Czy posiada Pan/Pani orzeczenie stwierdzające niepełnosprawność? Jeżeli tak, to jakie i z jakiej przyczyny. ........................................................................................................................................")
    ]
    
    for lp, tekst in pytania_p2:
        is_header = True if lp == "10." else False
        pdf.draw_question_row(lp, tekst, is_header)
        
    pdf.ln(10)
    
    # --- IV. OŚWIADCZENIE I PODPIS ---
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "IV", ln=1)
    
    pdf.set_font("Roboto", size=9)
    pdf.multi_cell(0, 5, "Oświadczam, że jestem świadomy(-ma) konieczności zgłoszenia się do ponownej oceny stanu zdrowia w celu stwierdzenia istnienia lub braku przeciwskazań zdrowotnych do kierowania pojazdami w przypadku:")
    
    pdf.set_x(15)
    pdf.multi_cell(0, 5, "1) wystąpienia w porze czuwania epizodu ciężkiej hipoglikemii, także niezwiązanego z kierowaniem pojazdami (dotyczy osób chorych na cukrzycę);")
    pdf.set_x(15)
    pdf.multi_cell(0, 5, "2) wystąpienia napadu padaczki lub drgawek.")
    
    pdf.ln(15)
    pdf.cell(100, 5, "...............................................................")
    pdf.cell(0, 5, "...............................................................", align="R", ln=1)
    
    pdf.set_font("Roboto", size=7)
    pdf.cell(100, 4, "Data")
    pdf.cell(0, 4, "Podpis osoby składającej oświadczenie", align="R", ln=1)
    
    # --- OBJAŚNIENIA (STOPKA) ---
    pdf.set_y(260)
    pdf.set_font("Roboto", style="B", size=6)
    pdf.cell(0, 3, "Objaśnienie:", ln=1)
    pdf.set_font("Roboto", size=6)
    objasnienie = (
        "1) Zgodnie z art. 78 ustawy z dnia 5 stycznia 2011 r. o kierujących pojazdami (Dz.U. z 2021 r. poz. 1212, z późn. zm.) osoba podlegająca badaniu lekarskiemu, a w przypadku niepełnoletniego kandydata, ucznia i słuchacza, o których mowa w art. 75c ust. 1 pkt 7 i 8 tej ustawy, rodzic w rozumieniu art. 4 pkt 19 ustawy z dnia 14 grudnia 2016 r. - Prawo oświatowe (Dz. U. z 2021 r. poz. 1082, z późn zm.) są obowiązani wypełnić oświadczenie dotyczące stanu zdrowia pod rygorem odpowiedzialności karnej wynikającej z art. 233 ustawy z dnia 6 czerwca 1997 r. -Kodeks karny (Dz. U. z 2022 r. poz. 1138, z późn. zm.). Oświadczenie składa się uprawnionemu lekarzowi."
    )
    pdf.multi_cell(0, 3, objasnienie)
    
    return bytes(pdf.output())
