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
    """Cria o banco de dados e as tabelas necessárias se não existirem."""
    conn = sqlite3.connect('agenda_checks.db')
    c = conn.cursor()
    
    # 1. Cria a tabela das tarefas concluídas do calendário
    c.execute('''CREATE TABLE IF NOT EXISTS completed_events (event_id TEXT PRIMARY KEY)''')
    
    # 2. Cria a tabela de status do chefe
    c.execute('''CREATE TABLE IF NOT EXISTS chefe_status (id INTEGER PRIMARY KEY, status TEXT)''')
    
    # CORREÇÃO AQUI: Usa SELECT para verificar se a tabela está vazia
    c.execute("SELECT count(*) FROM chefe_status")
    if c.fetchone()[0] == 0:
        # Se estiver vazia, define o primeiro status padrão como 'Presente'
        c.execute("INSERT INTO chefe_status (id, status) VALUES (1, 'Presente')")
    
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

def get_chefe_status():
    """Procura o status atual do chefe na base de dados global."""
    conn = sqlite3.connect('agenda_checks.db')
    c = conn.cursor()
    c.execute("SELECT status FROM chefe_status WHERE id=1")
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Presente"

def update_chefe_status(novo_status):
    """Atualiza o status do chefe na base de dados global."""
    conn = sqlite3.connect('agenda_checks.db')
    c = conn.cursor()
    c.execute("UPDATE chefe_status SET status=? WHERE id=1", (novo_status,))
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
    # Definição de página única
    st.set_page_config(page_title="Agenda Check-in", page_icon="images/LogoDec.png", layout="wide")

    col_title_1, col_title_2, col_title_3 = st.columns([1, 6, 1], vertical_alignment="center")
    col_title_1.image("images/LogoDec.png", width=50)
    col_title_2.markdown("<h1 style='text-align: center; margin: 0;'>SG1/DEC</h1>", unsafe_allow_html=True)

    with col_title_3:
        st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
        st.image("images/LogoDec.png", width=50)
        st.markdown("</div>", unsafe_allow_html=True)

    col_principal_esquerda, col_princial_meio, col_principal_direita = st.columns([1.5, 3, 1.5])

    with col_principal_esquerda:
        # Inicializa o banco de dados e insere o status 'Presente' se for a 1ª execução
        init_db()
        
        # Procura o status atual diretamente do banco de dados criado
        status_atual = get_chefe_status()
        
        # Configura as cores do botão com base no status ATUAL do chefe
        if status_atual == "Presente":
            proximo_status = "Em Reunião"
            cor_botao = "#2ecc71"       # Verde para Presente
            cor_texto_botao = "#ffffff" # Texto Branco
        elif status_atual == "Em Reunião":
            proximo_status = "Ausente"
            cor_botao = "#f1c40f"       # Amarelo para Em Reunião
            cor_texto_botao = "#000000" # Texto Preto
        else:
            status_atual = "Ausente" # Garante conformidade de texto
            proximo_status = "Presente"
            cor_botao = "#e74c3c"       # Vermelho para Ausente
            cor_texto_botao = "#ffffff" # Texto Branco

        # Título da secção centralizado
        st.markdown("<h3 style='text-align: center;'>📍 Status da Chefia</h3>", unsafe_allow_html=True)
    
        # Foto do chefe centralizada
        sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1])
        with sub_c2:
            st.image("images/foto_chefe.jpg", use_container_width=True)
            
        # Texto informativo com o estado atual do chefe
        st.markdown(
            f"""
            <p style='text-align: center; margin-top: 10px; font-size: 16px; color: #555;'>
                O Chefe está atualmente: <br>
                <strong style='font-size: 24px; color: {cor_botao if status_atual != "Em Reunião" else "#d35400"};'>{status_atual}</strong>
            </p>
            """, 
            unsafe_allow_html=True
        )
        
        # Injeta o CSS para colorir o botão dinamicamente na tela
        st.markdown(
            f"""
            <style>
            div[data-testid="stVerticalBlock"] button {{
                background-color: {cor_botao} !important;
                color: {cor_texto_botao} !important;
                border: 1px solid {cor_botao} !important;
                font-weight: bold !important;
                font-size: 16px !important;
                padding: 10px !important;
                transition: opacity 0.2s;
            }}
            div[data-testid="stVerticalBlock"] button:hover {{
                opacity: 0.85 !important;
                color: {cor_texto_botao} !important;
            }}
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        # Botão interativo que altera a cor e atualiza para todos os acessos do site
        if st.button(f"Mudar para: {proximo_status}", use_container_width=True):
            update_chefe_status(proximo_status)
            st.rerun()

    with col_princial_meio:

        st.subheader("Agenda Diária 📅")
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

    with col_principal_direita:
        st.subheader("🎈Próximos Aniversários🎈")
    
    # Lista de exemplo com as pessoas da secção
        aniversariantes = [
            {"nome": "Sd EVANGELISTA", "data": "16/09"},
            {"nome": "Cap AGILSON", "data": "28/10"},
            {"nome": "Cel PABLO", "data": "10/11"}
        ]
    
    # Renderizar os aniversários como pequenos cartões informativos
        for pessoa in aniversariantes:
            st.markdown(
                f"""
                <div style='background-color: #111111s; padding: 10px; border-radius: 5px; margin-bottom: 8px;'>
                    <span style='font-size: 18px;'>🎈</span> <b>{pessoa['nome']}</b> - {pessoa['data']}
                </div>
                """, 
                unsafe_allow_html=True
            )


if __name__ == '__main__':
    main()
