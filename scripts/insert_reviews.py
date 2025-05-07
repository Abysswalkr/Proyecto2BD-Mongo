# insert_reviews.py
import csv
from db import db
from bson import ObjectId

def load_reviews(filepath: str):
    registros = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convierte tipos y ObjectId
            try:
                rest_id = ObjectId(row["restaurant_id"])
                user_id = ObjectId(row["user_id"])
            except Exception:
                print(f"⚠️ ID inválido: {row}")
                continue

            registros.append({
                "restaurant_id": rest_id,
                "user_id": user_id,
                "rating": int(row["rating"]),
                "comment": row.get("comment") or "",
                "date": row["date"]
            })
    return registros

def main():
    csv_path = "../data/reviews.csv"
    coleccion = db["reviews"]

    docs = load_reviews(csv_path)
    if not docs:
        print("⚠️  No se encontraron filas en reviews.csv.")
        return

    try:
        res = coleccion.insert_many(docs)
        print(f"✅ Insertadas {len(res.inserted_ids)} reseñas.")
    except Exception as e:
        print("❌ Error al insertar reseñas:", e)

if __name__ == "__main__":
    main()
