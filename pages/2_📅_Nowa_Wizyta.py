import streamlit as st
import pandas as pd
import datetime
# Import funkcji z serwisu bazy danych (db_service.py)
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

col_p1, col_p2 = st.columns(2)

if not tryb_nowy_pacjent:
    with col_p1:
        if not df_pacjenci.empty:
            # Tworzenie listy wyszukiwania: Nazwisko Imię (PESEL)
            pacjent_options = {f"{row['Nazwisko']} {row['Imie']} ({row['PESEL']})": row['PESEL'] for _, row in df_pacjenci.iterrows()}
            wybrany_label = st.selectbox("Wyszukaj pacjenta w bazie:", options=["--- Zacznij wpisywać nazwisko ---"] + list(pacjent_options.keys()))
            pesel_final = pacjent_options.get(wybrany_label)
        else:
            st.warning("Baza pacjentów jest pusta. Przełącz na 'Nowy Pacjent'.")
            pesel_final = None
else:
    with col_p1:
        n_imie = st.text_input("Imię")
        n_nazwisko = st.text_input("Nazwisko")
    with col_p2:
        n_pesel = st.text_input("PESEL", max_chars=11, help="Wymagane 11 cyfr")
        n_tel = st.text_input("Telefon kontaktowy")
    pesel_final = n_pesel

st.divider()

# --- 4. WYBÓR TERMINU I PRZYNALEŻNOŚCI ---
st.subheader("🗓️ Termin i Firma")
c_date, c_time, c_firma = st.columns([1, 1, 2])

with c_date:
    data_wizyty = st.date_input("Data wizyty:", min_value=datetime.date.today(), value=datetime.date.today())

with c_time:
    # Generator slotów (08:00 - 16:00, co 15 minut)
    all_slots = [f"{h:02d}:{m:02d}" for h in range(8, 16) for m in (0, 15, 30, 45)]
    
    # Filtrowanie już zajętych godzin w wybranym dniu
    zajete_godziny = []
    if not df_wizyty.empty and 'Godzina' in df_wizyty.columns:
        mask = (df_wizyty['DataWizyty'].astype(str) == str(data_wizyty)) & (df_wizyty['Status'] != 'Anulowana')
        zajete_godziny = df_wizyty[mask]['Godzina'].astype(str).tolist()
    
    wolne_sloty = [s for s in all_slots if s not in zajete_godziny]
    godzina_final = st.selectbox(f"Dostępne sloty ({len(wolne_sloty)}):", options=wolne_sloty if wolne_sloty else ["Brak wolnych miejsc"])

with c_firma:
    # Opcja prywatna jest domyślna, aby nie blokować procesu
    firma_options = {"🏢 BRAK / WIZYTA PRYWATNA": "0"}
    if not df_firmy.empty:
        for _, row in df_firmy.iterrows():
            firma_options[f"{row['NazwaFirmy']} (NIP: {row['NIP']})"] = row['NIP']
    
    wybrana_firma_label = st.selectbox("Firma kierująca (opcjonalnie):", options=list(firma_options.keys()))
    nip_final = firma_options.get(wybrana_firma_label)

st.divider()

# --- 5. SZCZEGÓŁY BADANIA I STANOWISKO ---
st.subheader("🛠️ Szczegóły skierowania")
col_s1, col_s2 = st.columns(2)

with col_s1:
    typ_badania = st.radio("Rodzaj badania:", ["Wstępne", "Okresowe", "Kontrolne", "Sanitarno-Epidemiologiczne"], horizontal=True)
    
    # Jeśli wybrano firmę, pobierz jej słownik stanowisk
    if nip_final != "0":
        stanowiska_firmy = df_stanowiska[df_stanowiska['NIP_Firmy'].astype(str) == str(nip_final)] if not df_stanowiska.empty else pd.DataFrame()
        opcje_st = ["--- Wybierz ze słownika firmy ---"] + (stanowiska_firmy['NazwaStanowiska'].tolist() if not stanowiska_firmy.empty else []) + ["➕ NOWE STANOWISKO"]
        wybrane_st = st.selectbox("Stanowisko pracy:", options=opcje_st)
    else:
        # Dla wizyt prywatnych od razu pozwalamy na wpisanie ręczne
        wybrane_st = "➕ NOWE STANOWISKO"
        st.caption("Wizyta prywatna: podaj stanowisko/cel badania ręcznie.")

with col_s2:
    if wybrane_st == "➕ NOWE STANOWISKO":
        final_st_nazwa = st.text_input("Nazwa stanowiska:", placeholder="np. Kierowca, Magazynier, Cele Sanitarno-Epid.")
        final_czynniki = st.text_area("Czynniki szkodliwe / Zagrożenia (opcjonalnie):")
    elif wybrane_st != "--- Wybierz ze słownika firmy ---":
        # Pobranie zagrożeń ze słownika
        row_st = stanowiska_firmy[stanowiska_firmy['NazwaStanowiska'] == wybrane_st].iloc[0]
        final_st_nazwa = wybrane_st
        final_czynniki = row_st['CzynnikiSzkodliwe']
        st.info(f"**Zagrożenia przypisane do stanowiska:**\n\n{final_czynniki}")
    else:
        final_st_nazwa = ""
        final_czynniki = ""

st.write("")

# --- 6. LOGIKA FINALIZACJI (ALL-IN-ONE) ---
if st.button("🚀 ZAREJESTRUJ WIZYTĘ I ZABLOKUJ TERMIN", type="primary", use_container_width=True):
    # Walidacja danych
    if not pesel_final or len(str(pesel_final)) != 11:
        st.error("Błąd: Podaj poprawny numer PESEL (11 cyfr).")
    elif godzina_final == "Brak wolnych miejsc":
        st.error("Błąd: Nie można zarezerwować terminu w tym dniu.")
    elif (wybrane_st == "--- Wybierz ze słownika firmy ---") or (wybrane_st == "➕ NOWE STANOWISKO" and not final_st_nazwa):
        st.error("Błąd: Podaj nazwę stanowiska pracy.")
    else:
        with st.spinner("Procesowanie rejestracji..."):
            # KROK 1: Jeśli pacjent jest nowy, stwórz mu kartę
            if tryb_nowy_pacjent:
                # Ustawiamy domyślną datę (do poprawy później przez lekarza), aby nie tracić czasu przez telefon
                sukces_p, msg_p = add_patient_to_db(n_pesel, n_imie, n_nazwisko, "1900-01-01", n_tel)
                if not sukces_p:
                    st.error(f"Nie udało się dodać pacjenta: {msg_p}")
                    st.stop()

            # KROK 2: Jeśli wybrano firmę i nowe stanowisko, zapisz je w jej katalogu
            if nip_final != "0" and wybrane_st == "➕ NOWE STANOWISKO":
                add_stanowisko_to_db(nip_final, final_st_nazwa, final_czynniki)

            # KROK 3: Zapisz wizytę w kalendarzu
            notatki_wizyty = f"Stanowisko: {final_st_nazwa}\nZagrożenia: {final_czynniki}"
            sukces_w, msg_w = add_appointment_to_db(
                pesel=pesel_final,
                nip_firmy=nip_final,
                typ_badania=typ_badania,
                notatki=notatki_wizyty,
                data_wizyty=data_wizyty,
                godzina=godzina_final
            )

            if sukces_w:
                st.balloons()
                st.success(f"Zakończono pomyślnie! {msg_w}")
                st.info(f"Slot {godzina_final} w dniu {data_wizyty} jest teraz zajęty.")
                # Odświeżenie danych, aby slot zniknął z listy
                st.cache_data.clear()
