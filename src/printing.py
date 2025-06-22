# printing.py
import subprocess, datetime

WIDTH = 42
CASH_REGISTER = 1   # oppure 2

def money(val: float) -> str:
    return f"{val:,.2f} EUR".replace(".", ",")

def print_receipt(order_items, printer_name):
    """order_items = list di tuple (nome, qty, prezzo_unitario)"""
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    header = f"Cassa {CASH_REGISTER} - {now}".center(WIDTH)
    lines = [header, "-"*WIDTH,
             f"{'Prodotto':<20}{'Pezzi':^6}{'Prezzo':>16}",
             "-"*WIDTH]

    for name, qty, price_each in order_items:
        lines.append(f"{name:<20}{qty:^6}{money(price_each):>16}")

    lines.append("-"*WIDTH)
    total = sum(q*p for _, q, p in order_items)
    lines.append(f"{'Totale:':<26}{money(total):>16}")
    lines.append("\n"*5)           # margine di strappo

    subprocess.run(
        ["lp", "-d", printer_name, "-o", "raw"],
        input="\n".join(lines).encode("utf-8"),
        check=True
    )
