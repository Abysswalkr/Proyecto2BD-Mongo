# main.py
import gridfs

from fastapi import FastAPI, HTTPException, Query, APIRouter, UploadFile, File, Response, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from pymongo import InsertOne, UpdateOne, DeleteOne
from bson import ObjectId

from db import db


# inicializar GridFS sobre la BD actual
fs = gridfs.GridFS(db, collection="fs")

# —— Validador de ObjectId para Pydantic V1 ——
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("ID inválido")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# —— Modelo Order (Pydantic V1) ——
class Order(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    order_id: int
    restaurant: str
    date: str
    total_amount: float
    rating: int

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# —— Modelo Restaurant (Pydantic V1) ——
class Restaurant(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    address: str
    phone: str
    cuisine: str
    opening_time: str
    closing_time: str
    ubicacion: dict  # GeoJSON with "type": "Point" and "coordinates": [lng, lat]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# — Modelo User —
class User(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    username: str
    email: str
    full_name: Optional[str]
    joined_date: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# — Modelo MenuItem —
class MenuItem(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    restaurant_id: PyObjectId
    name: str
    description: Optional[str]
    price: float
    available: bool

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# — Modelo Review —
class Review(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    restaurant_id: PyObjectId
    user_id: PyObjectId
    rating: int
    comment: Optional[str]
    date: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# - Modelo Pydamic para operaciones -
class BulkOp(BaseModel):
    type: Literal["insert","update","delete"]
    filter: Optional[dict] = None       # para update o delete
    document: Optional[dict] = None     # para insert
    update: Optional[dict] = None       # para update
    upsert: Optional[bool] = False      # para update


# —— FastAPI setup ——
app = FastAPI(title="API Pedidos y Restaurantes")


# — UTILIDADES COMUNES PARA LISTADOS —
def build_projection(fields: Optional[str]) -> Optional[dict]:
    if not fields:
        return None
    return {f: 1 for f in fields.split(",")}

def build_sort(sort_by: Optional[str], order: str) -> Optional[tuple]:
    if not sort_by:
        return None
    direction = 1 if order.lower() == "asc" else -1
    return (sort_by, direction)


# — RUTAS Orders —
@app.get("/orders/", response_model=List[Order])
def list_orders(
    restaurant: Optional[str] = Query(None, description="Filtrar por nombre de restaurante"),
    date:       Optional[str] = Query(None, description="Filtrar por fecha YYYY-MM-DD"),
    skip:       int = Query(0, ge=0),
    limit:      int = Query(10, ge=1),
    sort_by:    Optional[str] = Query("date"),
    order:      str = Query("asc", regex="^(asc|desc)$"),
    fields:     Optional[str] = Query(None, description="Campos separados por coma")
):
    filt = {}
    if restaurant:  filt["restaurant"] = restaurant
    if date:        filt["date"] = date

    proj = build_projection(fields)
    sort = build_sort(sort_by, order)

    cursor = db["orders"].find(filt, proj) if proj else db["orders"].find(filt)
    if sort:    cursor = cursor.sort([sort])
    cursor = cursor.skip(skip).limit(limit)
    return list(cursor)


@app.post("/orders/", response_model=Order)
def create_order(order: Order):
    data = order.dict(by_alias=True, exclude={"id"})
    res = db["orders"].insert_one(data)
    return db["orders"].find_one({"_id": res.inserted_id})


@app.get("/orders/{oid}", response_model=Order)
def get_order(oid: str):
    doc = db["orders"].find_one({"_id": ObjectId(oid)})
    if not doc:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return doc


@app.put("/orders/{oid}", response_model=Order)
def update_order(oid: str, order: Order):
    data = order.dict(by_alias=True, exclude={"id"})
    res = db["orders"].update_one({"_id": ObjectId(oid)}, {"$set": data})
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="No se actualizó el pedido")
    return db["orders"].find_one({"_id": ObjectId(oid)})


@app.delete("/orders/{oid}")
def delete_order(oid: str):
    res = db["orders"].delete_one({"_id": ObjectId(oid)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No se eliminó el pedido")
    return {"status": "eliminado"}


# — RUTAS Restaurants —
@app.get("/restaurants/", response_model=List[Restaurant])
def list_restaurants(
    name:       Optional[str] = Query(None, description="Buscar por nombre (regex ignore-case)"),
    cuisine:    Optional[str] = Query(None, description="Filtrar por tipo de cocina"),
    skip:       int = Query(0, ge=0),
    limit:      int = Query(10, ge=1),
    sort_by:    Optional[str] = Query(None),
    order:      str = Query("asc", regex="^(asc|desc)$"),
    fields:     Optional[str] = Query(None)
):
    filt = {}
    if name:
        filt["name"] = {"$regex": name, "$options": "i"}
    if cuisine:
        filt["cuisine"] = cuisine

    proj = build_projection(fields)
    sort = build_sort(sort_by, order)

    cursor = db["restaurants"].find(filt, proj) if proj else db["restaurants"].find(filt)
    if sort:    cursor = cursor.sort([sort])
    cursor = cursor.skip(skip).limit(limit)
    return list(cursor)



@app.post("/restaurants/", response_model=Restaurant)
def create_restaurant(restaurant: Restaurant):
    data = restaurant.dict(by_alias=True, exclude={"id"})
    res = db["restaurants"].insert_one(data)
    return db["restaurants"].find_one({"_id": res.inserted_id})


@app.get("/restaurants/{rid}", response_model=Restaurant)
def get_restaurant(rid: str):
    doc = db["restaurants"].find_one({"_id": ObjectId(rid)})
    if not doc:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
    return doc


@app.put("/restaurants/{rid}", response_model=Restaurant)
def update_restaurant(rid: str, restaurant: Restaurant):
    data = restaurant.dict(by_alias=True, exclude={"id"})
    res = db["restaurants"].update_one({"_id": ObjectId(rid)}, {"$set": data})
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="No se actualizó el restaurante")
    return db["restaurants"].find_one({"_id": ObjectId(rid)})


@app.delete("/restaurants/{rid}")
def delete_restaurant(rid: str):
    res = db["restaurants"].delete_one({"_id": ObjectId(rid)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No se eliminó el restaurante")
    return {"status": "eliminado"}


# — RUTAS Users —
@app.get("/users/", response_model=List[User])
def list_users(
    username:   Optional[str] = Query(None),
    email:      Optional[str] = Query(None),
    skip:       int = Query(0, ge=0),
    limit:      int = Query(10, ge=1),
    sort_by:    Optional[str] = Query(None),
    order:      str = Query("asc", regex="^(asc|desc)$"),
    fields:     Optional[str] = Query(None)
):
    filt = {}
    if username: filt["username"] = {"$regex": username, "$options": "i"}
    if email:    filt["email"]    = email

    proj = build_projection(fields)
    sort = build_sort(sort_by, order)

    cursor = db["users"].find(filt, proj) if proj else db["users"].find(filt)
    if sort:    cursor = cursor.sort([sort])
    cursor = cursor.skip(skip).limit(limit)
    return list(cursor)

@app.post("/users/", response_model=User)
def create_user(user: User):
    data = user.dict(by_alias=True, exclude={"id"})
    res = db["users"].insert_one(data)
    return db["users"].find_one({"_id": res.inserted_id})

@app.get("/users/{uid}", response_model=User)
def get_user(uid: str):
    doc = db["users"].find_one({"_id": ObjectId(uid)})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return doc

@app.put("/users/{uid}", response_model=User)
def update_user(uid: str, user: User):
    data = user.dict(by_alias=True, exclude={"id"})
    res = db["users"].update_one({"_id": ObjectId(uid)}, {"$set": data})
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="No se actualizó el usuario")
    return db["users"].find_one({"_id": ObjectId(uid)})

@app.delete("/users/{uid}")
def delete_user(uid: str):
    res = db["users"].delete_one({"_id": ObjectId(uid)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No se eliminó el usuario")
    return {"status": "eliminado"}


# — RUTAS MenuItems —
@app.get("/menu_items/", response_model=List[MenuItem])
def list_menu_items(
    restaurant_id: Optional[str] = Query(None, description="ObjectId del restaurante"),
    available:     Optional[bool] = Query(None),
    skip:          int = Query(0, ge=0),
    limit:         int = Query(10, ge=1),
    sort_by:       Optional[str] = Query(None),
    order:         str = Query("asc", regex="^(asc|desc)$"),
    fields:        Optional[str] = Query(None)
):
    filt = {}
    if restaurant_id:
        try:
            filt["restaurant_id"] = ObjectId(restaurant_id)
        except:
            raise HTTPException(400, "restaurant_id inválido")
    if available is not None:
        filt["available"] = available

    proj = build_projection(fields)
    sort = build_sort(sort_by, order)

    cursor = db["menu_items"].find(filt, proj) if proj else db["menu_items"].find(filt)
    if sort:    cursor = cursor.sort([sort])
    cursor = cursor.skip(skip).limit(limit)
    return list(cursor)

@app.post("/menu_items/", response_model=MenuItem)
def create_menu_item(item: MenuItem):
    data = item.dict(by_alias=True, exclude={"id"})
    res = db["menu_items"].insert_one(data)
    return db["menu_items"].find_one({"_id": res.inserted_id})

@app.get("/menu_items/{mid}", response_model=MenuItem)
def get_menu_item(mid: str):
    doc = db["menu_items"].find_one({"_id": ObjectId(mid)})
    if not doc:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    return doc

@app.put("/menu_items/{mid}", response_model=MenuItem)
def update_menu_item(mid: str, item: MenuItem):
    data = item.dict(by_alias=True, exclude={"id"})
    res = db["menu_items"].update_one({"_id": ObjectId(mid)}, {"$set": data})
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="No se actualizó el artículo")
    return db["menu_items"].find_one({"_id": ObjectId(mid)})

@app.delete("/menu_items/{mid}")
def delete_menu_item(mid: str):
    res = db["menu_items"].delete_one({"_id": ObjectId(mid)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No se eliminó el artículo")
    return {"status": "eliminado"}


# — RUTAS Reviews —
@app.get("/reviews/", response_model=List[Review])
def list_reviews(
    restaurant_id: Optional[str] = Query(None),
    user_id:       Optional[str] = Query(None),
    skip:          int = Query(0, ge=0),
    limit:         int = Query(10, ge=1),
    sort_by:       Optional[str] = Query(None),
    order:         str = Query("asc", regex="^(asc|desc)$"),
    fields:        Optional[str] = Query(None)
):
    filt = {}
    if restaurant_id:
        try:
            filt["restaurant_id"] = ObjectId(restaurant_id)
        except:
            raise HTTPException(400, "restaurant_id inválido")
    if user_id:
        try:
            filt["user_id"] = ObjectId(user_id)
        except:
            raise HTTPException(400, "user_id inválido")

    proj = build_projection(fields)
    sort = build_sort(sort_by, order)

    cursor = db["reviews"].find(filt, proj) if proj else db["reviews"].find(filt)
    if sort:    cursor = cursor.sort([sort])
    cursor = cursor.skip(skip).limit(limit)
    return list(cursor)

@app.post("/reviews/", response_model=Review)
def create_review(review: Review):
    data = review.dict(by_alias=True, exclude={"id"})
    res = db["reviews"].insert_one(data)
    return db["reviews"].find_one({"_id": res.inserted_id})

@app.get("/reviews/{rid}", response_model=Review)
def get_review(rid: str):
    doc = db["reviews"].find_one({"_id": ObjectId(rid)})
    if not doc:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return doc

@app.put("/reviews/{rid}", response_model=Review)
def update_review(rid: str, review: Review):
    data = review.dict(by_alias=True, exclude={"id"})
    res = db["reviews"].update_one({"_id": ObjectId(rid)}, {"$set": data})
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="No se actualizó la reseña")
    return db["reviews"].find_one({"_id": ObjectId(rid)})

@app.delete("/reviews/{rid}")
def delete_review(rid: str):
    res = db["reviews"].delete_one({"_id": ObjectId(rid)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No se eliminó la reseña")
    return {"status": "eliminado"}


# 1. Menú por restaurante
@app.get("/restaurants/{rid}/menu", response_model=List[MenuItem])
def get_menu_by_restaurant(rid: str):
    try:
        rest_oid = ObjectId(rid)
    except:
        raise HTTPException(400, "ID de restaurante inválido")
    return list(db["menu_items"].find({"restaurant_id": rest_oid}))

# 2. Órdenes por restaurante
@app.get("/restaurants/{rid}/orders", response_model=List[Order])
def get_orders_by_restaurant(rid: str):
    try:
        rest_oid = ObjectId(rid)
    except:
        raise HTTPException(400, "ID de restaurante inválido")
    return list(db["orders"].find({"restaurant_id": rest_oid}))

# 3. Reseñas por restaurante
@app.get("/restaurants/{rid}/reviews", response_model=List[Review])
def get_reviews_by_restaurant(rid: str):
    try:
        rest_oid = ObjectId(rid)
    except:
        raise HTTPException(400, "ID de restaurante inválido")
    return list(db["reviews"].find({"restaurant_id": rest_oid}))

# 4. Órdenes por usuario
@app.get("/users/{uid}/orders", response_model=List[Order])
def get_orders_by_user(uid: str):
    try:
        user_oid = ObjectId(uid)
    except:
        raise HTTPException(400, "ID de usuario inválido")
    return list(db["orders"].find({"user_id": user_oid}))

# 5. Reseñas por usuario
@app.get("/users/{uid}/reviews", response_model=List[Review])
def get_reviews_by_user(uid: str):
    try:
        user_oid = ObjectId(uid)
    except:
        raise HTTPException(400, "ID de usuario inválido")
    return list(db["reviews"].find({"user_id": user_oid}))


# - Reportes -
reports = APIRouter(prefix="/reports", tags=["reports"])

@reports.get("/orders/count")
def total_orders():
    """Total de órdenes en la colección."""
    count = db["orders"].count_documents({})
    return {"total_orders": count}

@reports.get("/restaurants/distinct_cuisines")
def distinct_cuisines():
    """Lista de tipos de cocina únicos."""
    cuisines = db["restaurants"].distinct("cuisine")
    return {"cuisines": cuisines}

@reports.get("/orders/daily_revenue")
def daily_revenue():
    """
    Ingreso total agrupado por fecha.
    """
    pipeline = [
        {"$group": {
            "_id": "$date",
            "total_revenue": {"$sum": "$total_amount"},
            "orders_count":   {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(db["orders"].aggregate(pipeline))

@reports.get("/reviews/top_restaurants")
def top_restaurants_by_rating(limit: int = 5):
    """
    Top‐N restaurantes por calificación promedio (basado en reviews),
    con restaurant_id convertido a string.
    """
    pipeline = [
        {"$group": {
            "_id": "$restaurant_id",
            "avgRating":     {"$avg": "$rating"},
            "reviews_count": {"$sum": 1}
        }},
        {"$sort": {"avgRating": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from":         "restaurants",
            "localField":   "_id",
            "foreignField": "_id",
            "as":           "restaurant"
        }},
        {"$unwind": "$restaurant"},
        {"$project": {
            "_id":             0,
            "restaurant_id":   "$_id",
            "restaurant_name": "$restaurant.name",
            "avgRating":       1,
            "reviews_count":   1
        }}
    ]
    raw = list(db["reviews"].aggregate(pipeline))

    # Convertir el ObjectId de restaurant_id a str para JSON
    for doc in raw:
        doc["restaurant_id"] = str(doc["restaurant_id"])

    return raw


@reports.get("/menu_items/most_expensive")
def most_expensive_items(limit: int = 5):
    """
    Top‐N artículos de menú más caros, con restaurant_id como string.
    """
    pipeline = [
        {"$sort": {"price": -1}},
        {"$limit": limit},
        {"$project": {
            "_id": 0,
            "name": 1,
            "price": 1,
            "restaurant_id": 1
        }}
    ]
    raw = list(db["menu_items"].aggregate(pipeline))
    # Convertir ObjectId a str
    for doc in raw:
        doc["restaurant_id"] = str(doc["restaurant_id"])
    return raw

# Incluye el router de reports en la app
app.include_router(reports)


# - Publicaciones -
@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Sube un archivo a GridFS.
    Retorna el file_id.
    """
    content = await file.read()
    # metadata opcional: content_type, filename
    file_id = fs.put(content,
                     filename=file.filename,
                     content_type=file.content_type)
    return {"file_id": str(file_id),
            "filename": file.filename}


@app.get("/files/{file_id}")
def download_file(file_id: str):
    """
    Descarga un archivo de GridFS a partir de su ObjectId.
    """
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "file_id inválido")

    try:
        gfile = fs.get(oid)
    except gridfs.NoFile:
        raise HTTPException(404, "Archivo no encontrado")

    data = gfile.read()
    return Response(content=data,
                    media_type=gfile.content_type,
                    headers={"Content-Disposition": f"attachment; filename={gfile.filename}"})


# - BulkOP -
@app.post("/bulk/{collection_name}")
def bulk_write(
    collection_name: str,
    ops: List[BulkOp] = Body(..., description="Lista de operaciones bulk")
):
    # 1) Validar que la colección exista
    if collection_name not in db.list_collection_names():
        raise HTTPException(400, f"Colección '{collection_name}' no existe")

    coll = db[collection_name]
    requests = []

    # 2) Convertir cada BulkOp en la operación de PyMongo
    for op in ops:
        if op.type == "insert" and op.document:
            requests.append(InsertOne(op.document))
        elif op.type == "update" and op.filter is not None and op.update is not None:
            requests.append(UpdateOne(op.filter, {"$set": op.update}, upsert=op.upsert))
        elif op.type == "delete" and op.filter is not None:
            requests.append(DeleteOne(op.filter))
        else:
            raise HTTPException(400, f"Operación inválida o campos faltantes: {op}")

    # 3) Ejecutar bulk_write
    result = coll.bulk_write(requests)

    # 4) Devolver resumen del resultado
    return {
        "inserted_count": result.inserted_count,
        "matched_count": result.matched_count,
        "modified_count": result.modified_count,
        "deleted_count": result.deleted_count,
        "upserted_ids": [str(v) for v in result.upserted_ids.values()],
    }
