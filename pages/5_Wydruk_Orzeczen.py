import streamlit as st
import pandas as pd  # <--- Brakowało tego importu!
import streamlit.components.v1 as components
from db_service import get_data_as_df

st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="centered")
st.markdown("# 🖨️ Wydruk Orzeczeń z Podpisem Cyfrowym")
st.write("Wygeneruj oficjalny dokument PDF opatrzony kryptograficznym certyfikatem autentyczności.")

# 1. Pobieranie danych z bazy
df_orzeczenia = get_data_as_df("Orzeczenia")
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if df_orzeczenia.empty:
    st.info("Brak wydanych orzeczeń w bazie. Najpierw wystaw orzeczenie w Panelu Lekarza.")
    st.stop()

# 2. Przygotowanie czytelnej listy orzeczeń do wyboru
opcje_wydruku = ["--- Wybierz orzeczenie ---"]
orzeczenia_dict = {}

for idx, orz in df_orzeczenia.iterrows():
    pesel = str(orz['PESEL_Pacjenta'])
    
    # Zabezpieczenie na wypadek brakującego pacjenta
    pacjent_df = df_pacjenci[df_pacjenci['PESEL'].astype(str) == pesel]
    imie = pacjent_df.iloc[0]['Imie'] if not pacjent_df.empty else "Nieznane"
    nazwisko = pacjent_df.iloc[0]['Nazwisko'] if not pacjent_df.empty else "Nieznane"
    
    decyzja_skrot = orz['Decyzja'].split(' ')[0]
    
    etykieta = f"{orz['ID_Orzeczenia']} | {nazwisko} {imie} | {decyzja_skrot}"
    opcje_wydruku.append(etykieta)
    orzeczenia_dict[etykieta] = orz

# 3. Wybór konkretnego dokumentu
wybrane = st.selectbox("Wybierz dokument z archiwum:", opcje_wydruku)

if wybrane != "--- Wybierz orzeczenie ---":
    orz_data = orzeczenia_dict[wybrane]
    
    # Wyciągamy resztę powiązanych danych
    wizyta = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(orz_data['ID_Wizyty'])].iloc[0]
    pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(orz_data['PESEL_Pacjenta'])].iloc[0]
    firma = df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].iloc[0]
    
    # Obsługa starszych orzeczeń, które mogły nie mieć podpisu cyfrowego
    podpis_cyfrowy = orz_data.get('Podpis_Cyfrowy', 'Brak autoryzacji cyfrowej (Stary dokument)')
    if not isinstance(podpis_cyfrowy, str) or pd.isna(podpis_cyfrowy):
        podpis_cyfrowy = "Brak autoryzacji cyfrowej (Stary dokument)"
    
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success("✅ Dokument jest gotowy do wydruku.")
        st.write("Kliknij prawym przyciskiem myszy na dokument i wybierz **Drukuj** (lub naciśnij `Ctrl+P`), a następnie wybierz **'Zapisz jako PDF'**.")
    with col2:
        st.info(f"🔑 **Status:**\nAutoryzowano")
    
    # 4. Generowanie estetycznego dokumentu A4 z wizualną "Pieczęcią Cyfrową"
    data_wystawienia = f"{orz_data['ID_Orzeczenia'].split('/')[1][:4]}-{orz_data['ID_Orzeczenia'].split('/')[1][4:6]}-{orz_data['ID_Orzeczenia'].split('/')[1][6:8]}"
    
    dokument_html = f"""
    <div style="border: 1px solid #ccc; padding: 40px; margin: 10px; background-color: white; color: black; font-family: 'Arial', sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1); position: relative; min-height: 800px;">
        
        <div style="text-align: right; margin-bottom: 20px; font-size: 14px;">
            Miejscowość, data: <strong>Luboń, {data_wystawienia}</strong>
        </div>
        
        <h2 style="text-align: center; margin-bottom: 20px; color: black; font-size: 22px;">
            ORZECZENIE LEKARSKIE<br>
            <span style="font-size: 14px; font-weight: normal; color: #555;">Nr {orz_data['ID_Orzeczenia']}</span>
        </h2>
        
        <p style="font-size: 14px; line-height: 1.6;">Wydane na podstawie skierowania z dnia: <strong>{wizyta['DataWizyty']}</strong></p>
        <p style="font-size: 14px; line-height: 1.6;">Wystawionego przez pracodawcę:<br>
        <strong>{firma['NazwaFirmy']}</strong> (NIP: {firma['NIP']})<br>{firma['Adres']}</p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        
        <p style="font-size: 14px; line-height: 1.6;">W wyniku badania profilaktycznego (<strong>{wizyta['TypBadania']}</strong>) pacjenta:</p>
        <p style="font-size: 16px; margin: 5px 0;">Pana/Pani: <strong>{pacjent['Imie']} {pacjent['Nazwisko']}</strong></p>
        <p style="font-size: 14px; margin: 5px 0;">PESEL: <strong>{pacjent['PESEL']}</strong></p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        
        <h3 style="text-align: center; margin: 20px 0 15px 0; color: black; font-size: 16px;">ORZEKAM, ŻE BADANY JEST:</h3>
        <div style="text-align: center; border: 2px solid black; padding: 15px; font-size: 18px; font-weight: bold; margin-bottom: 20px; background-color: #fcfcfc;">
            {orz_data['Decyzja'].upper()}
        </div>
        
        <p style="font-size: 14px;">Wobec braku przeciwwskazań zdrowotnych.<br>
        Data następnego badania okresowego: <strong>{orz_data['DataKolejnegoBadania']}</strong></p>
        
        <div style="margin-top: 60px; display: flex; justify-content: space-between; align-items: flex-end;">
            
            <div style="width: 45%; text-align: center;">
                <p style="font-size: 12px; margin-bottom: 40px;">Potwierdzam odbiór orzeczenia</p>
                <div style="border-top: 1px dotted black; padding-top: 5px; font-size: 12px;">Podpis pracownika</div>
            </div>
            
            <div style="width: 50%;">
                <div style="border: 2px solid #2980b9; border-radius: 8px; padding: 10px; background-color: #f4f9fd;">
                    <div style="display: flex; align-items: center;">
                        <div style="font-size: 30px; margin-right: 15px;">🛡️</div>
                        <div>
                            <p style="margin: 0; font-size: 11px; color: #2980b9; font-weight: bold; text-transform: uppercase;">Zatwierdzono Elektronicznie</p>
                            <p style="margin: 2px 0; font-size: 13px; font-family: monospace; color: #333;">Certyfikat: <strong>{podpis_cyfrowy}</strong></p>
                            <p style="margin: 0; font-size: 10px; color: #666;">Dokument wygenerowany w systemie MedycynaPracy v1.0. Nie wymaga podpisu odręcznego lekarza ani tradycyjnej pieczątki.</p>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>
    </div>
    """
    
    # Wyświetlamy dokument
    components.html(dokument_html, height=850, scrolling=True)
