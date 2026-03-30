import streamlit as st
import datetime
from db_service import get_data_as_df, add_orzeczenie_to_db

st.set_page_config(page_title="Panel Lekarza", page_icon="👨‍⚕️", layout="wide")
st.markdown("# 👨‍⚕️ Gabinet Orzecznika")

# 1. Pobranie danych o wizytach i pacjentach
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")

if df_wizyty.empty:
    st.info("Brak jakichkolwiek wizyt w systemie.")
    st.stop()

# 2. Filtrujemy TYLKO pacjentów w poczekalni (status: Zaplanowana)
zaplanowane = df_wizyty[df_wizyty['Status'] == 'Zaplanowana']

if zaplanowane.empty:
    st.success("🎉 Świetna robota, Panie Doktorze! Brak oczekujących pacjentów na dziś.")
    st.stop()

st.subheader("Bieżąca kolejka pacjentów")

# 3. Przygotowanie listy do wyboru
lista_wyboru = ["--- Wybierz pacjenta z poczekalni ---"]
wizyty_dict = {} # Słownik ułatwiający wyciągnięcie danych po kliknięciu

for index, wizyta in zaplanowane.iterrows():
    # Szukamy imienia i nazwiska na podstawie PESELu
    pacjent_dane = df_pacjenci[df_pacjenci['PESEL'] == str(wizyta['PESEL_Pacjenta'])]
    
    imie = pacjent_dane.iloc[0]['Imie'] if not pacjent_dane.empty else "Nieznane"
    nazwisko = pacjent_dane.iloc[0]['Nazwisko'] if not pacjent_dane.empty else "Nieznane"
    
    etykieta = f"{wizyta['DataWizyty']} | {nazwisko} {imie} ({wizyta['TypBadania']})"
    lista_wyboru.append(etykieta)
    wizyty_dict[etykieta] = wizyta

# 4. Lekarz wybiera kogo zaprasza do gabinetu
wybrana_etykieta = st.selectbox("Oczekujący:", options=lista_wyboru)

if wybrana_etykieta != "--- Wybierz pacjenta z poczekalni ---":
    wizyta = wizyty_dict[wybrana_etykieta]
    
    # --- KARTA BADANIA ---
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Informacje ze skierowania")
        st.write(f"**PESEL:** {wizyta['PESEL_Pacjenta']}")
        st.write(f"**NIP Firmy:** {wizyta['NIP_Firmy']}")
        st.write(f"**Rodzaj badania:** {wizyta['TypBadania']}")
    
    with col2:
        st.markdown("### ⚠️ Czynniki szkodliwe")
        st.info(wizyta['Notatki'] if wizyta['Notatki'] else "Brak wpisanych uwag od pracodawcy.")
        
    st.divider()
    
    # --- FORMULARZ ORZECZNICZY ---
    st.markdown("### 📝 Wystawienie orzeczenia")
    with st.form("orzeczenie_form"):
        decyzja = st.radio(
            "Decyzja lekarza:",
            ("ZDOLNY do wykonywania pracy.",
             "NIEZDOLNY do wykonywania pracy.")
        )
        
        data_kolejnego = st.date_input("Data kolejnego badania okresowego:", min_value=datetime.date.today())
        
        uwagi = st.text_area("Wewnętrzne notatki medyczne (wywiad, wyniki badań):", height=100)
        
        zapisz_btn = st.form_submit_button("Wystaw Orzeczenie i Zakończ Wizytę", type="primary")
        
        if zapisz_btn:
            with st.spinner("Zapisywanie w systemie..."):
                sukces, wiadomosc = add_orzeczenie_to_db(
                    id_wizyty=wizyta['ID_Wizyty'],
                    pesel=wizyta['PESEL_Pacjenta'],
                    decyzja=decyzja,
                    data_kolejnego=data_kolejnego,
                    uwagi=uwagi
                )
            if sukces:
                st.success(wiadomosc)
                st.info("Zaktualizuj stronę (F5), aby pobrać kolejnego pacjenta z kolejki.")
            else:
                st.error("Wystąpił błąd podczas zapisu.")
