"""Regras de negócio do LabAgenda (RN01 a RN10 em docs/01-escopo.md)."""
import datetime as dt
import re

from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .messages import CAMPO_POR_CODIGO, MSG

ABERTURA = dt.time(7, 0)
FECHAMENTO = dt.time(22, 0)
DURACAO_MAXIMA = dt.timedelta(hours=4)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegraDeNegocio(Exception):
    """Erro previsto, com mensagem pronta para exibir ao usuário."""

    def __init__(self, codigo, erros=None, **kw):
        self.codigo = codigo
        texto = MSG[codigo].format(**kw)
        # erros: {campo: texto} exibido junto de cada campo com problema (v2.0)
        self.erros = erros or ({CAMPO_POR_CODIGO[codigo]: texto} if codigo in CAMPO_POR_CODIGO else {})
        super().__init__(texto)


def agora():
    return dt.datetime.now()


# ---------------------------------------------------------------- usuários
def criar_usuario(nome, email, senha, perfil="ALUNO"):
    nome, email = (nome or "").strip(), (email or "").strip().lower()
    erros = {}
    if not nome:
        erros["nome"] = "Informe seu nome completo."
    if not email:
        erros["email"] = "Informe o e-mail."
    elif not EMAIL_RE.match(email):
        erros["email"] = MSG["E06"]
    if not senha:
        erros["senha"] = "Informe uma senha."
    elif len(senha) < 8 or not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        erros["senha"] = MSG["E04"]
    if erros:
        if not nome or not email or not senha:
            raise RegraDeNegocio("E05", erros=erros)
        raise RegraDeNegocio("E06" if "email" in erros else "E04", erros=erros)
    if perfil not in ("ALUNO", "PROFESSOR"):  # técnico só entra via carga inicial
        perfil = "ALUNO"
    if db.one("SELECT 1 AS x FROM usuario WHERE email = ?", (email,)):
        raise RegraDeNegocio("E03")
    novo = db.execute(
        "INSERT INTO usuario (nome, email, senha_hash, perfil) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), perfil))
    db.commit()
    return novo


_FALHAS = {}                       # e-mail -> instantes das tentativas erradas (memória do processo)
LIMITE_TENTATIVAS = 5
JANELA = dt.timedelta(minutes=10)


def _falhas_recentes(chave):
    limite = agora() - JANELA
    _FALHAS[chave] = [t for t in _FALHAS.get(chave, []) if t > limite]
    return _FALHAS[chave]


def autenticar(email, senha):
    erros = {}
    if not (email or "").strip():
        erros["email"] = "Informe o e-mail."
    if not senha:
        erros["senha"] = "Informe a senha."
    if erros:
        raise RegraDeNegocio("E01", erros=erros)
    chave = email.strip().lower()
    if len(_falhas_recentes(chave)) >= LIMITE_TENTATIVAS:          # P03
        raise RegraDeNegocio("E25", min=int(JANELA.total_seconds() // 60))
    u = db.one("SELECT * FROM usuario WHERE email = ? AND ativo = 1", (chave,))
    if not u or not check_password_hash(u["senha_hash"], senha):
        _FALHAS[chave].append(agora())
        raise RegraDeNegocio("E02")  # mesma mensagem: não revela se o e-mail existe
    _FALHAS.pop(chave, None)
    return u


# ------------------------------------------------------------ laboratórios
def listar_laboratorios(apenas_ativos=False):
    sql = "SELECT * FROM laboratorio"
    if apenas_ativos:
        sql += " WHERE ativo = 1"
    return db.query(sql + " ORDER BY nome")


def salvar_laboratorio(nome, localizacao, capacidade, ativo=True, id_laboratorio=None):
    nome, localizacao = (nome or "").strip(), (localizacao or "").strip()
    if not nome or not localizacao:
        raise RegraDeNegocio("E05")
    try:
        capacidade = int(capacidade)
        if capacidade <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise RegraDeNegocio("E19")
    dup = db.one("SELECT id_laboratorio FROM laboratorio WHERE nome = ?", (nome,))
    if dup and dup["id_laboratorio"] != id_laboratorio:
        raise RegraDeNegocio("E20")
    if id_laboratorio:
        db.execute("UPDATE laboratorio SET nome=?, localizacao=?, capacidade=?, ativo=? "
                   "WHERE id_laboratorio=?",
                   (nome, localizacao, capacidade, 1 if ativo else 0, id_laboratorio))
    else:
        id_laboratorio = db.execute(
            "INSERT INTO laboratorio (nome, localizacao, capacidade, ativo) VALUES (?,?,?,?)",
            (nome, localizacao, capacidade, 1 if ativo else 0))
    db.commit()
    return id_laboratorio


def listar_equipamentos(id_laboratorio=None):
    sql = ("SELECT e.*, l.nome AS laboratorio FROM equipamento e "
           "JOIN laboratorio l ON l.id_laboratorio = e.id_laboratorio")
    params = ()
    if id_laboratorio:
        sql += " WHERE e.id_laboratorio = ?"
        params = (id_laboratorio,)
    return db.query(sql + " ORDER BY l.nome, e.nome", params)


def salvar_equipamento(id_laboratorio, nome, patrimonio):
    nome, patrimonio = (nome or "").strip(), (patrimonio or "").strip()
    if not id_laboratorio or not nome or not patrimonio:
        raise RegraDeNegocio("E05")
    if not db.one("SELECT 1 AS x FROM laboratorio WHERE id_laboratorio = ?", (id_laboratorio,)):
        raise RegraDeNegocio("E18")
    if db.one("SELECT 1 AS x FROM equipamento WHERE numero_patrimonio = ?", (patrimonio,)):
        raise RegraDeNegocio("E21")
    novo = db.execute(
        "INSERT INTO equipamento (id_laboratorio, nome, numero_patrimonio) VALUES (?,?,?)",
        (id_laboratorio, nome, patrimonio))
    db.commit()
    return novo


def alterar_status_equipamento(id_equipamento, status):
    if status not in ("DISPONIVEL", "MANUTENCAO", "BAIXADO"):
        raise RegraDeNegocio("E05")
    if not db.one("SELECT 1 AS x FROM equipamento WHERE id_equipamento = ?", (id_equipamento,)):
        raise RegraDeNegocio("E18")
    db.execute("UPDATE equipamento SET status = ? WHERE id_equipamento = ?",
               (status, id_equipamento))
    db.commit()


# ---------------------------------------------------------------- reservas
def _parse_hora(txt):
    try:
        h, m = str(txt).split(":")[:2]
        return dt.time(int(h), int(m))
    except (ValueError, TypeError):
        raise RegraDeNegocio("E05")


def _parse_data(txt):
    try:
        return dt.date.fromisoformat(str(txt))
    except (ValueError, TypeError):
        raise RegraDeNegocio("E24")


def horarios_ocupados(id_laboratorio, data):
    return db.query(
        "SELECT hora_inicio, hora_fim, status FROM reserva "
        "WHERE id_laboratorio = ? AND data_reserva = ? "
        "AND status IN ('PENDENTE','APROVADA') ORDER BY hora_inicio",
        (id_laboratorio, str(data)))


def criar_reserva(id_usuario, id_laboratorio, data, inicio, fim, finalidade, ids_equipamento=()):
    erros = {}
    if not id_laboratorio:
        erros["id_laboratorio"] = "Escolha o laboratório na consulta acima."
    if not data:
        erros["data"] = "Escolha a data na consulta acima."
    if not inicio:
        erros["hora_inicio"] = "Informe o horário de início."
    if not fim:
        erros["hora_fim"] = "Informe o horário de término."
    if not (finalidade or "").strip():
        erros["finalidade"] = "Informe a finalidade da reserva."
    if erros:
        raise RegraDeNegocio("E05", erros=erros)
    d, hi, hf = _parse_data(data), _parse_hora(inicio), _parse_hora(fim)
    finalidade = finalidade.strip()[:200]

    lab = db.one("SELECT * FROM laboratorio WHERE id_laboratorio = ?", (id_laboratorio,))
    if not lab:
        raise RegraDeNegocio("E18")
    if not lab["ativo"]:
        raise RegraDeNegocio("E13")
    if dt.datetime.combine(d, hi) <= agora():                       # RN02
        raise RegraDeNegocio("E07")
    if hf <= hi:                                                    # RN03
        raise RegraDeNegocio("E08")
    if dt.datetime.combine(d, hf) - dt.datetime.combine(d, hi) > DURACAO_MAXIMA:
        raise RegraDeNegocio("E09")
    if hi < ABERTURA or hf > FECHAMENTO:                            # RN04
        raise RegraDeNegocio("E10")

    try:
        db.lock_laboratorio(id_laboratorio)
        conflito = db.one(                                          # RN05
            "SELECT 1 AS x FROM reserva WHERE id_laboratorio = ? AND data_reserva = ? "
            "AND status IN ('PENDENTE','APROVADA') AND hora_inicio < ? AND hora_fim > ?",
            (id_laboratorio, d.isoformat(), hf.strftime("%H:%M:%S"), hi.strftime("%H:%M:%S")))
        if conflito:
            raise RegraDeNegocio("E11")

        equips = []
        for ide in ids_equipamento:                                 # RN06
            e = db.one("SELECT * FROM equipamento WHERE id_equipamento = ? "
                       "AND id_laboratorio = ?", (ide, id_laboratorio))
            if not e:
                raise RegraDeNegocio("E18")
            ocupado = db.one(
                "SELECT 1 AS x FROM reserva_equipamento re "
                "JOIN reserva r ON r.id_reserva = re.id_reserva "
                "WHERE re.id_equipamento = ? AND r.data_reserva = ? "
                "AND r.status IN ('PENDENTE','APROVADA') "
                "AND r.hora_inicio < ? AND r.hora_fim > ?",
                (ide, d.isoformat(), hf.strftime("%H:%M:%S"), hi.strftime("%H:%M:%S")))
            if e["status"] != "DISPONIVEL" or ocupado:
                raise RegraDeNegocio("E12", nome=e["nome"])
            equips.append(ide)

        id_reserva = db.execute(
            "INSERT INTO reserva (id_usuario, id_laboratorio, data_reserva, hora_inicio, "
            "hora_fim, finalidade, status) VALUES (?,?,?,?,?,?,'PENDENTE')",
            (id_usuario, id_laboratorio, d.isoformat(), hi.strftime("%H:%M:%S"),
             hf.strftime("%H:%M:%S"), finalidade))
        for ide in equips:
            db.execute("INSERT INTO reserva_equipamento (id_reserva, id_equipamento) VALUES (?,?)",
                       (id_reserva, ide))
        db.commit()
        return {"id": id_reserva, "lab": lab["nome"], "data": f"{d:%d/%m/%Y}",
                "inicio": hi.strftime("%H:%M"), "fim": hf.strftime("%H:%M")}
    except Exception:
        db.rollback()
        raise


_SQL_RESERVA = (
    "SELECT r.*, l.nome AS laboratorio, u.nome AS solicitante, "
    "(SELECT GROUP_CONCAT(e.nome, ', ') FROM reserva_equipamento re "
    " JOIN equipamento e ON e.id_equipamento = re.id_equipamento "
    " WHERE re.id_reserva = r.id_reserva) AS equipamentos "
    "FROM reserva r JOIN laboratorio l ON l.id_laboratorio = r.id_laboratorio "
    "JOIN usuario u ON u.id_usuario = r.id_usuario ")


def _sql_reserva():
    # GROUP_CONCAT: sintaxe com separador difere entre MySQL e SQLite
    if db._is_mysql():
        return _SQL_RESERVA.replace("GROUP_CONCAT(e.nome, ', ')",
                                    "GROUP_CONCAT(e.nome SEPARATOR ', ')")
    return _SQL_RESERVA


def listar_reservas(id_usuario=None, status=None):
    cond, params = [], []
    if id_usuario:
        cond.append("r.id_usuario = ?")
        params.append(id_usuario)
    if status:
        cond.append("r.status = ?")
        params.append(status)
    where = (" WHERE " + " AND ".join(cond)) if cond else ""
    return db.query(_sql_reserva() + where +
                    " ORDER BY r.data_reserva DESC, r.hora_inicio DESC", tuple(params))


def decidir_reserva(id_reserva, id_avaliador, aprovar, motivo=None):
    r = db.one("SELECT * FROM reserva WHERE id_reserva = ?", (id_reserva,))
    if not r:
        raise RegraDeNegocio("E18")
    if r["status"] != "PENDENTE":                                   # RN07
        raise RegraDeNegocio("E15", status=r["status"].lower())
    if aprovar:
        db.execute("UPDATE reserva SET status='APROVADA', id_avaliador=? WHERE id_reserva=?",
                   (id_avaliador, id_reserva))
    else:
        motivo = (motivo or "").strip()
        if len(motivo) < 5:
            raise RegraDeNegocio("E14")
        db.execute("UPDATE reserva SET status='RECUSADA', id_avaliador=?, motivo_recusa=? "
                   "WHERE id_reserva=?", (id_avaliador, motivo[:200], id_reserva))
    db.commit()
    quem = db.one("SELECT nome FROM usuario WHERE id_usuario = ?", (r["id_usuario"],))
    return {"id": id_reserva, "nome": quem["nome"] if quem else "?"}


def cancelar_reserva(id_reserva, id_usuario):
    r = db.one("SELECT * FROM reserva WHERE id_reserva = ?", (id_reserva,))
    if not r:
        raise RegraDeNegocio("E18")
    if r["status"] not in ("PENDENTE", "APROVADA"):
        raise RegraDeNegocio("E15", status=r["status"].lower())
    inicio = dt.datetime.fromisoformat(f"{r['data_reserva']} {r['hora_inicio']}")
    if r["id_usuario"] != id_usuario or inicio <= agora():          # RN08
        raise RegraDeNegocio("E16")
    db.execute("UPDATE reserva SET status='CANCELADA' WHERE id_reserva=?", (id_reserva,))
    db.commit()


# -------------------------------------------------------------- ocorrências
def registrar_ocorrencia(id_reserva, descricao, id_equipamento=None):
    descricao = (descricao or "").strip()
    if len(descricao) < 5:
        raise RegraDeNegocio("E05")
    r = db.one("SELECT * FROM reserva WHERE id_reserva = ?", (id_reserva,))
    if not r:
        raise RegraDeNegocio("E18")
    inicio = dt.datetime.fromisoformat(f"{r['data_reserva']} {r['hora_inicio']}")
    if r["status"] != "APROVADA" or inicio > agora():               # RN09
        raise RegraDeNegocio("E22")
    if id_equipamento:
        if not db.one("SELECT 1 AS x FROM reserva_equipamento WHERE id_reserva=? AND "
                      "id_equipamento=?", (id_reserva, id_equipamento)):
            raise RegraDeNegocio("E18")
    novo = db.execute(
        "INSERT INTO ocorrencia (id_reserva, id_equipamento, descricao) VALUES (?,?,?)",
        (id_reserva, id_equipamento or None, descricao[:500]))
    db.commit()
    return novo


def listar_ocorrencias():
    return db.query(
        "SELECT o.*, r.data_reserva, l.nome AS laboratorio, e.nome AS equipamento "
        "FROM ocorrencia o JOIN reserva r ON r.id_reserva = o.id_reserva "
        "JOIN laboratorio l ON l.id_laboratorio = r.id_laboratorio "
        "LEFT JOIN equipamento e ON e.id_equipamento = o.id_equipamento "
        "ORDER BY o.registrada_em DESC")


# ---------------------------------------------------------------- relatório
def relatorio_uso(data_ini, data_fim):
    """Reservas aprovadas e horas de uso por laboratório no período (RN10)."""
    di, df = _parse_data(data_ini), _parse_data(data_fim)
    if df < di:
        raise RegraDeNegocio("E24")
    linhas = db.query(
        "SELECT l.nome AS laboratorio, r.hora_inicio, r.hora_fim FROM reserva r "
        "JOIN laboratorio l ON l.id_laboratorio = r.id_laboratorio "
        "WHERE r.status='APROVADA' AND r.data_reserva BETWEEN ? AND ?",
        (di.isoformat(), df.isoformat()))
    res = {}
    for ln in linhas:  # soma feita em Python para funcionar igual em qualquer SGBD
        h1, h2 = _parse_hora(ln["hora_inicio"]), _parse_hora(ln["hora_fim"])
        minutos = (h2.hour * 60 + h2.minute) - (h1.hour * 60 + h1.minute)
        item = res.setdefault(ln["laboratorio"], {"laboratorio": ln["laboratorio"],
                                                  "reservas": 0, "horas": 0.0})
        item["reservas"] += 1
        item["horas"] += minutos / 60
    return sorted(res.values(), key=lambda x: -x["horas"])
