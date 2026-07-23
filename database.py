"""
Camada de acesso a dados (SQLite) do Painel SG1/DEC.

Todas as escritas usam `with sqlite3.connect(...)` para garantir commits
atômicos por operação. O SQLite lida bem com esse padrão de baixa
concorrência (múltiplas sessões do Streamlit lendo/escrevendo no mesmo
arquivo), o que é o que permite a sincronização entre navegadores: cada
sessão simplesmente relê o banco periodicamente (veja app.py).
"""
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "agenda_checks.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS chefe_atual (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nome TEXT NOT NULL DEFAULT '',
                posto TEXT NOT NULL DEFAULT '',
                foto_path TEXT,
                status TEXT NOT NULL DEFAULT 'Presente'
            )
        """)
        c.execute("SELECT COUNT(*) FROM chefe_atual")
        if c.fetchone()[0] == 0:
            c.execute(
                "INSERT INTO chefe_atual (id, nome, posto, foto_path, status) "
                "VALUES (1, ?, ?, ?, ?)",
                ("da Seção", "Chefe", "images/foto_chefe.jpg", "Presente"),
            )

        c.execute("""
            CREATE TABLE IF NOT EXISTS aniversariantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpf TEXT,
                posto TEXT,
                nome TEXT NOT NULL,
                data_nascimento TEXT NOT NULL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS tarefas_locais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                horario TEXT,
                criado_em TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS tarefas_concluidas (
                tarefa_id TEXT PRIMARY KEY,
                concluido_em TEXT
            )
        """)

        conn.commit()


# ---------------------------------------------------------------
# Chefia
# ---------------------------------------------------------------
STATUS_SEGUINTE = {
    "Presente": "Em Reunião",
    "Em Reunião": "Ausente",
    "Ausente": "Presente",
}

STATUS_SLUG = {
    "Presente": "presente",
    "Em Reunião": "reuniao",
    "Ausente": "ausente",
}


def get_chefe_atual() -> Dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM chefe_atual WHERE id = 1").fetchone()
        return dict(row) if row else {}


def atualizar_status_chefe(novo_status: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE chefe_atual SET status = ? WHERE id = 1", (novo_status,))
        conn.commit()


def trocar_chefe(nome: str, posto: str, foto_path: Optional[str]) -> None:
    """Troca quem é o chefe atual (nome, posto e, opcionalmente, foto).
    O status é reiniciado para 'Presente' a cada troca de pessoa."""
    with _conn() as conn:
        if foto_path:
            conn.execute(
                "UPDATE chefe_atual SET nome=?, posto=?, foto_path=?, status='Presente' WHERE id=1",
                (nome, posto, foto_path),
            )
        else:
            conn.execute(
                "UPDATE chefe_atual SET nome=?, posto=?, status='Presente' WHERE id=1",
                (nome, posto),
            )
        conn.commit()


# ---------------------------------------------------------------
# Aniversariantes
# ---------------------------------------------------------------
def add_aniversariante(cpf: str, posto: str, nome: str, data_nascimento_iso: str) -> None:
    """data_nascimento_iso no formato AAAA-MM-DD (o que st.date_input fornece)."""
    with _conn() as conn:
        conn.execute(
            "INSERT INTO aniversariantes (cpf, posto, nome, data_nascimento) VALUES (?, ?, ?, ?)",
            (cpf, posto, nome, data_nascimento_iso),
        )
        conn.commit()


def list_aniversariantes() -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM aniversariantes ORDER BY nome").fetchall()
        return [dict(r) for r in rows]


def remover_aniversariante(aniversariante_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM aniversariantes WHERE id = ?", (aniversariante_id,))
        conn.commit()


def list_proximos_aniversariantes() -> List[Dict[str, Any]]:
    """Aniversariantes cujo dia/mês ainda não ocorreu neste ano civil,
    ordenados do mais próximo para o mais distante."""
    hoje = datetime.date.today()
    proximos = []
    for pessoa in list_aniversariantes():
        try:
            nascimento = datetime.date.fromisoformat(pessoa["data_nascimento"])
        except (ValueError, TypeError):
            continue
        try:
            data_este_ano = nascimento.replace(year=hoje.year)
        except ValueError:
            # 29 de fevereiro em ano não bissexto -> trata como 28/02
            data_este_ano = nascimento.replace(year=hoje.year, day=28)
        if data_este_ano >= hoje:
            pessoa = dict(pessoa)
            pessoa["proxima_data"] = data_este_ano
            proximos.append(pessoa)
    proximos.sort(key=lambda p: p["proxima_data"])
    return proximos


# ---------------------------------------------------------------
# Tarefas locais (manuais)
# ---------------------------------------------------------------
def add_tarefa_local(titulo: str, horario: Optional[str]) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO tarefas_locais (titulo, horario, criado_em) VALUES (?, ?, ?)",
            (titulo, horario, datetime.datetime.now().isoformat()),
        )
        conn.commit()


def list_tarefas_locais() -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM tarefas_locais ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def remover_tarefa_local(tarefa_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM tarefas_locais WHERE id = ?", (tarefa_id,))
        conn.execute(
            "DELETE FROM tarefas_concluidas WHERE tarefa_id = ?", (f"local-{tarefa_id}",)
        )
        conn.commit()


# ---------------------------------------------------------------
# Conclusão de tarefas (unificado: eventos do Google + tarefas locais)
# ---------------------------------------------------------------
def get_concluidas() -> set:
    with _conn() as conn:
        rows = conn.execute("SELECT tarefa_id FROM tarefas_concluidas").fetchall()
        return {r["tarefa_id"] for r in rows}


def set_tarefa_concluida(tarefa_id: str, concluida: bool) -> None:
    with _conn() as conn:
        if concluida:
            conn.execute(
                "INSERT OR IGNORE INTO tarefas_concluidas (tarefa_id, concluido_em) VALUES (?, ?)",
                (tarefa_id, datetime.datetime.now().isoformat()),
            )
        else:
            conn.execute("DELETE FROM tarefas_concluidas WHERE tarefa_id = ?", (tarefa_id,))
        conn.commit()
