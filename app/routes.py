import csv
import datetime as dt
import io
from functools import wraps

from flask import (Blueprint, Response, flash, redirect, render_template, request,
                   session, url_for)

from . import services as sv
from .messages import MSG
from .services import RegraDeNegocio

bp = Blueprint("main", __name__)


def login_required(*perfis):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if "uid" not in session:
                return redirect(url_for("main.login"))
            if perfis and session["perfil"] not in perfis:        # RN01
                flash(MSG["E17"], "erro")
                return redirect(url_for("main.painel"))
            return fn(*a, **kw)
        return wrapper
    return deco


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ acesso
@bp.route("/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            u = sv.autenticar(request.form.get("email"), request.form.get("senha"))
        except RegraDeNegocio as e:
            flash(str(e), "erro")
            return render_template("login.html", email=request.form.get("email", ""),
                                   erros=e.erros), 401
        csrf = session.get("csrf")
        session.clear()
        session.update(uid=u["id_usuario"], nome=u["nome"], perfil=u["perfil"], csrf=csrf)
        return redirect(url_for("main.painel"))
    return render_template("login.html", email="", erros={})


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        f = request.form
        try:
            sv.criar_usuario(f.get("nome"), f.get("email"), f.get("senha"), f.get("perfil"))
        except RegraDeNegocio as e:
            flash(str(e), "erro")
            return render_template("cadastro.html", f=f, erros=e.erros), 400
        flash(MSG["S01"], "ok")
        return redirect(url_for("main.login"))
    return render_template("cadastro.html", f={}, erros={})


@bp.post("/sair")
def sair():
    session.clear()
    return redirect(url_for("main.login"))


# ------------------------------------------------------------------ painel
@bp.route("/painel")
@login_required()
def painel():
    if session["perfil"] == "TECNICO":
        pend = sv.listar_reservas(status="PENDENTE")
        return render_template("painel_tecnico.html", pendentes=pend, erro_reserva=None, erros={})
    reservas = sv.listar_reservas(session["uid"])
    agora = sv.agora()
    for r in reservas:  # só mostra "Cancelar" se ainda der tempo (RN08)
        inicio = dt.datetime.fromisoformat(f"{r['data_reserva']} {r['hora_inicio']}")
        r["pode_cancelar"] = r["status"] in ("PENDENTE", "APROVADA") and inicio > agora
    return render_template("painel.html", reservas=reservas)


# ---------------------------------------------------------------- reservas
@bp.route("/reservas/nova", methods=["GET", "POST"])
@login_required("ALUNO", "PROFESSOR")
def nova_reserva():
    labs = sv.listar_laboratorios(apenas_ativos=True)
    f = request.form if request.method == "POST" else request.args
    id_lab = _int(f.get("id_laboratorio"))
    equips = [e for e in sv.listar_equipamentos(id_lab) if e["status"] == "DISPONIVEL"] if id_lab else []
    ocupados = sv.horarios_ocupados(id_lab, f.get("data")) if id_lab and f.get("data") else []
    if request.method == "POST":
        try:
            res = sv.criar_reserva(session["uid"], id_lab, f.get("data"), f.get("hora_inicio"),
                                   f.get("hora_fim"), f.get("finalidade"),
                                   [i for i in (_int(x) for x in request.form.getlist("equipamentos")) if i])
        except RegraDeNegocio as e:
            flash(str(e), "erro")
            return render_template("nova_reserva.html", labs=labs, equips=equips, f=f,
                                   ocupados=ocupados, erros=e.erros), 400
        flash(MSG["S02"].format(**res), "ok")
        return redirect(url_for("main.painel"))
    return render_template("nova_reserva.html", labs=labs, equips=equips, f=f, ocupados=ocupados,
                           erros={})


@bp.post("/reservas/<int:id_reserva>/cancelar")
@login_required()
def cancelar(id_reserva):
    try:
        sv.cancelar_reserva(id_reserva, session["uid"])
        flash(MSG["S05"], "ok")
    except RegraDeNegocio as e:
        flash(str(e), "erro")
    return redirect(url_for("main.painel"))


@bp.post("/reservas/<int:id_reserva>/decidir")
@login_required("TECNICO")
def decidir(id_reserva):
    aprovar = request.form.get("acao") == "aprovar"
    try:
        info = sv.decidir_reserva(id_reserva, session["uid"], aprovar, request.form.get("motivo"))
        flash((MSG["S03"] if aprovar else MSG["S04"]).format(**info), "ok")
    except RegraDeNegocio as e:
        flash(str(e), "erro")
        if e.codigo == "E14":  # volta ao painel mostrando o erro junto do campo certo
            return render_template("painel_tecnico.html", pendentes=sv.listar_reservas(status="PENDENTE"),
                                   erro_reserva=id_reserva, erros=e.erros), 400
    return redirect(url_for("main.painel"))


# ------------------------------------------------- laboratórios/equipamentos
@bp.route("/laboratorios", methods=["GET", "POST"])
@login_required()
def laboratorios():
    if request.method == "POST":
        if session["perfil"] != "TECNICO":
            flash(MSG["E17"], "erro")
            return redirect(url_for("main.laboratorios"))
        f = request.form
        try:
            sv.salvar_laboratorio(f.get("nome"), f.get("localizacao"), f.get("capacidade"),
                                  f.get("ativo") == "1", _int(f.get("id_laboratorio")))
            flash(MSG["S06"], "ok")
        except RegraDeNegocio as e:
            flash(str(e), "erro")
        return redirect(url_for("main.laboratorios"))
    return render_template("laboratorios.html", labs=sv.listar_laboratorios())


@bp.route("/equipamentos", methods=["GET", "POST"])
@login_required("TECNICO")
def equipamentos():
    if request.method == "POST":
        f = request.form
        try:
            if f.get("acao") == "status":
                sv.alterar_status_equipamento(_int(f.get("id_equipamento")), f.get("status"))
                flash(MSG["S09"], "ok")
            else:
                sv.salvar_equipamento(_int(f.get("id_laboratorio")), f.get("nome"),
                                      f.get("numero_patrimonio"))
                flash(MSG["S07"], "ok")
        except RegraDeNegocio as e:
            flash(str(e), "erro")
        return redirect(url_for("main.equipamentos"))
    return render_template("equipamentos.html", itens=sv.listar_equipamentos(),
                           labs=sv.listar_laboratorios())


# --------------------------------------------------------------- ocorrências
@bp.route("/ocorrencias", methods=["GET", "POST"])
@login_required("TECNICO")
def ocorrencias():
    if request.method == "POST":
        f = request.form
        try:
            sv.registrar_ocorrencia(_int(f.get("id_reserva")), f.get("descricao"),
                                    _int(f.get("id_equipamento")))
            flash(MSG["S08"], "ok")
        except RegraDeNegocio as e:
            flash(str(e), "erro")
        return redirect(url_for("main.ocorrencias"))
    aprovadas = [r for r in sv.listar_reservas(status="APROVADA")
                 if r["data_reserva"] <= dt.date.today().isoformat()]
    return render_template("ocorrencias.html", lista=sv.listar_ocorrencias(), reservas=aprovadas)


@bp.route("/relatorio")
@login_required("TECNICO")
def relatorio():
    hoje = dt.date.today()
    ini = request.args.get("inicio", (hoje - dt.timedelta(days=30)).isoformat())
    fim = request.args.get("fim", hoje.isoformat())
    linhas = []
    try:
        linhas = sv.relatorio_uso(ini, fim)
    except RegraDeNegocio as e:
        flash(str(e), "erro")
    return render_template("relatorio.html", linhas=linhas, ini=ini, fim=fim)


@bp.route("/relatorio.csv")
@login_required("TECNICO")
def relatorio_csv():
    hoje = dt.date.today()
    ini = request.args.get("inicio", (hoje - dt.timedelta(days=30)).isoformat())
    fim = request.args.get("fim", hoje.isoformat())
    try:
        linhas = sv.relatorio_uso(ini, fim)
    except RegraDeNegocio as e:
        flash(str(e), "erro")
        return redirect(url_for("main.relatorio"))
    saida = io.StringIO()
    w = csv.writer(saida, delimiter=";")        # ';' abre direto no Excel em português
    w.writerow(["Laboratório", "Reservas aprovadas", "Horas de uso"])
    for ln in linhas:
        nome = ln["laboratorio"]
        if nome[:1] in "=+-@":                   # evita injeção de fórmula em planilhas
            nome = "'" + nome
        w.writerow([nome, ln["reservas"], f"{ln['horas']:.1f}".replace(".", ",")])
    return Response("\ufeff" + saida.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=uso_{ini}_{fim}.csv"})
