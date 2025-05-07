from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://Proyecto:picher@proyect2.yiteaze.mongodb.net/?retryWrites=true&w=majority&appName=Proyect2"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("✅ Conectado a MongoDB Atlas")
except Exception as e:
    print("❌ No se pudo conectar:", e)

# Base de datos y colección genérica
db = client['Proyect2']