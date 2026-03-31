import streamlit as st
import pandas as pd
import datetime
from db_service import get_data_as_df, add_appointment_to_db, add_stanowisko_to_db, apply_pro_style

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Nowa Wizyta", page_icon="📅", layout="wide")

# Uruchomienie profesjonalnego stylu CSS
apply_pro_style()

st.markdown("# 📅 Rejestracja Wizyty")
st.write("Wybierz pacjenta, firmę oraz wolny termin w 15-minutowym grafiku.")

# --- 2. POBIERANIE DANYCH ---
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")
df_stanowiska = get_data_as_df("Stanowiska")
df_wizyty = get_data_as_df("Wizyty")

if df_pacjenci.empty or df_firmy.empty:
    st.warning("⚠️ Baza pacjentów lub firm jest pusta. Uzupełnij dane przed rejestracją wizyt.")
    st.stop()

# Przygotowanie list do selectboxów
pacjent_options = {f"{row['Nazwisko']} {row['Imie']} (PESEL: {row['PESEL']})": row['PESEL'] for _, row in df_pacjenci.iterrows()}
firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for _, row in df_firmy.iterrows()}

# --- 3. SEKCJA WYBORU PACJENTA I FIRMY ---
st.subheader("1. Kto i Gdzie?")
col1, col2 = st.columns(2)

with col1:
    wybrany_label_pacjent = st.selectbox("Wybierz Pacjenta:", options=["--- Wybierz pacjenta ---"] + list(pacjent_options.keys()))
with col2:
    wybrany_label_firma = st.selectbox("Wybierz Firmę kierującą:", options=["--- Wybierz firmę ---"] + list(firma_options.keys()))

st.divider()

# --- 4. SEKCJA TERMINU I SLOTÓW ---
st.subheader("2. Termin i Godzina")
c_date, c_time = st.columns(2)

with c_date:
    data_wizyty = st.date_input("Data wizyty:", min_value=datetime.date.today(), value=datetime.date.today())

# Generator slotów (08:00 - 16:00, co 15 minut)
def get_available_slots(selected_date, df_existing_wizyty):
    all_slots = []
    start = datetime.datetime.combine(selected_date, datetime.time(8, 0))
    end = datetime.datetime.combine(selected_date, datetime.time(16, 0))
    
    current = start
    while current < end:
        all_slots.append(current.strftime("%H:%M"))
        current += datetime.timedelta(minutes=15)
    
    zajete_godziny = []
    if not df_existing_wizyty.empty and 'Godzina' in df_existing_wizyty.columns:
        mask = df_existing_wizyty['DataWizyty'].astype(str) == str(selected_date)
        zajete_godziny = df_existing_wizyty[mask]['Godzina'].astype(str).tolist()
    
    return [slot for slot in all_slots if slot not in zajete_godziny]

wolne_sloty = get_available_slots(data_wizyty, df_wizyty)

with c_time:
    if not wolne_sloty:
        st.error("Brak wolnych terminów w wybranym dniu.")
        wybrana_godzina = None
    else:
        wybrana_godzina = st.selectbox(f"Dostępne godziny ({len(wolne_sloty)} wolnych):", wolne_sloty)

st.divider()

# --- 5. SEKCJA STANOWISKA I ZAGROŻEŃ ---
nip_firmy = firma_options.get(wybrany_label_firma)
pesel_pacjenta = pacjent_options.get(wybrany_label_pacjent)

# Inicjalizacja zmiennych
final_stanowisko = ""
final_czynniki = ""
wybrane_st = "--- Wybierz stanowisko ---"

if nip_firmy:
    st.subheader("3. Stanowisko i Zagrożenia")
    
    stanowiska_firmy = df_stanowiska[df_stanowiska['NIP_Firmy'].astype(str) == str(nip_firmy)] if not df_stanowiska.empty else pd.DataFrame()
    
    opcje_st = ["--- Wybierz stanowisko ---"]
    if not stanowiska_firmy.empty:
        opcje_st += stanowiska_firmy['NazwaStanowiska'].tolist()
    opcje_st += ["➕ DODAJ NOWE STANOWISKO"]
    
    wybrane_st = st.selectbox("Stanowisko pracy:", opcje_st)
    
    if wybrane_st == "➕ DODAJ NOWE STANOWISKO":
        final_stanowisko = st.text_input("Nazwa nowego stanowiska:")
        final_czynniki = st.text_area("Wpisz czynniki szkodliwe:")
    elif wybrane_st != "--- Wybierz stanowisko ---":
        row_st = stanowiska_firmy[stanowiska_firmy['NazwaStanowiska'] == wybrane_st].iloc[0]
        final_stanowisko = wybrane_st
        final_czynniki = st.text_area("Czynniki szkodliwe:", value=row_st['CzynnikiSzkodliwe'])

    st.divider()
    
    # --- 6. TYP BADANIA I ZAPIS ---
    st.subheader("4. Rodzaj badania")
    typ_badania = st.radio(
        "Wybierz typ badania profilaktycznego:",
        ("Wstępne", "Okresowe", "Kontrolne", "Sanitarno-Epidemiologiczne"),
        horizontal=True
    )

    if st.button("ZAREJESTRUJ WIZYTĘ", type="primary", use_container_width=True):
        if not pesel_pacjenta:
            st.error("Proszę wybrać pacjenta.")
        elif not wybrana_godzina:
            st.error("Proszę wybrać godzinę wizyty.")
        elif wybrane_st == "--- Wybierz stanowisko ---" or (wybrane_st == "➕ DODAJ NOWE STANOWISKO" and not final_stanowisko):
            st.error("Proszę określić stanowisko pracy.")
        else:
            with st.spinner("Zapisywanie wizyty..."):
                if wybrane_st == "➕ DODAJ NOWE STANOWISKO":
                    add_stanowisko_to_db(nip_firmy, final_stanowisko, final_czynniki)
                
                notatki_lekarz = f"Stanowisko: {final_stanowisko}\nZagrożenia: {final_czynniki}"
                
                sukces, msg = add_appointment_to_db(
                    pesel=pesel_pacjenta,
                    nip_firmy=nip_firmy,
                    typ_badania=typ_badania,
                    notatki=notatki_lekarz,
                    data_wizyty=data_wizyty,
                    godzina=wybrana_godzina
                )
                
                if sukces:
                    st.balloons()
                    st.success(f"✅ Sukces! {msg}")
                else:
                    st.error(msg)
