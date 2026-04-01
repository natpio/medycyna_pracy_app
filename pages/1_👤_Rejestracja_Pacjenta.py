import streamlit as st
from db_service import add_patient_to_db, apply_pro_style
import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Rejestracja Pacjenta", page_icon="👤", layout="centered")

# --- URUCHOMIENIE STYLU PRO ---
apply_pro_style()

st.markdown("# 👤 Nowa Karta Pacjenta")
st.write("Wprowadź pełne dane pacjenta, który zgłasza się do gabinetu po raz pierwszy.")

# Używamy st.form, aby zgrupować pola i wysłać je jednym przyciskiem
with st.form("patient_form", clear_on_submit=False):
    st.subheader("Dane podstawowe")
    col1, col2 = st.columns(2)
    with col1:
        imie = st.text_input("Imię", placeholder="np. Jan")
        pesel = st.text_input("PESEL (Wymagany)", max_chars=11, placeholder="11 cyfr")
    with col2:
        nazwisko = st.text_input("Nazwisko", placeholder="np. Kowalski")
        telefon = st.text_input("Numer telefonu", placeholder="np. 500 123 456")
    
    st.divider()
    st.subheader("Dane szczegółowe i kontaktowe")
    
    data_urodzenia = st.date_input(
        "Data urodzenia", 
        min_value=datetime.date(1940, 1, 1),
        max_value=datetime.date.today(),
        value=datetime.date(1990, 1, 1)
    )
    
    # Podział na dwie kolumny dla adresu i e-maila
    col_adres, col_email = st.columns(2)
    with col_adres:
        adres = st.text_input("Adres zamieszkania", placeholder="ul. Medyczna 1/2, 00-000 Miasto")
    with col_email:
        email = st.text_input("Adres E-mail", placeholder="pacjent@domena.pl")

    # Przycisk wysyłający formularz
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button("💾 Zapisz Pacjenta w Bazie", type="primary", use_container_width=True)

    if submitted:
        # Prosta walidacja po stronie frontendu
        if not pesel or len(pesel) != 11 or not pesel.isdigit():
            st.error("Błąd: Podaj poprawny, 11-cyfrowy numer PESEL.")
        elif not imie or not nazwisko:
            st.error("Błąd: Imię i nazwisko są wymagane.")
        elif not adres:
            st.error("Błąd: Adres zamieszkania jest wymagany do dokumentacji.")
        else:
            # Zapis do bazy danych (7 argumentów: dodany adres i email na końcu)
            sukces, msg = add_patient_to_db(pesel, imie, nazwisko, str(data_urodzenia), telefon, adres, email)
            if sukces:
                st.success(f"✅ {msg}")
                st.balloons()
            else:
                st.error(f"❌ {msg}")
