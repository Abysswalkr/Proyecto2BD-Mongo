# insert_data.py
import csv
from db import db

def load_csv(filepath: str):
    registros = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convierte campos numéricos:
            row['order_id']     = int(row['order_id'])
            row['total_amount'] = float(row['total_amount'])
            row['rating']       = int(row['rating'])
            registros.append(row)
    return registros

def main():
    csv_path = "../data/orders.csv"  # Asegúrate que exista junto a este script
    coleccion = db['orders']         # Colección destino

    docs = load_csv(csv_path)
    if not docs:
        print("⚠️  No se encontraron filas en el CSV.")
        return

    try:
        resultado = coleccion.insert_many(docs)
        print(f"✅ Insertados {len(resultado.inserted_ids)} documentos en 'orders'")
    except Exception as e:
        print("❌ Error durante la inserción masiva:", e)

if __name__ == "__main__":
    main()
