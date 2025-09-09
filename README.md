CRUD Clientes - Flask (templates) + MongoDB - Docker Compose

Servicios:
- mongo: MongoDB sin autenticación
- app: Flask (render de plantillas) + API REST

Ejecutar:
  docker compose up --build

Acceder:
  http://localhost:5000/   -> frontend (plantillas)
  API REST en http://localhost:5000/api/clientes
