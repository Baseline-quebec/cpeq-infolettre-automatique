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
Le projet a été pensé en quatre livrables selon [l'offre de service](https://drive.google.com/file/d/1CXcWgHzNSVqqh-7YNDEFkvVNWOD3L7zY/view?usp=drive_link):
  1. Démonstration technique du modèle d'outil
    * Démonstration du prototype initial à l'équipe afin de recueillir des commentaires. Aucune utilisation possible de leur part jusqu'à présent.
  2. Déploiement de la version alpha
    * Mise dans les mains des utilisateurs d'une première version de la solution pendant un mois afin de recueillir des commentaires.
  3. Déploiement de la version beta
    * Mise dans les mains des utilisateurs d'une seconde version de la solution pendant un mois. Accès client au code source et aux diverses technologies utilisées.
  4. Déploiement de la version release
    * Relâche de la solution (?)

Une Powerapp avait initialement été utilisée pour réaliser ce projet. Après avoir rencontré plusieurs limitations, cette technologie fut abandonnée au profit d'un API en python avec une interface Web avec Vue.js. La pertinence d'une interface web est présentement remise en question.

La technologie de Webscrapping choisie est [Webscraper.io](https://webscraper.io). Le produit de ce scrapping devra être mis dans le Sharepoint du CPEQ.

## Decision Drivers

* Le CPEQ utilise déjà une suite de logiciels à l'interne avec lesquels nous pourrions nous intégrer pour ne pas les dépayser.
* Les fonctionnalités visées pour la prochaine itération du développement sont :
  1. Scrapping des sources
     * Sources sans API
     * Sources avec API (en quoi consistent-elles?)
  2. Stockage des sources dans une base de données
     * Sharepoint sert-il seulement à l'archivage?
     * Ça nous prendrait donc une BD en plus de Sharepoint?
  1. Indexation des articles en fonction de la date (du scraping ou des articles?).
  2. Catégorisation des articles via Embeddings d'OpenAI.
  3. Ajout dynamique de nouvelles sources d'information par le juriste sans passer par le code.
  4. Génération d'une synthèse de chaque article via ChatGPT.
  5. Génération d'un rapport complet (*À VALIDER*)
  5. Présentation centralisée des choses suivantes:
     * Synthèses d'articles sous le format XXX (*À VALIDER*)
     * Problèmes de scrapping d'une ou de certaines sources.
     * 
  6. 

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
