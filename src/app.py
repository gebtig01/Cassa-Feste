#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash, logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func
import argparse
from printing import print_receipt
from datetime import datetime


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "Xwenjkxw8o9wjndki3e"
db = SQLAlchemy(app)

# ----- Modello ---------------------------------------------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    category = db.Column(db.String(60), nullable=False, default="altro")
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_order = db.Column(db.Integer, nullable=False) 
    id_product = db.Column(db.String(60), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)

# ----- Rotte -----------------------------------------------------------------
@app.route("/")
def home():
    return redirect(url_for("products"))

# --- pagina listino ---
@app.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        name  = request.form["name"].strip()
        category  = request.form["category"].strip()
        price = float(request.form["price"].replace(",", "."))
        if name and price >= 0:
            db.session.add(Product(name=name, category=category, price=price))
            db.session.commit()
            flash("Prodotto aggiunto!", "success")
        return redirect(url_for("products"))

    items = Product.query.all()
    return render_template("products.html", items=items)

# --- pagina listino ---
@app.route("/orders", methods=["GET", "POST"])
def orders():
    # 1) Otteniamo righe già contate per (id_order, prodotto)
    rows = (
        db.session.query(
            Order.id_order,
            Product.name,
            func.count().label("qty"),
            func.min(Order.date).label("order_date"),
        )
        .join(Product, Order.id_product == Product.id)
        .group_by(Order.id_order, Product.id)          # <- conta le ripetizioni
        .order_by(Order.id_order.desc())
        .all()
    )

    # 2) Riorganizziamo i dati così:
    #    { 15: {"date": ..., "products": ["Panino (2)", "Coca-Cola"]}, ... }
    summary = {}
    for id_order, name, qty, order_date in rows:
        entry = summary.setdefault(
            id_order, {"date": order_date, "products": []}
        )
        label = f"{name} ({qty})" if qty > 1 else name
        entry["products"].append(label)

    # 3) Prepariamo la lista che passeremo al template
    items = [
        {
            "id_order": oid,
            "products": ", ".join(data["products"]),
            "order_date": data["date"],
        }
        for oid, data in summary.items()
    ]

    return render_template("orders.html", items=items)

@app.route("/update/<int:pid>", methods=["POST"])
def update_product(pid):
    p = Product.query.get_or_404(pid)
    p.name = request.form["name"].strip()
    p.category = request.form["category"].strip()
    p.price = float(request.form["price"].replace("€ ","").replace(",", "."))
    db.session.commit()
    flash("Prodotto aggiornato.", "success")
    return redirect(url_for("products"))


@app.route("/delete/product/<int:pid>", methods=["GET"])
def delete_product(pid):
    Product.query.filter_by(id=pid).delete()
    db.session.commit()
    flash("Prodotto rimosso.", "info")
    return redirect(url_for("products"))

@app.route("/delete/order/<int:pid>", methods=["POST"])
def delete_order(pid):
    Order.query.filter_by(id_order=pid).delete()
    db.session.commit()
    flash("Ordine cancellato", "info")
    return redirect(url_for("orders"))

@app.route("/print/<int:pid>", methods=["POST"])
def print_order(pid):
    app.logger.info(f"Devo stampare l'ordine {pid}")
    order = []
    results = (
        db.session.query(
            Product.name,
            func.count().label("qty"),
            Product.price
        )
        .join(Order, Order.id_product == Product.id)
        .filter(Order.id_order == pid)
        .group_by(Product.id)
        .all()
    )

    # Restituisce una lista di tuple: (nome, quantità, prezzo)
    order = [(name, qty, price) for name, qty, price in results]
    app.logger.info(f"{order}")
    print_receipt(order, pid, printer_name=app.config["PRINTER_NAME"])
    return redirect(url_for('orders'))

# --- pagina cassa ---
@app.route("/cash", methods=["GET", "POST"])
def cash():
    items = Product.query.order_by(desc(Product.category), Product.name).all()

    if request.method == "POST":
        order = []
        for it in items:
            qty = int(request.form.get(f"qty_{it.id}", 0))
            if qty > 0:
                order.append((it.name, qty, it.price))

        if not order:
            flash("Nessun articolo selezionato.", "warning")
            return redirect(url_for("cash"))

        # Conferma ordine e stampa
        try:
            next_id_order = (db.session.query(func.max(Order.id_order)).scalar() or 0) + 1
            order_ok = False
            for it in request.form:
                if it.startswith("qty"):
                    product_id = it.split("_")[1]
                    product_qty = int(request.form.get(it))
                    app.logger.info(f"Ordine con {product_id} in {product_qty} pezzi")
                    for q in range(0,product_qty):
                        db.session.add(Order(id_order=next_id_order, id_product=product_id))
                    db.session.commit()
                    order_ok = True
            if order_ok:                
                print_receipt(order, next_id_order, printer_name=app.config["PRINTER_NAME"])
                flash("Scontrino stampato!", "success")
            else:
                flash("Errore con l'ordine!", "success")
        except Exception as e:
            flash(f"Errore di stampa: {e}", "danger")
        return redirect(url_for("cash"))

    return render_template("cash.html", items=items)

# ----- main ------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--printer", required=True, help="Nome CUPS della stampante termica")
    args = parser.parse_args()
    app.config["PRINTER_NAME"] = args.printer

    try:
        with app.app_context():
            db.create_all()
        app.run(debug=True, host="0.0.0.0", port=3000)
    except Exception as e:
        app.logger.error(f"{e}")
