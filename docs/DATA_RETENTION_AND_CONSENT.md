# Données personnelles, consentement et rétention

## Données traitées

IARH peut traiter l’identité du candidat, ses coordonnées, ses documents, ses réponses, ses enregistrements audio/vidéo, les transcriptions et les rapports d’évaluation.

## Règles applicables

- L’enregistrement audio/vidéo doit être précédé d’un consentement explicite et révocable.
- Les médias et transcriptions sont conservés uniquement pendant la durée annoncée à l’utilisateur.
- Une suppression via `DELETE /api/v1/auth/me/data` supprime le compte, les données relationnelles et les objets médias connus dans le bucket configuré.
- Les sauvegardes doivent appliquer la même durée de rétention et une procédure d’effacement différé documentée.
- Les URLs présignées doivent avoir une durée courte et ne doivent jamais être écrites dans les logs.
- Les logs d’accès doivent contenir l’identité technique, la ressource, l’action et l’horodatage, sans contenu de réponse ni transcription.

## Avant production

Le responsable du traitement doit compléter les durées exactes, les bases légales, les sous-traitants IA/stockage, les procédures d’export et de rectification, ainsi que le registre des accès. Cette documentation ne remplace pas la validation juridique.
