"""
Identidade visual do Painel SG1/DEC.

Direção: painel de plantão/situação institucional (não um dashboard SaaS
genérico) — fundo azul-marinho profundo, painéis em "ardósia", detalhes
em latão/dourado envelhecido para o que precisa de destaque (a chefia em
exercício), tipografia condensada (Oswald) no cabeçalho para lembrar
placas e crachás, e uma fonte monoespaçada (JetBrains Mono) reservada
para dados que mudam — relógio e horários — reforçando que aquilo é
"informação ao vivo".
"""
import streamlit as st

COLORS = {
    "bg": "#0E1826",
    "panel": "#16243A",
    "panel_alt": "#1D2E48",
    "border": "#2A3B54",
    "text": "#ECEFF4",
    "text_dim": "#8CA0B8",
    "gold": "#C6A15B",
    "presente": "#3E9161",
    "reuniao": "#C0902E",
    "ausente": "#B4453F",
}

STATUS_CORES = {
    "Presente": COLORS["presente"],
    "Em Reunião": COLORS["reuniao"],
    "Ausente": COLORS["ausente"],
}


def inject_global_css() -> None:
    st.markdown(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

    :root {{
        --bg: {COLORS['bg']};
        --panel: {COLORS['panel']};
        --panel-alt: {COLORS['panel_alt']};
        --border: {COLORS['border']};
        --text: {COLORS['text']};
        --text-dim: {COLORS['text_dim']};
        --gold: {COLORS['gold']};
        --presente: {COLORS['presente']};
        --reuniao: {COLORS['reuniao']};
        --ausente: {COLORS['ausente']};
    }}

    html, body {{
        overflow: hidden;
        height: 100%;
    }}

    [data-testid="stAppViewContainer"], .main {{
        background: var(--bg) !important;
        color: var(--text);
        font-family: 'Inter', sans-serif;
        overflow: hidden;
    }}

    .block-container {{
        padding-top: 0.8rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100% !important;
    }}

    h1, h2, h3, h4 {{
        font-family: 'Oswald', sans-serif !important;
        letter-spacing: 0.02em;
        color: var(--text) !important;
    }}

    [data-testid="stSidebar"] {{
        background: var(--panel) !important;
        border-right: 1px solid var(--border);
    }}
    [data-testid="stSidebar"] * {{
        color: var(--text);
    }}

    hr {{ border-color: var(--border) !important; }}

    /* ---- Cabeçalho / relógio ---- */
    .eyebrow {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        letter-spacing: 0.14em;
        color: var(--gold);
        text-transform: uppercase;
        margin-bottom: 8px;
    }}

    .relogio {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        color: var(--text);
        text-align: right;
        letter-spacing: 0.03em;
        line-height: 1.1;
    }}
    .relogio-data {{
        text-align: right;
        color: var(--text-dim);
        font-size: 12px;
        letter-spacing: 0.05em;
    }}

    /* ---- Painéis principais (via st.container(key=...)) ---- */
    .st-key-painel_chefia, .st-key-painel_agenda, .st-key-painel_aniversarios {{
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 18px 22px;
        min-height: 74vh;
    }}

    .st-key-agenda_scroll, .st-key-aniversarios_scroll {{
        max-height: 56vh;
        overflow-y: auto;
        padding-right: 4px;
    }}
    .st-key-agenda_scroll::-webkit-scrollbar,
    .st-key-aniversarios_scroll::-webkit-scrollbar {{
        width: 6px;
    }}
    .st-key-agenda_scroll::-webkit-scrollbar-thumb,
    .st-key-aniversarios_scroll::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 3px;
    }}

    /* ---- Crachá de foto da chefia (anel colorido = status) ---- */
    .st-key-foto_badge_presente, .st-key-foto_badge_reuniao, .st-key-foto_badge_ausente {{
        width: 132px;
        margin: 6px auto 14px auto;
        border-radius: 50%;
        overflow: hidden;
        aspect-ratio: 1 / 1;
    }}
    .st-key-foto_badge_presente {{ border: 4px solid var(--presente); }}
    .st-key-foto_badge_reuniao {{ border: 4px solid var(--reuniao); }}
    .st-key-foto_badge_ausente {{ border: 4px solid var(--ausente); }}
    .st-key-foto_badge_presente img, .st-key-foto_badge_reuniao img, .st-key-foto_badge_ausente img {{
        object-fit: cover;
    }}

    /* ---- Linhas de tarefa ---- */
    .tarefa-linha {{
        font-size: 14.5px;
        padding: 6px 0;
        border-bottom: 1px solid var(--border);
    }}
    .tarefa-hora {{
        font-family: 'JetBrains Mono', monospace;
        color: var(--gold);
        font-size: 12.5px;
        margin-right: 10px;
    }}
    .tarefa-concluida {{
        text-decoration: line-through;
        opacity: 0.42;
    }}

    /* ---- Cartões de aniversário ---- */
    .aniversario-card {{
        background: var(--panel-alt);
        border: 1px solid var(--border);
        border-left: 3px solid var(--gold);
        border-radius: 6px;
        padding: 9px 12px;
        margin-bottom: 8px;
        font-size: 14px;
    }}
    .aniversario-data {{
        color: var(--text-dim);
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        margin-top: 2px;
    }}

    /* Botão de abrir/fechar a sidebar (dentro do componente HTML) */
    .btn-menu {{
        background: var(--panel-alt);
        border: 1px solid var(--border);
        color: var(--text);
        border-radius: 6px;
        width: 38px;
        height: 38px;
        font-size: 18px;
        cursor: pointer;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )
