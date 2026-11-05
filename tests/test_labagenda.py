import datetime as dt
import os
import re
import tempfile
import unittest

from app import create_app, db, seed, services as sv
from app.services import RegraDeNegocio

RAIZ = os.path.dirname(os.path.dirname(__file__))
AMANHA = (dt.date.today() + dt.timedelta(days=1)).isoformat()
ONTEM = (dt.date.today() - dt.timedelta(days=1)).isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        db.init_sqlite(self.path, os.path.join(RAIZ, "database", "schema_sqlite.sql"))
        self.app = create_app({"DB_ENGINE": "sqlite", "SQLITE_PATH": self.path, "TESTING": True})
        self.ctx = self.app.app_context()
        self.ctx.push()
        seed.carregar()
        sv._FALHAS.clear()
        self.prof = db.one("SELECT * FROM usuario WHERE perfil='PROFESSOR'")["id_usuario"]
        self.tec = db.one("SELECT * FROM usuario WHERE perfil='TECNICO'")["id_usuario"]

    def tearDown(self):
        db.close_conn()
        self.ctx.pop()
        os.remove(self.path)

    def reservar(self, lab=1, data=AMANHA, i="08:00", f="10:00", eq=()):
        return sv.criar_reserva(self.prof, lab, data, i, f, "Aula prática", eq)["id"]

    def erro(self, codigo, fn, *a, **kw):
        with self.assertRaises(RegraDeNegocio) as cm:
            fn(*a, **kw)
        self.assertEqual(cm.exception.codigo, codigo)


class TestUsuarios(Base):
    def test_cadastro_ok_e_hash(self):
        i = sv.criar_usuario("Ana Lima", "ANA@x.com", "Senha1234", "ALUNO")
        u = db.one("SELECT * FROM usuario WHERE id_usuario=?", (i,))
        self.assertEqual(u["email"], "ana@x.com")
        self.assertNotIn("Senha1234", u["senha_hash"])

    def test_cadastro_nao_permite_virar_tecnico(self):
        i = sv.criar_usuario("Ana Lima", "ana@x.com", "Senha1234", "TECNICO")
        self.assertEqual(db.one("SELECT perfil FROM usuario WHERE id_usuario=?", (i,))["perfil"], "ALUNO")

    def test_validacoes(self):
        self.erro("E05", sv.criar_usuario, "", "a@b.com", "Senha1234")
        self.erro("E06", sv.criar_usuario, "Ana", "sem-arroba", "Senha1234")
        self.erro("E04", sv.criar_usuario, "Ana", "a@b.com", "curta1")
        self.erro("E04", sv.criar_usuario, "Ana", "a@b.com", "somenteletras")
        self.erro("E03", sv.criar_usuario, "Ana", "aluno@labagenda.test", "Senha1234")

    def test_login(self):
        self.assertEqual(sv.autenticar("aluno@labagenda.test", "Aluno1234")["perfil"], "ALUNO")
        self.erro("E02", sv.autenticar, "aluno@labagenda.test", "errada123")
        self.erro("E02", sv.autenticar, "naoexiste@x.com", "Aluno1234")
        self.erro("E01", sv.autenticar, "", "")


class TestReservas(Base):
    def test_reserva_valida_nasce_pendente(self):
        r = self.reservar()
        self.assertEqual(db.one("SELECT status FROM reserva WHERE id_reserva=?", (r,))["status"], "PENDENTE")

    def test_data_passada(self):
        self.erro("E07", self.reservar, data=ONTEM)

    def test_horarios_invalidos(self):
        self.erro("E08", self.reservar, i="10:00", f="09:00")
        self.erro("E09", self.reservar, i="08:00", f="12:30")
        self.erro("E10", self.reservar, i="06:00", f="08:00")
        self.erro("E10", self.reservar, i="21:00", f="23:00")
        self.erro("E05", sv.criar_reserva, self.prof, 1, AMANHA, "08:00", "09:00", "  ")
        self.erro("E24", self.reservar, data="31/12/2030")

    def test_limite_exato_de_4h_e_horarios_de_borda(self):
        self.reservar(i="07:00", f="11:00")
        self.reservar(i="18:00", f="22:00")

    def test_conflito_de_horario(self):
        self.reservar(i="08:00", f="10:00")
        self.erro("E11", self.reservar, i="09:00", f="11:00")   # sobreposição parcial
        self.erro("E11", self.reservar, i="07:00", f="11:00")   # envolve a existente
        self.reservar(i="10:00", f="11:00")                     # encostado, sem sobrepor
        self.reservar(lab=2, i="08:00", f="10:00")              # outro laboratório

    def test_reserva_cancelada_ou_recusada_libera_horario(self):
        r = self.reservar()
        sv.cancelar_reserva(r, self.prof)
        r2 = self.reservar()
        sv.decidir_reserva(r2, self.tec, False, "Laboratório em manutenção")
        self.reservar()

    def test_laboratorio_desativado(self):
        sv.salvar_laboratorio("Laboratório de Redes", "Bloco B - Sala 12", 30, ativo=False, id_laboratorio=1)
        self.erro("E13", self.reservar)

    def test_equipamentos(self):
        self.reservar(eq=[1])
        # mesmo horário no mesmo laboratório já é barrado pelo conflito do laboratório (E11);
        # a checagem de equipamento ocupado é defesa em profundidade.
        self.erro("E11", self.reservar, i="09:00", f="10:00", eq=[1])
        self.reservar(i="10:00", f="11:00", eq=[2])
        self.erro("E18", self.reservar, lab=2, eq=[1])                  # de outro laboratório
        sv.alterar_status_equipamento(2, "MANUTENCAO")
        self.erro("E12", self.reservar, i="14:00", f="15:00", eq=[2])

    def test_falha_em_equipamento_nao_deixa_reserva_pela_metade(self):
        sv.alterar_status_equipamento(2, "BAIXADO")
        self.erro("E12", self.reservar, eq=[1, 2])
        self.assertEqual(db.one("SELECT COUNT(*) AS n FROM reserva")["n"], 0)

    def test_aprovar_recusar(self):
        r = self.reservar()
        self.erro("E14", sv.decidir_reserva, r, self.tec, False, "x")
        sv.decidir_reserva(r, self.tec, True)
        self.assertEqual(db.one("SELECT status, id_avaliador FROM reserva WHERE id_reserva=?", (r,))["status"], "APROVADA")
        self.erro("E15", sv.decidir_reserva, r, self.tec, True)

    def test_cancelamento(self):
        r = self.reservar()
        outro = sv.criar_usuario("Outro", "outro@x.com", "Senha1234")
        self.erro("E16", sv.cancelar_reserva, r, outro)
        sv.cancelar_reserva(r, self.prof)
        self.erro("E15", sv.cancelar_reserva, r, self.prof)
        self.erro("E18", sv.cancelar_reserva, 999, self.prof)

    def test_horarios_ocupados(self):
        self.reservar(i="08:00", f="09:00")
        self.assertEqual(len(sv.horarios_ocupados(1, AMANHA)), 1)


class TestAdmin(Base):
    def test_laboratorio_e_equipamento(self):
        self.erro("E19", sv.salvar_laboratorio, "Novo", "Bloco Z", 0)
        self.erro("E19", sv.salvar_laboratorio, "Novo", "Bloco Z", "abc")
        self.erro("E20", sv.salvar_laboratorio, "Laboratório de Redes", "Outro", 10)
        sv.salvar_laboratorio("Redes", "Bloco B - Sala 12", 30, id_laboratorio=1)  # renomear
        self.erro("E21", sv.salvar_equipamento, 1, "Outro switch", "PAT-0001")
        self.erro("E18", sv.salvar_equipamento, 99, "X", "PAT-9")
        sv.salvar_equipamento(1, "Access point", "PAT-0100")

    def test_ocorrencia(self):
        r = self.reservar()
        self.erro("E22", sv.registrar_ocorrencia, r, "Cabo rompido no rack")   # pendente
        db.execute("UPDATE reserva SET status='APROVADA', data_reserva=? WHERE id_reserva=?", (ONTEM, r))
        db.commit()
        sv.registrar_ocorrencia(r, "Cabo rompido no rack")
        self.assertEqual(len(sv.listar_ocorrencias()), 1)

    def test_relatorio(self):
        a = self.reservar(i="08:00", f="10:00")
        b = self.reservar(i="10:00", f="11:30")
        self.reservar(lab=2, i="08:00", f="09:00")
        sv.decidir_reserva(a, self.tec, True)
        sv.decidir_reserva(b, self.tec, True)
        rel = sv.relatorio_uso(AMANHA, AMANHA)
        self.assertEqual(rel, [{"laboratorio": "Laboratório de Redes", "reservas": 2, "horas": 3.5}])
        self.erro("E24", sv.relatorio_uso, AMANHA, ONTEM)


class TestHTTP(Base):
    def setUp(self):
        super().setUp()
        self.c = self.app.test_client()

    def token(self, url="/login"):
        html = self.c.get(url).get_data(as_text=True)
        return re.search(r'name="csrf" value="([0-9a-f]+)"', html).group(1)

    def entrar(self, email, senha):
        return self.c.post("/login", data={"csrf": self.token(), "email": email, "senha": senha})

    def test_acesso_sem_login_redireciona(self):
        self.assertEqual(self.c.get("/painel").status_code, 302)

    def test_post_sem_csrf_rejeitado(self):
        r = self.c.post("/login", data={"email": "aluno@labagenda.test", "senha": "Aluno1234"})
        self.assertEqual(r.status_code, 302)
        with self.c.session_transaction() as s:
            self.assertNotIn("uid", s)

    def test_login_errado_401(self):
        r = self.entrar("aluno@labagenda.test", "senhaerrada1")
        self.assertEqual(r.status_code, 401)
        self.assertIn("E-mail ou senha incorretos", r.get_data(as_text=True))

    def test_fluxo_completo(self):
        self.assertEqual(self.entrar("professor@labagenda.test", "Professor123").status_code, 302)
        t = self.token("/reservas/nova")
        r = self.c.post("/reservas/nova", data={"csrf": t, "id_laboratorio": "1", "data": AMANHA,
                        "hora_inicio": "08:00", "hora_fim": "09:00", "finalidade": "Aula"}, follow_redirects=True)
        self.assertIn("aguarda a aprovação", r.get_data(as_text=True))
        # professor não acessa o painel de técnico
        self.assertEqual(self.c.get("/equipamentos", follow_redirects=True).status_code, 200)
        self.assertIn("permissão", self.c.get("/relatorio", follow_redirects=True).get_data(as_text=True))
        self.c.post("/sair", data={"csrf": self.token("/painel")})
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        pag = self.c.get("/painel").get_data(as_text=True)
        self.assertIn("Aula", pag)
        rid = re.search(r"/reservas/(\d+)/decidir", pag).group(1)
        r = self.c.post(f"/reservas/{rid}/decidir", data={"csrf": self.token("/painel"), "acao": "aprovar"},
                        follow_redirects=True)
        self.assertIn("de Paulo Ribeiro aprovada", r.get_data(as_text=True))

    def test_conflito_mostra_mensagem(self):
        self.entrar("professor@labagenda.test", "Professor123")
        dados = {"csrf": self.token("/reservas/nova"), "id_laboratorio": "1", "data": AMANHA,
                 "hora_inicio": "08:00", "hora_fim": "09:00", "finalidade": "Aula"}
        self.c.post("/reservas/nova", data=dados)
        r = self.c.post("/reservas/nova", data=dados)
        self.assertEqual(r.status_code, 400)
        self.assertIn("já está reservado", r.get_data(as_text=True))

    def test_xss_escapado(self):
        self.entrar("professor@labagenda.test", "Professor123")
        self.c.post("/reservas/nova", data={"csrf": self.token("/reservas/nova"), "id_laboratorio": "1",
                    "data": AMANHA, "hora_inicio": "08:00", "hora_fim": "09:00",
                    "finalidade": "<script>alert(1)</script>"})
        self.assertNotIn("<script>alert(1)", self.c.get("/painel").get_data(as_text=True))


class TestFeedbackV2(Base):
    """Cada teste nasce de um ponto levantado pelos colegas (docs/08-feedback-e-versao-2.md)."""

    def setUp(self):
        super().setUp()
        self.c = self.app.test_client()

    def token(self, url="/login"):
        return re.search(r'name="csrf" value="([0-9a-f]+)"', self.c.get(url).get_data(as_text=True)).group(1)

    def entrar(self, email, senha):
        return self.c.post("/login", data={"csrf": self.token(), "email": email, "senha": senha})

    def sair(self):
        self.c.post("/sair", data={"csrf": self.token("/painel")})

    # --- Colega 1: campos vazios, e-mail inválido, bloqueio após sair
    def test_login_vazio_marca_os_dois_campos(self):
        r = self.entrar("", "")
        h = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 401)
        self.assertIn("Informe o e-mail.", h)
        self.assertIn("Informe a senha.", h)
        self.assertEqual(h.count('aria-invalid="true"'), 2)

    def test_cadastro_erros_ao_lado_de_cada_campo(self):
        r = self.c.post("/cadastro", data={"csrf": self.token("/cadastro"), "nome": "", "email": "sem-arroba",
                                           "senha": "", "perfil": "ALUNO"})
        h = r.get_data(as_text=True)
        self.assertIn("Informe seu nome completo.", h)
        self.assertIn("Informe um e-mail válido", h)
        self.assertIn("Informe uma senha.", h)
        self.assertIn('id="erro-email"', h)

    def test_email_invalido_sozinho(self):
        with self.assertRaises(RegraDeNegocio) as cm:
            sv.criar_usuario("Ana", "sem-arroba", "Senha1234")
        self.assertEqual(cm.exception.codigo, "E06")
        self.assertIn("email", cm.exception.erros)

    def test_depois_de_sair_o_painel_exige_login(self):
        self.entrar("aluno@labagenda.test", "Aluno1234")
        self.assertEqual(self.c.get("/painel").status_code, 200)
        self.sair()
        r = self.c.get("/painel")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers["Location"])

    def test_bloqueio_apos_cinco_senhas_erradas(self):
        for _ in range(5):
            self.erro("E02", sv.autenticar, "aluno@labagenda.test", "errada1234")
        self.erro("E25", sv.autenticar, "aluno@labagenda.test", "Aluno1234")  # mesmo com a senha certa
        sv._FALHAS["aluno@labagenda.test"] = [agora_menos(11)]               # passou a janela
        self.assertEqual(sv.autenticar("aluno@labagenda.test", "Aluno1234")["perfil"], "ALUNO")

    # --- Colega 2: reservas
    def test_mensagem_de_reserva_traz_detalhes(self):
        self.entrar("professor@labagenda.test", "Professor123")
        r = self.c.post("/reservas/nova", data={"csrf": self.token("/reservas/nova"), "id_laboratorio": "1",
                        "data": AMANHA, "hora_inicio": "08:00", "hora_fim": "09:30", "finalidade": "Aula"},
                        follow_redirects=True)
        h = r.get_data(as_text=True)
        self.assertIn("Laboratório de Redes", h)
        self.assertIn("das 08:00 às 09:30", h)

    def test_reserva_sem_horario_marca_campos(self):
        self.entrar("professor@labagenda.test", "Professor123")
        r = self.c.post("/reservas/nova", data={"csrf": self.token("/reservas/nova"), "id_laboratorio": "1",
                        "data": AMANHA, "hora_inicio": "", "hora_fim": "", "finalidade": ""})
        h = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 400)
        self.assertIn("Informe o horário de início.", h)
        self.assertIn("Informe a finalidade da reserva.", h)

    def test_erro_de_conflito_aparece_no_campo_de_horario(self):
        self.reservar(i="08:00", f="10:00")
        self.entrar("professor@labagenda.test", "Professor123")
        r = self.c.post("/reservas/nova", data={"csrf": self.token("/reservas/nova"), "id_laboratorio": "1",
                        "data": AMANHA, "hora_inicio": "09:00", "hora_fim": "11:00", "finalidade": "x"})
        self.assertIn('id="erro-hora_inicio"', r.get_data(as_text=True))

    # --- Colega 3: painel do técnico
    def test_recusa_sem_motivo_mostra_erro_na_linha_certa(self):
        rid = self.reservar()
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        r = self.c.post(f"/reservas/{rid}/decidir", data={"csrf": self.token("/painel"), "acao": "recusar", "motivo": ""})
        h = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 400)
        self.assertIn('id="erro-motivo"', h)
        self.assertEqual(sv.listar_reservas(status="PENDENTE")[0]["id_reserva"], rid)  # continua pendente

    def test_solicitante_ve_motivo_da_recusa(self):
        rid = self.reservar()
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        r = self.c.post(f"/reservas/{rid}/decidir", data={"csrf": self.token("/painel"), "acao": "recusar",
                        "motivo": "Manutenção do ar-condicionado"}, follow_redirects=True)
        self.assertIn("recusada", r.get_data(as_text=True))
        self.sair()
        self.entrar("professor@labagenda.test", "Professor123")
        self.assertIn("Manutenção do ar-condicionado", self.c.get("/painel").get_data(as_text=True))

    def test_aluno_nao_acessa_area_do_tecnico(self):
        self.entrar("aluno@labagenda.test", "Aluno1234")
        for rota in ("/relatorio", "/relatorio.csv", "/equipamentos", "/ocorrencias"):
            r = self.c.get(rota, follow_redirects=True)
            self.assertIn("não tem permissão", r.get_data(as_text=True), rota)

    # --- Colega 4: laboratórios, ocorrências e relatório
    def test_laboratorio_desativado_some_da_nova_reserva(self):
        sv.salvar_laboratorio("Laboratório de Redes", "Bloco B - Sala 12", 30, ativo=False, id_laboratorio=1)
        self.entrar("professor@labagenda.test", "Professor123")
        self.assertNotIn("Laboratório de Redes", self.c.get("/reservas/nova").get_data(as_text=True))

    def test_ocorrencia_pela_tela_em_reserva_ja_iniciada(self):
        rid = self.reservar()
        db.execute("UPDATE reserva SET status='APROVADA', data_reserva=? WHERE id_reserva=?", (ONTEM, rid))
        db.commit()
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        r = self.c.post("/ocorrencias", data={"csrf": self.token("/ocorrencias"), "id_reserva": rid,
                        "descricao": "Projetor sem imagem"}, follow_redirects=True)
        self.assertIn("Ocorrência registrada", r.get_data(as_text=True))

    def test_ocorrencia_em_reserva_futura_e_recusada_pela_tela(self):
        rid = self.reservar()
        sv.decidir_reserva(rid, self.tec, True)
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        r = self.c.post("/ocorrencias", data={"csrf": self.token("/ocorrencias"), "id_reserva": rid,
                        "descricao": "Projetor sem imagem"}, follow_redirects=True)
        self.assertIn("só pode ser registrada", r.get_data(as_text=True))

    def test_relatorio_mensal_na_tela_e_em_csv(self):
        rid = self.reservar(i="08:00", f="10:30")
        sv.decidir_reserva(rid, self.tec, True)
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        url = f"/relatorio?inicio={AMANHA}&fim={AMANHA}"
        self.assertIn("2.5", self.c.get(url).get_data(as_text=True))
        r = self.c.get(f"/relatorio.csv?inicio={AMANHA}&fim={AMANHA}")
        self.assertEqual(r.mimetype, "text/csv")
        txt = r.get_data(as_text=True)
        self.assertTrue(txt.startswith("\ufeffLaboratório;Reservas aprovadas;Horas de uso"))
        self.assertIn("Laboratório de Redes;1;2,5", txt)

    def test_csv_neutraliza_formula(self):
        sv.salvar_laboratorio("=SOMA(1;1)", "Bloco X", 10)
        rid = self.reservar(lab=4)
        sv.decidir_reserva(rid, self.tec, True)
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        txt = self.c.get(f"/relatorio.csv?inicio={AMANHA}&fim={AMANHA}").get_data(as_text=True)
        self.assertIn("'=SOMA", txt)

    # --- Colega 5: usabilidade
    def test_pagina_tem_link_de_salto_foco_e_idioma(self):
        h = self.c.get("/login").get_data(as_text=True)
        self.assertIn('<html lang="pt-BR">', h)
        self.assertIn("Pular para o conteúdo", h)
        self.assertIn('name="viewport"', h)

    def test_painel_vazio_ensina_a_reservar(self):
        self.entrar("aluno@labagenda.test", "Aluno1234")
        self.assertIn("Como reservar em 3 passos", self.c.get("/painel").get_data(as_text=True))

    def test_tela_de_reserva_mostra_etapas(self):
        self.entrar("professor@labagenda.test", "Professor123")
        h = self.c.get("/reservas/nova").get_data(as_text=True)
        self.assertIn("1. Consultar horários", h)
        self.assertIn("2. Pedir a reserva", h)


class TestExclusaoV21(Base):
    """Versão 2.1: exclusão lógica de equipamentos e laboratórios, com histórico e reativação."""

    def setUp(self):
        super().setUp()
        self.c = self.app.test_client()

    def token(self, url="/login"):
        return re.search(r'name="csrf" value="([0-9a-f]+)"', self.c.get(url).get_data(as_text=True)).group(1)

    def entrar(self, email, senha):
        return self.c.post("/login", data={"csrf": self.token(), "email": email, "senha": senha})

    def nomes_eq(self):
        return [e["nome"] for e in sv.listar_equipamentos()]

    # --- equipamentos
    def test_exclusao_de_equipamento_exige_motivo(self):
        self.erro("E26", sv.excluir_equipamento, 3, self.tec, "  ab ")
        self.assertIn("Projetor Epson", self.nomes_eq())

    def test_equipamento_excluido_some_das_listas_e_guarda_o_registro(self):
        sv.excluir_equipamento(3, self.tec, "Quebrou e não será substituído")
        self.assertNotIn("Projetor Epson", self.nomes_eq())
        self.assertNotIn("Projetor Epson", [e["nome"] for e in sv.listar_equipamentos(2)])
        ex = sv.listar_excluidos()["equipamentos"]
        self.assertEqual([e["nome"] for e in ex], ["Projetor Epson"])
        self.assertEqual(ex[0]["motivo_exclusao"], "Quebrou e não será substituído")
        self.assertEqual(ex[0]["excluido_por_nome"], "Teresa Almeida")
        self.assertTrue(ex[0]["excluido_em"])

    def test_historico_de_reservas_e_ocorrencias_mantem_equipamento_excluido(self):
        rid = self.reservar(lab=2, eq=[3])
        db.execute("UPDATE reserva SET status='APROVADA', data_reserva=? WHERE id_reserva=?", (ONTEM, rid))
        db.commit()
        sv.registrar_ocorrencia(rid, "Lâmpada queimada", 3)
        sv.excluir_equipamento(3, self.tec, "Quebrou definitivamente")
        self.assertIn("Projetor Epson", sv.listar_reservas(status="APROVADA")[0]["equipamentos"])
        self.assertEqual(sv.listar_ocorrencias()[0]["equipamento"], "Projetor Epson")

    def test_equipamento_com_reserva_futura_nao_pode_ser_excluido(self):
        self.reservar(lab=2, eq=[3])
        self.erro("E28", sv.excluir_equipamento, 3, self.tec, "Quebrou definitivamente")
        self.assertIn("Projetor Epson", self.nomes_eq())

    def test_equipamento_excluido_nao_pode_ser_reservado_nem_alterado(self):
        sv.excluir_equipamento(3, self.tec, "Quebrou definitivamente")
        self.erro("E18", self.reservar, 2, AMANHA, "08:00", "10:00", [3])
        self.erro("E18", sv.alterar_status_equipamento, 3, "MANUTENCAO")

    def test_patrimonio_de_excluido_continua_reservado_e_pode_reativar(self):
        sv.excluir_equipamento(3, self.tec, "Quebrou definitivamente")
        self.erro("E21", sv.salvar_equipamento, 2, "Projetor novo", "PAT-0003")
        sv.reativar_equipamento(3)
        self.assertIn("Projetor Epson", self.nomes_eq())
        self.assertEqual(sv.listar_excluidos()["equipamentos"], [])
        self.assertIsNone(db.one("SELECT motivo_exclusao AS m FROM equipamento WHERE id_equipamento=3")["m"])

    # --- laboratórios
    def test_laboratorio_com_reserva_futura_nao_pode_ser_excluido(self):
        self.reservar(lab=3)
        self.erro("E27", sv.excluir_laboratorio, 3, self.tec, "Virou sala de aula")
        self.assertEqual(len(sv.listar_laboratorios()), 3)

    def test_exclusao_de_laboratorio_exige_motivo(self):
        self.erro("E26", sv.excluir_laboratorio, 3, self.tec, "")

    def test_laboratorio_excluido_com_equipamentos_some_de_tudo(self):
        sv.excluir_laboratorio(3, self.tec, "Virou sala de aula", com_equipamentos=True)
        self.assertNotIn("Laboratório de Eletrônica", [l["nome"] for l in sv.listar_laboratorios()])
        self.assertNotIn("Osciloscópio digital", self.nomes_eq())
        ex = sv.listar_excluidos()
        self.assertEqual(ex["laboratorios"][0]["motivo_exclusao"], "Virou sala de aula")
        self.assertEqual(ex["laboratorios"][0]["qtd_equipamentos"], 2)
        self.assertEqual(len(ex["equipamentos"]), 2)
        self.erro("E18", self.reservar, 3)

    def test_laboratorio_excluido_mantendo_equipamentos_nao_aceita_reserva(self):
        sv.excluir_laboratorio(3, self.tec, "Virou sala de aula", com_equipamentos=False)
        mantidos = [e for e in sv.listar_equipamentos() if e["id_laboratorio"] == 3]
        self.assertEqual(len(mantidos), 2)
        self.assertTrue(all(e["laboratorio_excluido"] for e in mantidos))
        self.erro("E18", self.reservar, 3)

    def test_relatorio_mantem_horas_de_laboratorio_excluido(self):
        rid = self.reservar(lab=3)
        db.execute("UPDATE reserva SET status='APROVADA', data_reserva=? WHERE id_reserva=?", (ONTEM, rid))
        db.commit()
        sv.excluir_laboratorio(3, self.tec, "Virou sala de aula", com_equipamentos=True)
        linhas = sv.relatorio_uso(ONTEM, ONTEM)
        self.assertEqual([ln["laboratorio"] for ln in linhas], ["Laboratório de Eletrônica"])
        self.assertEqual(linhas[0]["horas"], 2)

    def test_reativacao_de_laboratorio_e_de_equipamento(self):
        sv.excluir_laboratorio(3, self.tec, "Virou sala de aula", com_equipamentos=True)
        eq = sv.listar_excluidos()["equipamentos"][0]["id_equipamento"]
        self.erro("E29", sv.reativar_equipamento, eq)                  # laboratório ainda excluído
        sv.reativar_laboratorio(3)
        self.assertIn("Laboratório de Eletrônica", [l["nome"] for l in sv.listar_laboratorios()])
        self.assertEqual(len(sv.listar_excluidos()["equipamentos"]), 2)  # equipamentos reativam um a um
        sv.reativar_equipamento(eq)
        self.assertEqual(len(sv.listar_excluidos()["equipamentos"]), 1)
        self.erro("E18", sv.reativar_laboratorio, 3)                   # já está ativo

    # --- telas
    def test_tecnico_exclui_e_reativa_pelas_telas(self):
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        self.assertIn("Confirmar exclusão", self.c.get("/equipamentos/3/excluir").get_data(as_text=True))
        r = self.c.post("/equipamentos/3/excluir", data={"csrf": self.token("/painel"), "motivo": ""})
        h = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 400)
        self.assertIn('id="erro-motivo_exclusao"', h)
        r = self.c.post("/equipamentos/3/excluir", data={"csrf": self.token("/painel"),
                        "motivo": "Quebrou e não será substituído"}, follow_redirects=True)
        self.assertIn("Equipamento &#39;Projetor Epson&#39; excluído", r.get_data(as_text=True))
        h = self.c.get("/excluidos").get_data(as_text=True)
        self.assertIn("Quebrou e não será substituído", h)
        self.assertIn("Laboratórios (0)", h)
        r = self.c.post("/excluidos", data={"csrf": self.token("/painel"), "tipo": "equipamento", "id": "3"},
                        follow_redirects=True)
        self.assertIn("reativado", r.get_data(as_text=True))
        self.assertIn("Projetor Epson", self.nomes_eq())

    def test_tela_de_exclusao_de_laboratorio_mostra_equipamentos_e_aba(self):
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        h = self.c.get("/laboratorios/3/excluir").get_data(as_text=True)
        self.assertIn("Osciloscópio digital", h)
        self.assertIn("Excluir junto com o laboratório", h)
        self.c.post("/laboratorios/3/excluir", data={"csrf": self.token("/painel"), "motivo": "Virou sala de aula",
                    "equipamentos": "excluir"})
        h = self.c.get("/excluidos?aba=laboratorio").get_data(as_text=True)
        self.assertIn("Laboratório de Eletrônica", h)
        self.assertIn("Virou sala de aula", h)

    def test_bloqueio_de_laboratorio_mostra_aviso_na_tela(self):
        self.reservar(lab=3)
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        r = self.c.post("/laboratorios/3/excluir", data={"csrf": self.token("/painel"), "motivo": "Virou sala de aula",
                        "equipamentos": "excluir"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("reserva(s) futura(s)", r.get_data(as_text=True))

    def test_aluno_e_professor_nao_acessam_exclusao(self):
        self.entrar("aluno@labagenda.test", "Aluno1234")
        for rota in ("/excluidos", "/equipamentos/3/excluir", "/laboratorios/3/excluir"):
            r = self.c.get(rota, follow_redirects=True)
            self.assertIn("não tem permissão", r.get_data(as_text=True), rota)
        r = self.c.post("/laboratorios/3/excluir", data={"csrf": self.token("/painel"), "motivo": "Virou sala de aula"},
                        follow_redirects=True)
        self.assertIn("não tem permissão", r.get_data(as_text=True))
        self.assertEqual(len(sv.listar_laboratorios()), 3)


class TestV22(Base):
    """Versão 2.2: histórico de alterações, edição de equipamentos, ocorrência com equipamento e filtros."""

    def setUp(self):
        super().setUp()
        self.c = self.app.test_client()

    def token(self, url="/login"):
        return re.search(r'name="csrf" value="([0-9a-f]+)"', self.c.get(url).get_data(as_text=True)).group(1)

    def entrar(self, email, senha):
        return self.c.post("/login", data={"csrf": self.token(), "email": email, "senha": senha})

    def aprovada_ontem(self, lab=2, eq=()):
        rid = self.reservar(lab=lab, eq=eq)
        db.execute("UPDATE reserva SET status='APROVADA', data_reserva=? WHERE id_reserva=?", (ONTEM, rid))
        db.commit()
        return rid

    # --- edição de equipamento
    def test_edicao_de_equipamento_registra_o_que_mudou(self):
        sv.editar_equipamento(3, "Projetor Epson X1", "PAT-0300", 2, self.tec)
        e = db.one("SELECT * FROM equipamento WHERE id_equipamento=3")
        self.assertEqual((e["nome"], e["numero_patrimonio"]), ("Projetor Epson X1", "PAT-0300"))
        h = sv.listar_historico("EQUIPAMENTO")[0]
        self.assertEqual(h["acao"], "EDICAO")
        self.assertIn("'PAT-0003' → 'PAT-0300'", h["detalhe"])
        self.assertEqual(h["usuario"], "Teresa Almeida")

    def test_edicao_sem_mudanca_nao_gera_historico(self):
        sv.editar_equipamento(3, "Projetor Epson", "PAT-0003", 2, self.tec)
        self.assertEqual(sv.listar_historico(), [])

    def test_edicao_nao_aceita_patrimonio_de_outro_equipamento(self):
        self.erro("E21", sv.editar_equipamento, 3, "Projetor Epson", "PAT-0001", 2, self.tec)
        self.erro("E05", sv.editar_equipamento, 3, "", "PAT-0003", 2, self.tec)

    def test_mudar_equipamento_de_laboratorio(self):
        sv.editar_equipamento(3, "Projetor Epson", "PAT-0003", 1, self.tec)
        self.assertEqual([e["nome"] for e in sv.listar_equipamentos(1)].count("Projetor Epson"), 1)
        self.assertIn("Laboratório", sv.listar_historico()[0]["detalhe"])

    def test_nao_muda_de_laboratorio_com_reserva_futura(self):
        self.reservar(lab=2, eq=[3])
        self.erro("E30", sv.editar_equipamento, 3, "Projetor Epson", "PAT-0003", 1, self.tec)
        sv.editar_equipamento(3, "Projetor Epson 2", "PAT-0003", 2, self.tec)   # só o nome: permitido

    # --- histórico
    def test_historico_registra_cadastro_situacao_exclusao_e_reativacao(self):
        sv.salvar_equipamento(1, "Hub USB", "PAT-0900", self.tec)
        sv.alterar_status_equipamento(3, "MANUTENCAO", self.tec)
        sv.excluir_equipamento(4, self.tec, "Quebrou definitivamente")
        sv.reativar_equipamento(4, self.tec)
        sv.salvar_laboratorio("Laboratório de Redes", "Bloco B - Sala 13", 30, True, 1, self.tec)
        acoes = [h["acao"] for h in sv.listar_historico()]
        self.assertEqual(sorted(acoes), sorted(["CADASTRO", "SITUACAO", "EXCLUSAO", "REATIVACAO", "EDICAO"]))
        lab = sv.listar_historico("LABORATORIO")
        self.assertEqual(len(lab), 1)
        self.assertIn("Bloco B - Sala 12", lab[0]["detalhe"])

    def test_exclusao_de_laboratorio_com_equipamentos_entra_no_historico(self):
        sv.excluir_laboratorio(3, self.tec, "Virou sala de aula", com_equipamentos=True)
        h = sv.listar_historico()
        self.assertEqual(len([x for x in h if x["entidade"] == "EQUIPAMENTO"]), 2)
        self.assertEqual(len([x for x in h if x["entidade"] == "LABORATORIO"]), 1)

    def test_busca_no_historico(self):
        sv.alterar_status_equipamento(3, "MANUTENCAO", self.tec)
        sv.alterar_status_equipamento(1, "BAIXADO", self.tec)
        self.assertEqual([h["referencia"] for h in sv.listar_historico(busca="epson")], ["Projetor Epson"])
        self.assertEqual(sv.listar_historico("LABORATORIO"), [])

    # --- ocorrência com equipamento
    def test_ocorrencia_ligada_ao_equipamento_e_manutencao(self):
        rid = self.aprovada_ontem(eq=[3])
        sv.registrar_ocorrencia(rid, "Lâmpada queimada", 3, True, self.tec)
        self.assertEqual(db.one("SELECT status FROM equipamento WHERE id_equipamento=3")["status"], "MANUTENCAO")
        self.assertEqual(sv.listar_ocorrencias()[0]["equipamento"], "Projetor Epson")
        self.assertEqual(sv.listar_historico()[0]["acao"], "MANUTENCAO")

    def test_ocorrencia_sem_manutencao_nao_muda_a_situacao(self):
        rid = self.aprovada_ontem(eq=[3])
        sv.registrar_ocorrencia(rid, "Cabo solto", 3, False, self.tec)
        self.assertEqual(db.one("SELECT status FROM equipamento WHERE id_equipamento=3")["status"], "DISPONIVEL")

    def test_manutencao_exige_equipamento_e_equipamento_da_reserva(self):
        rid = self.aprovada_ontem(eq=[3])
        self.erro("E31", sv.registrar_ocorrencia, rid, "Cabo solto", None, True, self.tec)
        self.erro("E18", sv.registrar_ocorrencia, rid, "Cabo solto", 1, False, self.tec)

    def test_tela_de_ocorrencia_oferece_equipamento_e_coloca_em_manutencao(self):
        rid = self.aprovada_ontem(eq=[3])
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        h = self.c.get("/ocorrencias").get_data(as_text=True)
        self.assertIn("Equipamento envolvido", h)
        self.assertIn("Projetor Epson", h)
        r = self.c.post("/ocorrencias", data={"csrf": self.token("/painel"), "id_reserva": rid, "descricao": "Lâmpada queimada",
                        "id_equipamento": "3", "manutencao": "1"}, follow_redirects=True)
        self.assertIn("colocado em manutenção", r.get_data(as_text=True))
        self.assertEqual(db.one("SELECT status FROM equipamento WHERE id_equipamento=3")["status"], "MANUTENCAO")

    # --- filtros
    def test_filtros_de_reservas(self):
        a = self.reservar(lab=1, i="08:00", f="10:00")
        b = self.reservar(lab=2, i="08:00", f="10:00")
        sv.decidir_reserva(b, self.tec, False, "Sala em manutenção")
        self.assertEqual({r["id_reserva"] for r in sv.buscar_reservas()}, {a, b})
        self.assertEqual([r["id_reserva"] for r in sv.buscar_reservas(id_laboratorio=1)], [a])
        self.assertEqual([r["id_reserva"] for r in sv.buscar_reservas(status="RECUSADA")], [b])
        self.assertEqual(len(sv.buscar_reservas(busca="paulo")), 2)
        self.assertEqual(sv.buscar_reservas(busca="marina"), [])
        self.assertEqual(sv.buscar_reservas(data_ini=AMANHA, data_fim=AMANHA).__len__(), 2)
        self.assertEqual(sv.buscar_reservas(data_ini=ONTEM, data_fim=ONTEM), [])
        self.erro("E24", sv.buscar_reservas, data_ini="31/02/2026")

    def test_filtro_de_equipamentos(self):
        itens = sv.listar_equipamentos()
        sv.alterar_status_equipamento(3, "MANUTENCAO", self.tec)
        itens = sv.listar_equipamentos()
        self.assertEqual([e["nome"] for e in sv.filtrar_equipamentos(itens, status="MANUTENCAO")], ["Projetor Epson"])
        self.assertEqual(len(sv.filtrar_equipamentos(itens, id_laboratorio=1)), 2)
        self.assertEqual([e["numero_patrimonio"] for e in sv.filtrar_equipamentos(itens, busca="0005")], ["PAT-0005"])

    # --- telas
    def test_tecnico_usa_telas_novas(self):
        self.reservar(lab=1)
        self.entrar("tecnico@labagenda.test", "Tecnico123")
        h = self.c.get("/reservas?situacao=PENDENTE&q=paulo").get_data(as_text=True)
        self.assertIn("1 reserva(s) encontrada(s)", h)
        self.assertIn("Nenhuma reserva encontrada", self.c.get("/reservas?q=zzz").get_data(as_text=True))
        h = self.c.get("/equipamentos?q=projetor").get_data(as_text=True)
        self.assertIn("Projetor Epson", h)
        self.assertNotIn("Osciloscópio", h)
        r = self.c.post("/equipamentos/3/editar", data={"csrf": self.token("/painel"), "nome": "Projetor Epson",
                        "numero_patrimonio": "PAT-0001", "id_laboratorio": "2"})
        self.assertEqual(r.status_code, 400)
        self.assertIn('id="erro-numero_patrimonio"', r.get_data(as_text=True))
        r = self.c.post("/equipamentos/3/editar", data={"csrf": self.token("/painel"), "nome": "Projetor Epson 2",
                        "numero_patrimonio": "PAT-0003", "id_laboratorio": "2"}, follow_redirects=True)
        self.assertIn("atualizado", r.get_data(as_text=True))
        h = self.c.get("/historico?tipo=EQUIPAMENTO&q=epson").get_data(as_text=True)
        self.assertIn("Edição", h)
        self.assertIn("Teresa Almeida", h)

    def test_telas_novas_so_para_o_tecnico(self):
        self.entrar("professor@labagenda.test", "Professor123")
        for rota in ("/reservas", "/historico", "/equipamentos/3/editar"):
            r = self.c.get(rota, follow_redirects=True)
            self.assertIn("não tem permissão", r.get_data(as_text=True), rota)


def agora_menos(minutos):
    return dt.datetime.now() - dt.timedelta(minutes=minutos)


if __name__ == "__main__":
    unittest.main()
