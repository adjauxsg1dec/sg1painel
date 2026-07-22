import streamlit as st
import sqlite3
import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Permissões que a nossa app precisa (Letra minúscula e apenas leitura)
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# -------------------------------------------------------------
# 1. FUNÇÕES DO BANCO DE DADOS (SQLite)
# -------------------------------------------------------------
def init_db():
    """Cria a tabela no SQLite para guardar as tarefas concluídas, se não existir."""
    conn = sqlite3.connect('agenda_checks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS completed_events (event_id TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def is_event_completed(event_id):
    """Verifica se um evento específico já foi marcado como concluído."""
    conn = sqlite3.connect('agenda_checks.db')
    c = conn.cursor()
    c.execute("SELECT event_id FROM completed_events WHERE event_id=?", (event_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def toggle_event_status(event_id, completed):
    """Marca ou desmarca um evento no SQLite."""
    conn = sqlite3.connect('agenda_checks.db')
    c = conn.cursor()
    if completed:
        c.execute("INSERT OR IGNORE INTO completed_events (event_id) VALUES (?)", (event_id,))
    else:
        c.execute("DELETE FROM completed_events WHERE event_id=?", (event_id,))
    conn.commit()
    conn.close()

# -------------------------------------------------------------
# 2. FUNÇÕES DO GOOGLE CALENDAR (ADAPTADO PARA PRODUÇÃO)
# -------------------------------------------------------------
def get_calendar_service():
    """Lida com a autenticação no Google através dos Secrets do Streamlit."""
    creds = None
    
    # 1. Tenta carregar as credenciais autorizadas diretamente dos Secrets do Streamlit
    if "google_token" in st.secrets:
        token_info = dict(st.secrets["google_token"])
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    
    # 2. Se o token estiver expirado mas tiver Refresh Token, tenta renovar em segundo plano
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                st.error(f"Erro ao renovar o token de acesso: {e}")
                st.stop()
        else:
            st.error("Erro de Configuração: O bloco 'google_token' não foi encontrado nos Secrets do Streamlit.")
            st.info("Gere o ficheiro 'token.json' localmente e cole as propriedades no painel do Streamlit Cloud.")
            st.stop()

    return build('calendar', 'v3', credentials=creds)

def get_todays_events(service):
    """Puxa os eventos programados para o dia de hoje de uma agenda específica."""
    hoje = datetime.datetime.now().astimezone()
    
    inicio_dia = hoje.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    fim_dia = hoje.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

    ID_DA_AGENDA_PARTILHADA = "chefe.sg1.dec@gmail.com"

    events_result = service.events().list(
        calendarId=ID_DA_AGENDA_PARTILHADA, 
        timeMin=inicio_dia, 
        timeMax=fim_dia,
        singleEvents=True, 
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])

# -------------------------------------------------------------
# 3. INTERFACE VISUAL (STREAMLIT)
# -------------------------------------------------------------
def main():
    # Definição de página única (duplicação removida)
    st.set_page_config(page_title="Agenda Check-in", page_icon="images/LogoDec.png")

    # Layout do cabeçalho corrigido
    col_title_1, col_title_2, col_title_3 = st.columns([1, 6, 1], vertical_alignment="center")

    col_title_1.image("images/LogoDec.png", width=50)
    col_title_2.markdown("<h1 style='text-align: center; margin: 0;'>Agenda Diária - SG1/DEC</h1>", unsafe_allow_html=True)

    with col_title_3:
        st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
        st.image("images/LogoDec.png", width=50)
        st.markdown("</div>", unsafe_allow_html=True)

    # Inicializar Banco de Dados SQLite
    init_db()

    # Tentar conectar ao Google Calendar utilizando st.secrets
    try:
        service = get_calendar_service()
        eventos = get_todays_events(service)
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Calendar. Verifique os Secrets configurados. Erro: {e}")
        return

    st.subheader(f"Eventos de Hoje ({datetime.date.today().strftime('%d/%m/%Y')})")

    if not eventos:
        st.info("Não tem eventos agendados para hoje na sua Google Agenda!")
        return

    # Desenhar a lista de eventos no ecrã
    for evento in eventos:
        nome_evento = evento.get('summary', 'Sem Título')
        event_id = evento['id']
        
        inicio = evento['start'].get('dateTime', evento['start'].get('date'))
        try:
            hora_formatada = datetime.datetime.fromisoformat(inicio.replace('Z', '+00:00')).strftime('%H:%M')
        except:
            hora_formatada = "Dia inteiro"

        is_done = is_event_completed(event_id)

        # Colunas reconfiguradas corretamente
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.write(f"**{hora_formatada}**")
            
        with col2:
            novo_status = st.checkbox(f"{nome_evento}", value=is_done, key=event_id)
            
            if novo_status != is_done:
                toggle_event_status(event_id, novo_status)
                st.rerun()

if __name__ == '__main__':
    main()
