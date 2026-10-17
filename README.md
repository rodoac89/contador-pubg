# Contador PUBG (BETA)

Aplicación para crear torneos entre amigos de PUBG usando la API del developer portal de PUBG obtenida en [https://developer.pubg.com/](https://developer.pubg.com/).

Tiene la posibilidad de cargar partidas Custom de manera masiva y poder administrarlas desde la aplicación.

Se muestra una tabla de posiciones mostrando el puntaje de cada jugador acumulado entrete todas las partidas realizadas, además de un historial de partidas jugadas y la posibilidad de marcar partidas como de calentamiento para que no cuenten en la tabla.

Las reglas son totalmente configurables desde la aplicación, permitiendo definir el puntaje por posición, por kills, por tiempo de sobrevivencia y por muertes fuera de la zona.

## Arranque

Desde esta carpeta:

```bash
docker compose up --build
```

La aplicación se levanta en `http://localhost:4200/`.

Para cargar partidas desde PUBG hace falta la clave de la API, se debe obtener desde [https://developer.pubg.com/](https://developer.pubg.com/) y escribirla en el archivo `docker-compose.yml`:

```bash
PUBG_API_KEY=tu-clave
```

## Persistencia

Se utiliza una base de datos SQLite para almacenar los datos de las partidas y los jugadores. La base SQLite vive en el volumen `contador-data`, en `/data/db.sqlite3` dentro del backend. Recrear los contenedores no borra las partidas. El primer arranque aplica las migraciones.

## Despliegue

Nginx publica el puerto 80 y reenvía `/api` a `127.0.0.1:8000`. El backend no tiene red propia: usa la del frontend. Si cambias uno, vuelve a crear los dos:

```bash
docker compose up --build -d
```

## Administración

Entra en `http://localhost:4200/admin`. La primera cuenta que se registra queda como administración y el registro se cierra. Desde ahí se cargan partidas y se marcan las de calentamiento. Con la sesión iniciada, **Ver partidas** permite quitar una partida inválida.

## Desarrollo

El backend es Django y el frontend es Angular 22.

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

```bash
cd frontend
npm install
npm start
```

`npm start` abre `http://localhost:4200/` y reenvía `/api` a `http://127.0.0.1:8000`. Node tiene que ser `^22.22.3`, `^24.15.0` o `>=26`.

## Otro despliegue

`zimaos/container-compose.yml` usa las imágenes ya publicadas en `tea.rodoaravena.cl/rodoac/contador-pubg-backend:latest` y `tea.rodoaravena.cl/rodoac/contador-pubg-frontend:latest`. Ese archivo es para CasaOS. Este compose de la raíz construye las imágenes desde `backend.dockerfile` y `frontend.dockerfile`.
