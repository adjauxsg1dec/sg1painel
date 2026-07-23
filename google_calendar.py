"""Integração com o Google Calendar (somente leitura)."""
import datetime
from typing import Any, List, Dict

import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CALENDAR_ID = "chefe.sg1.dec@gmail.com"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_service() -> Any:
    creds = None
    if "google_token" in st.secrets:
        token_info = dict(st.secrets["google_token"])
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "Bloco 'google_token' ausente ou inválido em .streamlit/secrets.toml"
            )

    return build("calendar", "v3", credentials=creds)


@st.cache_data(ttl=45, show_spinner=False)
def get_todays_events() -> List[Dict]:
    """Eventos do dia atual. Cache de 45s para não sobrecarregar a API do
    Google durante o polling automático do painel (que relê a cada poucos
    segundos para manter as sessões sincronizadas)."""
    service = get_calendar_service()
    hoje = datetime.datetime.now().astimezone()
    inicio_dia = hoje.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    fim_dia = hoje.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=inicio_dia,
        timeMax=fim_dia,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return events_result.get("items", [])
