import os 
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Carichiamo le variabili d'ambiente dal file .env
load_dotenv()

# Configura Airtable
AIRTABLE_API_KEY = "patVvkwrcLfpSQFlN.6284937647e50b10895d44cd1c0829a183bfd24d488be47ca84c9538f90938e3"
BASE_ID = 'appGyD33GmhodfxlW'  # Il tuo Base ID
TABLE_ID = 'tblCPYQNiEie2tEyy'  # ID della tua tabella LEADS NUOVI

# Definiamo le colonne che vogliamo visualizzare
view_columns = ['Nome', 'Cognome', 'Servizio richiesto', 'Telefono', 'Presentato/a?', 'Importo pagato']

# Funzione per connettersi a Airtable e ottenere i dati con gestione della paginazione
def connect_to_airtable():
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    records = []
    offset = None  # Variabile per tracciare l'offset per la paginazione
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            
            # Aggiungiamo l'ID di ogni record ai dati
            for record in data.get('records', []):
                fields = record['fields']
                fields['id'] = record['id']  # Aggiungiamo l'ID del record
                records.append(fields)
            
            # Controlla se c'è un offset per la prossima pagina
            offset = data.get('offset', None)
            
            # Se non ci sono più pagine da recuperare, esci dal ciclo
            if not offset:
                break
        else:
            st.error(f"Errore nel recupero dei dati da Airtable: {response.status_code}")
            return None
    
    # Convertiamo i record in un DataFrame Pandas
    df = pd.DataFrame(records)

    df = df[df['Esito telefonata'] == 'App. Fissato']

    # Assicuriamoci che le colonne 'Presentato/a?' e 'Importo pagato' siano presenti, anche se vuote
    df['Presentato/a?'] = df.get('Presentato/a?', False)  # Predefinito False
    df['Importo pagato'] = df.get('Importo pagato', 0.0)  # Predefinito 0.0
    
    # Selezioniamo solo le colonne specificate in 'view_columns'
    return df[view_columns + ['id']]  # Includiamo l'ID per l'aggiornamento

# Funzione per aggiornare i record in Airtable
def update_airtable_record(record_id, updated_fields):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "fields": updated_fields
    }

    response = requests.patch(url, json=data, headers=headers)

    if response.status_code == 200:
        st.success(f"Cliente aggiornato correttamente.")
    else:
        st.error(f"Errore durante l'aggiornamento del record {record_id}: {response.text}")

# Funzione Streamlit per visualizzare e modificare i dati
def app():
    st.title("Dama point | Gestione outcome appuntamento")

    # Ottieni i dati da Airtable
    df = connect_to_airtable()

    if df is not None:
        # Barra di ricerca per nome o cognome
        search_query = st.text_input("Cerca cliente per Nome o Cognome")

        # Filtriamo i dati in base alla ricerca
        if search_query:
            filtered_df = df[df['Nome'].str.contains(search_query, case=False) | df['Cognome'].str.contains(search_query, case=False)]
            
            if not filtered_df.empty:
                st.write(f"**{len(filtered_df)} CLIENTI TROVATI:**")

                # Mostra i clienti trovati con le colonne "Nome", "Cognome", "Servizio richiesto", e "Telefono"
                for index, row in filtered_df.iterrows():
                    st.write(f"**{row['Nome']} {row['Cognome']}**")
                    st.write(f"Servizio richiesto: {row['Servizio richiesto']}")
                    st.write(f"Telefono: {row['Telefono']}")

                    # Inizializza i valori di session state solo se non sono già presenti
                    if f"presentato_{index}" not in st.session_state:
                        st.session_state[f"presentato_{index}"] = row['Presentato/a?']
                    
                    if f"importo_{index}" not in st.session_state:
                        st.session_state[f"importo_{index}"] = row['Importo pagato']

                    # Creiamo un form per impedire l'esecuzione automatica del codice
                    with st.form(key=f"form_{index}"):
                        # Non modifichiamo session_state, usiamo direttamente il valore
                        col1, col2 = st.columns(2)

                        # Valore iniziale del checkbox e del numero di input preso dallo stato della sessione
                        presentato_a = col1.checkbox("Presentato/a?", value=st.session_state[f"presentato_{index}"], key=f"presentato_{index}_widget")
                        importo_pagato = col2.number_input("Importo pagato", min_value=0.0, value=st.session_state[f"importo_{index}"], key=f"importo_{index}_widget")

                        # Pulsante per inviare il form e aggiornare i dati
                        submit_button = st.form_submit_button(f"Aggiorna {row['Nome']} {row['Cognome']}")

                        if submit_button:
                            # Aggiorna lo stato della sessione solo quando viene cliccato il pulsante "Aggiorna"
                            st.session_state[f"presentato_{index}"] = presentato_a
                            st.session_state[f"importo_{index}"] = importo_pagato

                            # Prepara il dizionario con i campi aggiornati
                            updated_fields = {
                                'Presentato/a?': st.session_state[f"presentato_{index}"],
                                'Importo pagato': st.session_state[f"importo_{index}"]
                            }

                            # Usa l'ID del record per aggiornare i dati in Airtable
                            record_id = row['id']
                            update_airtable_record(record_id, updated_fields)

                            

                    # Aggiungiamo una linea divisoria tra un cliente e l'altro
                    st.divider()
            else:
                st.write("Nessun cliente trovato.")
    else:
        st.write("Nessun record trovato.")







if __name__ == "__main__":
    app()