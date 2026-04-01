import streamlit as st
import pandas as pd
from datetime import datetime
from db_service import get_data_as_df, update_record, apply_pro_style

# --- KONFIGURACJA ---
st.set_page_config(page_title="Dashboard Recepcji", page_icon="📊", layout="wide")
apply_pro_style()

st.markdown("# 📊 Dashboard Recepcji")
st.write("Zarządzanie ruchem pacjentów i statusami wizyt w czasie rzeczywistym.")

# --- POBIERANIE DANYCH ---
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")

if df_wizyty.empty:
    st.info("Brak zarejestrowanych wizyt w bazie.")
    st.stop()

# --- LOGIKA KOLOROWANIA (Poprawiona na .map()) ---
def color_status(val):
    color = '#f1f5f9' # domyślny
    if val == 'Zaplanowana': color = '#fef3c7' # żółty
    elif val == 'Zakończona': color = '#d1fae5' # zielony
    elif val == 'Anulowana': color = '#fee2e2' # czerwony
    elif val == 'Nieobecny': color = '#e2e8f0' # szary
    return f'background-color: {color}'

# --- FILTROWANIE ---
col_f1, col_f2 = st.columns(2)
with col_f1:
    search_pesel = st.text_input("🔍 Szukaj po PESEL pacjenta:")
with col_f2:
    status_filter = st.multiselect("Filtruj statusy:", 
                                  options=['Zaplanowana', 'Zakończona', 'Anulowana', 'Nieobecny'],
                                  default=['Zaplanowana'])

# Przygotowanie widoku
widok = df_wizyty.copy()
if search_pesel:
    widok = widok[widok['PESEL_Pacjenta'].astype(str).str.contains(search_pesel)]
if status_filter:
    widok = widok[widok['Status'].isin(status_filter)]

# Sortowanie: najnowsze na górze
widok = widok.sort_values(by="ID_Wizyty", ascending=False)

# --- WYŚWIETLANIE TABELI ---
st.subheader("Lista wizyt")
# Używamy .map() zamiast applymap() dla zgodności z nowym Pandas
st.dataframe(
    widok.style.map(color_status, subset=['Status']), 
    use_container_width=True, 
    hide_index=True
)

st.divider()

# --- SEKCJA ZARZĄDZANIA WIZYTĄ (NOWOŚĆ) ---
st.subheader("⚡ Szybka zmiana statusu")
st.write("Wybierz wizytę, aby zmienić jej stan (np. gdy pacjent odwoła wizytę).")

# Tylko wizyty zaplanowane można anulować/zmienić na nieobecny
wizyty_do_zmiany = widok[widok['Status'] == 'Zaplanowana']

if not wizyty_do_zmiany.empty:
    with st.expander("Zmień status wybranej wizyty"):
        # Przygotowanie listy do wyboru: "Data - Godzina - PESEL"
        opcje_wizyt = {
            f"{row['DataWizyty']} {row['Godzina']} (PESEL: {row['PESEL_Pacjenta']})": row['ID_Wizyty'] 
            for _, row in wizyty_do_zmiany.iterrows()
        }
        wybrana_label = st.selectbox("Wybierz wizytę z listy:", options=list(opcje_wizyt.keys()))
        wybrane_id = opcje_wizyt[wybrana_label]
        
        c1, c2, c3 = st.columns(3)
        
        if c1.button("❌ ANULUJ WIZYTĘ", use_container_width=True, type="secondary"):
            if update_record("Wizyty", "ID_Wizyty", wybrane_id, {"Status": "Anulowana"}):
                st.success("Wizyta została anulowana.")
                st.rerun()
        
        if c2.button("🚫 PACJENT NIEPRZYBYŁ", use_container_width=True, type="secondary"):
            if update_record("Wizyty", "ID_Wizyty", wybrane_id, {"Status": "Nieobecny"}):
                st.warning("Oznaczono brak obecności pacjenta.")
                st.rerun()
                
        if c3.button("🔄 PRZYWRÓĆ DO ZAPLANOWANYCH", use_container_width=True):
             # (Opcjonalnie, gdyby ktoś się pomylił)
             if update_record("Wizyty", "ID_Wizyty", wybrane_id, {"Status": "Zaplanowana"}):
                st.info("Przywrócono status Zaplanowana.")
                st.rerun()
else:
    st.caption("Brak wizyt o statusie 'Zaplanowana' do edycji.")
