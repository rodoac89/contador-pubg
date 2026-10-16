# Contador

Tabla pública de posiciones del torneo custom de PUBG. Hecha con Angular 22.

## Requisitos

- Node.js `^22.22.3`, `^24.15.0` o `>=26`
- El backend en `http://127.0.0.1:8000`

## Desarrollo

```bash
cd frontend
npm start
```

La app queda en `http://localhost:4200/` y lee `/api/match/records/`. En local, el servidor de desarrollo reenvía `/api` a `http://127.0.0.1:8000`.

## Docker

Desde la raíz del repositorio:

```bash
docker compose up --build
```

La tabla queda en `http://localhost:4200/`. Nginx reenvía `/api` al backend.
