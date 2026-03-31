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
        # multi_cell rysuje ramkę (border=1) i łamie tekst, jeśli jest za długi
        self.multi_cell(w, h - 4, str(value), border=1, align='L')

# --- GENERATORY SZABLONÓW ---

def init_pdf():
    pdf = OrzeczeniePDF()
    pdf.add_page()
    if os.path.exists(font_regular) and os.path.exists(font_bold):
        pdf.add_font("Roboto", style="", fname=font_regular)
        pdf.add_font("Roboto", style="B", fname=font_bold)
        pdf.set_font("Roboto", size=10)
    else:
        pdf.set_font("Arial", size=10)
    return pdf

def create_standard_pdf(orz_data, wizyta, pacjent, firma):
    pdf = init_pdf()
    
    # Prawy górny róg
    pdf.set_font("Roboto", size=9)
    pdf.cell(0, 5, f"Luboń, dnia: {wizyta.get('DataWizyty', '')}", align="R", ln=1)
    
    # Tytuł
    pdf.ln(10)
    pdf.set_font("Roboto", style="B", size=16)
    pdf.cell(0, 10, "ORZECZENIE LEKARSKIE", align="C", ln=1)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 5, f"Nr {orz_data.get('ID_Orzeczenia', '')}", align="C", ln=1)
    
    # Sekcja: Pracodawca
    pdf.ln(10)
    pdf.draw_form_box(10, 50, 190, 15, "Wystawione przez pracodawcę (Nazwa, Adres, NIP):", 
                      f"{firma.get('NazwaFirmy', '')}, {firma.get('Adres', '')}, NIP: {firma.get('NIP', '')}")
    
    # Sekcja: Pacjent
    pdf.draw_form_box(10, 70, 130, 12, "Osoba badana (Imię i Nazwisko):", f"{pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')}", is_bold=True)
    pdf.draw_form_box(145, 70, 55, 12, "PESEL:", f"{pacjent.get('PESEL', '')}", is_bold=True)
    
    # Sekcja: Stanowisko
    notatki = str(wizyta.get('Notatki', ''))
    stanowisko = notatki.split('\n')[0].replace('Stanowisko: ', '') if 'Stanowisko: ' in notatki else notatki
    pdf.draw_form_box(10, 87, 190, 12, "Stanowisko pracy:", stanowisko)
    
    # Sekcja: Decyzja
    pdf.ln(25)
    pdf.set_font("Roboto", style="B", size=12)
    pdf.cell(0, 10, "ORZEKAM, ŻE BADANY JEST:", align="C", ln=1)
    
    pdf.set_font("Roboto", style="B", size=14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 15, f"{str(orz_data.get('Decyzja', '')).upper()}", border=1, align="C", fill=True, ln=1)
    
    # Stopka
    pdf.ln(10)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 6, f"Data następnego badania: {orz_data.get('DataKolejnegoBadania', '')}", ln=1)
    
    return bytes(pdf.output())

def create_driver_pdf(orz_data, wizyta, pacjent, firma):
    pdf = init_pdf()
    
    pdf.set_font("Roboto", size=9)
    pdf.cell(0, 5, f"Miejscowość: Luboń, Data: {wizyta.get('DataWizyty', '')}", align="R", ln=1)
    
    pdf.ln(10)
    pdf.set_font("Roboto", style="B", size=14)
    pdf.cell(0, 8, "ORZECZENIE LEKARSKIE", align="C", ln=1)
    pdf.set_font("Roboto", size=10)
    pdf.cell(0, 5, "(Dla kierowców / art. 39j ustawy o transporcie drogowym)", align="C", ln=1)
    
    # Ramki
    pdf.draw_form_box(10, 45, 120, 12, "Osoba badana (Imię i Nazwisko):", f"{pacjent.get('Imie', '')} {pacjent.get('Nazwisko', '')}", is_bold=True)
    pdf.draw_form_box(135, 45, 65, 12, "PESEL:", f"{pacjent.get('PESEL', '')}", is_bold=True)
    
    pdf.draw_form_box(10, 62, 190, 15, "Pracodawca:", f"{firma.get('NazwaFirmy', '')}, NIP: {firma.get('NIP', '')}")
    
    pdf.ln(45)
    pdf.set_font("Roboto", size=10)
    pdf.multi_cell(0, 5, "W wyniku badania lekarskiego i oceny narażeń występujących na stanowisku pracy, orzekam, że badany jest:")
    
    pdf.ln(5)
    pdf.set_font("Roboto", style="B", size=14)
    pdf.cell(0, 15, f"{str(orz_data.get('Decyzja', '')).upper()}", border=1, align="C", ln=1)
    
    # Pouczenie prawne
    pdf.ln(15)
    pdf.set_font("Roboto", size=7)
    pouczenie = (
        "POUCZENIE:\n"
        "1. Osoba badana lub pracodawca może w terminie 7 dni od dnia otrzymania orzeczenia lekarskiego wnieść "
        "odwołanie wraz z jego uzasadnieniem za pośrednictwem lekarza, który je wydał, do wojewódzkiego ośrodka medycyny pracy.\n"
        "2. Orzeczenie wydano na podstawie skierowania na badania profilaktyczne."
    )
    pdf.multi_cell(0, 4, pouczenie)
    
    return bytes(pdf.output())

# --- GŁÓWNY KONTROLER (ROUTER) ---
def generate_pdf_router(orz_data, wizyta, pacjent, firma):
    notatki = str(wizyta.get('Notatki', '')).lower()
    
    # Prosta logika rozpoznawania szablonu
    if "kierowca" in notatki or "kat." in notatki:
        return create_driver_pdf(orz_data, wizyta, pacjent, firma), "Kierowca"
    else:
        return create_standard_pdf(orz_data, wizyta, pacjent, firma), "Standardowe"

# --- INTERFEJS UI ---
st.markdown("# 🖨️ Generator Orzeczeń (Silnik Szablonów)")

df_orz = get_data_as_df("Orzeczenia")
df_wiz = get_data_as_df("Wizyty")
df_pac = get_data_as_df("Pacjenci")
df_fir = get_data_as_df("Firmy")

if not df_orz.empty:
    st.subheader("Lista najnowszych dokumentów")
    for _, orz in df_orz.sort_values("ID_Orzeczenia", ascending=False).head(10).iterrows():
        
        # Bezpieczne łączenie danych z bazą
        id_wiz = str(orz.get('ID_Wizyty', ''))
        wiz = df_wiz[df_wiz['ID_Wizyty'].astype(str) == id_wiz].iloc[0] if not df_wiz.empty and id_wiz in df_wiz['ID_Wizyty'].astype(str).values else {}
        
        pesel = str(orz.get('PESEL_Pacjenta', ''))
        pac = df_pac[df_pac['PESEL'].astype(str) == pesel].iloc[0] if not df_pac.empty and pesel in df_pac['PESEL'].astype(str).values else {"Imie": "Brak", "Nazwisko": "Danych", "PESEL": pesel}
        
        nip = str(wiz.get('NIP_Firmy', '0'))
        fir = df_fir[df_fir['NIP'].astype(str) == nip].iloc[0] if not df_fir.empty and nip in df_fir['NIP'].astype(str).values else {"NazwaFirmy": "Prywatnie / Brak Firmy", "Adres": "-", "NIP": nip}

        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1])
            
            try:
                pdf_bytes, typ_szablonu = generate_pdf_router(orz, wiz, pac, fir)
                
                with col_info:
                    st.markdown(f"**{pac.get('Nazwisko', '')} {pac.get('Imie', '')}** (PESEL: {pac.get('PESEL', '')})")
                    st.caption(f"Firma: {fir.get('NazwaFirmy', '')} | Użyty szablon: **{typ_szablonu}**")
                
                with col_btn:
                    st.download_button(
                        label="📄 Pobierz PDF",
                        data=pdf_bytes,
                        file_name=f"Orzeczenie_{typ_szablonu}_{pac.get('Nazwisko', '')}.pdf",
                        mime="application/pdf",
                        key=f"dl_{orz.get('ID_Orzeczenia', '')}",
                        use_container_width=True
                    )
            except Exception as e:
                with col_info:
                    st.error(f"Błąd generowania dokumentu: {e}")
else:
    st.info("Brak wystawionych orzeczeń w bazie.")
