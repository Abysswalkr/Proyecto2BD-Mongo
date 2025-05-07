# cli.py
import sys
import json
import requests

API = "http://localhost:8000"

MENU_OPTIONS = {
    "1": "Listado de órdenes",
    "2": "Crear nueva orden",
    "3": "Ver detalle de orden",
    "4": "Actualizar orden",
    "5": "Eliminar orden",

    "6": "Listado de restaurantes",
    "7": "Crear nuevo restaurante",
    "8": "Ver detalle de restaurante",
    "9": "Actualizar restaurante",
    "10": "Eliminar restaurante",

    "11": "Listado de usuarios",
    "12": "Crear nuevo usuario",
    "13": "Ver detalle de usuario",
    "14": "Actualizar usuario",
    "15": "Eliminar usuario",

    "16": "Listado de artículos de menú",
    "17": "Crear artículo de menú",
    "18": "Ver detalle de artículo",
    "19": "Actualizar artículo de menú",
    "20": "Eliminar artículo de menú",

    "21": "Listado de reseñas",
    "22": "Crear reseña",
    "23": "Ver detalle de reseña",
    "24": "Actualizar reseña",
    "25": "Eliminar reseña",

    "26": "Operación masiva (bulk)",
    "27": "Subir archivo (GridFS)",
    "28": "Descargar archivo (GridFS)",

    "29": "Reporte: total de órdenes",
    "30": "Reporte: tipos de cocina",
    "31": "Reporte: top restaurantes",
    "32": "Reporte: artículos más caros",

    "0": "Salir"
}

def print_menu():
    print("\n=== MENÚ CONSOLA ===")
    for key, desc in MENU_OPTIONS.items():
        print(f" {key}) {desc}")
    print()

def print_list(items, fields, title):
    print(f"\n-- {title} --")
    if not items:
        print("(sin resultados)")
        return
    for item in items:
        line = " | ".join(f"{label}: {item.get(field, '')}" for field, label in fields)
        print(line)
    print()

# --- CRUD Órdenes ---
def listar_orders():
    # 1) Pide primero el restaurante
    rid = select_restaurant()
    params = {}
    if rid:
        # 2) Obtén el name para filtrar
        resp = requests.get(f"{API}/restaurants/{rid}")
        if resp.status_code == 200:
            params["restaurant"] = resp.json().get("name")
        else:
            print("⚠️ Restaurante no encontrado, mostrando todas las órdenes.")
    # 3) Límite de registros
    limite = input("Límite de registros (enter=100): ").strip()
    params["limit"] = int(limite) if limite.isdigit() else 100
    # 4) Llamada a la API con params
    r = requests.get(f"{API}/orders/", params=params)
    print_list(
        r.json(),
        [
            ("_id","ID"),("order_id","OrderID"),
            ("restaurant","Restaurante"),("date","Fecha"),
            ("total_amount","Total"),("rating","Calificación")
        ],
        "Órdenes"
    )


def crear_order():
    o = {
        "order_id": int(input("order_id: ")),
        "restaurant": input("restaurant: "),
        "date": input("date (YYYY-MM-DD): "),
        "total_amount": float(input("total_amount: ")),
        "rating": int(input("rating (1-5): "))
    }
    r = requests.post(f"{API}/orders/", json=o)
    print(json.dumps(r.json(), indent=2))

def ver_order():
    oid = input("ID del pedido: ")
    r = requests.get(f"{API}/orders/{oid}")
    o = r.json()
    if r.status_code != 200 or "_id" not in o:
        print(f"No se encontró la orden con ID {oid}\n")
        return
    print("\n-- Detalle de Orden --")
    print(f"ID: {o['_id']}")
    print(f"Número de Orden: {o['order_id']}")
    print(f"Restaurante: {o['restaurant']}")
    print(f"Fecha: {o['date']}")
    print(f"Total: {o['total_amount']}")
    print(f"Calificación: {o['rating']}\n")

def actualizar_order():
    oid = input("ID del pedido: ")
    o = {
        "order_id": int(input("order_id: ")),
        "restaurant": input("restaurant: "),
        "date": input("date (YYYY-MM-DD): "),
        "total_amount": float(input("total_amount: ")),
        "rating": int(input("rating (1-5): "))
    }
    r = requests.put(f"{API}/orders/{oid}", json=o)
    print(json.dumps(r.json(), indent=2))

def eliminar_order():
    oid = input("ID del pedido a eliminar: ").strip()
    r = requests.delete(f"{API}/orders/{oid}")
    if r.status_code == 200:
        res = r.json()
        if res.get("status") == "eliminado":
            print(f"✅ Pedido con ID {oid} eliminado correctamente.\n")
        else:
            print(f"⚠️ Respuesta inesperada del servidor: {res}\n")
    else:
        print(f"❌ Error al eliminar el pedido (HTTP {r.status_code}): {r.text}\n")


# --- CRUD Restaurantes ---
def listar_restaurants():
    r = requests.get(f"{API}/restaurants/")
    data = r.json()
    print_list(data,
        [('_id','ID'),('name','Nombre'),('address','Dirección'),
         ('cuisine','Cocina')],
        'Restaurantes')

def crear_restaurant():
    rt = {
        "name": input("name: "),
        "address": input("address: "),
        "phone": input("phone: "),
        "cuisine": input("cuisine: "),
        "opening_time": input("opening_time (HH:MM): "),
        "closing_time": input("closing_time (HH:MM): "),
        "ubicacion": {
            "type": "Point",
            "coordinates": [
                float(input("longitude: ")),
                float(input("latitude: "))
            ]
        }
    }
    r = requests.post(f"{API}/restaurants/", json=rt)
    print(json.dumps(r.json(), indent=2))

def ver_restaurant():
    rid = input("ID del restaurante: ")
    r = requests.get(f"{API}/restaurants/{rid}")
    d = r.json()
    if r.status_code != 200 or "_id" not in d:
        print(f"No se encontró el restaurante con ID {rid}\n")
        return
    print("\n-- Detalle de Restaurante --")
    print(f"ID: {d['_id']}")
    print(f"Nombre: {d['name']}")
    print(f"Dirección: {d['address']}")
    print(f"Teléfono: {d['phone']}")
    print(f"Cocina: {d['cuisine']}")
    print(f"Horario: {d['opening_time']} - {d['closing_time']}")
    coords = d.get('ubicacion', {}).get('coordinates', [])
    if coords:
        print(f"Ubicación: longitud {coords[0]}, latitud {coords[1]}\n")
    else:
        print()

def actualizar_restaurant():
    rid = input("ID del restaurante: ")
    rt = {
        "name": input("name: "),
        "address": input("address: "),
        "phone": input("phone: "),
        "cuisine": input("cuisine: "),
        "opening_time": input("opening_time (HH:MM): "),
        "closing_time": input("closing_time (HH:MM): "),
        "ubicacion": {
            "type": "Point",
            "coordinates": [
                float(input("longitude: ")),
                float(input("latitude: "))
            ]
        }
    }
    r = requests.put(f"{API}/restaurants/{rid}", json=rt)
    print(json.dumps(r.json(), indent=2))

def eliminar_restaurant():
    rid = input("ID del restaurante a eliminar: ").strip()
    r = requests.delete(f"{API}/restaurants/{rid}")
    if r.status_code == 200:
        res = r.json()
        if res.get("status") == "eliminado":
            print(f"✅ Restaurante con ID {rid} eliminado correctamente.\n")
        else:
            print(f"⚠️ Respuesta inesperada del servidor: {res}\n")
    else:
        print(f"❌ Error al eliminar el restaurante (HTTP {r.status_code}): {r.text}\n")


def select_restaurant():
    resp = requests.get(f"{API}/restaurants/")
    restos = resp.json() or []
    if not restos:
        print("❌ No hay restaurantes registrados.")
        return None
    print("\n-- Restaurantes --")
    for r in restos:
        print(f"{r['_id']} : {r['name']}")
    rid = input("Seleccione el ID del restaurante (enter para ninguno): ").strip()
    return rid or None


# --- CRUD Usuarios ---
def listar_users():
    r = requests.get(f"{API}/users/")
    data = r.json()
    print_list(data,
        [('_id','ID'),('username','Usuario'),('email','Email'),
         ('full_name','Nombre')],
        'Usuarios')

def crear_user():
    u = {
        "username": input("username: "),
        "email": input("email: "),
        "full_name": input("full_name: "),
        "joined_date": input("joined_date (YYYY-MM-DD): ")
    }
    r = requests.post(f"{API}/users/", json=u)
    print(json.dumps(r.json(), indent=2))

def ver_user():
    uid = input("ID del usuario: ")
    r = requests.get(f"{API}/users/{uid}")
    u = r.json()
    if r.status_code != 200 or "_id" not in u:
        print(f"No se encontró el usuario con ID {uid}\n")
        return
    print("\n-- Detalle de Usuario --")
    print(f"ID: {u['_id']}")
    print(f"Usuario: {u['username']}")
    print(f"Email: {u['email']}")
    print(f"Nombre completo: {u.get('full_name','')}\n")

def actualizar_user():
    uid = input("ID del usuario: ")
    u = {
        "username": input("username: "),
        "email": input("email: "),
        "full_name": input("full_name: "),
        "joined_date": input("joined_date (YYYY-MM-DD): ")
    }
    r = requests.put(f"{API}/users/{uid}", json=u)
    print(json.dumps(r.json(), indent=2))

def eliminar_user():
    uid = input("ID del usuario a eliminar: ").strip()
    r = requests.delete(f"{API}/users/{uid}")
    if r.status_code == 200:
        res = r.json()
        if res.get("status") == "eliminado":
            print(f"✅ Usuario con ID {uid} eliminado correctamente.\n")
        else:
            print(f"⚠️ Respuesta inesperada del servidor: {res}\n")
    else:
        print(f"❌ Error al eliminar el usuario (HTTP {r.status_code}): {r.text}\n")


# --- CRUD Artículos de Menú ---
def listar_menu_items():
    # 1) Pide primero el restaurante
    rid = select_restaurant()
    params = {}
    if rid:
        # 2) Filtra por restaurant_id
        params["restaurant_id"] = rid
    # 3) Llamada a la API con params
    r = requests.get(f"{API}/menu_items/", params=params)
    print_list(
        r.json(),
        [("_id","ID"),("name","Artículo"),("price","Precio"),("available","Disponible")],
        "Menú Items"
    )

def crear_menu_item():
    print("\n--- Crear Menú Item ---")

    rid = select_restaurant()
    if not rid:
        print("❌ Debes seleccionar un restaurante primero.")
        return


    mi = {
        "restaurant_id": rid,
        "name": input("name: "),
        "description": input("description: "),
        "price": float(input("price: ")),
        "available": input("available (True/False): ").strip().lower() in ("true","1","yes")
    }

    
    r = requests.post(f"{API}/menu_items/", json=mi)
    print(json.dumps(r.json(), indent=2))

def ver_menu_item():
    mid = input("ID del artículo: ")
    r = requests.get(f"{API}/menu_items/{mid}")
    m = r.json()
    if r.status_code != 200 or "_id" not in m:
        print(f"No se encontró el artículo con ID {mid}\n")
        return
    print("\n-- Detalle de Artículo de Menú --")
    print(f"ID: {m['_id']}")
    print(f"Nombre: {m['name']}")
    print(f"Descripción: {m.get('description','')}")
    print(f"Precio: {m['price']}")
    print(f"Disponible: {m['available']}\n")

def actualizar_menu_item():
    mid = input("ID del artículo: ")
    mi = {
        "restaurant_id": input("restaurant_id: "),
        "name": input("name: "),
        "description": input("description: "),
        "price": float(input("price: ")),
        "available": input("available (True/False): ").lower() in ("true","1","yes")
    }
    r = requests.put(f"{API}/menu_items/{mid}", json=mi)
    print(json.dumps(r.json(), indent=2))

def eliminar_menu_item():
    mid = input("ID del artículo de menú a eliminar: ").strip()
    r = requests.delete(f"{API}/menu_items/{mid}")
    if r.status_code == 200:
        res = r.json()
        if res.get("status") == "eliminado":
            print(f"✅ Artículo de menú con ID {mid} eliminado correctamente.\n")
        else:
            print(f"⚠️ Respuesta inesperada del servidor: {res}\n")
    else:
        print(f"❌ Error al eliminar el artículo de menú (HTTP {r.status_code}): {r.text}\n")


# --- CRUD Reseñas ---
def listar_reviews():
    # -- pide primero el restaurante --
    rid = select_restaurant()
    params = {}
    if rid:
        params["restaurant_id"] = rid

    # -- llamada filtrada --
    r = requests.get(f"{API}/reviews/", params=params)
    print_list(
        r.json(),
        [("_id","ID"),("user_id","UserID"),("rating","Rating"),("comment","Comentario")],
        "Reseñas"
    )

def crear_review():
    rv = {
        "restaurant_id": input("restaurant_id: "),
        "user_id": input("user_id: "),
        "rating": int(input("rating: ")),
        "comment": input("comment: "),
        "date": input("date (YYYY-MM-DD): ")
    }
    r = requests.post(f"{API}/reviews/", json=rv)
    print(json.dumps(r.json(), indent=2))

def ver_review():
    rid = input("ID de reseña: ")
    r = requests.get(f"{API}/reviews/{rid}")
    rv = r.json()
    if r.status_code != 200 or "_id" not in rv:
        print(f"No se encontró la reseña con ID {rid}\n")
        return
    print("\n-- Detalle de Reseña --")
    print(f"ID: {rv['_id']}")
    print(f"Restaurante ID: {rv['restaurant_id']}")
    print(f"Usuario ID: {rv['user_id']}")
    print(f"Calificación: {rv['rating']}")
    print(f"Comentario: {rv.get('comment','')}")
    print(f"Fecha: {rv['date']}\n")


def actualizar_review():
    rid = input("ID de reseña: ")
    rv = {
        "restaurant_id": input("restaurant_id: "),
        "user_id": input("user_id: "),
        "rating": int(input("rating: ")),
        "comment": input("comment: "),
        "date": input("date (YYYY-MM-DD): ")
    }
    r = requests.put(f"{API}/reviews/{rid}", json=rv)
    print(json.dumps(r.json(), indent=2))

def eliminar_review():
    rid = input("ID de la reseña a eliminar: ").strip()
    r = requests.delete(f"{API}/reviews/{rid}")
    if r.status_code == 200:
        res = r.json()
        if res.get("status") == "eliminado":
            print(f"✅ Reseña con ID {rid} eliminada correctamente.\n")
        else:
            print(f"⚠️ Respuesta inesperada del servidor: {res}\n")
    else:
        print(f"❌ Error al eliminar la reseña (HTTP {r.status_code}): {r.text}\n")


# --- Operaciones Masivas (Bulk) ---
def bulk_operation():
    coll = input("Colección (orders, restaurants, users, menu_items, reviews): ")
    print("Introduce operaciones JSON y termina con Ctrl+D:")
    blob = sys.stdin.read()
    ops = json.loads(blob)
    r = requests.post(f"{API}/bulk/{coll}", json=ops)
    print(json.dumps(r.json(), indent=2))

# --- GridFS ---
def upload_file():
    path = input("Ruta al archivo: ")
    with open(path, "rb") as f:
        files = {"file": (path, f, "application/octet-stream")}
        r = requests.post(f"{API}/files/upload", files=files)
    print(json.dumps(r.json(), indent=2))

def download_file():
    fid = input("file_id: ")
    r = requests.get(f"{API}/files/{fid}")
    if r.status_code == 200:
        out = input("Guardar como: ")
        with open(out, "wb") as f:
            f.write(r.content)
        print(f"Archivo guardado en {out}")
    else:
        try:
            print(json.dumps(r.json(), indent=2))
        except:
            print(r.text)

# --- Reportes ---
def report_total_orders():
    r = requests.get(f"{API}/reports/orders/count")
    print(json.dumps(r.json(), indent=2))

def report_distinct_cuisines():
    r = requests.get(f"{API}/reports/restaurants/distinct_cuisines")
    print(json.dumps(r.json(), indent=2))

def report_top_restaurants():
    n = input("Top N: ")
    r = requests.get(f"{API}/reports/reviews/top_restaurants?limit={n}")
    print(json.dumps(r.json(), indent=2))

def report_most_expensive():
    n = input("Top N: ")
    r = requests.get(f"{API}/reports/menu_items/most_expensive?limit={n}")
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    while True:
        print_menu()
        opt = input("Opción: ").strip()
        if opt in ['1','2','3','4','5']:
            { '1': listar_orders, '2': crear_order, '3': ver_order,
              '4': actualizar_order, '5': eliminar_order }[opt]()
        elif opt in ['6','7','8','9','10']:
            { '6': listar_restaurants, '7': crear_restaurant, '8': ver_restaurant,
              '9': actualizar_restaurant, '10': eliminar_restaurant }[opt]()
        elif opt in ['11','12','13','14','15']:
            { '11': listar_users, '12': crear_user, '13': ver_user,
              '14': actualizar_user, '15': eliminar_user }[opt]()
        elif opt in ['16','17','18','19','20']:
            { '16': listar_menu_items, '17': crear_menu_item, '18': ver_menu_item,
              '19': actualizar_menu_item, '20': eliminar_menu_item }[opt]()
        elif opt in ['21','22','23','24','25']:
            { '21': listar_reviews, '22': crear_review, '23': ver_review,
              '24': actualizar_review, '25': eliminar_review }[opt]()
        elif opt == '26':
            bulk_operation()
        elif opt == '27':
            upload_file()
        elif opt == '28':
            download_file()
        elif opt in ['29','30','31','32']:
            { '29': report_total_orders, '30': report_distinct_cuisines,
              '31': report_top_restaurants, '32': report_most_expensive }[opt]()
        elif opt == '0':
            print("Saliendo…")
            sys.exit(0)
        else:
            print("Opción no válida. Intenta de nuevo.")
