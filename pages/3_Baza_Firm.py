import streamlit as st
from db_service import add_company_to_db, get_data_as_df, add_stanowisko_to_db, apply_pro_style

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Baza Firm", page_icon="🏢", layout="wide")

# --- URUCHOMIENIE STYLU PRO ---
apply_pro_style()

st.markdown("# 🏢 Obsługiwane Firmy i Kontrakty")

# Podział na zakładki dla lepszej organizacji pracy
tab1, tab2, tab3 = st.tabs(["➕ Dodaj Nową Firmę", "📋 Lista Firm i Cenniki", "👷 Katalog Stanowisk"])

# --- ZAKŁADKA 1: DODAWANIE NOWEJ FIRMY ---
with tab1:
    st.write("Wprowadź dane kontrahenta oraz wynegocjowane stawki za badania profilaktyczne.")
    
    with st.form("company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 Dane podstawowe")
            nip = st.text_input("NIP (10 cyfr)", max_chars=10, help="Unikalny identyfikator podatkowy firmy")
            nazwa = st.text_input("Pełna nazwa firmy")
            adres = st.text_area("Adres siedziby", height=100, placeholder="ul. Przykładowa 1, 00-000 Miasto")
        
        with col2:
            st.markdown("### 💰 Cennik badań (PLN)")
            c_wst = st.number_input("Badanie Wstępne", min_value=0, value=150, step=10)
            c_okr = st.number_input("Badanie Okresowe", min_value=0, value=150, step=10)
            c_kon = st.number_input("Badanie Kontrolne", min_value=0, value=120, step=10)
            c_san = st.number_input("Badanie Sanitarne (Sanepid)", min_value=0, value=80, step=10)
        
        st.divider()
        submitted_company = st.form_submit_button("Zapisz Firmę i Kontrakt", type="primary")
        
        if submitted_company:
            # Walidacja danych
            if not nip or len(nip) != 10 or not nip.isdigit():
                 st.error("Błąd: Podaj poprawny 10-cyfrowy NIP.")
            elif not nazwa:
                 st.error("Błąd: Nazwa firmy jest wymagana.")
            else:
                # Wywołanie funkcji z db_service.py
                success, message = add_company_to_db(nip, nazwa, adres, c_wst, c_okr, c_kon, c_san)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

# --- ZAKŁADKA 2: LISTA FIRM I CENNIKI ---
with tab2:
    st.write("Podgląd wszystkich kontrahentów zapisanych w systemie wraz z przypisanymi stawkami.")
    df_firmy = get_data_as_df("Firmy")
    
    if not df_firmy.empty:
        # Mapowanie nazw kolumn na bardziej przyjazne dla użytkownika
        df_display = df_firmy.rename(columns={
            "NIP": "NIP",
            "NazwaFirmy": "Nazwa Firmy",
            "Adres": "Adres",
            "Cena_Wstepne": "Wstępne [zł]",
            "Cena_Okresowe": "Okresowe [zł]",
            "Cena_Kontrolne": "Kontrolne [zł]",
            "Cena_Sanepid": "Sanepid [zł]"
        })
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Baza firm jest obecnie pusta.")

# --- ZAKŁADKA 3: KATALOG STANOWISK ---
with tab3:
    st.markdown("### 👷 Zarządzanie stanowiskami i zagrożeniami")
    st.write("Przypisz konkretne stanowiska pracy do wybranych firm, aby zautomatyzować proces rejestracji.")
    
    df_firmy_stanowiska = get_data_as_df("Firmy")
    
    if df_firmy_stanowiska.empty:
        st.warning("Najpierw dodaj przynajmniej jedną firmę w zakładce obok.")
    else:
        # Słownik do wyboru firmy (Etykieta: NIP)
        firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for index, row in df_firmy_stanowiska.iterrows()}
        wybrana_firma_etykieta = st.selectbox("Wybierz firmę do edycji katalogu:", options=["--- Wybierz firmę ---"] + list(firma_options.keys()))
        
        if wybrana_firma_etykieta != "--- Wybierz firmę ---":
            wybrany_nip = firma_options[wybrana_firma_etykieta]
            
            # Formularz dodawania stanowiska
            with st.form("stanowisko_form"):
                nazwa_stanowiska = st.text_input("Nazwa stanowiska (np. Spawacz, Kierowca)")
                czynniki = st.text_area("Czynniki szkodliwe i uciążliwe", placeholder="Wpisz zagrożenia oddzielone przecinkami...")
                
                zapisz_stanowisko = st.form_submit_button("Zapisz stanowisko w słowniku firmy")
                
                if zapisz_stanowisko:
                    if not nazwa_stanowiska or not czynniki:
                        st.error("Wypełnij oba pola, aby dodać stanowisko.")
                    else:
                        with st.spinner("Aktualizacja katalogu..."):
                            sukces, msg = add_stanowisko_to_db(wybrany_nip, nazwa_stanowiska, czynniki)
                            if sukces:
                                st.success(msg)
                            else:
                                st.error("Wystąpił problem przy zapisie stanowiska.")
            
            # Tabela pokazująca stanowiska tylko dla wybranej firmy
            st.divider()
            st.markdown(f"**Istniejące stanowiska dla firmy o NIP: {wybrany_nip}:**")
            df_all_stanowiska = get_data_as_df("Stanowiska")
            
            if not df_all_stanowiska.empty:
                stanowiska_firmy = df_all_stanowiska[df_all_stanowiska['NIP_Firmy'].astype(str) == str(wybrany_nip)]
                
                if not stanowiska_firmy.empty:
                    st.dataframe(stanowiska_firmy[['NazwaStanowiska', 'CzynnikiSzkodliwe']], use_container_width=True, hide_index=True)
                else:
                    st.info("Ta firma nie ma jeszcze zdefiniowanych stanowisk w katalogu.")
            else:
                 st.info("Katalog stanowisk jest pusty.")
