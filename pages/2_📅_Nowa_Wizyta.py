import streamlit as st
import pandas as pd
import datetime
# Import funkcji z serwisu bazy danych
from db_service import (
    get_data_as_df, 
    add_appointment_to_db, 
    add_patient_to_db, 
    add_stanowisko_to_db, 
    apply_pro_style
)

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Szybka Rejestracja", page_icon="📞", layout="wide")

# Zaaplikowanie profesjonalnego stylu CSS
apply_pro_style()

st.markdown("# 📞 Szybka Rejestracja i Wizyta")
st.write("Idealne rozwiązanie podczas rozmowy telefonicznej: zarejestruj pacjenta i umów termin w jednym formularzu.")

# --- 2. POBIERANIE DANYCH ---
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")
df_wizyty = get_data_as_df("Wizyty")
df_stanowiska = get_data_as_df("Stanowiska")

# --- 3. IDENTYFIKACJA PACJENTA ---
st.info("💡 Sprawdź, czy pacjent jest już w bazie. Jeśli nie, użyj przełącznika 'Nowy Pacjent'.")

# Przełącznik trybu rejestracji
tryb_nowy_pacjent = st.toggle("✨ **NOWY PACJENT** (dodaj do bazy przed umówieniem wizyty)", value=False)

col_p1, col_p2 = st.columns(2)

if not tryb_nowy_pacjent:
    with col_p1:
        if not df_pacjenci.empty:
            pacjent_options = {f"{row['Nazwisko']} {row['Imie']} ({row['PESEL']})": row['PESEL'] for _, row in df_pacjenci.iterrows()}
            wybrany_label = st.selectbox("Wyszukaj pacjenta:", options=["--- Wybierz z listy ---"] + list(pacjent_options.keys()))
            pesel_final = pacjent_options.get(wybrany_label)
        else:
            st.warning("Baza pacjentów jest pusta. Użyj opcji 'Nowy Pacjent'.")
            pesel_final = None
else:
    with col_p1:
        st.markdown("#### 📝 Dane osobowe")
        n_imie = st.text_input("Imię", placeholder="np. Jan")
        n_nazwisko = st.text_input("Nazwisko", placeholder="np. Kowalski")
    with col_p2:
        st.markdown("#### &nbsp;")
        n_pesel = st.text_input("PESEL", max_chars=11, help="Wymagane 11 cyfr")
        n_tel = st.text_input("Telefon", placeholder="np. 500 600 700")
    pesel_final = n_pesel

st.divider()

# --- 4. WYBÓR TERMINU (SLOTY 15-MINUTOWE) ---
st.subheader("🗓️ Termin i Godzina")
c_date, c_time, c_firma = st.columns([1, 1, 2])

with c_date:
    data_wizyty = st.date_input("Data wizyty:", min_value=datetime.date.today(), value=datetime.date.today())

with c_time:
    # Generator slotów (08:00 - 16:00, co 15 minut)
    all_slots = [f"{h:02d}:{m:02d}" for h in range(8, 16) for m in (0, 15, 30, 45)]
    
    # Filtrowanie zajętych slotów
    zajete = []
    if not df_wizyty.empty and 'Godzina' in df_wizyty.columns:
        mask = (df_wizyty['DataWizyty'].astype(str) == str(data_wizyty)) & (df_wizyty['Status'] != 'Anulowana')
        zajete = df_wizyty[mask]['Godzina'].astype(str).tolist()
    
    wolne = [s for s in all_slots if s not in zajete]
    godzina_final = st.selectbox(f"Dostępne sloty ({len(wolne)}):", options=wolne if wolne else ["Brak wolnych miejsc"])

with c_firma:
    if not df_firmy.empty:
        firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for _, row in df_firmy.iterrows()}
        wybrana_firma_label = st.selectbox("Firma kierująca:", options=["--- Wybierz firmę ---"] + list(firma_options.keys()))
        nip_final = firma_options.get(wybrana_firma_label)
    else:
        st.error("Błąd: Nie znaleziono żadnych firm w bazie danych.")
        nip_final = None

# --- 5. STANOWISKO I FINALIZACJA ---
if nip_final:
    st.divider()
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.subheader("🛠️ Szczegóły skierowania")
        # Pobieranie stanowisk dla konkretnej firmy
        stanowiska_firmy = df_stanowiska[df_stanowiska['NIP_Firmy'].astype(str) == str(nip_final)] if not df_stanowiska.empty else pd.DataFrame()
        
        opcje_st = ["--- Wybierz stanowisko ---"]
        if not stanowiska_firmy.empty:
            opcje_st += stanowiska_firmy['NazwaStanowiska'].tolist()
        opcje_st += ["➕ DODAJ NOWE STANOWISKO"]
        
        wybrane_st = st.selectbox("Stanowisko pracy:", options=opcje_st)
        typ_badania = st.radio("Rodzaj badania:", ["Wstępne", "Okresowe", "Kontrolne", "Sanitarno-Epidemiologiczne"], horizontal=True)

    with col_s2:
        st.markdown("#### &nbsp;")
        if wybrane_st == "➕ DODAJ NOWE STANOWISKO":
            nowe_st_nazwa = st.text_input("Nazwa stanowiska (np. Spawacz):")
            nowe_st_czynniki = st.text_area("Czynniki szkodliwe i uciążliwe:")
        elif wybrane_st != "--- Wybierz stanowisko ---":
            czynniki_info = stanowiska_firmy[stanowiska_firmy['NazwaStanowiska'] == wybrane_st].iloc[0]['CzynnikiSzkodliwe']
            st.info(f"**Zagrożenia przypisane do stanowiska:**\n\n{czynniki_info}")

    st.write("")
    
    # --- 6. LOGIKA ZAPISU (ALL-IN-ONE) ---
    if st.button("🚀 POTWIERDŹ REJESTRACJĘ I TERMIN", type="primary", use_container_width=True):
        # Walidacja
        if not pesel_final or len(str(pesel_final)) != 11:
            st.error("Błąd: Podaj poprawny numer PESEL (11 cyfr).")
        elif not nip_final:
            st.error("Błąd: Wybierz firmę kierującą.")
        elif wybrane_st == "--- Wybierz stanowisko ---":
            st.error("Błąd: Wybierz lub zdefiniuj stanowisko pracy.")
        elif godzina_final == "Brak wolnych miejsc":
            st.error("Błąd: Nie można zarezerwować terminu w tym dniu.")
        else:
            with st.spinner("Przetwarzanie zgłoszenia..."):
                # KROK 1: Jeśli nowy pacjent, dodaj go do bazy [cite: 1]
                if tryb_nowy_pacjent:
                    # Domyślna data urodzenia "1900-01-01" do późniejszej edycji w EDM
                    sukces_p, msg_p = add_patient_to_db(n_pesel, n_imie, n_nazwisko, "1900-01-01", n_tel)
                    if not sukces_p:
                        st.error(f"Błąd rejestracji pacjenta: {msg_p}")
                        st.stop()

                # KROK 2: Jeśli nowe stanowisko, zapisz w słowniku firmy [cite: 1]
                final_stanowisko_nazwa = wybrane_st
                final_czynniki = ""
                
                if wybrane_st == "➕ DODAJ NOWE STANOWISKO":
                    add_stanowisko_to_db(nip_final, nowe_st_nazwa, nowe_st_czynniki)
                    final_stanowisko_nazwa = nowe_st_nazwa
                    final_czynniki = nowe_st_czynniki
                else:
                    final_czynniki = stanowiska_firmy[stanowiska_firmy['NazwaStanowiska'] == wybrane_st].iloc[0]['CzynnikiSzkodliwe']

                # KROK 3: Zapisz wizytę z uwzględnieniem slotu czasowego [cite: 1]
                notatki_dla_lekarza = f"Stanowisko: {final_stanowisko_nazwa}\nZagrożenia: {final_czynniki}"
                sukces_w, msg_w = add_appointment_to_db(
                    pesel=pesel_final,
                    nip_firmy=nip_final,
                    typ_badania=typ_badania,
                    notatki=notatki_dla_lekarza,
                    data_wizyty=data_wizyty,
                    godzina=godzina_final
                )

                if sukces_w:
                    st.balloons()
                    st.success(f"Sukces! {msg_w}")
                    st.info(f"Pacjent umówiony na godz. {godzina_final}. Slot został zablokowany w kalendarzu.")
                    # Wyczyszczenie cache, aby nowa wizyta była widoczna na dashboardzie
                    st.cache_data.clear()
