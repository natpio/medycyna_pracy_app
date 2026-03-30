import streamlit as st
from db_service import get_data_as_df, add_appointment_to_db

st.set_page_config(page_title="Nowa Wizyta", page_icon="📅")
st.markdown("# 📅 Rejestracja Wizyty")
st.write("Przypisz pacjenta do firmy i określ cel wizyty.")

# 1. Pobranie danych
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if df_pacjenci.empty or df_firmy.empty:
    st.warning("Uzupełnij najpierw bazę pacjentów i firm, aby móc umawiać wizyty.")
    st.stop()

# Tworzymy słowniki
pacjent_options = {f"{row['Nazwisko']} {row['Imie']} (PESEL: {row['PESEL']})": row['PESEL'] for index, row in df_pacjenci.iterrows()}
firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for index, row in df_firmy.iterrows()}

# DODAJEMY PUSTE OPCJE NA POCZĄTEK LISTY
lista_pacjentow = ["--- Wybierz pacjenta ---"] + list(pacjent_options.keys())
lista_firm = ["--- Wybierz firmę ---"] + list(firma_options.keys())

with st.form("appointment_form"):
    st.subheader("1. Kto i Gdzie?")
    col1, col2 = st.columns(2)
    with col1:
        # Używamy nowej listy z pustą opcją
        selected_patient_label = st.selectbox("Wybierz Pacjenta", options=lista_pacjentow)
        
    with col2:
        # Używamy nowej listy z pustą opcją
        selected_company_label = st.selectbox("Wybierz Firmę kierującą", options=lista_firm)

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
        # ZABEZPIECZENIE: Sprawdzamy czy użytkownik faktycznie coś wybrał
        if selected_patient_label == "--- Wybierz pacjenta ---" or selected_company_label == "--- Wybierz firmę ---":
            st.error("Błąd: Musisz ręcznie wybrać pacjenta oraz firmę z listy rozwijanej!")
        else:
            # Jeśli wybrano poprawnie, wyciągamy PESEL i NIP
            pesel_to_save = pacjent_options[selected_patient_label]
            nip_to_save = firma_options[selected_company_label]
            
            with st.spinner("Planowanie wizyty..."):
                success, message = add_appointment_to_db(pesel_to_save, nip_to_save, typ_badania, notatki)
            
            if success:
                st.balloons()
                st.success(message)
            else:
                st.error(message)
