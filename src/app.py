#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash, logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import argparse
from printing import print_receipt


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

@app.route("/update/<int:pid>", methods=["POST"])
def update_product(pid):
    p = Product.query.get_or_404(pid)
    p.name = request.form["name"].strip()
    p.category = request.form["category"].strip()
    p.price = float(request.form["price"].replace("€ ","").replace(",", "."))
    db.session.commit()
    flash("Prodotto aggiornato.", "success")
    return redirect(url_for("products"))


@app.route("/delete/<int:pid>")
def delete(pid):
    Product.query.filter_by(id=pid).delete()
    db.session.commit()
    flash("Prodotto rimosso.", "info")
    return redirect(url_for("products"))

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

        # stampa scontrino
        try:
            print_receipt(order, printer_name=app.config["PRINTER_NAME"])
            flash("Scontrino stampato!", "success")
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
