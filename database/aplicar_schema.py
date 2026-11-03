"""Executa o schema.sql no MySQL indicado pelas variáveis de ambiente DB_*.

Pula os comandos que bancos em nuvem não permitem (criar banco, criar usuário, USE).
Uso:  python database/aplicar_schema.py database/schema.sql
"""
import os
import sys

import pymysql

IGNORAR = ("DROP DATABASE", "CREATE DATABASE", "USE ", "CREATE USER", "GRANT ", "FLUSH ")


def comandos(texto):
    linhas = [l for l in texto.splitlines() if not l.strip().startswith("--")]
    todos = [c.strip() for c in "\n".join(linhas).split(";") if c.strip()]
    return [c for c in todos if not c.upper().startswith(IGNORAR)]


def main(arquivo):
    with open(arquivo, encoding="utf-8") as f:
        cmds = comandos(f.read())
    extra = {"ssl": {"ca": os.environ["DB_SSL_CA"]}} if os.environ.get("DB_SSL_CA") else {}
    conn = pymysql.connect(
        host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"], charset="utf8mb4", connect_timeout=15, **extra)
    try:
        with conn.cursor() as cur:
            for i, c in enumerate(cmds, 1):
                cur.execute(c)
                print(f"[{i}/{len(cmds)}] ok: {c.splitlines()[0][:70]}")
        conn.commit()
    finally:
        conn.close()
    print("Concluído.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python database/aplicar_schema.py database/schema.sql")
    main(sys.argv[1])