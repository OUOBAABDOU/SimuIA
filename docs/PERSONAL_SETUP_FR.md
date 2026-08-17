# Actions personnelles obligatoires avant soumission

Ce fichier distingue ce que le code prépare de ce que seul le participant peut
faire avec ses comptes, son identité et ses preuves réelles.

## 1. Créer les comptes et confirmer l'éligibilité

- Créer/connecter le compte Devpost et cliquer sur **Participer au hackathon**.
- Vérifier l'âge légal, le pays de résidence, les conflits d'intérêts et, si
  nécessaire, désigner officiellement le représentant de l'équipe.
- Conserver une preuve de la date de création du projet après le 19 mai 2026.
- Vérifier avec Devpost toute incertitude concernant du code ou un travail
  commencé avant cette date.

## 2. Créer le projet Google Cloud

Installer `gcloud`, puis exécuter avec votre propre projet :

```powershell
gcloud auth login
gcloud config set project [PROJECT_ID]
gcloud services enable run.googleapis.com cloudbuild.googleapis.com `
  artifactregistry.googleapis.com aiplatform.googleapis.com secretmanager.googleapis.com
```

Accorder au compte de service Cloud Run les rôles Vertex AI User, Cloud SQL
Client et Secret Manager Secret Accessor. Créer aussi PostgreSQL, Redis,
MinIO/Cloud Storage et le worker Celery sur des services accessibles depuis
Cloud Run. Le Compose local ne constitue pas une infrastructure de production.

## 3. Créer les secrets sans les mettre dans Git

Créer les secrets nommés dans `cloudbuild.yaml` avec des valeurs nouvelles :

```powershell
'value' | gcloud secrets versions add iarh-jwt-secret --data-file=-
```

Répéter pour chaque secret requis, en remplaçant `value` et le nom. Ne jamais
coller une clé Gemini, un mot de passe SMTP ou une clé de stockage dans un
commit, une capture d'écran ou une vidéo.

## 4. Déployer et vérifier

```powershell
gcloud builds submit --config cloudbuild.yaml .
gcloud run services list --region us-central1
```

Récupérer l'URL Cloud Run, tester `/api/v1/health/ready` et `/api/v1/health/ai`,
puis effectuer une vraie simulation jusqu'au rapport. Capturer une preuve
Cloud Logging montrant l'évaluation Gemini/Vertex AI réussie et une preuve
d'utilisation Vertex AI. Une réponse `configured` seule ne suffit pas.

## 5. Créer les preuves utilisateurs et financières

Compléter `docs/SUBMISSION_EVIDENCE_TEMPLATE_EN.md` avec des chiffres réels :

- utilisateurs indépendants et profil anonymisé ;
- témoignages avec consentement explicite ;
- revenus indépendants et revenus liés, mois par mois ;
- dépenses d'hébergement, API, prestataires, marketing et acquisition ;
- captures ou journaux de fonctionnement continu, avec secrets et données
  personnelles masqués.

Si une valeur est zéro, inscrire `0` et expliquer pourquoi. Ne jamais inventer
de revenu, d'utilisateur, de témoignage ou de journal.

## 6. Préparer Devpost

- Rédiger la candidature à partir de `docs/DEVPOST_SUBMISSION_EN.md`.
- Fournir le dépôt public avec `LICENSE`, ou partager le dépôt privé avec les
  adresses Devpost exigées par le règlement.
- Enregistrer une vidéo publique en anglais de trois minutes maximum, sans
  musique protégée ni marques non autorisées.
- Fournir `docs/TEST_INSTRUCTIONS_EN.md`, une URL de démonstration publique et,
  si elle est privée, un compte juge temporaire avec sa date d'expiration.
- Choisir un seul prix/catégorie pour le projet.

## 7. Activer le déploiement GitHub/Firebase

Le dépôt cible est `https://github.com/OUOBAABDOU/SimuIA`. Le projet contient
déjà `.firebaserc`, `firebase.json` et le workflow
`.github/workflows/firebase-hosting.yml`.

Dans GitHub, ajouter :

- une variable de dépôt `API_BASE_URL` contenant l'URL publique réelle du
  backend Cloud Run ;
- un secret de dépôt `FIREBASE_SERVICE_ACCOUNT_SIMUIA` contenant le JSON du
  compte de service Firebase autorisé à déployer Hosting.

Le workflow construit Flutter Web puis déploie `frontend/build/web` sur le
projet Firebase `simuia` à chaque push sur `main`. Ne jamais committer le JSON
du compte de service.
