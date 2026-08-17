# IARH Frontend — Flutter unique

Ce dossier est l'unique client Flutter officiel du projet et la source de vérité pour le Web et les cibles mobiles.

## Local

```bash
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

## Docker

Le `Dockerfile` construit Flutter Web puis sert `build/web` avec Nginx.

Depuis la racine :

```bash
docker compose up --build -d
```

Frontend Web : `http://localhost`
Backend : `http://localhost:8000/docs`

L'URL de l'API est injectée au build avec `FRONTEND_API_BASE_URL` ou `API_BASE_URL` en développement Flutter.

Pour Android Emulator, utilisez `--dart-define=API_BASE_URL=http://10.0.2.2:8000`. Pour iOS Simulator, utilisez `http://localhost:8000`.
