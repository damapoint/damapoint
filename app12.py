import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
from google.oauth2.service_account import Credentials

# Ottieni il percorso delle credenziali dalla variabile d'ambiente
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if credentials_path:
    # Usa il percorso per autenticarti
    credentials = Credentials.from_service_account_file(credentials_path)
else:
    print("La variabile d'ambiente GOOGLE_APPLICATION_CREDENTIALS non è impostata.")
# Dati degli utenti per l'autenticazione
user_data = {
    'damapoint1': {'password': 'dama321', 'istituto': 'DamaPoint - Vomero, Via Kerbaker 92'},
    'damapoint2': {'password': 'dama322', 'istituto': 'DamaPoint -  Portici, P.zzale Brunelleschi 21'},
    'damapoint3': {'password': 'dama323', 'istituto': 'DamaPoint - Nocera, Via Roma 70'},
    'damapoint4': {'password': 'dama324', 'istituto': 'DamaPoint - Benevento, C.so Vittore Emanuele III 24'},
    'damapoint5': {'password': 'dama325', 'istituto': 'DamaPoint  - Torre Annunziata, C.so Umberto I 209'},
    'damapoint6': {'password': 'dama326', 'istituto': 'DamaPoint - Nola, Via Circumvallazione 12/14'},
    'damapoint7': {'password': 'dama327', 'istituto': 'DamaPoint - Salerno, Corso Giuseppe Garibaldi 217'},
    'damapoint8': {'password': 'dama328', 'istituto': 'DamaPoint - Scafati, C.so Nazionale 454'},
    'damapoint9': {'password': 'dama329', 'istituto': 'Damapoint - Castellammare, Via Roma 15'},
    'damapoint10': {'password': 'dama330', 'istituto': 'DamaPoint - Chiaia, Via Arcoleo 35'},
    'damapoint11': {'password': 'dama331', 'istituto': 'DamaPoint - San Giuseppe Vesuviano, C.so Emanuele 16'},
    'damapoint12': {'password': 'dama332', 'istituto': "DamaPoint - Cava De' Tirreni, C.so Principe Amedeo 5"},
    'damapoint13': {'password': 'dama333', 'istituto': 'DamaPoint - Battipaglia, Via Roma 52'},
    'damapoint14': {'password': 'dama334', 'istituto': 'DamaPoint - Pomigliano, Via F. Terracciano  119'}
}

# Funzione per connettersi a Google Sheets
def connect_to_gsheets(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file('credentials.json', scopes=scope)
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(sheet_url).sheet1
    return sheet

# Funzione per ottenere i dati filtrati da Google Sheets
def get_filtered_data(sheet):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    required_columns = ['Nome', 'Cognome', 'Telefono', 'Servizio richiesto', 'Presentato/a?', 'Importo Pagato', 'Istituto di origine']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"La colonna '{col}' non esiste nel foglio Google Sheets.")
            return None

    df['Telefono'] = df['Telefono'].astype(str).apply(lambda x: f"{x[:3]} {x[3:6]} {x[6:]}")
    return df[required_columns]

# Funzione per aggiornare i dati nel foglio Google Sheets
def update_lead(sheet, original_df, filtered_row, came_to_appointment, payment_amount):
    original_row = original_df.loc[
        (original_df['Nome'] == filtered_row['Nome']) & (original_df['Cognome'] == filtered_row['Cognome'])
    ].index[0] + 2  # Regola per l'intestazione

    sheet.update_cell(original_row, 19, came_to_appointment)  # Aggiorna la colonna S (19)
    sheet.update_cell(original_row, 20, payment_amount)       # Aggiorna la colonna T (20)

# Funzione principale con l'interfaccia utente
def main():
    st.title("Benvenuti nel portale Tracciamento Leads | Dama Point")
    sheet_url = 'https://docs.google.com/spreadsheets/d/14zGUrYNs9uHiM84C4oRG79kVHag2FZ2YzqvvrkIGzlY/edit?gid=1767112410'

    sheet = connect_to_gsheets(sheet_url)
    original_data = get_filtered_data(sheet)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Accedi"):
            if username in user_data and user_data[username]['password'] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login effettuato con successo!")
            else:
                st.error("Credenziali errate. Riprova.")
    else:
        st.subheader(f"Benvenuto, Dama Point")

        if original_data is not None:
            # Normalizza il nome dell'istituto dell'utente loggato
            istituto_di_origine = user_data[st.session_state.username]['istituto'].strip().lower()
            original_data['istituto_normalizzato'] = original_data['Istituto di origine'].str.strip().str.lower()

            # Filtra i dati in base all'istituto di origine normalizzato
            user_data_filtered = original_data[original_data['istituto_normalizzato'] == istituto_di_origine]

            search_term = st.text_input("Cerca per Nome o Cognome:")
            filtered_data = user_data_filtered

            if search_term:
                filtered_data = filtered_data[
                    filtered_data['Nome'].str.contains(search_term, case=False) | 
                    filtered_data['Cognome'].str.contains(search_term, case=False)
                ]

            if not filtered_data.empty:
                st.write("Leads con possibilità di modifica:")
                for idx, row in filtered_data.iterrows():
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1.5, 1.5, 1.5, 1.5])  # Larghezza delle colonne

                    with col1:
                        st.markdown("**Nome**")
                        st.text_input(
                            "",
                            value=row['Nome'],
                            key=f"nome_{idx}",
                            disabled=True
                        )
                    with col2:
                        st.markdown("**Cognome**")
                        st.text_input(
                            "",
                            value=row['Cognome'],
                            key=f"cognome_{idx}",
                            disabled=True
                        )
                    with col3:
                        st.markdown("**Telefono**")
                        st.text_input(
                            "",
                            value=row['Telefono'],
                            key=f"telefono_{idx}",
                            disabled=True
                        )
                    with col4:
                        st.markdown("**Servizio richiesto**")
                        st.text_input(
                            "",
                            value=row['Servizio richiesto'],
                            key=f"servizio_{idx}",
                            disabled=True
                        )
                    with col5:
                        st.markdown("**Presentato/a?**")
                        came_to_appointment = st.selectbox(
                            "",
                            options=["Sì", "No"],
                            index=0 if row['Presentato/a?'] == "Sì" else 1,
                            key=f"came_{idx}"
                        )
                    with col6:
                        st.markdown("**Importo Pagato**")
                        payment_amount = st.text_input(
                            "",
                            value=row['Importo Pagato'],
                            key=f"pay_{idx}"
                        )

                    if st.button(f"Aggiorna {row['Nome']}", key=f"update_{idx}"):
                        update_lead(sheet, original_data, row, came_to_appointment, payment_amount)
                        st.success(f"Dati aggiornati per {row['Nome']}")

                    st.markdown("---")
            else:
                st.write("Nessun lead trovato.")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ''
            st.success("Sei stato disconnesso.")

if __name__ == "__main__":
    main()
