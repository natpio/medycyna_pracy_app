import streamlit as st
from db_service import add_company_to_db, get_data_as_df, add_stanowisko_to_db

st.set_page_config(page_title="Baza Firm", page_icon="🏢")
st.markdown("# 🏢 Obsługiwane Firmy i Stanowiska")

# Dodaliśmy trzecią zakładkę
tab1, tab2, tab3 = st.tabs(["➕ Dodaj Nową Firmę", "📋 Lista Firm", "👷 Katalog Stanowisk"])

with tab1:
    st.write("Wprowadź dane nowego kontrahenta.")
    with st.form("company_form"):
        col1, col2 = st.columns(2)
        with col1:
            nip = st.text_input("NIP (Unikalny identyfikator)", max_chars=10)
            nazwa = st.text_input("Pełna nazwa firmy")
        with col2:
            adres = st.text_area("Adres siedziby", height=100)
        
        submitted_company = st.form_submit_button("Dodaj Firmę", type="primary")
        
        if submitted_company:
            if not nip or len(nip) != 10 or not nip.isdigit():
                 st.error("Podaj poprawny 10-cyfrowy NIP.")
            elif not nazwa:
                 st.error("Nazwa firmy jest wymagana.")
            else:
                success, message = add_company_to_db(nip, nazwa, adres)
                if success:
                    st.success(message)
                else:
                    st.error(message)

with tab2:
    st.write("Podgląd firm w bazie.")
    df_firmy = get_data_as_df("Firmy")
    if not df_firmy.empty:
        st.dataframe(df_firmy, use_container_width=True, hide_index=True)
    else:
        st.info("Baza firm jest pusta.")

# --- NOWY MODUŁ: KATALOG STANOWISK ---
with tab3:
    st.markdown("### Zdefiniuj stanowiska dla firmy")
    df_firmy_stanowiska = get_data_as_df("Firmy")
    
    if df_firmy_stanowiska.empty:
        st.warning("Najpierw dodaj firmę, aby móc przypisać do niej stanowiska.")
    else:
        # Wybór firmy
        firma_options = {f"{row['NazwaFirmy']} (NIP: {row['NIP']})": row['NIP'] for index, row in df_firmy_stanowiska.iterrows()}
        wybrana_firma_etykieta = st.selectbox("Wybierz firmę:", options=["--- Wybierz firmę ---"] + list(firma_options.keys()))
        
        if wybrana_firma_etykieta != "--- Wybierz firmę ---":
            wybrany_nip = firma_options[wybrana_firma_etykieta]
            
            # Formularz dodawania stanowiska
            with st.form("stanowisko_form"):
                nazwa_stanowiska = st.text_input("Nazwa stanowiska (np. Kierowca, Spawacz, Księgowa)")
                czynniki = st.text_area("Czynniki szkodliwe i uciążliwe na tym stanowisku", height=80, 
                                        placeholder="np. praca na wysokości do 3m, praca przy monitorze ekranowym > 4h, hałas, zapylenie...")
                
                zapisz_stanowisko = st.form_submit_button("Zapisz stanowisko w bazie")
                
                if zapisz_stanowisko:
                    if not nazwa_stanowiska or not czynniki:
                        st.error("Wypełnij oba pola!")
                    else:
                        with st.spinner("Zapisywanie..."):
                            sukces, msg = add_stanowisko_to_db(wybrany_nip, nazwa_stanowiska, czynniki)
                            if sukces:
                                st.success(msg)
                            else:
                                st.error("Wystąpił błąd podczas zapisu.")
            
            # Tabela pokazująca dodane już stanowiska dla tej firmy
            st.divider()
            st.markdown(f"**Istniejące stanowiska w tej firmie:**")
            df_stanowiska = get_data_as_df("Stanowiska")
            
            if not df_stanowiska.empty:
                # Filtrujemy stanowiska tylko dla wybranej firmy (po NIP)
                stanowiska_firmy = df_stanowiska[df_stanowiska['NIP_Firmy'].astype(str) == str(wybrany_nip)]
                
                if not stanowiska_firmy.empty:
                    # Ukrywamy kolumnę NIP_Firmy dla lepszej czytelności
                    st.dataframe(stanowiska_firmy[['NazwaStanowiska', 'CzynnikiSzkodliwe']], use_container_width=True, hide_index=True)
                else:
                    st.info("Brak zdefiniowanych stanowisk dla tej firmy.")
            else:
                 st.info("Katalog stanowisk w całej bazie jest pusty.")
