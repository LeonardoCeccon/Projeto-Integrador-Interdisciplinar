import sqlite3, datetime as dt
ontem = (dt.date.today() - dt.timedelta(days=1)).isoformat()
c = sqlite3.connect("labagenda_dev.sqlite3")
hoje = dt.date.today().isoformat()
r = c.execute("SELECT id_reserva FROM reserva WHERE status='APROVADA' AND data_reserva >= ? ORDER BY id_reserva DESC LIMIT 1", (hoje,)).fetchone()
if not r:
    print("Nenhuma reserva aprovada com data futura. Aprove uma primeiro.")
else:
    c.execute("UPDATE reserva SET data_reserva = ? WHERE id_reserva = ?", (ontem, r[0]))
    c.commit()
    print("Reserva", r[0], "ajustada para", ontem)
