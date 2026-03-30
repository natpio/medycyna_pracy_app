import streamlit as st
from db_service import get_data_as_df, add_appointment_to_db
import datetime

st.set_page_config(page_title="Nowa Wizyta", page_icon="📅")
st.markdown("# 📅 Rejestracja Wizyty")
st.write("Przypisz pacjenta do firmy i określ cel oraz termin wizyty.")

# 1. Pobranie danych
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")

if df_pacjenci.empty or df_firmy.empty:
    st.warning("Uzupełnij najpierw bazę pacjentów i firm, aby móc umawiać wizyty.")
    st.stop()

# Tworzymy słowniki dla selectboxów
pacjent_options = {f"{row['Nazwisko']} {row['Imie']} (PESEL: {row['PESEL']})": row['PESEL'] for index, row in df_pacjenci.iterrows()}
firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for index, row in df_firmy.iterrows()}

lista_pacjentow = ["--- Wybierz pacjenta ---"] + list(pacjent_options.keys())
lista_firm = ["--- Wybierz firmę ---"] + list(firma_options.keys())

with st.form("appointment_form"):
    st.subheader("1. Kto i Gdzie?")
    col1, col2 = st.columns(2)
    with col1:
        selected_patient_label = st.selectbox("Wybierz Pacjenta", options=lista_pacjentow)
        
    with col2:
        selected_company_label = st.selectbox("Wybierz Firmę kierującą", options=lista_firm)

    st.divider()
    st.subheader("2. Szczegóły wizyty")
    
    # --- NOWE POLE: WYBÓR DATY ---
    col_date, col_type = st.columns(2)
    with col_date:
        data_wizyty = st.date_input("Termin wizyty:", value=datetime.date.today())
    
    with col_type:
        typ_badania = st.radio(
            "Typ badań:",
            ("Wstępne", "Okresowe", "Kontrolne", "Sanitarno-Epidemiologiczne"),
            horizontal=True
        )
    
    notatki = st.text_area("Notatki / Czynniki szkodliwe ze skierowania", height=100, placeholder="np. praca na wysokości, monitor ekranowy > 4h...")

    submitted_visit = st.form_submit_button("Zatwierdź Wizytę", type="primary")

    if submitted_visit:
        if selected_patient_label == "--- Wybierz pacjenta ---" or selected_company_label == "--- Wybierz firmę ---":
            st.error("Błąd: Musisz ręcznie wybrać pacjenta oraz firmę z listy rozwijanej!")
        else:
            pesel_to_save = pacjent_options[selected_patient_label]
            nip_to_save = firma_options[selected_company_label]
            
            with st.spinner("Planowanie wizyty..."):
                # Przekazujemy wybraną datę do funkcji
                success, message = add_appointment_to_db(
                    pesel=pesel_to_save, 
                    nip_firmy=nip_to_save, 
                    typ_badania=typ_badania, 
                    notatki=notatki,
                    data_wizyty=data_wizyty
                )
            
            if success:
                st.balloons()
                st.success(message)
            else:
                st.error(message)
