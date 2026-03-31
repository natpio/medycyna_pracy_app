import streamlit as st
import pandas as pd
import os
import urllib.request
import io
import qrcode
from fpdf import FPDF
from db_service import get_data_as_df

st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="centered")
st.markdown("# 🖨️ Generator Certyfikatów PDF")
st.write("Wygeneruj nienaruszalny dokument PDF z kodem QR i faksymile podpisu.")

# --- POBIERANIE POLSKICH CZCIONEK ---
# FPDF wymaga czcionek TTF do obsługi polskich znaków (ą, ę, ł itp.)
@st.cache_resource
def load_fonts():
    font_reg = "Roboto-Regular.ttf"
    font_bold = "Roboto-Bold.ttf"
    
    # Automatyczne pobieranie czcionek z serwerów Google, jeśli ich nie ma w folderze
    if not os.path.exists(font_reg):
        urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf", font_reg)
    if not os.path.exists(font_bold):
        urllib.request.urlretrieve("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf", font_bold)
    
    return font_reg, font_bold

font_regular, font_bold = load_fonts()

# 1. Pobieranie danych z bazy
df_orzeczenia = get_data_as_df("Orzeczenia")
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if df_orzeczenia.empty:
    st.info("Brak wydanych orzeczeń w bazie.")
    st.stop()

# 2. Wybór orzeczenia
opcje_wydruku = ["--- Wybierz orzeczenie ---"]
orzeczenia_dict = {}

for idx, orz in df_orzeczenia.iterrows():
    pesel = str(orz['PESEL_Pacjenta'])
    pacjent_df = df_pacjenci[df_pacjenci['PESEL'].astype(str) == pesel]
    imie = pacjent_df.iloc[0]['Imie'] if not pacjent_df.empty else "Nieznane"
    nazwisko = pacjent_df.iloc[0]['Nazwisko'] if not pacjent_df.empty else "Nieznane"
    
    decyzja_skrot = orz['Decyzja'].split(' ')[0]
    etykieta = f"{orz['ID_Orzeczenia']} | {nazwisko} {imie} | {decyzja_skrot}"
    opcje_wydruku.append(etykieta)
    orzeczenia_dict[etykieta] = orz

wybrane = st.selectbox("Wybierz dokument z archiwum:", opcje_wydruku)

if wybrane != "--- Wybierz orzeczenie ---":
    orz_data = orzeczenia_dict[wybrane]
    wizyta = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(orz_data['ID_Wizyty'])].iloc[0]
    pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(orz_data['PESEL_Pacjenta'])].iloc[0]
    firma = df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].iloc[0]
    
    podpis_cyfrowy = str(orz_data.get('Podpis_Cyfrowy', 'Brak autoryzacji'))
    data_wystawienia = f"{orz_data['ID_Orzeczenia'].split('/')[1][:4]}-{orz_data['ID_Orzeczenia'].split('/')[1][4:6]}-{orz_data['ID_Orzeczenia'].split('/')[1][6:8]}"
    
    st.divider()
    
    # --- GENEROWANIE PDF ---
    with st.spinner("Kompilowanie zabezpieczonego dokumentu PDF..."):
        pdf = FPDF()
        pdf.add_page()
        
        # Wczytanie czcionek
        pdf.add_font("Roboto", style="", fname=font_regular)
        pdf.add_font("Roboto", style="B", fname=font_bold)
        
        # Datownik (Prawy górny róg)
        pdf.set_font("Roboto", size=10)
        pdf.cell(0, 10, f"Luboń, dnia: {data_wystawienia} r.", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Tytuł
        pdf.set_font("Roboto", style="B", size=18)
        pdf.cell(0, 10, "ORZECZENIE LEKARSKIE", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=10)
        pdf.cell(0, 5, f"Nr {orz_data['ID_Orzeczenia']}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)
        
        # Informacje o skierowaniu
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, f"Wydane na podstawie skierowania z dnia: {wizyta['DataWizyty']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, "Wystawionego przez pracodawcę:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="B", size=11)
        pdf.cell(0, 6, f"{firma['NazwaFirmy']} (NIP: {firma['NIP']})", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, f"{firma['Adres']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Informacje o pacjencie
        pdf.cell(0, 6, f"W wyniku badania profilaktycznego ({wizyta['TypBadania']}) pacjenta:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", style="B", size=12)
        pdf.cell(0, 8, f"Pana/Pani: {pacjent['Imie']} {pacjent['Nazwisko']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, f"PESEL: {pacjent['PESEL']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)
        
        # Orzeczenie
        pdf.set_font("Roboto", style="B", size=14)
        pdf.cell(0, 10, "ORZEKAM, ŻE BADANY JEST:", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        # Ramka z decyzją
        pdf.set_font("Roboto", style="B", size=16)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 15, f"{orz_data['Decyzja'].upper()}", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)
        pdf.set_font("Roboto", size=11)
        pdf.cell(0, 6, "Wobec braku przeciwwskazań zdrowotnych.", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Data następnego badania okresowego: {orz_data['DataKolejnegoBadania']}", new_x="LMARGIN", new_y="NEXT")
        
        # --- GENEROWANIE KODU QR W LOCIE ---
        qr = qrcode.make(f"Dokument wydany przez MedycynaPracy Lubon. Certyfikat: {podpis_cyfrowy}")
        qr_img_bytes = io.BytesIO()
        qr.save(qr_img_bytes, format='PNG')
        
        # Wstawienie kodu QR
        y_bottom = 220
        pdf.image(qr_img_bytes, x=15, y=y_bottom, w=35)
        pdf.set_xy(55, y_bottom + 5)
        pdf.set_font("Roboto", size=8)
        pdf.multi_cell(60, 4, f"Zatwierdzono Elektronicznie\nKod autoryzacji:\n{podpis_cyfrowy}\nSkrypt: MedycynaPracy v1.0", align="L")
        
        # --- WSTAWIANIE FAKSYMILE (PIECZĄTKI) ---
        if os.path.exists("pieczatka.png"):
            pdf.image("pieczatka.png", x=140, y=y_bottom, w=50)
        else:
            # Jeśli nie ma wgranego zdjęcia pieczątki, robimy ramkę
            pdf.set_xy(140, y_bottom + 10)
            pdf.set_font("Roboto", size=10)
            pdf.cell(50, 20, "Pieczęć i podpis lekarza", border=1, align="C")

        # Zapisz PDF do bufora pamięci (nie na dysk!)
        pdf_out = pdf.output()
        pdf_bytes = bytes(pdf_out)
    
    # 5. Przycisk pobierania na froncie
    st.success("✅ Orzeczenie gotowe do wydania.")
    st.download_button(
        label="📥 POBIERZ ORZECZENIE (PDF)",
        data=pdf_bytes,
        file_name=f"Orzeczenie_{pacjent['Nazwisko']}_{orz_data['ID_Orzeczenia'].replace('/','_')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
    
    st.info("💡 Wskazówka: Zeskanuj kod QR z wygenerowanego pliku PDF za pomocą aparatu w telefonie!")
