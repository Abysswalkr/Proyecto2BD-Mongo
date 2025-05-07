# insert_users.py
import csv
from db import db  # tu conexión a Atlas
from bson import ObjectId

def load_users(filepath: str):
    registros = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # No hay tipos especiales aquí, todo queda como string
            registros.append({
                "username": row["username"],
                "email": row["email"],
                "full_name": row.get("full_name") or None,
                "joined_date": row["joined_date"]
            })
    return registros

def main():
    csv_path = "../data/users.csv"
    coleccion = db["users"]

    docs = load_users(csv_path)
    if not docs:
        print("⚠️  No se encontraron filas en users.csv.")
        return

    try:
        res = coleccion.insert_many(docs)
        print(f"✅ Insertados {len(res.inserted_ids)} usuarios.")
    except Exception as e:
        print("❌ Error al insertar usuarios:", e)

if __name__ == "__main__":
    main()
