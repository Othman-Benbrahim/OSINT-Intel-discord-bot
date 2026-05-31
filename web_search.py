"""
Module de recherche web via DuckDuckGo (gratuit, sans clé API).
Injecte les résultats dans le contexte de l'analyse OSINT avec sources citables.
"""

import logging
from ddgs import DDGS

log = logging.getLogger("osint-bot.search")


def search_web(query: str, max_results: int = 6) -> str:
    """
    Effectue une recherche DuckDuckGo et retourne un bloc de contexte
    formaté avec sources numérotées, prêt à être cité par le modèle.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"[RECHERCHE WEB] Aucun résultat pour : {query}"

        lines = [
            f"## Sources web disponibles pour : « {query} »\n",
            "Tu DOIS citer ces sources dans ta réponse en utilisant le format [N] "
            "où N est le numéro de la source. "
            "Liste toutes les sources utilisées à la fin sous la section "
            "📚 SOURCES en indiquant [N] Titre — URL\n"
        ]

        for i, r in enumerate(results, 1):
            title = r.get("title", "Sans titre")
            body  = r.get("body", "")[:400].replace("\n", " ")
            href  = r.get("href", "")
            lines.append(
                f"[{i}] **{title}**\n"
                f"Contenu : {body}\n"
                f"URL : {href}\n"
            )

        log.info(f"Recherche web : {len(results)} résultats pour '{query[:60]}'")
        return "\n".join(lines)

    except Exception as e:
        log.warning(f"Erreur recherche web ({query[:40]}): {e}")
        return f"[RECHERCHE WEB] Erreur lors de la recherche : {e}"


def should_search(query: str) -> bool:
    """
    Active la recherche web pour toute requête d'analyse ou de veille.
    """
    keywords = [
        "osint", "veille", "signal", "analyse", "actualité", "récent",
        "dernier", "2024", "2025", "2026", "situation", "crise", "conflit",
        "élection", "gouvernement", "entreprise", "profil", "qui est",
        "qu'est-ce", "que se passe", "forecast", "prédiction", "iran",
        "russie", "chine", "france", "europe", "guerre", "économie",
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)
