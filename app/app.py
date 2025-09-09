import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.exceptions import abort

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "devsecret")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/clientesdb")
app.config["MONGO_URI"] = MONGO_URI

mongo = PyMongo(app)
col = mongo.db.cliente

def serialize(doc):
    return {
        "id": str(doc.get("_id")),
        "nombre": doc.get("nombre"),
        "dni": doc.get("dni"),
        "email": doc.get("email"),
        "fecha_nacimiento": doc.get("fecha_nacimiento")
    }

def parse_fecha(f):
    if not f:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(f, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return None

@app.route("/")
def index():
    clientes = [serialize(c) for c in col.find()]
    return render_template("index.html", clientes=clientes)

@app.route("/cliente/nuevo", methods=["GET","POST"])
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form.get("nombre","").strip()
        dni = request.form.get("dni","").strip()
        email = request.form.get("email","").strip()
        fecha = parse_fecha(request.form.get("fecha_nacimiento","").strip())

        errors = []
        if not nombre: errors.append("Nombre es requerido")
        if dni:
            try: int(dni)
            except: errors.append("DNI debe ser numérico")
        if email and "@" not in email: errors.append("Email inválido")
        if request.form.get("fecha_nacimiento") and not fecha:
            errors.append("Fecha con formato incorrecto (YYYY-MM-DD o DD/MM/YYYY)")

        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("nuevo_cliente"))

        doc = {"nombre": nombre, "dni": dni, "email": email, "fecha_nacimiento": fecha}
        res = col.insert_one(doc)
        flash("Cliente creado correctamente", "success")
        return redirect(url_for("index"))

    return render_template("nuevo.html")

@app.route("/cliente/editar/<id>", methods=["GET","POST"])
def editar_cliente(id):
    try:
        doc = col.find_one({"_id": ObjectId(id)})
    except Exception:
        abort(404)
    if not doc:
        abort(404)
    if request.method == "POST":
        nombre = request.form.get("nombre","").strip()
        dni = request.form.get("dni","").strip()
        email = request.form.get("email","").strip()
        fecha = parse_fecha(request.form.get("fecha_nacimiento","").strip())

        errors = []
        if not nombre: errors.append("Nombre es requerido")
        if dni:
            try: int(dni)
            except: errors.append("DNI debe ser numérico")
        if email and "@" not in email: errors.append("Email inválido")
        if request.form.get("fecha_nacimiento") and not fecha:
            errors.append("Fecha con formato incorrecto (YYYY-MM-DD o DD/MM/YYYY)")

        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("editar_cliente", id=id))

        upd = {"nombre": nombre, "dni": dni, "email": email, "fecha_nacimiento": fecha}
        col.update_one({"_id": ObjectId(id)}, {"$set": upd})
        flash("Cliente actualizado", "success")
        return redirect(url_for("index"))

    cliente = serialize(doc)
    return render_template("editar.html", cliente=cliente)

@app.route("/cliente/eliminar/<id>", methods=["POST"])
def eliminar_cliente(id):
    try:
        res = col.delete_one({"_id": ObjectId(id)})
    except Exception:
        flash("ID inválido", "error")
        return redirect(url_for("index"))
    flash("Cliente eliminado" if res.deleted_count else "Cliente no encontrado", "success")
    return redirect(url_for("index"))

# --- REST API ---
@app.route("/api/clientes", methods=["GET"])
def api_listar():
    return jsonify([serialize(c) for c in col.find()])

@app.route("/api/clientes/<id>", methods=["GET"])
def api_get(id):
    try:
        doc = col.find_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error":"id inválido"}), 400
    if not doc:
        return jsonify({"error":"cliente no encontrado"}), 404
    return jsonify(serialize(doc))

@app.route("/api/clientes", methods=["POST"])
def api_create():
    data = request.get_json(force=True, silent=True) or {}
    nombre = data.get("nombre")
    dni = data.get("dni")
    email = data.get("email")
    fecha = parse_fecha(data.get("fecha_nacimiento"))

    if not nombre:
        return jsonify({"error":"nombre es requerido"}), 400
    if dni:
        try: int(dni)
        except: return jsonify({"error":"dni debe ser numérico"}), 400
    if email and "@" not in email:
        return jsonify({"error":"email inválido"}), 400

    doc = {"nombre": nombre, "dni": dni, "email": email, "fecha_nacimiento": fecha}
    res = col.insert_one(doc)
    return jsonify(serialize(col.find_one({"_id": res.inserted_id}))), 201

@app.route("/api/clientes/<id>", methods=["PUT","PATCH"])
def api_update(id):
    try:
        doc = col.find_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error":"id inválido"}), 400
    if not doc:
        return jsonify({"error":"cliente no encontrado"}), 404
    data = request.get_json(force=True, silent=True) or {}
    upd = {}
    if "nombre" in data: upd["nombre"] = data["nombre"]
    if "dni" in data: 
        try: int(data["dni"]); upd["dni"]=data["dni"]
        except: return jsonify({"error":"dni debe ser numérico"}), 400
    if "email" in data:
        if "@" not in data["email"]: return jsonify({"error":"email inválido"}), 400
        upd["email"]=data["email"]
    if "fecha_nacimiento" in data:
        fecha = parse_fecha(data["fecha_nacimiento"])
        if data["fecha_nacimiento"] and not fecha:
            return jsonify({"error":"fecha inválida"}), 400
        upd["fecha_nacimiento"]=fecha

    col.update_one({"_id": ObjectId(id)}, {"$set": upd})
    return jsonify(serialize(col.find_one({"_id": ObjectId(id)})))

@app.route("/api/clientes/<id>", methods=["DELETE"])
def api_delete(id):
    try:
        res = col.delete_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error":"id inválido"}), 400
    if res.deleted_count==0:
        return jsonify({"error":"cliente no encontrado"}), 404
    return jsonify({"deleted": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)