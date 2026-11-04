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


def agora_menos(minutos):
    return dt.datetime.now() - dt.timedelta(minutes=minutos)


if __name__ == "__main__":
    unittest.main()
