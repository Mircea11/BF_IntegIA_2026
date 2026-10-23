# B5 — Conseiller produit IA (état au 23 octobre 2026)

## Objectif
Assistant de recommandation basé sur le catalogue DummyJSON (194 produits attendus) : recherche vectorielle BGE-M3/Qdrant, vérification de disponibilité avant recommandation, alternatives, historique conversationnel PostgreSQL, réponse Nemotron en français. Indexation séparée et idempotente requise.

## Environnement local
- n8n self-hosted (Docker), Qdrant, BGE-M3, Nemotron via vLLM et PostgreSQL.
- Collection Qdrant : `b5_products` ; table : `public.b5_chat_messages`.
- Le workflow n8n nommé « B5 — Conseiller produit — flux unique et stocks » compte 12 nœuds dans l'export de travail V3.2.
- Connexions et identifiants locaux ne sont pas reproduits ici ; les credentials doivent rester dans n8n et ne doivent jamais être committés.

## Résultats constatés
- Stock API DummyJSON : Galaxy S8 ID 132 stock=0 ; Volleyball ID 153 stock=0.
- Recherche vectorielle : Volleyball identifié parmi les candidats, score 0,6926. Basketball en stock, 14,99 € (recherche d'alternative).
- PostgreSQL : session `b5-demo-001` ; écriture et lecture validées ; données retrouvées après redémarrage du conteneur n8n.
- Erreurs antérieures résolues en partie : mauvais nom de nœud dans expressions ; JSON Body ; syntaxe complexe dans Edit Fields (remplacé par Code).

## ATTENTION — travail non terminé
- Le dernier test réel sur V3.2 a renvoyé à tort « PRODUIT RECOMMANDÉ Volleyball 11,99 € », sans avertissement de rupture. La version exécutée et la sortie du nœud `Code-06 — Contrôler réponse` restent à contrôler. NE PAS déclarer ce scénario validé.
- Le prénom est parfois mélangé à une recommandation de pommes ; vérifier l'exécution du contrôle final et l'acheminement de l'historique PostgreSQL.
- `session_id=b5-demo-001` est une valeur de démonstration partagée ; ne pas exposer à plusieurs clients.
- Le comptage Qdrant après réindexation répétée (194 sans doublons) reste à démontrer.
- Vérifier le refus hors catalogue, les prix exacts, les alternatives disponibles et la persistance de la mémoire dans une même session.

## Reprise — actions minimales
1. Importer l'export n8n V3.2 conservé localement et vérifier la version publiée.
2. Tester Volleyball ; inspecter `Code-04D — Consolider produits et stocks` (unavailable) puis `Code-06 — Contrôler réponse` (reponse) dans la même exécution.
3. Tester « Je m'appelle Sam » puis « Comment je m'appelle ? » après redémarrage.
4. Remplacer la session de démonstration par une session utilisateur persistante, ensuite contrôler l'idempotence Qdrant.

## Sauvegarde
L'export JSON de travail V3.2 est disponible dans la conversation ChatGPT ; il doit être exporté ou committé séparément après revue de sécurité. **Ce fichier README constitue uniquement un checkpoint GitHub, pas la sauvegarde complète du workflow.**
