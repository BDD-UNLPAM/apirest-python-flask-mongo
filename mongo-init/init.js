print("Inicializando base y colección clientesdb.cliente");
db = db.getSiblingDB("clientesdb");
if (!db.getCollectionNames().includes("cliente")) {
  db.createCollection("cliente");
  db.cliente.createIndex({ dni: 1 });
  db.cliente.createIndex({ email: 1 });
  print("Coleccion 'cliente' creada");
} else {
  print("Coleccion ya existe");
}
