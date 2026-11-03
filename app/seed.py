"""Carga inicial: usuários de demonstração (+ laboratórios se a tabela estiver vazia).

Uso:  python -m app.seed
Senhas de demonstração: troque em qualquer ambiente real.
"""
from werkzeug.security import generate_password_hash

from . import create_app, db

USUARIOS = [
    ("Teresa Almeida", "tecnico@labagenda.test", "Tecnico123", "TECNICO"),
    ("Paulo Ribeiro", "professor@labagenda.test", "Professor123", "PROFESSOR"),
    ("Marina Costa", "aluno@labagenda.test", "Aluno1234", "ALUNO"),
]
LABS = [("Laboratório de Redes", "Bloco B - Sala 12", 30),
        ("Laboratório de Programação", "Bloco A - Sala 03", 40),
        ("Laboratório de Eletrônica", "Bloco C - Sala 01", 20)]
EQUIPS = [(1, "Switch gerenciável 24p", "PAT-0001"), (1, "Roteador Cisco 2901", "PAT-0002"),
          (2, "Projetor Epson", "PAT-0003"), (2, "Kit de 10 notebooks", "PAT-0004"),
          (3, "Osciloscópio digital", "PAT-0005"), (3, "Fonte de bancada", "PAT-0006")]


def carregar():
    for nome, email, senha, perfil in USUARIOS:
        if not db.one("SELECT 1 AS x FROM usuario WHERE email = ?", (email,)):
            db.execute("INSERT INTO usuario (nome, email, senha_hash, perfil) VALUES (?,?,?,?)",
                       (nome, email, generate_password_hash(senha), perfil))
    if not db.one("SELECT 1 AS x FROM laboratorio"):
        for n, l, c in LABS:
            db.execute("INSERT INTO laboratorio (nome, localizacao, capacidade) VALUES (?,?,?)",
                       (n, l, c))
        for i, n, p in EQUIPS:
            db.execute("INSERT INTO equipamento (id_laboratorio, nome, numero_patrimonio) "
                       "VALUES (?,?,?)", (i, n, p))
    db.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        carregar()
        print("Carga inicial concluída.")
