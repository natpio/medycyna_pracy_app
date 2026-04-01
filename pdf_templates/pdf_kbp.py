import os
import datetime
from fpdf import FPDF

class KartaBadaniaPDF(FPDF):
    def strike_text(self, text, h=4):
        x, y = self.get_x(), self.get_y()
        w = self.get_string_width(text)
        self.cell(w, h, text)
        self.line(x, y + h/2.2, x + w, y + h/2.2)

    def print_options(self, options, selected_idx, h=4, spacer="; ", max_x=195):
        start_x = self.get_x()
        for i, opt in enumerate(options):
            opt_w = self.get_string_width(opt)
            spacer_w = self.get_string_width(spacer) if i < len(options)-1 else 0
            
            # Bezpieczne łamanie do nowej linii
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

    def draw_form_box(self, x, y, w, h, label, value, is_bold=False):
        self.set_xy(x, y)
        self.set_font("Roboto", size=6)
        self.cell(w, 3, label, ln=1)
        self.set_xy(x, y + 3)
        self.set_font("Roboto", style="B" if is_bold else "", size=9)
        self.multi_cell(w, h - 3, str(value), border=1, align='L')

def init_pdf(font_reg, font_bold, font_italic):
    pdf = KartaBadaniaPDF()
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

def create_kbp_pdf(orz_data, wizyta, pacjent, firma, signature_path, fonts):
    font_reg, font_bold, font_italic = fonts
    pdf = init_pdf(font_reg, font_bold, font_italic) 
    
    # --- STRONA 1: DANE OGÓLNE I ZATRUDNIENIE ---
    pdf.set_font("Roboto", size=8)
    pdf.rect(10, 10, 40, 18)
    pdf.set_xy(10, 16)
    pdf.multi_cell(40, 4, "Pieczęć zakładu\nopieki zdrowotnej", align="C")
    
    pdf.set_font("Roboto", style="B", size=14)
    pdf.set_xy(60, 12)
    pdf.cell(130, 6, f"{pacjent.get('Nazwisko', '').upper()} {pacjent.get('Imie', '').upper()}", align="C", ln=1)
    
    pdf.set_font("Roboto", style="B", size=16)
    pdf.set_xy(60, 20)
    pdf.cell(130, 6, "Karta badania profilaktycznego", align="C", ln=1)
    
    pdf.set_font("Roboto", size=8)
    pdf.set_xy(60, 26)
    nr_bad = orz_data.get('ID_Orzeczenia', '')[-6:] if orz_data.get('ID_Orzeczenia') else '......'
    pdf.cell(130, 4, f"(nr kolejny badania {nr_bad})", align="C", ln=1)
    
    pdf.ln(5)
    
    # Metryczka ze skreśleniami
    pdf.set_font("Roboto", size=7)
    pdf.cell(50, 6, "Rodzaj badania profilaktycznego", border=1)
    x_start, y_start = pdf.get_x(), pdf.get_y()
    pdf.cell(140, 6, "", border=1)
    pdf.set_xy(x_start + 2, y_start + 1)
    typ_bad = str(wizyta.get('TypBadania', 'okresowe')).lower()
    idx_bad = 0 if "wstępne" in typ_bad else (1 if "okresowe" in typ_bad else 2)
    pdf.print_options(["wstępne (W)", "okresowe (O)", "kontrolne (K)"], idx_bad, 4)
    pdf.set_xy(10, y_start + 6)
    
    pdf.cell(50, 8, "Pozostała działalność profilaktyczna", border=1)
    x_start, y_start = pdf.get_x(), pdf.get_y()
    pdf.cell(140, 8, "", border=1)
    pdf.set_xy(x_start + 2, y_start + 1)
    pdf.print_options(["monitoring stanu zdrowia (M)", "badania celowane (C)", "czynne poradnictwo (D)", "inne (I)"], -1, 4, max_x=195)
    pdf.set_xy(10, y_start + 8)
    
    pdf.cell(50, 8, "Objęty opieką jako", border=1)
    x_start, y_start = pdf.get_x(), pdf.get_y()
    pdf.cell(140, 8, "", border=1)
    pdf.set_xy(x_start + 2, y_start + 1)
    pdf.print_options(["pracownik (P)", "praca nakładcza (N)", "pobierający naukę (U)", "na własny wniosek (W)"], 0, 4, max_x=195)
    pdf.set_xy(10, y_start + 8)
    
    pdf.ln(5)
    
    y_start = pdf.get_y()
    pdf.draw_form_box(10, y_start, 95, 10, "Nazwisko i imię", f"{pacjent.get('Nazwisko', '')} {pacjent.get('Imie', '')}", is_bold=True)
    pesel_str = str(pacjent.get('PESEL', ''))
    formatted_pesel = "   ".join(list(pesel_str)) if pesel_str else "  ".join(["."] * 11)
    pdf.draw_form_box(105, y_start, 95, 10, "PESEL", formatted_pesel, is_bold=True)
    
    pdf.set_y(y_start + 12)
    adres = pacjent.get('Adres', '......................................................................................')
    pdf.draw_form_box(10, pdf.get_y(), 140, 10, "Adres zamieszkania", adres)
    pdf.draw_form_box(150, pdf.get_y()-10, 50, 10, "Kod pocztowy / Miejscowość", "...... - ......   ......................")
    
    pdf.set_y(pdf.get_y() + 12)
    pdf.draw_form_box(10, pdf.get_y(), 140, 10, "Zawód wyuczony / wykonywany", ".......................................................................")
    pdf.draw_form_box(150, pdf.get_y()-10, 50, 10, "Płeć (K / M)", "......................")
    
    pdf.ln(13)
    
    pdf.set_font("Roboto", style="B", size=8)
    pdf.cell(0, 4, "Dane identyfikacyjne miejsca pracy / pobierania nauki:", ln=1)
    
    y_start2 = pdf.get_y()
    pdf.draw_form_box(10, y_start2, 140, 10, "Nazwa", firma.get('NazwaFirmy', ''))
    pdf.draw_form_box(150, y_start2, 50, 10, "Kod pocztowy", "......... - .........")
    
    pdf.set_y(y_start2 + 12)
    pdf.draw_form_box(10, pdf.get_y(), 190, 10, "Adres", firma.get('Adres', ''))
    
    pdf.set_y(pdf.get_y() + 12)
    stanowisko_pelne = str(wizyta.get('Notatki', ''))
    stanowisko = stanowisko_pelne.split('\n')[0].replace('Stanowisko: ', '') if 'Stanowisko: ' in stanowisko_pelne else stanowisko_pelne
    czynniki = stanowisko_pelne.replace(stanowisko, '').replace('Stanowisko: ', '').replace('Zagrożenia: ', '').strip()
    
    pdf.draw_form_box(10, pdf.get_y(), 190, 10, "Stanowisko pracy / kierunek nauki / kierunek studiów", stanowisko)
    
    pdf.set_y(pdf.get_y() + 12)
    pdf.set_font("Roboto", size=8)
    
    # Bezpieczne łamanie wyrazów i skreślania
    pdf.cell(pdf.get_string_width("Skierowanie od pracodawcy / placówki dydaktycznej:   "), 5, "Skierowanie od pracodawcy / placówki dydaktycznej:   ")
    pdf.print_options(["TAK", "NIE"], 0, 5, spacer=" / ")
    pdf.set_x(150)
    pdf.cell(50, 5, f"Data: {wizyta.get('DataWizyty', '...........')}", ln=1)
    
    pdf.cell(pdf.get_string_width("Informacja o czynnikach szkodliwych na stanowisku pracy / nauki:   "), 5, "Informacja o czynnikach szkodliwych na stanowisku pracy / nauki:   ")
    pdf.print_options(["TAK", "NIE"], 0, 5, spacer=" / ")
    pdf.set_x(150)
    pdf.cell(50, 5, "Wyniki pomiarów:   TAK / NIE", ln=1)
    
    pdf.cell(pdf.get_string_width("Informacja o czynnikach uciążliwych na stanowisku pracy / nauki:   "), 5, "Informacja o czynnikach uciążliwych na stanowisku pracy / nauki:   ")
    pdf.print_options(["TAK", "NIE"], 0, 5, spacer=" / ")
    pdf.set_x(150)
    pdf.cell(50, 5, "Data badania: ........................", ln=1)
    
    pdf.ln(2)
    pdf.draw_form_box(10, pdf.get_y(), 190, 20, "Czynniki szkodliwe i uciążliwe dla zdrowia występujące w miejscu pracy (zgodnie z informacjami na skierowaniu)", czynniki)
    
    pdf.ln(23)
    
    pdf.set_font("Roboto", style="B", size=8)
    pdf.cell(0, 4, "Dotychczasowe zatrudnienie / dotychczasowa praktyczna nauka zawodu, studia lub studia doktoranckie", ln=1)
    
    pdf.set_font("Roboto", size=7)
    pdf.cell(60, 6, "Nazwa i adres pracodawcy/placówki", border=1, align="C")
    pdf.cell(40, 6, "Stanowisko pracy/nauki", border=1, align="C")
    pdf.cell(30, 6, "Okres zatrudnienia", border=1, align="C")
    pdf.cell(35, 6, "Czynniki szkodliwe/uciążliwe", border=1, align="C")
    pdf.cell(25, 6, "Okres w narażeniu", border=1, align="C", ln=1)
    
    for _ in range(4):
        pdf.cell(60, 5, "", border=1)
        pdf.cell(40, 5, "", border=1)
        pdf.cell(30, 5, "", border=1)
        pdf.cell(35, 5, "", border=1)
        pdf.cell(25, 5, "", border=1, ln=1)
        
    pdf.ln(5)
    
    pdf.set_font("Roboto", style="B", size=8)
    pdf.cell(0, 4, "Czy w przebiegu pracy zawodowej:", ln=1)
    pdf.set_font("Roboto", size=8)
    
    pdf.cell(pdf.get_string_width("a) stwierdzono chorobę zawodową?  "), 5, "a) stwierdzono chorobę zawodową?  ")
    pdf.print_options(["Tak", "Nie"], 1, 5, " / ")
    pdf.cell(0, 5, "  jaką? ................... Nr z wykazu chorób: ...........", ln=1)
    
    pdf.cell(pdf.get_string_width("b) lekarz wnioskował o zmianę stanowiska pracy ze względu na stan zdrowia?  "), 5, "b) lekarz wnioskował o zmianę stanowiska pracy ze względu na stan zdrowia?  ")
    pdf.print_options(["Tak", "Nie"], 1, 5, " / ")
    pdf.cell(0, 5, "  kiedy? ......................", ln=1)
    
    pdf.cell(pdf.get_string_width("c) badany(a) uległ(a) wypadkowi w pracy?  "), 5, "c) badany(a) uległ(a) wypadkowi w pracy?  ")
    pdf.print_options(["Tak", "Nie"], 1, 5, " / ")
    pdf.cell(0, 5, "  kiedy? ................. z jakiego powodu? ...........", ln=1)
    
    pdf.cell(pdf.get_string_width("d) orzeczono świadczenia rentowe? / stopień niepełnosprawności?  "), 5, "d) orzeczono świadczenia rentowe? / stopień niepełnosprawności?  ")
    pdf.print_options(["Tak", "Nie"], 1, 5, " / ")
    pdf.cell(0, 5, "  stopień/symbol: .........................", ln=1)
    
    # --- STRONA 2: WYWIAD CHOROBOWY I BADANIE PRZEDMIOTOWE ---
    pdf.add_page()
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "Badanie Podmiotowe:", ln=1)
    
    pdf.set_font("Roboto", size=8)
    pdf.cell(0, 5, "Skargi badanego (ej): ....................................................................................................................................", ln=1)
    pdf.cell(0, 5, "..........................................................................................................................................................", ln=1)
    
    pdf.ln(3)
    
    pdf.set_font("Roboto", style="B", size=7)
    pdf.cell(90, 6, "Czy badany(a) choruje lub chorował(a) na:", border=1, align="C")
    pdf.cell(10, 6, "Tak", border=1, align="C")
    pdf.cell(10, 6, "Nie", border=1, align="C")
    pdf.cell(80, 6, "Zaburzenia / Opis", border=1, align="C", ln=1)
    
    pdf.set_font("Roboto", size=7)
    pytania_wywiad = [
        "Urazy czaszki i układu ruchu",
        "Omdlenia, zawroty głowy, zab. Równowagi",
        "Padaczka, napadowe utraty świadomości",
        "Inne choroby układu nerwowego, lecz. u neurol.",
        "Choroby psychiczne, leczenie u psychiatry",
        "Cukrzyca, zab. świadomości, senność, niski cukier",
        "Ch. narządu słuchu i głosu",
        "Ch. narządu wzroku",
        "Ch. układu krwiotwórczego",
        "Ch. układu krążenia",
        "Ch. układu oddechowego",
        "Ch. ukł. pokarmowego",
        "Ch. ukł. moczowo-płciowego",
        "Ch. ukł. ruchu, ograniczenia ruchu w stawach",
        "Ch. skóry / uczulenia/alergia w pracy",
        "Ch. zakaźne / pasożytnicze"
    ]
    
    for p in pytania_wywiad:
        pdf.cell(90, 5, p, border=1)
        pdf.cell(10, 5, "", border=1)
        pdf.cell(10, 5, "", border=1)
        pdf.cell(80, 5, "", border=1, ln=1)
        
    pdf.cell(90, 5, "U kobiet: Data ostatniej miesiączki: ........................", border=1)
    pdf.cell(100, 5, " cyklu: Tak / Nie; porody: .........; poronienia: .........; leki hormonalne: .........", border=1, ln=1)
    
    pdf.cell(90, 5, "Inne problemy zdrowotne", border=1)
    pdf.cell(10, 5, "", border=1)
    pdf.cell(10, 5, "", border=1)
    pdf.cell(80, 5, "", border=1, ln=1)
    
    pdf.cell(90, 5, "Palenie tytoniu: obecnie [ ]  w przeszłości [ ]  nie palę [ ]", border=1)
    pdf.cell(100, 5, " Inne używki  Nie / Tak   jakie? ..............................", border=1, ln=1)
    
    pdf.ln(4)
    
    pdf.set_font("Roboto", size=8)
    pdf.cell(0, 5, "Wywiad rodzinny: alergie, astma, cukrzyca, chor.psychiczne, choroby serca, nadciśnienie tętnicze, nowotwory, inne:", ln=1)
    pdf.cell(0, 5, "..........................................................................................................................................................", ln=1)
    
    pdf.ln(2)
    pdf.cell(0, 5, "Subiektywna ocena stanu zdrowia:", ln=1)
    pdf.cell(pdf.get_string_width(" "), 5, " ")
    pdf.print_options(["Bardzo Dobre", "Dobre", "Raczej dobre", "Raczej słabe", "Słabe"], 1, 5, " / ")
    pdf.cell(0, 5, "    opis uwagi: .......................................", ln=1)
    
    pdf.ln(2)
    pdf.cell(0, 5, "Czy badany(a) przebył(a) zabieg / i operacyjny/e? Jakie? Kiedy? ....................................................", ln=1)
    pdf.cell(0, 5, "Czy jest pod opieką poradni specjalistycznej? Jakiej? ..............................................................", ln=1)
    pdf.cell(0, 5, "Czy badany(a) przyjmuje leki? Jakie? ...............................................................................", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Roboto", style="I", size=8)
    pdf.cell(0, 4, "Oświadczam, że zrozumiałem(am) treść zadawanych pytań i odpowiedziałem(am) zgodnie z prawdą.", ln=1)
    pdf.ln(6)
    pdf.cell(0, 4, "....................................................................", ln=1, align="R")
    pdf.cell(0, 3, "(podpis badanego)", ln=1, align="R")
    
    pdf.ln(4)
    
    pdf.set_font("Roboto", style="B", size=10)
    pdf.cell(0, 6, "Badanie przedmiotowe*", ln=1)
    
    pdf.set_font("Roboto", size=8)
    pdf.cell(0, 5, "Wzrost ........ cm    Masa ciała ........ kg    Tętno ...... / min.    RR ...... / ...... mmHg", ln=1)
    pdf.cell(0, 5, "Wzrok: VIS: OP: .................... C.C: ....................  OL: .................... C.C: ....................", ln=1)
    pdf.cell(0, 5, "rozpoznawanie barw: .................. zez: TAK / NIE     słuch: szept UP .......... m, UL .......... m", ln=1)
    pdf.cell(0, 5, "Orientacyjne pole widzenia: .............................. Układ równowagi: Romberg: ..............................", ln=1)
    pdf.cell(0, 5, "Oczopląs obecny / nieobecny", ln=1)
    
    pdf.ln(3)
    
    pdf.set_font("Roboto", style="B", size=7)
    pdf.cell(40, 5, "Narząd / Układ", border=1, align="C")
    pdf.cell(15, 5, "Norma", border=1, align="C")
    pdf.cell(15, 5, "Pat.", border=1, align="C")
    pdf.cell(15, 5, "N.B.", border=1, align="C")
    pdf.cell(105, 5, "Patologia (opis)", border=1, align="C", ln=1)

    uklady = [
        "Skóra", "Czaszka", "Węzły chłonne", "Nos", "Jama ustno-gardłowa", 
        "Szyja", "Klatka piersiowa", "Płuca", "Układ sercowo-naczyniowy", 
        "Jama brzuszna", "Układ moczowo-płciowy", "Układ ruchu", "Układ nerwowy", "Stan psychiczny"
    ]
    pdf.set_font("Roboto", size=7)
    for u in uklady:
        pdf.cell(40, 5, u, border=1)
        pdf.cell(15, 5, "", border=1)
        pdf.cell(15, 5, "", border=1)
        pdf.cell(15, 5, "", border=1)
        pdf.cell(105, 5, "", border=1, ln=1)
        
    pdf.set_font("Roboto", size=6)
    pdf.cell(0, 4, "*Niewłaściwe skreślić, przy czym stwierdzenie patologii powinno być uzupełnione jej opisem. N.B. - Nie Badano", ln=1)
    
    # --- STRONA 3: BADANIA POMOCNICZE I DECYZJA ---
    pdf.add_page()
    
    pdf.set_font("Roboto", style="B", size=9)
    pdf.cell(0, 5, "Badania pomocnicze", ln=1)
    pdf.set_font("Roboto", size=7)
    pdf.cell(10, 6, "L.p", border=1, align="C")
    pdf.cell(50, 6, "Rodzaj badania", border=1, align="C")
    pdf.cell(30, 6, "Data skierowania", border=1, align="C")
    pdf.cell(30, 6, "data wykonania bad.", border=1, align="C")
    pdf.cell(70, 6, "Wyniki badania (najważniejsze)", border=1, align="C", ln=1)
    for i in range(1, 4):
        pdf.cell(10, 5, str(i), border=1, align="C")
        pdf.cell(50, 5, "", border=1)
        pdf.cell(30, 5, "", border=1)
        pdf.cell(30, 5, "", border=1)
        pdf.cell(70, 5, "", border=1, ln=1)
        
    pdf.ln(5)
    
    pdf.set_font("Roboto", style="B", size=9)
    pdf.cell(0, 5, "Konsultacje specjalistyczne", ln=1)
    pdf.set_font("Roboto", size=7)
    pdf.cell(10, 6, "L.p", border=1, align="C")
    pdf.cell(50, 6, "Skierowanie do specjalisty", border=1, align="C")
    pdf.cell(30, 6, "Data skierowania", border=1, align="C")
    pdf.cell(30, 6, "Data konsultacji", border=1, align="C")
    pdf.cell(70, 6, "Wynik konsultacji", border=1, align="C", ln=1)
    for i in range(1, 5):
        pdf.cell(10, 5, str(i), border=1, align="C")
        pdf.cell(50, 5, "", border=1)
        pdf.cell(30, 5, "", border=1)
        pdf.cell(30, 5, "", border=1)
        pdf.cell(70, 5, "", border=1, ln=1)
        
    pdf.ln(5)
    
    pdf.set_font("Roboto", size=8)
    pdf.cell(pdf.get_string_width("Zakres badań poszerzony poza wskazówki metodyczne:   "), 5, "Zakres badań poszerzony poza wskazówki metodyczne:   ")
    pdf.print_options(["NIE", "TAK"], 0, 5, " / ")
    pdf.cell(0, 5, "   Uzasadnienie: ........................................", ln=1)
    
    pdf.cell(pdf.get_string_width("Zmiana częstotliwości wykonywania badań okresowych:   "), 5, "Zmiana częstotliwości wykonywania badań okresowych:   ")
    pdf.print_options(["NIE", "TAK"], 0, 5, " / ")
    pdf.cell(0, 5, "   Uzasadnienie: ........................................", ln=1)
    
    pdf.ln(3)
    pdf.cell(0, 5, "Rozpoznanie: ..........................................................................................................", ln=1)
    pdf.cell(0, 5, "Dane adresowe jednostki podstawowej opieki zdrowotnej: ................................................................", ln=1)
    pdf.cell(0, 5, "Informacje dla lekarza rodzinnego: ....................................................................................", ln=1)
    pdf.cell(0, 5, "Zalecenia: ............................................................................................................", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Roboto", style="I", size=8)
    pdf.cell(0, 4, "Oświadczam, że zrozumiałe(am) treść zaleceń i konsekwencji zdrowotnych wynikających z niedostosowania się do nich:", ln=1)
    pdf.ln(6)
    pdf.cell(0, 4, "....................................................................", ln=1, align="R")
    pdf.cell(0, 3, "Podpis pacjenta:", ln=1, align="R")
    
    pdf.ln(5)
    
    # 5. DECYZJA ORZECZNICZA - SKREŚLANIE AKAPITÓW
    pdf.set_font("Roboto", style="B", size=9)
    pdf.cell(0, 5, "Wydano orzeczenie o:", ln=1)
    
    pdf.set_font("Roboto", size=8)
    decyzja_z_bazy = str(orz_data.get('Decyzja', '')).upper()
    jest_zdolny = "NIEZDOLNY" not in decyzja_z_bazy
    
    # Decyzja Zdolny
    y_start = pdf.get_y()
    pdf.multi_cell(0, 4, "- brak przeciwwskazań zdrowotnych do pracy na stanowisku")
    if not jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 4)
    
    y_start = pdf.get_y()
    pdf.multi_cell(0, 4, "- braku przeciwwskazań zdrowotnych do podjęcia lub kontynuowania nauki, studiów lub studiów doktoranckich")
    if not jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 4)
    
    # Decyzja Niezdolny
    y_start = pdf.get_y()
    pdf.multi_cell(0, 4, "- przeciwwskazaniach zdrowotnych do pracy na stanowisku")
    if jest_zdolny: pdf.strike_block(y_start, pdf.get_y(), 4)
    
    # Skreślenie całej reszty długiego bloku
    y_start = pdf.get_y()
    txt_rest = (
        "- przeciwwskazaniach zdrowotnych do podjęcia lub kontynuowania nauki, studiów lub studiów doktoranckich\n"
        "- utracie zdolność do wykonywania dotychczasowej pracy\n"
        "- przeciwwskazaniach zdrowotnych do wykonywania dotychczasowej pracy przez pracownicę w ciąży lub karmiącą dziecko piersią uzasadniających:\n"
        "       a) przeniesienie pracownicy do innej pracy, a jeżeli jest to niemożliwe, zwolnienie jej na czas niezbędny z obowiązku świadczenia pracy\n"
        "       b) zmianę warunków pracy na dotychczas zajmowanym stanowisku pracy lub skróceniu czasu pracy lub przeniesienia pracownicy do innej pracy...\n"
        "- niezdolności badanego (ej) do wykonywania dotychczasowej pracy i konieczności przeniesienia na inne stanowisko ze względu na:\n"
        "       * szkodliwy wpływ wykonywanej pracy na zdrowie; zagrożenie, jakie stwarza wykonywana praca dla zdrowia młodocianego;\n"
        "       * podejrzenie powstania choroby zawodowej; niezdolność ze względu na chorobę zawodową lub skutki wypadku przy pracy;\n"
        "- potrzebie stosowania okularów korygujących wzrok podczas pracy przy obsłudze monitora ekranowego\n"
        "- inne"
    )
    pdf.multi_cell(0, 4, txt_rest)
    pdf.strike_block(y_start, pdf.get_y(), 4)
    
    pdf.ln(3)
    uwagi = str(orz_data.get('UwagiLekarza', ''))
    if not uwagi: uwagi = "...................................................................................................."
    pdf.set_font("Roboto", style="B", size=8)
    pdf.cell(15, 5, "UWAGI: ")
    pdf.set_font("Roboto", size=8)
    pdf.multi_cell(0, 5, uwagi)
    
    pdf.ln(3)
    data_wystawienia = orz_data.get('DataWystawienia', datetime.datetime.now().strftime('%Y-%m-%d'))
    data_kolejnego = orz_data.get('DataKolejnegoBadania', '........................')
    pdf.cell(0, 5, f"Data wydania orzeczenia: {data_wystawienia}", ln=1)
    pdf.cell(0, 5, f"Data następnego badania: {data_kolejnego}", ln=1)
    pdf.cell(0, 5, "Badany(a) / podmiot kierujący na badanie odwołuje się do treści orzeczenia lekarskiego do ........................................... w dniu .................", ln=1)
    
    pdf.ln(5)
    y_signatures = pdf.get_y()
    
    pdf.set_xy(10, y_signatures)
    pdf.cell(100, 5, f"Dokumentację medyczną wydano osobie badanej do jednostki odwoławczej w dniu: .........................")
    
    if signature_path and os.path.exists(signature_path):
        pdf.image(signature_path, x=130, y=y_signatures - 15, w=55)
    else:
        pdf.set_xy(120, y_signatures)
        pdf.set_font("Roboto", style="B", size=8)
        pdf.multi_cell(70, 4, "Badanie profilaktyczne przeprowadził:\nJarosław Tarkowski\nspecjalista medycyny pracy\n30/1JT/370\n8776405", align="C")
        pdf.set_font("Roboto", size=6)
        pdf.set_xy(120, pdf.get_y() + 5)
        pdf.cell(70, 4, "Pieczęć i podpis lekarza :", align="C")

    pdf.set_y(260)
    pdf.set_font("Roboto", size=7)
    pdf.cell(10, 5, "Lp", border=1, align="C")
    pdf.cell(60, 5, "Imię Nazwisko, Pesel", border=1, align="C")
    pdf.cell(40, 5, "Rodzaj orzecz. Data wydania", border=1, align="C")
    pdf.cell(40, 5, "Potwierdzenie Odbioru, Podpis:", border=1, align="C")
    pdf.cell(40, 5, "Uwagi", border=1, align="C", ln=1)
    pdf.cell(10, 8, "1", border=1, align="C")
    pdf.cell(60, 8, f"{pacjent.get('Nazwisko','')} {pacjent.get('Imie','')}, {pacjent.get('PESEL','')}", border=1, align="C")
    pdf.cell(40, 8, f"Orzeczenie MP, {data_wystawienia}", border=1, align="C")
    pdf.cell(40, 8, "", border=1, align="C")
    pdf.cell(40, 8, "", border=1, align="C", ln=1)
        
    return bytes(pdf.output())
