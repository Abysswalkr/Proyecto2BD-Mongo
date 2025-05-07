# scripts/insert_menu_items.py

import csv
from bson import ObjectId
from db import db

# Ruta ABSOLUTA a tu archivo CSV según tu estructura
CSV_PATH = r"C:\Users\joses\PycharmProjects\Proyecto2BD\data\menu_items.csv"

def load_menu_items(filepath: str):
    registros = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rest_id = ObjectId(row["restaurant_id"])
            except Exception:
                print(f"⚠️ ID de restaurante inválido: {row['restaurant_id']}")
                continue

            registros.append({
                "restaurant_id": rest_id,
                "name": row["name"],
                "description": row.get("description") or "",
                "price": float(row["price"]),
                "available": row["available"].lower() in ("true", "1", "yes")
            })
    return registros

def main():
    coleccion = db["menu_items"]
    docs = load_menu_items(CSV_PATH)

    if not docs:
        print(f"⚠️  No se encontraron filas en {CSV_PATH}.")
        return

    try:
        res = coleccion.insert_many(docs)
        print(f"✅ Insertados {len(res.inserted_ids)} artículos de menú.")
    except Exception as e:
        print("❌ Error al insertar artículos de menú:", e)

if __name__ == "__main__":
    main()
