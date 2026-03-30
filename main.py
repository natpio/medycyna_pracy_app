import streamlit as st
import pandas as pd
from db_service import get_data_as_df

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Gabinet Medycyny Pracy",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS DLA PROFESJONALNEGO WYGLĄDU ---
# Ukrywamy standardowe menu Streamlit i stopkę, poprawiamy nagłówki.
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {padding-top: 2rem;}
            h1 {color: #2c3e50;}
            h2 {color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px;}
            .stAlert {box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- GŁÓWNY DASHBOARD ---
st.title("🏥 System Obsługi Gabinetu")
st.markdown("### Witaj w panelu recepcji.")
st.info("Wybierz moduł z menu po lewej stronie, aby rozpocząć pracę.")

# --- SZYBKI PODGLĄD (opcjonalne) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Dzisiejsze Wizyty")
    # Tu w przyszłości można dodać filtrowanie po dzisiejszej dacie
    df_wizyty = get_data_as_df("Wizyty")
    if not df_wizyty.empty:
        st.dataframe(df_wizyty.tail(5), use_container_width=True, hide_index=True)
    else:
        st.write("Brak zaplanowanych wizyt.")

with col2:
    st.subheader("📊 Statystyki bazy")
    df_pacjenci = get_data_as_df("Pacjenci")
    df_firmy = get_data_as_df("Firmy")
    
    st.metric("Liczba Pacjentów w bazie", len(df_pacjenci))
    st.metric("Liczba obsługiwanych Firm", len(df_firmy))

st.divider()
st.caption("System Medycyny Pracy v1.0 | Połączono z Google Sheets")
