import streamlit as st
import pandas as pd
from db_service import get_data_as_df, add_appointment_to_db, add_stanowisko_to_db
from db_service import get_data_as_df, apply_pro_style
import datetime

st.set_page_config(page_title="Nowa Wizyta", page_icon="📅")
st.markdown("# 📅 Rejestracja Wizyty")
st.write("Kompleksowy kreator: przypisz pacjenta, firmę i wybierz stanowisko.")

# 1. Pobranie danych bazowych
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")
df_stanowiska = get_data_as_df("Stanowiska")

if df_pacjenci.empty or df_firmy.empty:
    st.warning("Uzupełnij najpierw bazę pacjentów i firm, aby móc umawiać wizyty.")
    st.stop()

# Tworzymy słowniki z pustą opcją domyślną na start
pacjent_options = {"--- Wybierz pacjenta ---": None}
for idx, row in df_pacjenci.iterrows():
    pacjent_options[f"{row['Nazwisko']} {row['Imie']} (PESEL: {row['PESEL']})"] = row['PESEL']

firma_options = {"--- Wybierz firmę ---": None}
for idx, row in df_firmy.iterrows():
    firma_options[f"{row['NazwaFirmy']} (NIP: {row['NIP']})"] = row['NIP']

# SEKCJA 1: Wybór podstawowy
st.subheader("1. Kto i Gdzie?")
col1, col2 = st.columns(2)
with col1:
    wybrany_pacjent = st.selectbox("Wybierz Pacjenta", options=list(pacjent_options.keys()))
with col2:
    wybrana_firma = st.selectbox("Wybierz Firmę kierującą", options=list(firma_options.keys()))

pesel_to_save = pacjent_options[wybrany_pacjent]
nip_to_save = firma_options[wybrana_firma]

st.divider()

# SEKCJA 2: Dynamiczny wybór stanowiska (pojawia się dopiero po wybraniu firmy!)
wybrane_stanowisko = "--- Wybierz stanowisko ---"
nowe_stanowisko_nazwa = ""
czynniki_domyslne = ""

if nip_to_save:
    st.subheader("2. Stanowisko i Zagrożenia")
    
    # Szukamy stanowisk tylko dla wybranej firmy
    stanowiska_firmy = df_stanowiska[df_stanowiska['NIP_Firmy'].astype(str) == str(nip_to_save)] if not df_stanowiska.empty else pd.DataFrame()
    
    opcje_stanowisk = ["--- Wybierz stanowisko ---"] 
    if not stanowiska_firmy.empty:
        opcje_stanowisk += stanowiska_firmy['NazwaStanowiska'].tolist()
    opcje_stanowisk += ["➕ INNE (Stwórz nowe stanowisko)"]
    
    wybrane_stanowisko = st.selectbox("Stanowisko pracy ze skierowania:", opcje_stanowisk)
    
    # KREATOR NOWEGO STANOWISKA NA ŻYWO
    if wybrane_stanowisko == "➕ INNE (Stwórz nowe stanowisko)":
        st.info("💡 To stanowisko zostanie automatycznie zapisane w słowniku tej firmy na przyszłość.")
        nowe_stanowisko_nazwa = st.text_input("Nazwa nowego stanowiska (np. Kierowca C+E):")
        czynniki_domyslne = st.text_area("Wypisz czynniki szkodliwe i uciążliwe ze skierowania:", height=100)
    
    # POBIERANIE ISTNIEJĄCEGO STANOWISKA
    elif wybrane_stanowisko != "--- Wybierz stanowisko ---":
        wiersz = stanowiska_firmy[stanowiska_firmy['NazwaStanowiska'] == wybrane_stanowisko].iloc[0]
        czynniki_z_bazy = wiersz['CzynnikiSzkodliwe']
        # Pozwalamy recepcji podejrzeć i ewentualnie dopisać coś ekstra na ten konkretny raz
        czynniki_domyslne = st.text_area("Zagrożenia na tym stanowisku (możesz edytować):", value=czynniki_z_bazy, height=100)

st.divider()

# SEKCJA 3: Parametry wizyty
st.subheader("3. Szczegóły skierowania")
col_date, col_type = st.columns(2)
with col_date:
    data_wizyty = st.date_input("Termin wizyty:", value=datetime.date.today())
with col_type:
    typ_badania = st.radio(
        "Typ badań:",
        ("Wstępne", "Okresowe", "Kontrolne", "Sanitarno-Epidemiologiczne"),
        horizontal=True
    )

st.write("") # Trochę oddechu w UI

# PRZYCISK ZAPISU (Działa niezależnie od formularza)
if st.button("Zatwierdź Wizytę i Zapisz", type="primary", use_container_width=True):
    # Logika sprawdzająca, czy recepcjonistka wszystko wypełniła
    if not pesel_to_save or not nip_to_save:
        st.error("Błąd: Wybierz pacjenta oraz firmę z list!")
    elif nip_to_save and wybrane_stanowisko == "--- Wybierz stanowisko ---":
        st.error("Błąd: Wybierz stanowisko pracy ze słownika lub stwórz nowe!")
    elif wybrane_stanowisko == "➕ INNE (Stwórz nowe stanowisko)" and (not nowe_stanowisko_nazwa or not czynniki_domyslne):
        st.error("Błąd: Wpisz nazwę nowego stanowiska i jego czynniki szkodliwe!")
    else:
        with st.spinner("Zapisywanie w systemie..."):
            
            # Krok A: Jeśli tworzymy nowe stanowisko, wrzucamy je najpierw "w tło" do bazy firm
            if wybrane_stanowisko == "➕ INNE (Stwórz nowe stanowisko)":
                add_stanowisko_to_db(nip_to_save, nowe_stanowisko_nazwa, czynniki_domyslne)
                nazwa_stanowiska_do_orzeczenia = nowe_stanowisko_nazwa
            else:
                nazwa_stanowiska_do_orzeczenia = wybrane_stanowisko
                
            # Przygotowujemy sprytną notatkę dla lekarza (Stanowisko + Czynniki)
            kompletne_notatki = f"Stanowisko: {nazwa_stanowiska_do_orzeczenia}\nZagrożenia: {czynniki_domyslne}"
            
            # Krok B: Zapisujemy samą wizytę
            success, message = add_appointment_to_db(
                pesel=pesel_to_save, 
                nip_firmy=nip_to_save, 
                typ_badania=typ_badania, 
                notatki=kompletne_notatki,
                data_wizyty=data_wizyty
            )
        
        if success:
            st.balloons()
            st.success(message)
            if wybrane_stanowisko == "➕ INNE (Stwórz nowe stanowisko)":
                st.info(f"✨ Dodatkowo nowe stanowisko '{nowe_stanowisko_nazwa}' zostało pomyślnie dopisane do słownika tej firmy!")
        else:
            st.error(message)
