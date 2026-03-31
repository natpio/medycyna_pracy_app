import streamlit as st
import pandas as pd
import io
from datetime import datetime
from db_service import get_data_as_df

st.set_page_config(page_title="Żelazny Backup", page_icon="💾", layout="centered")

st.markdown("# 💾 Żelazny Backup Systemu")
st.write("Eksportuj całą bazę danych do jednego, bezpiecznego pliku Excel (.xlsx).")

st.info("""
**Dlaczego warto robić kopię zapasową?**
1. Zabezpieczenie przed przypadkowym usunięciem danych w arkuszach Google.
2. Możliwość pracy analitycznej w Excelu/OpenOffice.
3. Archiwizacja dokumentacji medycznej zgodnie z wymogami prawnymi na własnym nośniku.
""")

# Lista wszystkich arkuszy do zarchiwizowania
ARKUSZE_DO_KOPII = [
    "Pacjenci", 
    "Wizyty", 
    "Orzeczenia", 
    "Firmy", 
    "Stanowiska", 
    "Slownik_Badan"
]

if st.button("🚀 PRZYGOTUJ PEŁNĄ KOPIĘ ZAPASOWĄ", type="primary", use_container_width=True):
    try:
        # Tworzymy bufor w pamięci RAM dla pliku Excel
        buffer = io.BytesIO()
        
        with st.spinner("Pobieranie danych ze wszystkich modułów..."):
            # Inicjalizacja writera Excela
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                for nazwa_arkusza in ARKUSZE_DO_KOPII:
                    # Pobranie danych przez db_service
                    df = get_data_as_df(nazwa_arkusza)
                    
                    if not df.empty:
                        # Zapisanie każdego DF do osobnej zakładki w Excelu
                        df.to_excel(writer, sheet_name=nazwa_arkusza, index=False)
                        
                        # Automatyczne dopasowanie szerokości kolumn (bajer estetyczny)
                        worksheet = writer.sheets[nazwa_arkusza]
                        for i, col in enumerate(df.columns):
                            column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                            worksheet.set_column(i, i, column_len)
                    else:
                        # Jeśli arkusz jest pusty, tworzymy pustą zakładkę z nagłówkiem
                        pd.DataFrame(columns=["Brak danych"]).to_excel(writer, sheet_name=nazwa_arkusza, index=False)

            # Przygotowanie nazwy pliku z datą i godziną
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"BACKUP_MedycynaPracy_{timestamp}.xlsx"
            
            st.success(f"✅ Kopia zapasowa gotowa! Zawiera {len(ARKUSZE_DO_KOPII)} zakładek.")
            
            # Przycisk pobierania wygenerowanego pliku
            st.download_button(
                label="📥 POBIERZ PLIK BACKUPU (.XLSX)",
                data=buffer.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.warning("⚠️ Pamiętaj: Przechowuj ten plik w bezpiecznym miejscu (np. na szyfrowanym dysku). Zawiera on wrażliwe dane medyczne i osobowe (RODO).")

    except Exception as e:
        st.error(f"Wystąpił błąd podczas generowania kopii: {e}")

st.divider()
st.caption("System MedycynaPracy v1.0 | Moduł Bezpieczeństwa danych")
