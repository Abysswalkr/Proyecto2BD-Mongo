# scripts/create_indexes.py
from db import db

def main():
    # — Orders —
    # Índice único en order_id
    db["orders"].create_index("order_id", unique=True)
    # Índice compuesto en date + restaurant
    db["orders"].create_index([("date", 1), ("restaurant", 1)])

    # — Users —
    # Email único
    db["users"].create_index("email", unique=True)
    # Username con búsqueda regex
    db["users"].create_index("username")

    # — Restaurants —
    # Geoespacial 2dsphere en ubicacion
    db["restaurants"].create_index([("ubicacion", "2dsphere")])
    # Índice compuesto en cuisine + name
    db["restaurants"].create_index([("cuisine", 1), ("name", 1)])

    # — MenuItems —
    # Índice en restaurant_id
    db["menu_items"].create_index("restaurant_id")
    # Índice de texto en descripción
    db["menu_items"].create_index([("description", "text")])

    # — Reviews —
    # Índice en restaurant_id + rating (para top‐5)
    db["reviews"].create_index([("restaurant_id", 1), ("rating", -1)])
    # Índice de texto en comment
    db["reviews"].create_index([("comment", "text")])

    print("✅ Índices creados correctamente.")

if __name__ == "__main__":
    main()
