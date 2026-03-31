import streamlit as st
import pandas as pd
from db_service import get_data_as_df

st.set_page_config(page_title="Raporty i Finanse", page_icon="💰", layout="wide")
st.markdown("# 💰 Raporty i Rozliczenia")
st.write("Generuj zestawienia dla kontrahentów na podstawie zrealizowanych wizyt.")

# 1. Pobranie danych
df_wizyty = get_data_as_df("Wizyty")
df_firmy = get_data_as_df("Firmy")
df_pacjenci = get_data_as_df("Pacjenci")

if df_wizyty.empty or df_firmy.empty:
    st.warning("Brak danych w systemie do wygenerowania raportu.")
    st.stop()

# 2. Filtrowanie tylko zakończonych wizyt
df_zakonczone = df_wizyty[df_wizyty['Status'] == 'Zakończona'].copy()

if df_zakonczone.empty:
    st.info("Brak zakończonych wizyt podlegających rozliczeniu.")
    st.stop()

# Przygotowanie filtrów
st.sidebar.header("Parametry raportu")
wybrana_firma_label = st.sidebar.selectbox(
    "Wybierz Firmę:", 
    options=df_firmy['NazwaFirmy'].unique()
)

# Wyodrębnienie NIP wybranej firmy
wybrany_nip = df_firmy[df_firmy['NazwaFirmy'] == wybrana_firma_label]['NIP'].iloc[0]
cennik = df_firmy[df_firmy['NIP'] == wybrany_nip].iloc[0]

# Filtrowanie dat (zakładamy format YYYY-MM-DD)
df_zakonczone['DataWizyty'] = pd.to_datetime(df_zakonczone['DataWizyty'])
miesiace = df_zakonczone['DataWizyty'].dt.strftime('%Y-%m').unique()
wybrany_miesiac = st.sidebar.selectbox("Wybierz Miesiąc:", options=sorted(miesiace, reverse=True))

# 3. Logika filtrowania danych do raportu
mask = (df_zakonczone['NIP_Firmy'].astype(str) == str(wybrany_nip)) & \
       (df_zakonczone['DataWizyty'].dt.strftime('%Y-%m') == wybrany_miesiac)
raport_raw = df_zakonczone[mask].copy()

if raport_raw.empty:
    st.warning(f"Brak zrealizowanych wizyt dla firmy {wybrana_firma_label} w okresie {wybrany_miesiac}.")
else:
    # 4. Łączenie z danymi pacjentów i naliczanie cen
    # Mapowanie cen z cennika firmy
    cennik_map = {
        "Wstępne": cennik['Cena_Wstepne'],
        "Okresowe": cennik['Cena_Okresowe'],
        "Kontrolne": cennik['Cena_Kontrolne'],
        "Sanitarno-Epidemiologiczne": cennik['Cena_Sanepid']
    }
    
    raport_raw['Cena'] = raport_raw['TypBadania'].map(cennik_map)
    
    # Dołączanie imion i nazwisk
    pacjenci_map = df_pacjenci.set_index('PESEL').to_dict('index')
    
    def get_pacjent_name(pesel):
        p = pacjenci_map.get(str(pesel))
        return f"{p['Nazwisko']} {p['Imie']}" if p else "Nieznany"

    raport_raw['Pacjent'] = raport_raw['PESEL_Pacjenta'].apply(get_pacjent_name)

    # Prezentacja wyników
    st.subheader(f"Zestawienie dla: {wybrana_firma_label}")
    st.write(f"Okres: **{wybrany_miesiac}**")

    # Tabela końcowa
    tabela_finansowa = raport_raw[['DataWizyty', 'Pacjent', 'TypBadania', 'Cena']]
    tabela_finansowa['DataWizyty'] = tabela_finansowa['DataWizyty'].dt.date
    
    st.table(tabela_finansowa)

    # Podsumowanie
    total = raport_raw['Cena'].sum()
    st.metric(label="Suma do zafakturowania", value=f"{total:,.2f} PLN".replace(",", " "))
    
    st.divider()
    if st.button("Pobierz jako CSV"):
        csv = tabela_finansowa.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Potwierdź pobieranie pliku",
            data=csv,
            file_name=f"Raport_{wybrana_firma_label}_{wybrany_miesiac}.csv",
            mime='text/csv',
        )
