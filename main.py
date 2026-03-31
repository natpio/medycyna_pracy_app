import streamlit as st
import pandas as pd
from db_service import get_data_as_df, apply_pro_style

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Gabinet Medycyny Pracy",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- URUCHOMIENIE STYLU PRO ---
# Ta jedna funkcja ładuje Twój czysty kod z pliku style.css
apply_pro_style()

# --- GŁÓWNY DASHBOARD ---
st.title("🏥 System Obsługi Gabinetu")
st.markdown("### Witaj w panelu dowodzenia.")
st.info("Wybierz moduł z menu po lewej stronie, aby rozpocząć pracę.")

# --- SZYBKI PODGLĄD ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📅 Ostatnio dodane wizyty")
    df_wizyty = get_data_as_df("Wizyty")
    if not df_wizyty.empty:
        # Pokazujemy tylko kilka kluczowych kolumn, żeby wyglądało to czytelnie
        df_display = df_wizyty[['DataWizyty', 'TypBadania', 'Status']].tail(5)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.write("Brak zaplanowanych wizyt.")

with col2:
    st.subheader("📊 Statystyki bazy")
    df_pacjenci = get_data_as_df("Pacjenci")
    df_firmy = get_data_as_df("Firmy")
    
    st.metric("Pacjenci w bazie", len(df_pacjenci))
    st.metric("Obsługiwane Firmy", len(df_firmy))

st.divider()
st.caption("MedycynaPracy OS v2.0 | Wersja Autoryzowana")
