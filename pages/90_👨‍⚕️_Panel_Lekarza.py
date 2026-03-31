import streamlit as st
import datetime
import pandas as pd
from db_service import get_data_as_df, add_orzeczenie_to_db, apply_pro_style

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Panel Lekarza", page_icon="👨‍⚕️", layout="wide")

# --- URUCHOMIENIE STYLU PRO ---
apply_pro_style()

st.markdown("# 👨‍⚕️ Gabinet Orzecznika")

# --- KROK 2: FRAGMENT LIVE - AUTOMATYCZNY LICZNIK KOLEJKI ---
@st.fragment(run_every="30s")
def live_queue_indicator():
    """Automatycznie odświeżany wskaźnik pacjentów w poczekalni."""
    # Pobranie świeżych danych o wizytach
    df_wizyty_live = get_data_as_df("Wizyty")
    
    if not df_wizyty_live.empty:
        # Filtrowanie pacjentów ze statusem 'Zaplanowana'
        kolejka = df_wizyty_live[df_wizyty_live['Status'] == 'Zaplanowana']
        liczba_oczekujacych = len(kolejka)
        
        if liczba_oczekujacych > 0:
            # Powiadomienie typu "toast" w rogu ekranu
            st.toast(f"Poczekalnia: {liczba_oczekujacych} pacjentów", icon="🔔")
            
            # Wizualny baner informacyjny
            st.markdown(f"""
                <div style="background: #fff7ed; padding: 16px; border-radius: 12px; border: 1px solid #ffedd5; margin-bottom: 25px; display: flex; align-items: center; gap: 15px;">
                    <span style="font-size: 24px;">🚨</span>
                    <div>
                        <p style="margin: 0; color: #9a3412; font-weight: 800; font-size: 1.1rem;">Pacjenci w poczekalni: {liczba_oczekujacych}</p>
                        <p style="margin: 0; color: #c2410c; font-size: 0.85rem;">Lista odświeża się automatycznie w tle co 30 sekund.</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.success("🎉 Świtna robota! Brak oczekujących pacjentów w poczekalni.")
    else:
        st.info("Brak zarejestrowanych wizyt w systemie.")

# Wywołanie wskaźnika na górze strony
live_queue_indicator()

# --- 2. POBIERANIE DANYCH DO FORMULARZA ---
df_wizyty = get_data_as_df("Wizyty")
df_pacjenci = get_data_as_df("Pacjenci")
df_slownik = get_data_as_df("Slownik_Badan")

# Filtrowanie pacjentów w poczekalni (status: Zaplanowana) do formularza
zaplanowane = df_wizyty[df_wizyty['Status'] == 'Zaplanowana'] if not df_wizyty.empty else pd.DataFrame()

if zaplanowane.empty:
    st.stop() # Zatrzymujemy renderowanie formularza, jeśli nikogo nie ma

st.subheader("Bieżąca kolejka pacjentów")

# Przygotowanie listy do wyboru pacjenta
wizyty_dict = {
    f"{row['DataWizyty']} | {row['Godzina'] if 'Godzina' in row else ''} | PESEL: {row['PESEL_Pacjenta']} ({row['TypBadania']})": row['ID_Wizyty'] 
    for _, row in zaplanowane.iterrows()
}

wybrana_wizyta_label = st.selectbox("Wybierz pacjenta z listy, aby rozpocząć badanie:", options=list(wizyty_dict.keys()))
id_wizyty_wybranej = wizyty_dict[wybrana_wizyta_label]

# Pobranie danych wybranej wizyty i pacjenta
wizyta = zaplanowane[zaplanowane['ID_Wizyty'].astype(str) == str(id_wizyty_wybranej)].iloc[0]
pacjent = df_pacjenci[df_pacjenci['PESEL'].astype(str) == str(wizyta['PESEL_Pacjenta'])].iloc[0]

# --- 3. WIDOK BADANIA I FORMULARZ ORZECZNICZY ---
st.divider()
c1, c2 = st.columns([1, 1.5])

with c1:
    st.markdown("### 👤 Dane Pacjenta")
    st.write(f"**Imię i Nazwisko:** {pacjent['Imie']} {pacjent['Nazwisko']}")
    st.write(f"**PESEL:** {pacjent['PESEL']}")
    st.write(f"**Rodzaj badania:** {wizyta['TypBadania']}")
    
    st.info(f"**📋 Notatki ze skierowania (Stanowisko / Zagrożenia):**\n\n{wizyta['Notatki']}")

with c2:
    st.markdown("### 🩺 Treść Orzeczenia")
    
    with st.form("orzeczenie_form"):
        decyzja = st.radio(
            "Wynik badania / Decyzja orzecznicza:",
            ("Zdolny do pracy", "Zdolny z ograniczeniami", "Niezdolny do pracy"),
            index=0
        )
        
        # Automatyczne sugerowanie daty kolejnego badania (np. za rok)
        domyslna_data = datetime.date.today() + datetime.timedelta(days=365)
        data_kolejnego = st.date_input("Termin kolejnego badania / Ważność orzeczenia do:", value=domyslna_data)
        
        uwagi_lek = st.text_area("Wnioski lekarza / Uwagi / Zalecenia / Ograniczenia:", height=120)
        
        st.markdown("---")
        st.subheader("🔐 Autoryzacja i Podpis Elektroniczny")
        st.write("Wprowadzenie kodu PIN wygeneruje unikalną pieczęć cyfrową (Hash SHA-256) potwierdzającą autentyczność dokumentu.")
        
        pin_input = st.text_input("Wprowadź PIN Lekarza (autoryzacja zapisu):", type="password", help="Kod potrzebny do wystawienia certyfikatu")

        submit_btn = st.form_submit_button("Podpisz i Zakończ Wizytę", type="primary", use_container_width=True)
        
        if submit_btn:
            if not pin_input:
                st.error("Błąd: Dokument musi zostać zautoryzowany kodem PIN.")
            else:
                with st.spinner("Generowanie podpisu cyfrowego SHA-256 i zamykanie wizyty..."):
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
                    st.info("Dokument został zabezpieczony. Recepcja może teraz go wydrukować.")
                    # Czyścimy cache, aby panel recepcji i dashboard uaktualniły się natychmiast
                    st.cache_data.clear()
