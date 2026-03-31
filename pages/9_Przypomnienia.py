import streamlit as st
import pandas as pd
import datetime
from db_service import get_data_as_df
from db_service import get_data_as_df, apply_pro_style

st.set_page_config(page_title="Przypomnienia", page_icon="🔔", layout="wide")
st.markdown("# 🔔 Kontrola Terminów i Przypomnienia")
st.write("System analizuje bazę orzeczeń i znajduje pacjentów, którym kończą się badania.")

# 1. Pobranie danych
df_orzeczenia = get_data_as_df("Orzeczenia")
df_pacjenci = get_data_as_df("Pacjenci")
df_firmy = get_data_as_df("Firmy")
df_wizyty = get_data_as_df("Wizyty")

if df_orzeczenia.empty:
    st.info("Brak wystawionych orzeczeń w bazie.")
    st.stop()

# 2. Przetwarzanie dat
# Konwertujemy datę kolejnego badania na format daty Pythona
df_orzeczenia['DataKolejnegoBadania'] = pd.to_datetime(df_orzeczenia['DataKolejnegoBadania']).dt.date
dzis = datetime.date.today()
za_30_dni = dzis + datetime.timedelta(days=30)

# 3. Logika: Wybieramy tylko NAJNOWSZE orzeczenie dla każdego pacjenta
# (żeby nie wysyłać przypomnień o starych, już przedłużonych badaniach)
df_latest = df_orzeczenia.sort_values('ID_Orzeczenia').groupby('PESEL_Pacjenta').last().reset_index()

# 4. Filtrowanie osób, którym kończy się ważność w ciągu 30 dni LUB już wygasła
wygasajace = df_latest[df_latest['DataKolejnegoBadania'] <= za_30_dni].copy()

if wygasajace.empty:
    st.success("✅ Wszyscy pacjenci mają aktualne badania na najbliższe 30 dni.")
else:
    st.warning(f"Znaleziono {len(wygasajace)} osób wymagających kontaktu.")

    # Łączenie danych dla czytelności
    # Dodajemy dane pacjenta
    df_pacjenci['PESEL'] = df_pacjenci['PESEL'].astype(str)
    wygasajace['PESEL_Pacjenta'] = wygasajace['PESEL_Pacjenta'].astype(str)
    
    merged = wygasajace.merge(df_pacjenci, left_on='PESEL_Pacjenta', right_on='PESEL', how='left')
    
    # Wyświetlanie listy
    for idx, row in merged.iterrows():
        status_kolor = "🔴 PRZETERMINOWANE" if row['DataKolejnegoBadania'] < dzis else "🟡 KOŃCZY SIĘ"
        
        with st.expander(f"{status_kolor} | {row['Nazwisko']} {row['Imie']} (Wygasa: {row['DataKolejnegoBadania']})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Pacjent:** {row['Imie']} {row['Nazwisko']}")
                st.write(f"**Telefon:** {row['Telefon']}")
                st.write(f"**PESEL:** {row['PESEL_Pacjenta']}")
                
                # Przycisk do szybkiego kopiowania gotowej treści SMS
                tresc_sms = f"Dzien dobry, przypominamy o konczacym sie terminie badan Medycyny Pracy ({row['DataKolejnegoBadania']}). Prosimy o kontakt w celu umowienia wizyty. Gabinet Lubon."
                st.text_area("Treść przypomnienia (do skopiowania):", value=tresc_sms, height=80, key=f"sms_{idx}")
            
            with col2:
                # Obliczanie ile dni zostało lub o ile przekroczono
                dni = (row['DataKolejnegoBadania'] - dzis).days
                if dni < 0:
                    st.error(f"Po terminie o {abs(dni)} dni")
                else:
                    st.warning(f"Zostało {dni} dni")
                
                # Przycisk do oznaczenia jako "Powiadomiony" (opcjonalnie do rozbudowy w przyszłości)
                if st.button("Oznacz jako powiadomiony", key=f"btn_{idx}"):
                    st.success("Zapisano kontakt (funkcja symulowana)")

# --- STATYSTYKI OGÓLNE ---
st.divider()
st.subheader("📊 Analiza bazy orzeczeń")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Wszystkie orzeczenia", len(df_orzeczenia))
with c2:
    st.metric("Aktywne badania", len(df_latest[df_latest['DataKolejnegoBadania'] > za_30_dni]))
with c3:
    st.metric("Do odnowienia", len(wygasajace))
