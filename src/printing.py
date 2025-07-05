# printing.py
import subprocess, datetime

WIDTH = 48
CASH_REGISTER = 1   # oppure 2

def money(val: float) -> str:
    return f"{val:,.2f} EUR".replace(".", ",")

def print_receipt(order_items, order_id, table_no, rest, printer_name):
    """order_items = list di tuple (nome, qty, prezzo_unitario)"""
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    header1 = f"Cassa {CASH_REGISTER} - {now}".center(WIDTH)
    header2 = f"Ordine {order_id} - Tavolo {table_no}".center(WIDTH)
    lines = [header1, header2, "-"*WIDTH,
             f"{'Prodotto':<26}{'Quantita':^6}{'Prezzo':>14}",
             "-"*WIDTH]

    for name, qty, price_each in order_items:
        lines.append(f"{name:<26}{qty:^6}{money(price_each):>16}")

    lines.append("-"*WIDTH)
    total = sum(q*p for _, q, p in order_items)
    lines.append(f"{'Totale:':<28}{money(total):>20}")
    lines.append(f"{'Incasso dato:':<28}{money(rest):>20}")
    lines.append(f"{'Resto ricevuto:':<28}{money(rest):>20}")
    lines.append("\n"*12)           # margine di strappo

    subprocess.run(
        ["lp", "-d", printer_name, "-o", "raw"],
        input="\n".join(lines).encode("utf-8"),
        check=True
    )
