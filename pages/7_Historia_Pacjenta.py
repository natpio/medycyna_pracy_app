import streamlit as st
import pandas as pd
from db_service import get_data_as_df

st.set_page_config(page_title="Karta Pacjenta", page_icon="🗂️", layout="wide")
st.markdown("# 🗂️ Elektroniczna Dokumentacja Medyczna (EDM)")
st.write("Wyszukaj pacjenta, aby przejrzeć pełną historię badań i wydanych orzeczeń.")

# 1. Pobranie danych
df_pacjenci = get_data_as_df("Pacjenci")
df_wizyty = get_data_as_df("Wizyty")
df_orzeczenia = get_data_as_df("Orzeczenia")
df_firmy = get_data_as_df("Firmy")

if df_pacjenci.empty:
    st.info("Baza pacjentów jest pusta.")
    st.stop()

# 2. Wyszukiwarka pacjenta
st.subheader("🔍 Znajdź Pacjenta")
pacjent_options = {f"{row['Nazwisko']} {row['Imie']} (PESEL: {row['PESEL']})": row['PESEL'] for _, row in df_pacjenci.iterrows()}
wybrany_label = st.selectbox("Zacznij wpisywać Nazwisko lub PESEL:", options=["--- Wybierz pacjenta ---"] + list(pacjent_options.keys()))

if wybrany_label != "--- Wybierz pacjenta ---":
    pesel = str(pacjent_options[wybrany_label])
    pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == pesel].iloc[0]
    
    # --- NAGŁÓWEK KARTY PACJENTA ---
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"### {pacjent['Imie']} {pacjent['Nazwisko']}")
        st.write(f"**PESEL:** {pacjent['PESEL']}")
    with c2:
        st.write(f"**Data urodzenia:** {pacjent['DataUrodzenia']}")
        st.write(f"**Telefon:** {pacjent['Telefon']}")
    with c3:
        # Obliczanie wieku (opcjonalnie)
        rok_urodz = int(str(pacjent['DataUrodzenia'])[:4])
        wiek = 2026 - rok_urodz
        st.metric("Wiek pacjenta", f"{wiek} lat")

    # --- HISTORIA WIZYT I ORZECZEŃ ---
    tab1, tab2 = st.tabs(["🕒 Chronologiczna Historia", "📄 Wydane Orzeczenia"])
    
    with tab1:
        st.markdown("#### Oś czasu wizyt")
        wizyty_pacjenta = df_wizyty[df_wizyty['PESEL_Pacjenta'].astype(str) == pesel].sort_values(by='DataWizyty', ascending=False)
        
        if wizyty_pacjenta.empty:
            st.info("Brak zarejestrowanych wizyt dla tego pacjenta.")
        else:
            for _, wiz in wizyty_pacjenta.iterrows():
                # Znalezienie nazwy firmy
                nazwa_firmy = df_firmy[df_firmy['NIP'].astype(str) == str(wiz['NIP_Firmy'])]['NazwaFirmy'].iloc[0] if not df_firmy.empty else wiz['NIP_Firmy']
                
                with st.expander(f"📅 {wiz['DataWizyty']} - {wiz['TypBadania']} ({nazwa_firmy})"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Status:**", wiz['Status'])
                        st.write("**ID Wizyty:**", wiz['ID_Wizyty'])
                    with col_b:
                        st.write("**Zagrożenia wpisane na skierowaniu:**")
                        st.caption(wiz['Notatki'])
                    
                    # Czy do tej wizyty jest orzeczenie?
                    if not df_orzeczenia.empty:
                        orz = df_orzeczenia[df_orzeczenia['ID_Wizyty'].astype(str) == str(wiz['ID_Wizyty'])]
                        if not orz.empty:
                            st.success(f"✅ **Decyzja:** {orz.iloc[0]['Decyzja']}")
                            st.info(f"📝 **Uwagi lekarza:** {orz.iloc[0]['UwagiLekarza']}")
    
    with tab2:
        st.markdown("#### Wszystkie dokumenty prawne")
        if not df_orzeczenia.empty:
            orz_pacjenta = df_orzeczenia[df_orzeczenia['PESEL_Pacjenta'].astype(str) == pesel].sort_values(by='ID_Orzeczenia', ascending=False)
            if not orz_pacjenta.empty:
                # Wyświetlamy tabelę z samymi orzeczeniami
                st.dataframe(orz_pacjenta[['ID_Orzeczenia', 'Decyzja', 'DataKolejnegoBadania', 'UwagiLekarza']], use_container_width=True, hide_index=True)
            else:
                st.write("Nie wystawiono jeszcze żadnych orzeczeń.")
        else:
            st.write("Baza orzeczeń jest pusta.")
