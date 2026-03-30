import streamlit as st
from db_service import get_data_as_df, add_appointment_to_db

st.set_page_config(page_title="Nowa Wizyta", page_icon="📅")
st.markdown("# 📅 Rejestracja Wizyty")
st.write("Przypisz pacjenta do firmy i określ cel wizyty.")

# 1. Pobranie danych słownikowych (Pacjenci i Firmy)
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if df_pacjenci.empty or df_firmy.empty:
    st.warning("Uzupełnij najpierw bazę pacjentów i firm, aby móc umawiać wizyty.")
    st.stop()

# Tworzymy listy rozwijane (słowniki) dla łatwiejszego wyboru
# Kluczem będzie czytelny tekst, wartością ID (PESEL lub NIP)
pacjent_options = {f"{row['Nazwisko']} {row['Imie']} (PESEL: {row['PESEL']})": row['PESEL'] for index, row in df_pacjenci.iterrows()}
firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for index, row in df_firmy.iterrows()}

with st.form("appointment_form"):
    st.subheader("1. Kto i Gdzie?")
    col1, col2 = st.columns(2)
    with col1:
        selected_patient_label = st.selectbox("Wybierz Pacjenta", options=list(pacjent_options.keys()))
        # Wyciągamy PESEL na podstawie wybranej etykiety
        pesel_to_save = pacjent_options[selected_patient_label]
        
    with col2:
        selected_company_label = st.selectbox("Wybierz Firmę kierującą", options=list(firma_options.keys()))
        # Wyciągamy NIP na podstawie wybranej etykiety
        nip_to_save = firma_options[selected_company_label]

    st.divider()
    st.subheader("2. Szczegóły skierowania")
    
    typ_badania = st.radio(
        "Typ badań:",
        ("Wstępne", "Okresowe", "Kontrolne", "Sanitarno-Epidemiologiczne"),
        horizontal=True
    )
    
    notatki = st.text_area("Notatki / Czynniki szkodliwe ze skierowania", height=100, placeholder="np. praca na wysokości, monitor ekranowy > 4h...")

    submitted_visit = st.form_submit_button("Zatwierdź Wizytę", type="primary")

    if submitted_visit:
        with st.spinner("Planowanie wizyty..."):
            success, message = add_appointment_to_db(pesel_to_save, nip_to_save, typ_badania, notatki)
        
        if success:
            st.balloons() # Trochę radości dla recepcjonistki :)
            st.success(message)
        else:
            st.error(message)
