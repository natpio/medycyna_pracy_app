import streamlit as st
from db_service import add_patient_to_db
import datetime

st.set_page_config(page_title="Rejestracja Pacjenta", page_icon="👤")
st.markdown("# 👤 Nowa Karta Pacjenta")
st.write("Wprowadź dane pacjenta, który zgłasza się do gabinetu po raz pierwszy.")

# Używamy st.form, aby zgrupować pola i wysłać je jednym przyciskiem
with st.form("patient_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        imie = st.text_input("Imię", placeholder="np. Jan")
        pesel = st.text_input("PESEL (Wymagany)", max_chars=11, placeholder="11 cyfr")
    with col2:
        nazwisko = st.text_input("Nazwisko", placeholder="np. Kowalski")
        telefon = st.text_input("Numer telefonu", placeholder="np. 500 123 456")
    
    data_urodzenia = st.date_input("Data urodzenia", min_value=datetime.date(1940, 1, 1))

    submitted = st.form_submit_button("Zapisz Pacjenta w Bazie", type="primary")

    if submitted:
        # Prosta walidacja po stronie frontendu
        if not pesel or len(pesel) != 11 or not pesel.isdigit():
            st.error("Błąd: Podaj poprawny, 11-cyfrowy numer PESEL.")
        elif not imie or not nazwisko:
            st.error("Błąd: Imię i nazwisko są wymagane.")
        else:
            # Wywołanie funkcji z backendu
            with st.spinner("Zapisywanie w Google Sheets..."):
                success, message = add_patient_to_db(pesel, imie, nazwisko, data_urodzenia, telefon)
            
            if success:
                st.success(message)
            else:
                st.error(message)
