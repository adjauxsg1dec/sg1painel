"""
Painel SG1/DEC — Chefia, Agenda e Aniversariantes
"""
import datetime
import os

import streamlit as st
import streamlit.components.v1 as components

import database as db
import style
from google_calendar import get_todays_events

LOGO_PATH = "images/LogoDec.png"
FOTO_PADRAO = "images/foto_chefe.jpg"

# =================================================================
# CONFIGURAÇÃO DA PÁGINA
# =================================================================

st.set_page_config(
    page_title="Painel SG1",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)
db.init_db()
style.inject_global_css()

# =================================================================
# CABEÇALHO
# =================================================================

@st.fragment(run_every=1)
def render_relogio() -> None:
    agora = datetime.datetime.now()
    st.markdown(
        f"<div class='relogio'>{agora.strftime('%H:%M:%S')}</div>"
        f"<div class='relogio-data'>{agora.strftime('%d/%m/%Y')}</div>",
        unsafe_allow_html=True,
    )


def render_header() -> None:
    col_logo, col_titulo, col_relogio = st.columns(
        [0.6, 3.9, 1.5], vertical_alignment="center"
    )
    
    with col_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=44)
            
    with col_titulo:
        st.markdown(
            "<div class='eyebrow'>Seção de Pessoal</div>"
            "<h1 style='margin:0;font-size:28px;'>SG1</h1>",
            unsafe_allow_html=True,
        )
        
    with col_relogio:
        render_relogio()


# =================================================================
# PAINEL — STATUS DA CHEFIA
# =================================================================
@st.fragment(run_every=4)
def render_painel_chefia() -> None:
    chefe = db.get_chefe_atual()
    status = chefe.get("status", "Presente")
    slug = db.STATUS_SLUG.get(status, "presente")
    foto = chefe.get("foto_path") or FOTO_PADRAO
    foto = foto if foto and os.path.exists(foto) else None

    with st.container(key="painel_chefia"):
        st.markdown("<div class='eyebrow'>Status da Chefia</div>", unsafe_allow_html=True)

        _, col_img, _ = st.columns([1, 1.3, 1])
        with col_img:
            with st.container(key=f"foto_badge_{slug}"):
                if foto:
                    st.image(foto, use_container_width=True)
                else:
                    st.markdown(
                        "<div style='text-align:center;font-size:40px;padding:30px 0;'>👤</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown(
            f"""
            <div style="text-align:center;">
                <div style="font-size:18px;font-weight:600;">
                    {chefe.get('posto','')} {chefe.get('nome','')}
                </div>
                <div style="margin-top:8px;font-family:'JetBrains Mono',monospace;
                            color:{style.STATUS_CORES.get(status, style.COLORS['presente'])};
                            font-size:15px;font-weight:700;letter-spacing:0.05em;">
                    {status.upper()}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        proximo = db.STATUS_SEGUINTE[status]
        if st.button(f"Alterar para: {proximo}", use_container_width=True, key="btn_status_chefe"):
            db.atualizar_status_chefe(proximo)
            st.rerun(scope="fragment")


# =================================================================
# PAINEL — AGENDA (Google Calendar + tarefas locais)
# =================================================================
@st.fragment(run_every=4)
def render_painel_agenda() -> None:
    with st.container(key="painel_agenda"):
        st.markdown("<div class='eyebrow'>Agenda do Dia</div>", unsafe_allow_html=True)
        st.markdown(
            f"<h3 style='margin:0 0 10px 0;'>{datetime.date.today().strftime('%d/%m/%Y')}</h3>",
            unsafe_allow_html=True,
        )

        tarefas = []
        try:
            for ev in get_todays_events():
                inicio = ev["start"].get("dateTime", ev["start"].get("date"))
                hora = None
                if "T" in (inicio or ""):
                    try:
                        hora = datetime.datetime.fromisoformat(
                            inicio.replace("Z", "+00:00")
                        ).strftime("%H:%M")
                    except ValueError:
                        hora = None
                tarefas.append({"id": ev["id"], "titulo": ev.get("summary", "Sem título"), "horario": hora})
        except Exception as e:
            st.warning(f"Google Calendar indisponível no momento ({e}).")

        for t in db.list_tarefas_locais():
            tarefas.append({"id": f"local-{t['id']}", "titulo": t["titulo"], "horario": t["horario"]})

        if not tarefas:
            st.info("Nenhuma tarefa para hoje.")
            return

        tarefas.sort(key=lambda x: x["horario"] or "00:00")
        concluidas = db.get_concluidas()

        with st.container(key="agenda_scroll"):
            for t in tarefas:
                concluida = t["id"] in concluidas
                col_check, col_txt = st.columns([0.35, 5], vertical_alignment="center")
                with col_check:
                    novo = st.checkbox(
                        "", value=concluida, key=f"chk_{t['id']}", label_visibility="collapsed"
                    )
                with col_txt:
                    classe = "tarefa-concluida" if concluida else ""
                    hora_exibida = t["horario"] or "Dia todo"
                    st.markdown(
                        f"<div class='tarefa-linha'><span class='tarefa-hora'>{hora_exibida}</span>"
                        f"<span class='{classe}'>{t['titulo']}</span></div>",
                        unsafe_allow_html=True,
                    )
                if novo != concluida:
                    db.set_tarefa_concluida(t["id"], novo)
                    st.rerun(scope="fragment")


# =================================================================
# PAINEL — ANIVERSARIANTES
# =================================================================

@st.fragment(run_every=10)
def render_painel_aniversarios() -> None:
    with st.container(key="painel_aniversarios"):
        st.markdown("<div class='eyebrow'>Próximos Aniversários</div>", unsafe_allow_html=True)

        proximos = db.list_proximos_aniversariantes()
        if not proximos:
            st.info("Nenhum aniversário futuro cadastrado para este ano.")
            return

        with st.container(key="aniversarios_scroll"):
            for pessoa in proximos:
                data_fmt = pessoa["proxima_data"].strftime("%d/%m")
                st.markdown(
                    f"""
                    <div class='aniversario-card'>
                        🎂 <b>{pessoa['posto']} {pessoa['nome']}</b>
                        <div class='aniversario-data'>{data_fmt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# =================================================================
# SIDEBAR — ADMINISTRAÇÃO
# =================================================================

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ⚙️ Administração")

        with st.expander("🎂 Aniversariantes", expanded=False):
            with st.form("form_aniversariante", clear_on_submit=True):
                cpf = st.text_input("CPF")
                posto = st.text_input("Posto/Graduação")
                nome = st.text_input("Nome")
                data_nasc = st.date_input(
                    "Data de Nascimento",
                    value=datetime.date(1990, 1, 1),
                    min_value=datetime.date(1930, 1, 1),
                    max_value=datetime.date.today(),
                    format="DD/MM/YYYY",
                )
                if st.form_submit_button("Adicionar", use_container_width=True):
                    if nome.strip() and posto.strip():
                        db.add_aniversariante(cpf.strip(), posto.strip(), nome.strip(), data_nasc.isoformat())
                        st.success(f"{posto} {nome} adicionado(a).")
                    else:
                        st.warning("Informe ao menos nome e posto/graduação.")

            cadastrados = db.list_aniversariantes()
            if cadastrados:
                st.caption(f"{len(cadastrados)} cadastrado(s)")
                for pessoa in cadastrados:
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"{pessoa['posto']} {pessoa['nome']}")
                    if c2.button("🗑️", key=f"del_aniv_{pessoa['id']}"):
                        db.remover_aniversariante(pessoa["id"])
                        st.rerun()

        with st.expander("📌 Agenda — Tarefa Manual", expanded=False):
            with st.form("form_tarefa", clear_on_submit=True):
                titulo = st.text_input("Descrição da tarefa")
                dia_inteiro = st.checkbox("Dia inteiro (sem horário definido)")
                hora = st.time_input(
                    "Horário", value=datetime.time(8, 0), disabled=dia_inteiro
                )
                if st.form_submit_button("Adicionar Tarefa", use_container_width=True):
                    if titulo.strip():
                        horario = None if dia_inteiro else hora.strftime("%H:%M")
                        db.add_tarefa_local(titulo.strip(), horario)
                        st.success("Tarefa adicionada à agenda.")
                    else:
                        st.warning("Informe a descrição da tarefa.")

            tarefas_locais = db.list_tarefas_locais()
            if tarefas_locais:
                st.caption(f"{len(tarefas_locais)} tarefa(s) manual(is)")
                for t in tarefas_locais:
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"{t['horario'] or 'Dia todo'} — {t['titulo']}")
                    if c2.button("🗑️", key=f"del_tarefa_{t['id']}"):
                        db.remover_tarefa_local(t["id"])
                        st.rerun()

        with st.expander("👤 Alterar Chefia", expanded=False):
            chefe_atual = db.get_chefe_atual()
            st.caption(f"Atual: {chefe_atual.get('posto','')} {chefe_atual.get('nome','')}")
            with st.form("form_chefia", clear_on_submit=True):
                novo_posto = st.text_input("Posto/Graduação")
                novo_nome = st.text_input("Nome")
                nova_foto = st.file_uploader("Foto (opcional)", type=["png", "jpg", "jpeg"])
                if st.form_submit_button("Atualizar Chefia", use_container_width=True):
                    if novo_nome.strip() and novo_posto.strip():
                        caminho_foto = None
                        if nova_foto is not None:
                            os.makedirs("images", exist_ok=True)
                            ext = nova_foto.name.split(".")[-1]
                            timestamp = int(datetime.datetime.now().timestamp())
                            caminho_foto = f"images/chefe_{timestamp}.{ext}"
                            with open(caminho_foto, "wb") as f:
                                f.write(nova_foto.getbuffer())
                        db.trocar_chefe(novo_nome.strip(), novo_posto.strip(), caminho_foto)
                        st.success(f"Chefia atualizada: {novo_posto} {novo_nome}.")
                    else:
                        st.warning("Informe nome e posto/graduação.")


# =================================================================
# ENTRY POINT
# =================================================================

def main() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    render_header()
    render_sidebar()
    st.markdown("<br>", unsafe_allow_html=True)

    col_esq, col_meio, col_dir = st.columns([1.2, 2.1, 1.2])
    with col_esq:
        render_painel_chefia()
    with col_meio:
        render_painel_agenda()
    with col_dir:
        render_painel_aniversarios()


if __name__ == "__main__":
    main()
