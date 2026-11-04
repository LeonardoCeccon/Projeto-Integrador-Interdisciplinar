"""Acesso a dados.

Em produção usa MySQL (PyMySQL). Para testes automatizados e desenvolvimento
sem servidor, existe um modo SQLite com o mesmo esquema lógico. As consultas
são escritas com '?' e convertidas para '%s' quando o motor é MySQL.
"""
import datetime as dt
import sqlite3

from flask import current_app, g


def _is_mysql():
    return current_app.config["DB_ENGINE"] == "mysql"


def get_conn():
    if "conn" not in g:
        cfg = current_app.config
        if _is_mysql():
            import pymysql  # importado só quando necessário

            extra = {}
            if cfg.get("DB_SSL_CA"):  # bancos em nuvem (Aiven, etc.) exigem conexão criptografada
                extra["ssl"] = {"ca": cfg["DB_SSL_CA"]}
            g.conn = pymysql.connect(
                host=cfg["DB_HOST"], port=cfg["DB_PORT"], user=cfg["DB_USER"],
                password=cfg["DB_PASSWORD"], database=cfg["DB_NAME"],
                charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
                autocommit=False, connect_timeout=10, **extra,
            )
        else:
            conn = sqlite3.connect(cfg["SQLITE_PATH"])
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.conn = conn
    return g.conn


def close_conn(_exc=None):
    conn = g.pop("conn", None)
    if conn is not None:
        conn.close()


def _norm(value):
    """Converte tipos do MySQL para texto simples usado nos templates."""
    if isinstance(value, dt.timedelta):
        total = int(value.total_seconds())
        return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, dt.date):
        return value.isoformat()
    return value


def _sql(sql):
    return sql.replace("?", "%s") if _is_mysql() else sql


def query(sql, params=()):
    cur = get_conn().cursor()
    cur.execute(_sql(sql), params)
    rows = [{k: _norm(v) for k, v in dict(r).items()} for r in cur.fetchall()]
    cur.close()
    return rows


def one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    cur = get_conn().cursor()
    cur.execute(_sql(sql), params)
    last = cur.lastrowid
    cur.close()
    return last


def commit():
    get_conn().commit()


def rollback():
    get_conn().rollback()


def lock_laboratorio(id_laboratorio):
    """Serializa reservas concorrentes do mesmo laboratório (somente MySQL)."""
    if _is_mysql():
        query("SELECT id_laboratorio FROM laboratorio WHERE id_laboratorio = ? FOR UPDATE",
              (id_laboratorio,))


def init_sqlite(path, schema_file, seed_file=None):
    conn = sqlite3.connect(path)
    with open(schema_file, encoding="utf-8") as f:
        conn.executescript(f.read())
    if seed_file:
        with open(seed_file, encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()
