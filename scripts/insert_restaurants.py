# insert_restaurants.py
import csv
from db import db

def load_restaurants(filepath: str):
    registros = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['ubicacion'] = {
                "type": "Point",
                "coordinates": [
                    float(row.pop('longitude')),
                    float(row.pop('latitude'))
                ]
            }
            registros.append({
                "name":         row['name'],
                "address":      row['address'],
                "phone":        row['phone'],
                "cuisine":      row['cuisine'],
                "opening_time": row['opening_time'],
                "closing_time": row['closing_time'],
                "ubicacion":    row['ubicacion'],
            })
    return registros

def main():
    print("📂 Base de datos usada en insert_restaurants:", db.name)
    print("📋 Colecciones disponibles:", db.list_collection_names())
    before = db['restaurants'].count_documents({})
    print("🕒 Documentos antes de insertar:", before)

    docs = load_restaurants("../data/restaurants.csv")
    if not docs:
        print("⚠️ No hay restaurantes en el CSV.")
        return

    try:
        res = db['restaurants'].insert_many(docs)
        after = db['restaurants'].count_documents({})
        print(f"✅ Insertados {len(res.inserted_ids)} restaurantes.")
        print("🕒 Documentos después de insertar:", after)
    except Exception as e:
        print("❌ Error al insertar restaurantes:", e)

if __name__ == "__main__":
    main()
