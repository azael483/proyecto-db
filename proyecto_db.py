import mysql.connector
from tabulate import tabulate
from flask import Flask, render_template

conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Azael483",
    database="constructoradb"
)

app = Flask(__name__)

@app.route("/proyecto/<int:id>")
#@app.route("/proyecto/la_constructora_de_Bob")
def proyecto(id):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.callproc("PresupuestoProyecto", [id])

    for result in cursor.stored_results():
        filas = result.fetchall()
        columnas = [desc[0] for desc in result.description]

    cursor.close()
    conexion.close()

    return render_template("proyecto.html", columnas=columnas, filas=filas)

app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True)