import streamlit as st
import datetime
import pandas as pd
from db_service import get_data_as_df, add_orzeczenie_to_db
from db_service import get_data_as_df, apply_pro_style

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Panel Lekarza", page_icon="👨‍⚕️", layout="wide")
st.markdown("# 👨‍⚕️ Gabinet Orzecznika")

# 1. Pobranie danych z bazy
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_slownik = get_data_as_df("Slownik_Badan")

if df_wizyty.empty:
    st.info("Brak zarejestrowanych wizyt w systemie.")
    st.stop()

# 2. Filtrowanie pacjentów w poczekalni (status: Zaplanowana)
zaplanowane = df_wizyty[df_wizyty['Status'] == 'Zaplanowana']

if zaplanowane.empty:
    st.success("🎉 Świetna robota, Panie Doktorze! Brak oczekujących pacjentów w poczekalni.")
    st.stop()

st.subheader("Bieżąca kolejka pacjentów")

# 3. Przygotowanie listy do wyboru pacjenta
wizyty_dict = {
    f"{row['DataWizyty']} | PESEL: {row['PESEL_Pacjenta']} ({row['TypBadania']})": row 
    for _, row in zaplanowane.iterrows()
}
wybrana_etykieta = st.selectbox("Wybierz pacjenta z listy, aby rozpocząć badanie:", options=["--- Wybierz pacjenta ---"] + list(wizyty_dict.keys()))

if wybrana_etykieta != "--- Wybierz pacjenta ---":
    wizyta = wizyty_dict[wybrana_etykieta]
    
    # Pobranie szczegółowych danych pacjenta
    pacjent_dane = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(wizyta['PESEL_Pacjenta'])]
    pacjent = pacjent_dane.iloc[0] if not pacjent_dane.empty else None

    st.divider()
    
    # Układ panelu: Dane pacjenta vs Inteligentne podpowiedzi
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 👤 Dane Pacjenta")
        if pacjent is not None:
            st.write(f"**Imię i Nazwisko:** {pacjent['Imie']} {pacjent['Nazwisko']}")
            st.write(f"**PESEL:** {pacjent['PESEL']}")
            st.write(f"**Data urodzenia:** {pacjent['DataUrodzenia']}")
        else:
            st.error("Nie znaleziono danych osobowych dla tego numeru PESEL.")
        
        st.write(f"**Rodzaj badania:** {wizyta['TypBadania']}")
        st.write(f"**Data skierowania:** {wizyta['DataWizyty']}")
    
    with col2:
        st.markdown("### 🧠 Inteligentna Analiza Skierowania")
        notatki_raw = str(wizyta['Notatki'])
        notatki_lcase = notatki_raw.lower()
        
        st.info(f"**Treść skierowania (Stanowisko i zagrożenia):**\n\n{notatki_raw}")
        
        # LOGIKA PODPOWIEDZI NA PODSTAWIE SŁOWNIKA
        sugerowane_konsultacje = set()
        sugerowane_badania = set()
        
        if not df_slownik.empty:
            for _, regula in df_slownik.iterrows():
                czynnik_klucz = str(regula['Czynnik']).lower()
                if czynnik_klucz in notatki_lcase:
                    kons = str(regula['Konsultacje_Specjalistyczne'])
                    if kons and kons not in ["—", "nan", "None", ""]:
                        sugerowane_konsultacje.add(kons)
                    
                    diag = str(regula['Badania_Diagnostyczne'])
                    if diag and diag not in ["—", "nan", "None", ""]:
                        sugerowane_badania.add(diag)
        
        if sugerowane_konsultacje or sugerowane_badania:
            st.warning("⚠️ **Wymagane konsultacje i badania na podstawie czynników szkodliwych:**")
            if sugerowane_konsultacje:
                st.write(f"**Specjaliści:** {', '.join(sugerowane_konsultacje)}")
            if sugerowane_badania:
                st.write(f"**Badania diagnostyczne:** {', '.join(sugerowane_badania)}")
        else:
            st.success("System nie wykrył specyficznych wymogów prawnych dla podanych czynników.")

    st.divider()
    
    # --- FORMULARZ WYSTAWIANIA ORZECZENIA Z PODPISEM CYFROWYM ---
    st.markdown("### 📝 Decyzja Orzecznicza")
    with st.form("orzeczenie_form"):
        col_dec, col_date = st.columns(2)
        
        with col_dec:
            decyzja = st.radio(
                "Wynik badania profilaktycznego:",
                ("ZDOLNY do wykonywania pracy.", "NIEZDOLNY do wykonywania pracy.")
            )
        
        with col_date:
            domyslna_data = datetime.date.today() + datetime.timedelta(days=3*365)
            data_kolejnego = st.date_input("Data następnego badania okresowego:", value=domyslna_data)
        
        uwagi_lek = st.text_area("Uwagi lekarza / Ograniczenia / Zalecenia:", height=100)
        
        st.markdown("---")
        st.subheader("🔐 Autoryzacja i Podpis Elektroniczny")
        st.write("Wprowadzenie kodu PIN wygeneruje unikalną pieczęć cyfrową (Hash SHA-256) potwierdzającą autentyczność dokumentu.")
        
        pin_input = st.text_input("Wprowadź PIN Lekarza:", type="password", help="W celach testowych użyj: 1234")

        submit_btn = st.form_submit_button("Podpisz i Wystaw Orzeczenie", type="primary")
        
        if submit_btn:
            if not pin_input:
                st.error("Błąd: Dokument musi zostać zautoryzowany kodem PIN.")
            else:
                with st.spinner("Generowanie podpisu cyfrowego i zamykanie wizyty..."):
                    sukces, message = add_orzeczenie_to_db(
                        id_wizyty=wizyta['ID_Wizyty'],
                        pesel=wizyta['PESEL_Pacjenta'],
                        decyzja=decyzja,
                        data_kolejnego=data_kolejnego,
                        uwagi=uwagi_lek,
                        pin_lekarza=pin_input
                    )
                
                if sukces:
                    st.balloons()
                    st.success(message)
                    st.info("Dokument został zabezpieczony kryptograficznie. Odśwież stronę (F5), aby pobrać kolejnego pacjenta.")
                else:
                    st.error(message)
