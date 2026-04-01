import streamlit as st
import pandas as pd
import datetime
# Import funkcji z serwisu bazy danych (db_service.py)
from db_service import (
    get_data_as_df, 
    add_appointment_to_db, 
    add_patient_to_db, 
    add_stanowisko_to_db, 
    apply_pro_style,
    dekoduj_pesel
)

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybka Rejestracja", page_icon="📞", layout="wide")

# Zaaplikowanie profesjonalnego stylu CSS
apply_pro_style()

st.markdown("# 📞 Szybka Rejestracja i Wizyta")
st.write("Centrum obsługi pacjenta: zarejestruj nową osobę lub umów stałego pacjenta w kilka sekund.")

# --- 2. POBIERANIE DANYCH ---
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")
df_wizyty = get_data_as_df("Wizyty")
df_stanowiska = get_data_as_df("Stanowiska")

# --- 3. IDENTYFIKACJA PACJENTA ---
st.info("💡 Rozmawiasz z nowym pacjentem? Użyj przełącznika, aby dodać go do bazy.")

# Przełącznik trybu rejestracji
tryb_nowy_pacjent = st.toggle("✨ **NOWY PACJENT** (brak w systemie)", value=False)

if tryb_nowy_pacjent:
    st.subheader("🆕 Dane podstawowe nowego pacjenta")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        n_imie = st.text_input("Imię")
        n_pesel = st.text_input("PESEL", max_chars=11)
    with c2:
        n_nazwisko = st.text_input("Nazwisko")
        n_tel = st.text_input("Telefon")
        
    # --- LOGIKA AUTOUZUPEŁNIANIA Z PESEL ---
    calc_date = datetime.date(1990, 1, 1)
    calc_plec = "Mężczyzna"
    
    with c3:
        st.write("Automatyzacja")
        if st.button("🪄 Uzupełnij z PESEL", use_container_width=True):
            d, p = dekoduj_pesel(n_pesel)
            if d: 
                calc_date, calc_plec = d, p
                st.toast(f"Pobrano dane: {p}, ur. {d}")
            else: 
                st.error("Błędny lub niepełny numer PESEL.")
                
    st.divider()
    st.subheader("Dane szczegółowe i kontaktowe")
    
    # Dodatkowe pola, w tym Płeć i Data Urodzenia z wartościami domyślnymi (lub wyliczonymi)
    c4, c5 = st.columns(2)
    with c4:
        n_data_ur = st.date_input("Data urodzenia", value=calc_date)
        n_plec = st.radio("Płeć pacjenta:", options=["Mężczyzna", "Kobieta"], 
                          index=0 if calc_plec == "Mężczyzna" else 1, horizontal=True)
    with c5:
        n_adres = st.text_input("Adres zamieszkania", placeholder="ul. Medyczna 1, Miasto")
        n_email = st.text_input("Adres E-mail", placeholder="jan@kowalski.pl")
    
    pesel_final = n_pesel
else:
    st.subheader("🔍 Wybierz pacjenta z bazy")
    if not df_pacjenci.empty:
        # Tworzymy listę do wyszukiwania
        lista_p = {f"{row['Nazwisko']} {row['Imie']} ({row['PESEL']})": row['PESEL'] for _, row in df_pacjenci.iterrows()}
        wybrany_p = st.selectbox("Wyszukaj pacjenta:", options=list(lista_p.keys()))
        pesel_final = lista_p[wybrany_p]
    else:
        st.warning("Baza pacjentów jest pusta. Użyj trybu 'NOWY PACJENT'.")
        st.stop()

st.divider()

# --- 4. SZCZEGÓŁY WIZYTY ---
st.subheader("🏢 Firma i Stanowisko")
col_f1, col_f2 = st.columns(2)

with col_f1:
    if not df_firmy.empty:
        firmy_dict = {row['NazwaFirmy']: row['NIP'] for _, row in df_firmy.iterrows()}
        wybrana_f = st.selectbox("Firma kierująca:", options=["PRYWATNIE / BRAK"] + list(firmy_dict.keys()))
        nip_final = firmy_dict[wybrana_f] if wybrana_f != "PRYWATNIE / BRAK" else "0"
    else:
        st.error("Błąd: Nie znaleziono żadnych firm w bazie.")
        nip_final = "0"

with col_f2:
    if nip_final != "0":
        st_firmy = df_stanowiska[df_stanowiska['NIP_Firmy'].astype(str) == str(nip_final)]
        opcje_st = ["➕ NOWE STANOWISKO"] + list(st_firmy['NazwaStanowiska'].unique())
        wybrane_st = st.selectbox("Stanowisko pracy:", options=opcje_st)
    else:
        wybrane_st = "➕ NOWE STANOWISKO"

# Obsługa nowego stanowiska
if wybrane_st == "➕ NOWE STANOWISKO":
    c_s1, c_s2 = st.columns(2)
    final_st_nazwa = c_s1.text_input("Nazwa nowego stanowiska:", placeholder="np. Kierowca kat. C")
    final_czynniki = c_s2.text_area("Czynniki szkodliwe / Notatki:", placeholder="np. hałas, praca na wysokości...")
else:
    final_st_nazwa = wybrane_st
    row_st = st_firmy[st_firmy['NazwaStanowiska'] == wybrane_st].iloc[0]
    final_czynniki = row_st['CzynnikiSzkodliwe']
    st.caption(f"**Automatyczne czynniki:** {final_czynniki}")

st.divider()

# --- 5. TERMIN I FINALIZACJA ---
st.subheader("📅 Termin wizyty")
c_t1, c_t2, c_t3 = st.columns(3)

data_wizyty = c_t1.date_input("Data wizyty:", min_value=datetime.date.today())
typ_badania = c_t2.selectbox("Rodzaj badania:", ["Wstępne", "Okresowe", "Kontrolne", "Sanitarne", "Kierowca", "Inne"])

# Lista godzin
godziny = [f"{h:02d}:00" for h in range(8, 16)] + [f"{h:02d}:30" for h in range(8, 16)]
godziny.sort()
wybrana_godzina = c_t3.selectbox("Godzina:", godziny)

if st.button("🚀 ZAREJESTRUJ WIZYTĘ", type="primary", use_container_width=True):
    # Walidacja danych dla nowego pacjenta
    if tryb_nowy_pacjent and (not n_pesel or not n_imie or not n_nazwisko):
        st.error("Uzupełnij imię, nazwisko i PESEL nowego pacjenta!")
    elif not final_st_nazwa:
        st.error("Proszę podać nazwę stanowiska pracy!")
    else:
        with st.spinner("Zapisywanie w bazie danych..."):
            # KROK 1: Zapis pacjenta (8 parametrów: z płcią na końcu)
            if tryb_nowy_pacjent:
                sukces_p, msg_p = add_patient_to_db(n_pesel, n_imie, n_nazwisko, str(n_data_ur), n_tel, n_adres, n_email, n_plec)
                if not sukces_p:
                    st.error(f"Błąd rejestracji pacjenta: {msg_p}")
                    st.stop()

            # KROK 2: Jeśli wybrano firmę i nowe stanowisko
            if nip_final != "0" and wybrane_st == "➕ NOWE STANOWISKO":
                add_stanowisko_to_db(nip_final, final_st_nazwa, final_czynniki)

            # KROK 3: Zapisz wizytę
            notatki_wizyty = f"Stanowisko: {final_st_nazwa}\\nZagrożenia: {final_czynniki}"
            sukces_w, msg_w = add_appointment_to_db(
                pesel=pesel_final,
                nip_firmy=nip_final,
                typ_badania=typ_badania,
                notatki=notatki_wizyty,
                data_wizyty=data_wizyty,
                godzina=wybrana_godzina
            )

            if sukces_w:
                st.success(f"✅ Wizyta zarejestrowana poprawnie!")
                st.balloons()
            else:
                st.error(f"Błąd zapisu wizyty: {msg_w}")
