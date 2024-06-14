---
status: "{proposed | rejected | accepted | deprecated | … | superseded by [ADR-0005](0005-example.md)}"
date: 2024-06-04
deciders: Jean-Samuel Leboeuf (@jsleb333), Olivier Belhumeur (@GameSetAndMatch), Emile Turcotte (@emileturcotte)
consulted: 
informed: 
---
# ADR 0000 - Scoping initial de la version alpha

## Context and Problem Statement
Le Conseil Patronal de l'Environnement du Québec [(CPEQ)](https://www.cpeq.org/fr/) procède à une activité hebdomadaire de vigie juridique en matière d'environnement. Cette vigie est propulsée par plus de 100 sources d'informations (journalistiques, données probantes, communiqués de presse, etc.). Ces sources d'informations demandent à être collectées, lues et synthétisées, ce qui exige beaucoup de travail routinier pouvant aisément être automatisé et traité via intelligence artificielle. Actuellement, il faut à un juriste trois jours par semaine pour faire cette tâche.

L'objectif est de réduire à un seul jour le temps de création de cette vigie tout en maintenant sa qualité et son exhaustivité.

### État actuel du projet
Le projet a commencé le 18 mars.
Il a été pensé en quatre livrables selon [l'offre de service](https://drive.google.com/file/d/1CXcWgHzNSVqqh-7YNDEFkvVNWOD3L7zY/view?usp=drive_link). Ces livrables furent amendés par la suite, tel que l'explicite [le document suivant](https://docs.google.com/document/d/1MWF9x4-uGAP0Mth6wslMwZEJ7uKoYREk1f1EagN3_xc/edit?pli=1). 

Une Powerapp avait initialement été utilisée pour réaliser ce projet. Après avoir rencontré plusieurs limitations, cette technologie fut abandonnée au profit d'un API en python avec une interface Web avec Vue.js. La pertinence d'une interface web est présentement remise en question.

Le présent document cherche à définir les choses suivantes :
* Les fonctionnalités finales de la solution;
* Les fonctionnalités de la version alpha;
* Le flot d'exécution du service.

## Fonctionnalités de la solution finale

Les fonctionnalités de la solution finale sont :
  1. Collecte des sources d'information.
     * Sources Web (obtenues par Webscraper.io)
     * Sources avec API (à confirmer avec le client en quoi ça consiste, obtenues via un programme custom?)
     * Sources ponctuelles (sources non-hebdomadaires ajoutées manuellement par le juriste)
       * Il faudra voir dans quel format le juriste nous donne ses sources. PDF? Text? Web? Peut-être qu'on devra forcer le format.
     * Quand on fait les sitemaps, il faudrait valider combien de nouvelles par semaine la source publie pour savoir s'il faut paginer.
  2. Traitement des sources
     * Il faut valider la date de publication des sources pour ne pas collecter des données de la semaine précédente.
       * Qu'est-ce qui arrive si on n'arrive pas à obtenir la date de l'article? 
     * Il faut formatter les sources dans un format uniforme avant de les persister.
  2. Stockage des sources
     * Stockage des sources brutes dans le Sharepoint.
       * Dans quel format stockerons-nous les sources dans le Sharepoint?
       * Quelle arborescence utiliserons-nous dans le Sharepoint? Un dossier par semaine? Un fichier par source?
     * Le juriste va ajouter ses sources ponctuelles manuellement dans le bon dossier avant de lancer la génération du rapport.
       * Il faudra valider comment on gère le format des données pour que ce soit traitable.
     * Le Vector Store peut rouler en mémoire dans le service.
       * Vector Store = PostgreSQL + un field de vector de floats qui permet de naviguer de donnée en donnée.
       * Pour la Proof of Concept, on pourrait simplement avoir un fichier JSON avec les embeddings. On pourrait avoir un fichier dans le Sharepoint pour nos embeddings qu'on peut update.
  3. Catégorisation des articles.
     * Chaque article doit être automatiquement catégorisé à partir d'une liste de catégories préalablement déterminée.
       * S'assurer que les embeddings correspondent suffisamment. Le travail de paufinage va devoir être fait manuellement.
       * Utilisation des Embeddings d'OpenAI.
     * Les articles qui ne correspondent pas suffisamment à une ou l'autre des catégories doivent être classés comme non pertinents et retirés du rapport.
  4. Ajout dynamique de nouvelles sources d'information par le juriste sans passer par le code.
     * Le juriste doit être capable de modifier la liste de ses sources sans avoir à faire appel à l'équipe de développement.
     * Il faudra assurément former le juriste pour utiliser Webscraper.
  5. Génération d'un résumé de chaque article via ChatGPT.
     * Chaque article préalablement catégorisé devra être sommarisé par ChatGPT de sorte à le rendre plus digeste pour le rapport.
     * Il faudra stocker les résumés dans le Sharepoint pendant que les résumés se font.
  6. Génération d'un rapport complet des nouvelles, catégorisé par rubrique, qui regroupe le résumé de chaque article.
     * Un rapport regroupant tous les résumés d'articles catégorisés par rubrique est produit et stocké dans le Sharepoint. 
     * Le juriste doit être capable d'enclancher la génération du rapport selon sa convenance. Une PowerApp fut discuté.
     * On pourrait offrir de céduler la génération.
  7. Présentation du rapport au juriste.
     * Le rapport doit être présenté visuellement au juriste.
     * En ce moment, ils utilisent un CRM avec une fonction de newsletter, vieille affaire de bouette, nombre max de caractères, pas de changement de format comme ils veulent. Alexandre va s'asseoir avec eux pour voir quel outil ils veulent utiliser pour le format de la newsletter.
     * Pour l'instant, indéterminé.
     * Le juriste doit être capable de voir les erreurs de scraping qui sont survenues (système de vigie des erreurs).
  8. Notification de la génération du rapport.
     * Le juriste doit être notifié de la génération complétée du rapport.
     * Pas obligé d'être une notification Push, ça peut juste être un visuel quelconque, un email, etc.

## Fonctionnalités de la version alpha
* Les fonctionnalités de la première itération sont : 
  1. Collecte des sources d'information
     * Seulement quelques sources Web choisies sont collectés pour l'instant. Pas de sources par API, pas de sources ponctuelles.
     * On scrape une page dans la pagination et c'est tout. On ne se soucie pas des sources manquantes.
  2. Traitement des sources
     * Les sources sont filtrées par date de publication.
     * Les sources sont mises dans un format CSV pour être compatible avec Excel.
  2. Stockage des sources
     * Intégration avec Sharepoint fonctionnelle (OneDrive en arrière).
     * Les sources sont stockées dans un nouveau fichier CSV dans Sharepoint dans un nouveau dossier pour la semaine en cours.
  3. Catégorisation des articles
     * Les articles sont catégorisés. Le degré de précision n'est pas important pour l'instant.
  4. Ajout dynamique de nouvelles sources d'information par le juriste sans passer par le code.
     * Pas d'ajout dynamique des sources pour l'instant.
  5. Génération d'un résumé de chaque article via ChatGPT.
     * Les articles sont adéquatement sommarisés selon un modèle fourni à ChatGPT.
  6. Génération d'un rapport complet des sources d'information, catégorisé par rubrique, qui regroupe le résumé de chaque article.
     * Les résumés des sources d'information sont publiés dans un document de synthèse (en Markdown).
     * Les articles sont catégorisés dans le rapport. 
  7. Présentation du rapport au juriste.
     * Le rapport est stocké dans le Sharepoint.
  8. Notification de la génération du rapport.
     * Pas de notification pour l'instant.

## Flot d'exécution de la version alpha
Le flot d'exécution du programme ira comme suit :
  1. Une fois par semaine à un temps déterminé, une routine cédulée va activer le travail d'obtention des sources.
    * Pendant la nuit la veille du rapport, Webscraper initie le scraping. Il sera assurément complété au matin.
  2. Le juriste pourra ensuite lancer la génération du rapport.
    * On initialise le VectorStore en mémoire. On va garder un fichier json dans le repository pour commencer. À terme, on pourrait le persister quelque part et le mettre à jour à chaque fois.
    * Le service va chercher toutes les scraping jobs de la veille et récupère leurs IDs.
    * Un par un, il va downloader le JSON du contenu de la job. 
    * On va parse la date et éliminer les résultats trop vieux.
    * On catégorise l'article selon les rubriques.
    * On envoie le corps de l'article à ChatGPT pour qu'il le résume avec des exemples de résumés tirer du VectorStore pour informer sa réponse.
      * On pourrait générer les résumés en Markdown afin de faciliter la génération de la Newsletter.
    * Lorsque tous les résumés nous sont parvenus, on va assembler un fichier CSV d'un coup avec tous les résumés en mémoire. Cet fichier va être conservé en mémoire jusqu'à ce que toutes les jobs aient été downloadées.
      * On pourrait adjoindre le texte complet de l'article avec le résumé pour bâtir un meilleur VectorStore dans le futur.
    * Lorsque le fichier est complet, on persiste le CSV dans le Sharepoint.
    * À partir du CSV, on génère le newsletter et on le persiste dans le Sharepoint.
      * Pour la démo, on persiste la newsletter en Markdown.
  3. Le juriste va chercher le rapport dans le Sharepoint.
