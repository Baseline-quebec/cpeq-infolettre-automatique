---
status: "{proposed | rejected | accepted | deprecated | … | superseded by [ADR-0005](0005-example.md)}"
date: 2024-06-04
deciders: Jean-Samuel Leboeuf (@jsleb333), Olivier Belhumeur (@GameSetAndMatch), Emile Turcotte (@emileturcotte)
consulted: 
informed: 
---
# ADR 0000 - MVP Architecture Design

## Context and Problem Statement
Le Conseil Patronal de l'Environnement du Québec [(CPEQ)](https://www.cpeq.org/fr/) procède à une activité hebdomadaire de vigie juridique en matière d'environnement. Cette vigie est propulsée par plus de 100 sources d'informations (journalistiques, données probantes, communiqués de presse, etc.). Ces sources d'informations demandent à être collectées, lues et synthétisées, ce qui exige beaucoup de travail routinier pouvant aisément être automatisé et traité via intelligence artificielle. Actuellement, il faut à un juriste trois jours par semaine pour faire cette tâche.

L'objectif est de réduire à un seul jour le temps de création de cette vigie tout en maintenant sa qualité et son exhaustivité.

### État actuel du développement
Le projet a commencé le ___.
Le projet a été pensé en quatre livrables selon [l'offre de service](https://drive.google.com/file/d/1CXcWgHzNSVqqh-7YNDEFkvVNWOD3L7zY/view?usp=drive_link). Ces livrables furent amendés par la suite, tel que l'explicite [le document suivant](https://docs.google.com/document/d/1MWF9x4-uGAP0Mth6wslMwZEJ7uKoYREk1f1EagN3_xc/edit?pli=1). 

Une Powerapp avait initialement été utilisée pour réaliser ce projet. Après avoir rencontré plusieurs limitations, cette technologie fut abandonnée au profit d'un API en python avec une interface Web avec Vue.js. La pertinence d'une interface web est présentement remise en question.

La technologie de Webscrapping choisie est [Webscraper.io](https://webscraper.io). Le produit de ce scrapping devra être mis dans le Sharepoint du CPEQ.

## Decision Drivers

* Le CPEQ utilise déjà une suite de logiciels à l'interne avec lesquels nous pourrions nous intégrer pour ne pas les dépayser.

* Sources ponctuelles : des sources connues du juriste qui ne sont pas hebdomadaires
  * Le juriste sait quelles elles sont, il va les ajouter à un folder et va ensuite launch la génération du rapport manuellement avec la synthèse du scraping et des sources ponctuelles.

* À faire : connecteur Sharepoint
  * Microsoft Dev Program + Microsoft Graph
* Aussi : Utiliser ChatGPT pour synthétiser les articles
* Oli : Vector Store avec embedding

* Deadline : Août-septembre 2024 pour livrer. Tout doit être fait pour le mois d'octobre, mais pour les subventions 
  
* Dans un deuxième temps, job de catégorisation et de synthèse.
* Il faut filtrer les dates des trucs qu'on scrape pour pas ajouter des articles des semaines passées.
  * Voir aussi le scraping avec pagination, s'il faut scrape plus loin que la première page.
  * Éliminer les articles non pertinents (avec le vectorstore). Valider si l'embedding est similaire à celui des catégories.

* Le flow d'exécution du programme ira comme suit :
  1. Une fois par semaine à un temps déterminé, une routine cédulée va activer le travail d'obtention des sources.
    * Pour les sources Web :
      - Webscraper.io va exécuter son travail préalablement déterminé et stocker le résultat sur sa plateforme.
      - Quand Webscraper a terminé son travail, il va faire un appel POST sur notre service pour l'informer qu'il a terminé.
      - Notre service ayant reçu la notification, il va appeller Webscraper pour obtenir les données et les stocker dans Sharepoint.
    * Pour les sources API : 
      - À définir
    * Pour les sources ponctuelles :
      - Le matin où le juriste voudra 
  5. Le juriste pourra

* Les fonctionnalités de la solution finale sont :
  1. Collecte des sources d'information
     * Sources Web (obtenues par Webscraper.io)
     * Sources avec API (à confirmer avec le client en quoi ça consiste)
     * Sources ponctuelles (sources non-hebdomadaires ajoutées manuellement par le juriste)
     * Il faut valider la date de publication des sources pour ne pas collecter des données de la semaine précédente.
  2. Stockage des sources
     * Stockage des sources brutes dans le Sharepoint.
     * Le juriste va ajouter ses sources ponctuelles manuellement dans le bon dossier avant de lancer la génération du rapport.
       * Il faudra valider comment on gère le format des données pour que ce soit traitable.
     * Le Vector Store peut rouler en mémoire.
  3. Catégorisation des articles et filtrage des sources non pertinentes.
     * S'assurer que les embeddings correspondent suffisamment. Le travail de paufinage va devoir être fait manuellement.
     * Utilisation des Embeddings d'OpenAI.
  6. Ajout dynamique de nouvelles sources d'information par le juriste sans passer par le code.
  7. Génération d'une synthèse de chaque article via ChatGPT.
  8. Génération d'un rapport complet des nouvelles, catégorisé par rubrique, qui regroupe le résumé de chaque article.
  9. Présentation du rapport au juriste.
  
* Les fonctionnalités de la prochaine itération sont : 

## Considered Options

* {title of option 1}
* {title of option 2}
* {title of option 3}
* … <!-- numbers of options can vary -->

## Decision Outcome

Chosen option: "{title of option 1}", because
  * [ ] {justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->
### Consequences

* Good, because {positive consequence, e.g., improvement of one or more desired qualities, …}
* Bad, because {negative consequence, e.g., compromising one or more desired qualities, …}
* … <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->
### Confirmation

{Describe how the implementation of/compliance with the ADR is confirmed. E.g., by a review or an ArchUnit test.
 Although we classify this element as optional, it is included in most ADRs.}

<!-- This is an optional element. Feel free to remove. -->
## Pros and Cons of the Options

### {title of option 1}

<!-- This is an optional element. Feel free to remove. -->
{example | description | pointer to more information | …}

* Good, because {argument a}
* Good, because {argument b}
<!-- use "neutral" if the given argument weights neither for good nor bad -->
* Neutral, because {argument c}
* Bad, because {argument d}
* … <!-- numbers of pros and cons can vary -->

### {title of other option}

{example | description | pointer to more information | …}

* Good, because {argument a}
* Good, because {argument b}
* Neutral, because {argument c}
* Bad, because {argument d}
* …

<!-- This is an optional element. Feel free to remove. -->
## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or
 document the team agreement on the decision and/or
 define when/how this decision the decision should be realized and if/when it should be re-visited.
Links to other decisions and resources might appear here as well.}
