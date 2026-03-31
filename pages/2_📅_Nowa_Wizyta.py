import streamlit as st
import pandas as pd
import datetime
# KLUCZOWA LINIA: Importowanie funkcji z pliku db_service.py znajdującego się w folderze głównym
from db_service import get_data_as_df, add_appointment_to_db, add_stanowisko_to_db, apply_pro_style [cite: 1]

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Nowa Wizyta", page_icon="📅", layout="wide") [cite: 1]

# Uruchomienie profesjonalnego stylu CSS
apply_pro_style() [cite: 1]

st.markdown("# 📅 Rejestracja Wizyty") [cite: 1]
st.write("Wybierz pacjenta, firmę oraz wolny termin w 15-minutowym grafiku.") [cite: 1]

# --- 2. POBIERANIE DANYCH ---
# Tutaj występował błąd NameError - teraz funkcja jest zaimportowana powyżej
df_pacjenci = get_data_as_df("Pacjenci") [cite: 1]
df_firmy = get_data_as_df("Firmy") [cite: 1]
df_stanowiska = get_data_as_df("Stanowiska") [cite: 1]
df_wizyty = get_data_as_df("Wizyty") [cite: 1]

if df_pacjenci.empty or df_firmy.empty: [cite: 1]
    st.warning("⚠️ Baza pacjentów lub firm jest pusta. Uzupełnij dane przed rejestracją wizyt.") [cite: 1]
    st.stop() [cite: 1]

# Przygotowanie list do selectboxów
pacjent_options = {f"{row['Nazwisko']} {row['Imie']} (PESEL: {row['PESEL']})": row['PESEL'] for _, row in df_pacjenci.iterrows()} [cite: 1]
firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for _, row in df_firmy.iterrows()} [cite: 1]

# --- 3. SEKCJA WYBORU PACJENTA I FIRMY ---
st.subheader("1. Kto i Gdzie?") [cite: 1]
col1, col2 = st.columns(2) [cite: 1]

with col1: [cite: 1]
    wybrany_label_pacjent = st.selectbox("Wybierz Pacjenta:", options=["--- Wybierz pacjenta ---"] + list(pacjent_options.keys())) [cite: 1]
with col2: [cite: 1]
    wybrany_label_firma = st.selectbox("Wybierz Firmę kierującą:", options=["--- Wybierz firmę ---"] + list(firma_options.keys())) [cite: 1]

st.divider() [cite: 1]

# --- 4. SEKCJA TERMINU I SLOTÓW ---
st.subheader("2. Termin i Godzina") [cite: 1]
c_date, c_time = st.columns(2) [cite: 1]

with c_date: [cite: 1]
    data_wizyty = st.date_input("Data wizyty:", min_value=datetime.date.today(), value=datetime.date.today()) [cite: 1]

# Generator slotów (08:00 - 16:00, co 15 minut)
def get_available_slots(selected_date, df_existing_wizyty): [cite: 1]
    all_slots = [] [cite: 1]
    start = datetime.datetime.combine(selected_date, datetime.time(8, 0)) [cite: 1]
    end = datetime.datetime.combine(selected_date, datetime.time(16, 0)) [cite: 1]
    
    current = start [cite: 1]
    while current < end: [cite: 1]
        all_slots.append(current.strftime("%H:%M")) [cite: 1]
        current += datetime.timedelta(minutes=15) [cite: 1]
    
    # Pobieranie zajętych slotów z bazy dla wybranego dnia
    zajete_godziny = [] [cite: 1]
    if not df_existing_wizyty.empty and 'Godzina' in df_existing_wizyty.columns: [cite: 1]
        mask = df_existing_wizyty['DataWizyty'].astype(str) == str(selected_date) [cite: 1]
        zajete_godziny = df_existing_wizyty[mask]['Godzina'].astype(str).tolist() [cite: 1]
    
    # Filtrowanie wolnych slotów
    return [slot for slot in all_slots if slot not in zajete_godziny] [cite: 1]

wolne_sloty = get_available_slots(data_wizyty, df_wizyty) [cite: 1]

with c_time: [cite: 1]
    if not wolne_sloty: [cite: 1]
        st.error("Brak wolnych terminów w wybranym dniu.") [cite: 1]
        wybrana_godzina = None [cite: 1]
    else: [cite: 1]
        wybrana_godzina = st.selectbox(f"Dostępne godziny ({len(wolne_sloty)} wolnych):", wolne_sloty) [cite: 1]

st.divider() [cite: 1]

# --- 5. SEKCJA STANOWISKA I ZAGROŻEŃ ---
nip_firmy = firma_options.get(wybrany_label_firma) [cite: 1]
pesel_pacjenta = pacjent_options.get(wybrany_label_pacjent) [cite: 1]

if nip_firmy: [cite: 1]
    st.subheader("3. Stanowisko i Zagrożenia") [cite: 1]
    
    # Filtrowanie stanowisk przypisanych do tej firmy
    stanowiska_firmy = df_stanowiska[df_stanowiska['NIP_Firmy'].astype(str) == str(nip_firmy)] if not df_stanowiska.empty else pd.DataFrame() [cite: 1]
    
    opcje_st = ["--- Wybierz stanowisko ---"] [cite: 1]
    if not stanowiska_firmy.empty: [cite: 1]
        opcje_st += stanowiska_firmy['NazwaStanowiska'].tolist() [cite: 1]
    opcje_st += ["➕ DODAJ NOWE STANOWISKO"] [cite: 1]
    
    wybrane_st = st.selectbox("Stanowisko pracy:", opcje_st) [cite: 1]
    
    final_stanowisko = "" [cite: 1]
    final_czynniki = "" [cite: 1]
    
    if wybrane_st == "➕ DODAJ NOWE STANOWISKO": [cite: 1]
        final_stanowisko = st.text_input("Nazwa nowego stanowiska:") [cite: 1]
        final_czynniki = st.text_area("Wpisz czynniki szkodliwe (oddzielone przecinkami):") [cite: 1]
        st.info("💡 To stanowisko zostanie zapisane w słowniku firmy po zatwierdzeniu wizyty.") [cite: 1]
    elif wybrane_st != "--- Wybierz stanowisko ---": [cite: 1]
        row_st = stanowiska_firmy[stanowiska_firmy['NazwaStanowiska'] == wybrane_st].iloc[0] [cite: 1]
        final_stanowisko = wybrane_st [cite: 1]
        final_czynniki = st.text_area("Czynniki szkodliwe (możesz edytować):", value=row_st['CzynnikiSzkodliwe']) [cite: 1]

    st.divider() [cite: 1]
    
    # --- 6. TYP BADANIA I ZAPIS ---
    st.subheader("4. Rodzaj badania") [cite: 1]
    typ_badania = st.radio( [cite: 1]
        "Wybierz typ badania profilaktycznego:", [cite: 1]
        ("Wstępne", "Okresowe", "Kontrolne", "Sanitarno-Epidemiologiczne"), [cite: 1]
        horizontal=True [cite: 1]
    ) [cite: 1]

    if st.button("ZAREJESTRUJ WIZYTĘ", type="primary", use_container_width=True): [cite: 1]
        if not pesel_pacjenta: [cite: 1]
            st.error("Proszę wybrać pacjenta.") [cite: 1]
        elif not wybrana_godzina: [cite: 1]
            st.error("Proszę wybrać godzinę wizyty.") [cite: 1]
        elif wybrane_st == "--- Wybierz stanowisko ---" or (wybrane_st == "➕ DODAJ NOWE STANOWISKO" and not final_stanowisko): [cite: 1]
            st.error("Proszę określić stanowisko pracy.") [cite: 1]
        else: [cite: 1]
            with st.spinner("Zapisywanie wizyty w systemie..."): [cite: 1]
                # Jeśli wybrano nowe stanowisko, zapisz je w bazie firm
                if wybrane_st == "➕ DODAJ NOWE STANOWISKO": [cite: 1]
                    add_stanowisko_to_db(nip_firmy, final_stanowisko, final_czynniki) [cite: 1]
                
                notatki_lekarz = f"Stanowisko: {final_stanowisko}\nZagrożenia: {final_czynniki}" [cite: 1]
                
                # Dodanie wizyty z uwzględnieniem slotu czasowego
                sukces, msg = add_appointment_to_db( [cite: 1]
                    pesel=pesel_pacjenta, [cite: 1]
                    nip_firmy=nip_firmy, [cite: 1]
                    typ_badania=typ_badania, [cite: 1]
                    notatki=notatki_lekarz, [cite: 1]
                    data_wizyty=data_wizyty, [cite: 1]
                    godzina=wybrana_godzina [cite: 1]
                ) [cite: 1]
                
                if sukces: [cite: 1]
                    st.balloons() [cite: 1]
                    st.success(f"✅ Sukces! {msg}") [cite: 1]
                    st.info(f"Termin {data_wizyty} o godz. {wybrana_godzina} został zarezerwowany.") [cite: 1]
                else: [cite: 1]
                    st.error(msg) [cite: 1]
