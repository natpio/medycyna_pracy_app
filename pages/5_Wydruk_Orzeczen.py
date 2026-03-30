import streamlit as st
import streamlit.components.v1 as components
from db_service import get_data_as_df

st.set_page_config(page_title="Wydruk Orzeczeń", page_icon="🖨️", layout="centered")
st.markdown("# 🖨️ Wydruk Orzeczeń")
st.write("Wybierz wydane orzeczenie z bazy, aby wygenerować oficjalny dokument do druku.")

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
    
    # Krótki podgląd decyzji
    decyzja_skrot = orz['Decyzja'].split(' ')[0]
    
    etykieta = f"Orzeczenie {orz['ID_Orzeczenia']} | {nazwisko} {imie} | {decyzja_skrot}"
    opcje_wydruku.append(etykieta)
    orzeczenia_dict[etykieta] = orz

# 3. Wybór konkretnego dokumentu
wybrane = st.selectbox("Lista historycznych orzeczeń:", opcje_wydruku)

if wybrane != "--- Wybierz orzeczenie ---":
    orz_data = orzeczenia_dict[wybrane]
    
    # Wyciągamy resztę powiązanych danych
    wizyta = df_wizyty[df_wizyty['ID_Wizyty'].astype(str) == str(orz_data['ID_Wizyty'])].iloc[0]
    pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(orz_data['PESEL_Pacjenta'])].iloc[0]
    firma = df_firmy[df_firmy['NIP'].astype(str) == str(wizyta['NIP_Firmy'])].iloc[0]
    
    st.divider()
    
    # Instrukcja dla użytkownika
    st.success("✅ Dokument gotowy. Kliknij na niego prawym przyciskiem myszy i wybierz **'Drukuj'** (lub użyj skrótu Ctrl+P), aby wysłać na drukarkę lub zapisać jako PDF.")
    
    # 4. Generowanie estetycznego dokumentu A4 z użyciem HTML/CSS
    # Wyciągamy rok, miesiąc, dzień z ID orzeczenia dla daty wystawienia
    data_wystawienia = f"{orz_data['ID_Orzeczenia'].split('/')[1][:4]}-{orz_data['ID_Orzeczenia'].split('/')[1][4:6]}-{orz_data['ID_Orzeczenia'].split('/')[1][6:8]}"
    
    dokument_html = f"""
    <div style="border: 1px solid #ccc; padding: 50px; margin: 10px; background-color: white; color: black; font-family: 'Arial', sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <div style="text-align: right; margin-bottom: 30px; font-size: 14px;">
            Miejscowość, data: <strong>Luboń, {data_wystawienia}</strong>
        </div>
        <h2 style="text-align: center; margin-bottom: 30px; color: black; font-size: 22px;">
            ORZECZENIE LEKARSKIE<br>
            <span style="font-size: 14px; font-weight: normal; color: #555;">Nr {orz_data['ID_Orzeczenia']}</span>
        </h2>
        
        <p style="font-size: 14px; line-height: 1.6;">Wydane na podstawie skierowania z dnia: <strong>{wizyta['DataWizyty']}</strong></p>
        <p style="font-size: 14px; line-height: 1.6;">Wystawionego przez pracodawcę:<br>
        <strong>{firma['NazwaFirmy']}</strong> (NIP: {firma['NIP']})<br>{firma['Adres']}</p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;">
        
        <p style="font-size: 14px; line-height: 1.6;">W wyniku badania profilaktycznego (<strong>{wizyta['TypBadania']}</strong>) pacjenta:</p>
        <p style="font-size: 16px; margin: 5px 0;">Pana/Pani: <strong>{pacjent['Imie']} {pacjent['Nazwisko']}</strong></p>
        <p style="font-size: 14px; margin: 5px 0;">PESEL: <strong>{pacjent['PESEL']}</strong></p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;">
        
        <h3 style="text-align: center; margin: 30px 0 15px 0; color: black; font-size: 16px;">ORZEKAM, ŻE BADANY JEST:</h3>
        <div style="text-align: center; border: 2px solid black; padding: 15px; font-size: 18px; font-weight: bold; margin-bottom: 30px; background-color: #fcfcfc;">
            {orz_data['Decyzja'].upper()}
        </div>
        
        <p style="font-size: 14px;">Data następnego badania okresowego: <strong>{orz_data['DataKolejnegoBadania']}</strong></p>
        
        <div style="margin-top: 80px; display: flex; justify-content: space-between; font-size: 12px;">
            <div style="text-align: center; border-top: 1px solid black; width: 40%; padding-top: 5px;">Pieczęć i podpis lekarza orzecznika</div>
            <div style="text-align: center; border-top: 1px solid black; width: 40%; padding-top: 5px;">Podpis pracownika</div>
        </div>
    </div>
    """
    
    # Wyświetlamy dokument wewnątrz aplikacji
    components.html(dokument_html, height=750, scrolling=True)
