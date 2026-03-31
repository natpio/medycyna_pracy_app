import streamlit as st
import pandas as pd
import datetime
from db_service import get_data_as_df
from db_service import get_data_as_df, apply_pro_style

st.set_page_config(page_title="Pulpit Recepcji", page_icon="📊", layout="wide")

# --- NAGŁÓWEK ---
st.markdown("# 📊 Dzisiejszy Status Gabinetu")
dzis = datetime.date.today()
st.write(f"Podsumowanie operacyjne na dzień: **{dzis}**")

# 1. Pobranie danych
df_wizyty = get_data_as_df("Wizyty")
df_firmy = get_data_as_df("Firmy")
df_pacjenci = get_data_as_df("Pacjenci")

if df_wizyty.empty:
    st.info("Brak zarejestrowanych wizyt w systemie.")
    st.stop()

# 2. Filtrowanie wizyt na DZISIAJ
# Upewniamy się, że format daty w DF zgadza się z formatem str(dzis)
df_wizyty['DataWizyty'] = df_wizyty['DataWizyty'].astype(str)
df_dzis = df_wizyty[df_wizyty['DataWizyty'] == str(dzis)].copy()

if df_dzis.empty:
    st.warning("Na dziś nie zaplanowano jeszcze żadnych wizyt.")
    st.stop()

# 3. Obliczenia finansowe i statusowe
total_dzis = len(df_dzis)
zakonczone_dzis = len(df_dzis[df_dzis['Status'] == 'Zakończona'])
oczekujace_dzis = total_dzis - zakonczone_dzis

# Mapowanie cen dla dzisiejszych wizyt
def oblicz_cene(row):
    firma = df_firmy[df_firmy['NIP'].astype(str) == str(row['NIP_Firmy'])]
    if firma.empty:
        return 0
    
    cennik = firma.iloc[0]
    typ = row['TypBadania']
    
    if typ == "Wstępne": return cennik.get('Cena_Wstepne', 0)
    if typ == "Okresowe": return cennik.get('Cena_Okresowe', 0)
    if typ == "Kontrolne": return cennik.get('Cena_Kontrolne', 0)
    if typ == "Sanitarno-Epidemiologiczne": return cennik.get('Cena_Sanepid', 0)
    return 0

df_dzis['PrzewidywanyPrzychod'] = df_dzis.apply(oblicz_cene, axis=1)
# Konwersja na liczby, by uniknąć błędów sumowania
df_dzis['PrzewidywanyPrzychod'] = pd.to_numeric(df_dzis['PrzewidywanyPrzychod'], errors='coerce').fillna(0)

utarg_zrealizowany = df_dzis[df_dzis['Status'] == 'Zakończona']['PrzewidywanyPrzychod'].sum()
potencjalny_total = df_dzis['PrzewidywanyPrzychod'].sum()

# --- WIDOK 1: METRYKI ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Wszystkie wizyty", total_dzis)
with c2:
    st.metric("Zakończone", zakonczone_dzis, f"{zakonczone_dzis/total_dzis:.0%}")
with c3:
    st.metric("W poczekalni", oczekujace_dzis)
with c4:
    st.metric("Utarg (zakończone)", f"{utarg_zrealizowany:,.2f} zł".replace(",", " "))

# --- WIDOK 2: LISTA PACJENTÓW NA DZIŚ ---
st.divider()
st.subheader("📋 Lista pacjentów i statusy")

# Łączymy z danymi pacjentów dla czytelności (Imię i Nazwisko)
pacjenci_dict = {str(row['PESEL']): f"{row['Nazwisko']} {row['Imie']}" for _, row in df_pacjenci.iterrows()}
df_dzis['Pacjent'] = df_dzis['PESEL_Pacjenta'].astype(str).map(pacjenci_dict)

# Tabela do wyświetlenia
widok_tabeli = df_dzis[['Pacjent', 'TypBadania', 'Status', 'PrzewidywanyPrzychod']].copy()
widok_tabeli.columns = ['Pacjent', 'Rodzaj Badania', 'Status', 'Koszt [zł]']

# Kolorowanie statusów
def color_status(val):
    color = '#e1f5fe' if val == 'Zaplanowana' else '#c8e6c9'
    return f'background-color: {color}'

st.dataframe(widok_tabeli.style.applymap(color_status, subset=['Status']), use_container_width=True, hide_index=True)

# --- WIDOK 3: FINANSE DNIA ---
st.divider()
col_a, col_b = st.columns(2)

with col_a:
    st.info(f"💰 **Potencjalny przychód na dziś:** {potencjalny_total:,.2f} PLN".replace(",", " "))
    st.caption("Suma wartości wszystkich zaplanowanych badań na podstawie cenników firm.")

with col_b:
    progress = utarg_zrealizowany / potencjalny_total if potencjalny_total > 0 else 0
    st.write(f"**Realizacja planu finansowego:** {progress:.0%}")
    st.progress(progress)
