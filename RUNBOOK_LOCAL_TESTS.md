# Guide complet d’exécution et de tests locaux

Ce README couvre les méthodes de test suivantes :

- **A — Tout avec Docker Compose** (recommandé pour l’intégration)
- **B — PostgreSQL installé directement + FastAPI local**
- **C — PostgreSQL/FastAPI locaux + Redis/MinIO/LiveKit en Docker**
- **D — Tous les services installés directement**
- Flutter Web
- Android Emulator
- Téléphone Android physique
- tests API, migrations, Celery, LiveKit/Egress, MinIO et pipeline IA.

## 1. Prérequis

Vérifier :

```powershell
python --version
flutter --version
dart --version
docker --version
docker compose version
```

Copier la configuration :

```powershell
Copy-Item .env.example .env
```

Linux/macOS :

```bash
cp .env.example .env
```

Ne jamais mettre de vrais secrets de production dans Git.

---

## 2. Méthode A — Tout avec Docker Compose

### 2.1 Vérification

Depuis la racine :

```powershell
docker compose config
```

La commande doit se terminer sans erreur.

### 2.2 Démarrage

```powershell
docker compose up -d
docker compose ps
```

Logs :

```powershell
docker compose logs -f
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose logs -f livekit
docker compose logs -f livekit_egress
docker compose logs -f minio
```

### 2.3 Migrations

Si elles ne sont pas exécutées automatiquement :

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

### 2.4 API

Swagger :

```text
http://localhost:8000/docs
```

Health :

```text
http://localhost:8000/api/v1/health
```

### 2.5 Flutter Web

Dans un autre terminal :

```powershell
cd frontend
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

---

## 3. Méthode B — PostgreSQL installé directement + FastAPI local

Cette méthode n’utilise pas PostgreSQL Docker.

### 3.1 PostgreSQL

Vérifier :

```powershell
psql --version
```

Créer une base et un utilisateur adaptés aux valeurs de `.env` :

```sql
CREATE DATABASE iarh;
CREATE USER iarh_user WITH PASSWORD 'mot_de_passe_dev';
GRANT ALL PRIVILEGES ON DATABASE iarh TO iarh_user;
```

Configurer `.env` avec la variable réellement utilisée par le backend, par exemple :

```env
DATABASE_URL=postgresql+asyncpg://iarh_user:mot_de_passe_dev@localhost:5432/iarh
```

### 3.2 Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install .
alembic upgrade head
alembic current
```

Linux/macOS :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
alembic upgrade head
```

### 3.3 FastAPI

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Puis :

```text
http://localhost:8000/docs
```

---

## 4. Méthode C — PostgreSQL/FastAPI locaux + services auxiliaires Docker

Utile pour développer le backend tout en gardant les services complexes sous Docker.

Démarrer les services auxiliaires :

```powershell
docker compose up -d redis minio livekit livekit_egress
```

Puis lancer PostgreSQL localement et FastAPI avec la méthode B.

Celery peut être lancé localement si Redis et ses dépendances Python sont installés :

```powershell
cd backend
.venv\Scripts\Activate.ps1
celery -A app.core.celery_app.celery_app worker --loglevel=INFO
```

**Si le chemin de l'application Celery diffère dans le projet, utiliser celui indiqué dans le code/README du backend.**

---

## 5. Méthode D — Tous les services hors Docker

Possible uniquement si les services suivants sont installés et configurés localement :

```text
PostgreSQL
Redis
MinIO
LiveKit
LiveKit Egress
FastAPI
Celery
Flutter
```

Ordre recommandé :

```text
1. PostgreSQL
2. Redis
3. MinIO
4. LiveKit
5. LiveKit Egress
6. FastAPI
7. Celery
8. Flutter
```

Pour les tests d’intégration, Docker reste préférable pour LiveKit/Egress.

---

## 6. Flutter Web

Backend local :

```powershell
cd frontend
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

Avant :

```powershell
flutter analyze
flutter test
```

---

## 7. Android Emulator

L’émulateur Android ne doit généralement pas utiliser `localhost` pour atteindre le PC.

Utiliser :

```text
10.0.2.2
```

Exemple :

```powershell
cd frontend
flutter run -d <DEVICE_ID> --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Lister les appareils :

```powershell
flutter devices
```

---

## 8. Téléphone Android physique

Mettre le PC et le téléphone sur le même réseau.

Trouver l’IP du PC :

```powershell
ipconfig
```

Exemple :

```text
192.168.1.20
```

Puis :

```powershell
cd frontend
flutter run -d <DEVICE_ID> --dart-define=API_BASE_URL=http://192.168.1.20:8000
```

Autoriser le port `8000` dans le pare-feu si nécessaire.

---

## 9. LiveKit local

Pour le PC, l’URL publique de développement peut être du type :

```env
LIVEKIT_PUBLIC_URL=ws://127.0.0.1:7880
```

Pour Android Emulator, utiliser une adresse accessible depuis l’émulateur.

Pour un téléphone physique, utiliser l’IP LAN du PC, par exemple :

```env
LIVEKIT_PUBLIC_URL=ws://192.168.1.20:7880
```

En production :

```text
wss://...
```

et non `ws://`.

Vérifier :

```powershell
docker compose logs -f livekit
docker compose logs -f livekit_egress
```

---

## 10. MinIO / Egress

Vérifier :

```powershell
docker compose ps
docker compose logs -f minio
docker compose logs -f livekit_egress
```

La chaîne attendue :

```text
Flutter
  ↓
LiveKit
  ↓
Egress
  ↓
MinIO
  ↓
média
```

Le bucket utilisé par Egress doit exister et être accessible avec les identifiants DEV.

---

## 11. Redis / Celery

Redis :

```powershell
docker compose logs -f redis
```

Celery :

```powershell
docker compose logs -f celery_worker
```

Le pipeline attendu :

```text
FINISH
 ↓
PROCESSING
 ↓
TRANSCRIBING
 ↓
Whisper
 ↓
EVALUATING
 ↓
Gemini
 ↓
COMPLETED
 ↓
REPORT
```

---

## 12. Tests API

Swagger :

```text
http://localhost:8000/docs
```

Tester dans l’ordre :

```text
REGISTER
LOGIN
ME
CREATE SIMULATION
LIST SIMULATIONS
CREATE INTERVIEW
LIST INTERVIEWS
GET INTERVIEW
START
CURRENT QUESTION
ANSWER
JOIN
FINISH
REPORT
```

Le endpoint de liste des entretiens doit être :

```text
GET /api/v1/interviews
```

---

## 13. Tests Flutter

```powershell
cd frontend
flutter pub get
flutter analyze
flutter test
```

Puis lancer le client sur Web ou Android.

---

## 14. Parcours fonctionnel complet

### Authentification

```text
Inscription
 ↓
Connexion
 ↓
Token
 ↓
/auth/me
```

### Simulation

```text
Créer simulation
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
Flutter récupère la simulation
```

### Entretien

```text
Créer entretien
 ↓
GET /interviews
 ↓
START
 ↓
Questions
 ↓
Réponses
```

### LiveKit

```text
JOIN
 ↓
Token LiveKit
 ↓
Caméra
 ↓
Microphone
 ↓
Room
```

### Enregistrement

```text
FINISH
 ↓
Egress
 ↓
MinIO
```

### Pipeline IA

```text
Média
 ↓
MinIO
 ↓
Celery
 ↓
Whisper
 ↓
Transcript
 ↓
Gemini
 ↓
Evaluation
 ↓
COMPLETED
 ↓
REPORT
```

---

## 15. Diagnostic

### FastAPI

```powershell
docker compose logs backend
```

ou :

```powershell
uvicorn app.main:app --reload
```

### PostgreSQL

Docker :

```powershell
docker compose logs postgres
```

Local :

```powershell
psql -h localhost -U iarh_user -d iarh
```

### Migrations

```powershell
alembic current
alembic history
alembic upgrade head
```

Docker :

```powershell
docker compose exec backend alembic upgrade head
```

### Flutter/API

Web :

```text
http://localhost:8000
```

Android Emulator :

```text
http://10.0.2.2:8000
```

Téléphone :

```text
http://IP_DU_PC:8000
```

### LiveKit

```powershell
docker compose logs livekit
docker compose logs livekit_egress
```

Vérifier :

```text
LIVEKIT_URL
LIVEKIT_PUBLIC_URL
LIVEKIT_API_KEY
LIVEKIT_API_SECRET
```

### Celery

```powershell
docker compose logs -f celery_worker
```

---

## 16. Nettoyage Docker

Arrêter :

```powershell
docker compose down
```

Supprimer les volumes :

```powershell
docker compose down -v
```

⚠️ `down -v` supprime les données persistantes des volumes Docker concernés, notamment les données PostgreSQL.

---

## 17. Checklist d'exécution

```text
[ ] Docker OK
[ ] docker compose config OK
[ ] PostgreSQL OK
[ ] Redis OK
[ ] MinIO OK
[ ] LiveKit OK
[ ] Egress OK
[ ] migrations OK
[ ] FastAPI OK
[ ] Celery OK
[ ] flutter pub get OK
[ ] flutter analyze OK
[ ] flutter test OK
[ ] inscription OK
[ ] login OK
[ ] simulation OK
[ ] liste simulations OK
[ ] création entretien OK
[ ] liste entretiens OK
[ ] démarrage entretien OK
[ ] LiveKit OK
[ ] caméra OK
[ ] microphone OK
[ ] enregistrement OK
[ ] média présent dans MinIO
[ ] transcription OK
[ ] évaluation OK
[ ] rapport OK
```

## 18. Méthode recommandée

Pour les tests d'intégration complets :

```text
Docker :
PostgreSQL
Redis
MinIO
LiveKit
Egress
FastAPI
Celery

Local :
Flutter
```

Pour développer rapidement le backend :

```text
PostgreSQL local
FastAPI local
Redis/MinIO/LiveKit/Egress Docker
Flutter local
```

Pour un simple test frontend :

```text
Backend Docker
+
Flutter Web local
```

Ne pas considérer le projet comme « validé en production » tant que le parcours complet réel :

```text
Flutter → FastAPI → PostgreSQL → LiveKit → Egress → MinIO
→ Celery → Whisper → Gemini → Rapport
```

n'a pas été exécuté avec succès.
