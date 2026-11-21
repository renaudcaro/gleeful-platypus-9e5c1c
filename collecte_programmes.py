
#!/usr/bin/env python3
"""Collecte documentaire des programmes politiques 2027."""

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FICHIER = Path(__file__).with_name("programmes.json")
AUJOURDHUI = datetime.now(ZoneInfo("Europe/Paris")).date()

PERSONNALITES = [
    "David Lisnard", "Édouard Philippe", "Gabriel Attal",
    "Bruno Retailleau", "Jordan Bardella", "Marine Le Pen",
    "Raphaël Glucksmann", "Jean-Luc Mélenchon",
    "François Ruffin", "Marine Tondelier", "Teddy Riner",
"Dominique de Villepin"
    
]

THEMES = {
    "Retraites": ["retraite", "pension", "cotisation"],
    "Fiscalité": ["impôt", "fiscalité", "taxe"],
    "Économie": ["économie", "entreprise", "industrie"],
    "Emploi": ["emploi", "chômage", "salaire", "smic"],
    "Santé": ["santé", "hôpital", "médecin"],
    "Éducation": ["éducation", "école", "enseignant"],
    "Immigration": ["immigration", "asile"],
    "Sécurité": ["sécurité", "police", "justice"],
    "Énergie": ["énergie", "nucléaire", "électricité"],
    "Écologie": ["écologie", "climat", "environnement"],
    "Logement": ["logement", "loyer"],
    "Europe": ["europe", "union européenne"],
    "Défense": ["défense", "armée", "otan"],
    "Institutions": ["référendum", "constitution"]
}


def lire_base():
    if FICHIER.exists():
        data = json.loads(FICHIER.read_text(encoding="utf-8"))
    else:
        data = {"version": 1, "propositions": []}

    if not isinstance(data.get("propositions"), list):
        raise ValueError("Format de programmes.json invalide")

    data["personnalites"] = PERSONNALITES
    return data


def rechercher(nom):
    recherche = f'"{nom}" (programme OR proposition OR mesure)'
    params = urllib.parse.urlencode({
        "q": recherche, "hl": "fr", "gl": "FR", "ceid": "FR:fr"
    })
    url = "https://news.google.com/rss/search?" + params
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as rep:
        contenu = rep.read(500000)

    return ET.fromstring(contenu).findall(".//item")


def identifier_theme(titre):
    titre = titre.casefold()
    for theme, mots in THEMES.items():
        if any(mot in titre for mot in mots):
            return theme
    return "Autres propositions"


def date_publication(item):
    valeur = item.findtext("pubDate")
    if not valeur:
        return None
    try:
        return parsedate_to_datetime(valeur).date()
    except (ValueError, TypeError):
        return None


def collecter():
    data = lire_base()
    propositions = data["propositions"]

    urls = {
        s.get("url")
        for p in propositions
        for s in p.get("sources", [])
        if isinstance(s, dict)
    }
    ajouts = 0

    for nom in PERSONNALITES:
        try:
            publications = rechercher(nom)
        except Exception as erreur:
            print(f"Flux inaccessible pour {nom}: {erreur}")
            continue

        for item in publications[:15]:
            titre = (item.findtext("title") or "").strip()
            url = (item.findtext("link") or "").strip()
            date = date_publication(item)

            if not titre or not url or not date:
                continue
            if date > AUJOURDHUI or date < AUJOURDHUI - timedelta(days=30):
                continue
            if url in urls:
                continue

            # Un titre d'article n'est pas une promesse vérifiée.
            propositions.append({
                "personnalite": nom,
                "theme": identifier_theme(titre),
                "mesure": titre,
                "proposition": (
                    "Publication à examiner : aucune proposition "
                    "précise encore vérifiée."
                ),
                "date": date.isoformat(),
                "nature": "Repérage automatique dans un flux RSS",
                "statut": "Non vérifié — à examiner",
                "cout_annuel": None,
                "cout_cinq_ans": None,
                "financement": "Non documenté",
                "analyse": "Source primaire et contexte à vérifier.",
                "sources": [{
                    "titre": titre,
                    "url": url
                }]
            })
            urls.add(url)
            ajouts += 1

    data["derniere_mise_a_jour"] = AUJOURDHUI.isoformat()
    FICHIER.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"Collecte terminée : {ajouts} publications ajoutées.")
    print(f"Total : {len(propositions)} entrées.")


if __name__ == "__main__":
    collecter()
