import streamlit as st
from db_service import add_company_to_db, get_data_as_df

st.set_page_config(page_title="Baza Firm", page_icon="🏢")
st.markdown("# 🏢 Obsługiwane Firmy")

tab1, tab2 = st.tabs(["➕ Dodaj Nową Firmę", "📋 Lista Firm"])

with tab1:
    st.write("Wprowadź dane nowego kontrahenta.")
    with st.form("company_form"):
        col1, col2 = st.columns(2)
        with col1:
            nip = st.text_input("NIP (Unikalny identyfikator)", max_chars=10)
            nazwa = st.text_input("Pełna nazwa firmy")
        with col2:
            adres = st.text_area("Adres siedziby", height=100)
        
        submitted_company = st.form_submit_button("Dodaj Firmę")
        
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
    df = get_data_as_df("Firmy")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Baza firm jest pusta.")
