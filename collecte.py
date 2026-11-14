#!/usr/bin/env python3
"""Veille gratuite : signaux RSS à vérifier, jamais présentés comme faits établis."""
import datetime as dt
import email.utils
import hashlib
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from zoneinfo import ZoneInfo

FILE = Path(__file__).with_name('actualites.json')
PARIS = ZoneInfo('Europe/Paris')
NOW = dt.datetime.now(PARIS)
# Agrégateur de repérage : chaque résultat exige une vérification humaine.
QUERIES = [
    'site:vie-publique.fr (présidentielle OR budget OR réforme)',
    'site:insee.fr (inflation OR chômage OR croissance)',
    'site:assemblee-nationale.fr (budget OR proposition de loi)',
    'site:senat.fr (budget OR proposition de loi)',
]

def get_feed(query):
    params = urllib.parse.urlencode({'q': query, 'hl': 'fr', 'gl': 'FR', 'ceid': 'FR:fr'})
    req = urllib.request.Request('https://news.google.com/rss/search?' + params,
        headers={'User-Agent': 'AtlasPolitiquePersonnel/1.0'})
    with urllib.request.urlopen(req, timeout=18) as r:
        data = r.read(1_500_000)
    return ET.fromstring(data).findall('./channel/item')

def parse_date(raw):
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
        return parsed.astimezone(PARIS).date()
    except (TypeError, ValueError):
        return None

def main():
    if os.getenv('GITHUB_EVENT_NAME') == 'schedule' and NOW.hour != 7:
        print('Hors créneau de 7 h à Paris : aucune action')
        return
    content = json.loads(FILE.read_text(encoding='utf-8'))
    articles = content.setdefault('articles', [])
    seen = {str(a.get('sources', [{}])[0].get('url', '')).strip() for a in articles if a.get('sources')}
    seen_titles = {str(a.get('titre', '')).strip().casefold() for a in articles}
    added = 0
    successes = 0
    for query in QUERIES:
        try:
            items = get_feed(query)
            successes += 1
        except Exception as exc:
            print('Flux inaccessible :', query, repr(exc))
            continue
        for item in items[:12]:
            title = unescape((item.findtext('title') or '').strip())
            url = (item.findtext('link') or '').strip()
            date = parse_date(item.findtext('pubDate'))
            if not title or not url or not date or (NOW.date() - date).days not in range(0, 4):
                continue
            if url in seen or title.casefold() in seen_titles:
                continue
            # Un titre RSS ne suffit pas à valider la réalité d'un fait.
            articles.append({
                'titre': title,
                'date': date.isoformat(),
                'type': 'Repérage documentaire',
                'statut': 'Non vérifié — signalement RSS, à contrôler dans la source originale',
                'resume': 'Publication repérée automatiquement dans un flux d’actualités. Son contenu, sa date et ses affirmations n’ont pas été vérifiés indépendamment. Ouvrir la source avant toute conclusion.',
                'sources': [{'titre': 'Lien vers la publication repérée (Google Actualités)', 'url': url}]
            })
            seen.add(url)
            seen_titles.add(title.casefold())
            added += 1
            if added >= 12:
                break
        if added >= 12:
            break
    if successes == 0:
        print('Aucun flux accessible : fichier inchangé')
        return
    if added:
        articles.sort(key=lambda a: a.get('date', ''), reverse=True)
        content['derniere_mise_a_jour'] = NOW.date().isoformat()
        FILE.write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Flux consultés : {successes}; nouvelles notices : {added}; total : {len(articles)}')

if __name__ == '__main__':
    main()
