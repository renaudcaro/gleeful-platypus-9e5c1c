
(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const names = [
    'David Lisnard', 'Édouard Philippe', 'Gabriel Attal',
    'Bruno Retailleau', 'Jordan Bardella', 'Marine Le Pen',
    'Raphaël Glucksmann', 'Jean-Luc Mélenchon',
    'François Ruffin', 'Marine Tondelier','Teddy Riner', 
    'Dominique de Villepin'
  ];
  let db = { propositions: [] };

  function el(tag, text, cls) {
    const x = document.createElement(tag);
    if (text !== undefined) x.textContent = String(text);
    if (cls) x.className = cls;
    return x;
  }

  function field(parent, label, value) {
    const box = el('div', undefined, 'measure');
    box.append(
      el('b', label),
      el('p', value || 'Non documenté', 'muted')
    );
    parent.append(box);
  }

  function matches(name, theme, measure) {
    return db.propositions.filter(p =>
      p && names.includes(p.personnalite) &&
      (!name || p.personnalite === name) &&
      (!theme || p.theme === theme) &&
      (!measure || p.mesure === measure)
    );
  }

  function proposal(p) {
    const card = el('article', undefined, 'card');
    card.append(el('h3', p.mesure || p.titre || p.theme));
    card.append(el('p',
      [p.date, p.statut || 'Non vérifié', p.type]
        .filter(Boolean).join(' · '), 'muted'
    ));

    field(card, 'Proposition', p.proposition || p.resume);
    field(card, 'Coût annuel', p.cout_annuel);
    field(card, 'Coût sur cinq ans', p.cout_cinq_ans);
    field(card, 'Financement', p.financement);
    field(card, 'Contrôle indépendant',
      p.analyse || 'Analyse non réalisée');

    const sources = Array.isArray(p.sources) ? p.sources : [];
    const box = el('div', undefined, 'measure');
    box.append(el('b', 'Sources'));

    if (!sources.length) {
      box.append(el('p', 'Aucune source renseignée', 'muted'));
    }

    sources.forEach(s => {
      const url = typeof s === 'string' ? s : s && s.url;
      try {
        const u = new URL(url);
        if (!['https:', 'http:'].includes(u.protocol)) return;
        const a = el('a',
          typeof s === 'object' && s.titre ? s.titre : u.hostname
        );
        a.href = u.href;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        const line = el('p');
        line.append(a);
        box.append(line);
      } catch (_) {}
    });

    card.append(box);
    return card;
  }

  function empty() {
    return el('p',
      'Aucune proposition documentée dans la base. ' +
      'Cela ne signifie pas une absence de position.',
      'muted'
    );
  }

  function installPeople() {
    const grid = $('people-grid');
    if (!grid) return;

    const panel = el('div', undefined, 'card');
    panel.id = 'atlas-person-profile';
    grid.after(panel);

    function show(name) {
      const found = matches(name);
      panel.replaceChildren(el('h3', name));
      panel.append(el('p',
        found.length + ' proposition(s) documentée(s).',
        'muted'
      ));
      if (!found.length) panel.append(empty());
      found.forEach(p => panel.append(proposal(p)));
    }

    grid.replaceChildren();

    names.forEach(name => {
      const button = el('button', undefined, 'tile');
      button.type = 'button';
      button.append(
        el('span', '◉'),
        el('strong', name),
        el('span', 'Voir la fiche', 'muted')
      );
      button.addEventListener('click', () => {
        show(name);
        panel.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      });
      grid.append(button);
    });

    show(names[0]);
  }

  function installThemes() {
    const select = $('candidate');
    const title = $('topic-title');
    if (!select || !title) return;

    const parent = select.closest('.card');
    if (!parent) return;

    Array.from(parent.children)
      .filter(x => x.classList.contains('measure'))
      .forEach(x => x.hidden = true);

    const panel = el('div');
    parent.append(panel);

    function update() {
      const found = matches(select.value, title.textContent);
      panel.replaceChildren();
      if (!found.length) panel.append(empty());
      found.forEach(p => panel.append(proposal(p)));
    }

    select.addEventListener('change', update);
    $('topic-grid')?.addEventListener('click', () => {
      setTimeout(update, 0);
    });
    update();
  }

  function installComparison() {
    const topic = $('compare-topic');
    const measure = $('compare-measure');
    const results = $('compare-results');
    if (!topic || !measure || !results) return;

    function update() {
      results.replaceChildren();
      results.append(el('p',
        'Question commune : ' + measure.value +
        ' — ' + topic.value, 'muted'
      ));

      const wrap = el('div', undefined, 'comparison');

      names.forEach(name => {
        const card = el('article', undefined, 'card compare-card');
        card.append(el('h3', name));
        const found = matches(name, topic.value, measure.value);
        if (!found.length) card.append(empty());
        found.forEach(p => card.append(proposal(p)));
        wrap.append(card);
      });

      results.append(wrap);
    }

    topic.addEventListener('change', () => {
      setTimeout(update, 0);
    });
    measure.addEventListener('change', () => {
      setTimeout(update, 0);
    });
    update();
  }

  async function load() {
    try {
      const response = await fetch('./programmes.json', {
        cache: 'no-store'
      });
      if (!response.ok) throw Error('HTTP ' + response.status);

      const data = await response.json();
      if (!Array.isArray(data.propositions)) {
        throw Error('Format invalide');
      }

      db = {
        ...data,
        propositions: data.propositions.filter(p =>
          p && names.includes(p.personnalite) &&
          typeof p.theme === 'string'
        )
      };

      window.atlasProgrammes = db;
      window.dispatchEvent(
        new Event('atlas-programmes-charges')
      );
    } catch (error) {
      console.error('Base documentaire indisponible', error);
      db = { propositions: [] };
    }

    installPeople();
    installThemes();
    installComparison();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load, {
      once: true
    });
  } else {
    load();
  }
})();
  
