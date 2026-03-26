# Organize
Organize is a tool designed to simplify daily life: it helps you plan tasks, structure goals, and track progress through clear, precise analytics, allowing you to manage your time better and stay productive every day.
## 🚀 Lancement en 3 commandes

```bash
# 1. Installer les dépendances
npm install

# 2. Lancer en mode développement
npm run dev

# 3. Ouvrir http://localhost:5173
```

---

## 📦 Build pour la production

```bash
npm run build
npm run preview
```

---

## 🎯 Fonctionnalités

| Module | Description |
|--------|-------------|
| **Dashboard** | Vue d'ensemble, progression du jour, niveau XP |
| **Tâches** | CRUD complet, priorités, catégories, filtres, recherche |
| **Habitudes** | Suivi quotidien, streaks, grille hebdomadaire |
| **Statistiques** | Graphiques recharts (barres, aire, donut) |
| **Mode Focus** | Timer Pomodoro configurable, cycles de travail/pause |

---

## 🎮 Gamification (XP)

| Action | XP |
|--------|----|
| Créer une tâche | +10 XP |
| Terminer une tâche | +25 XP |
| Valider une habitude | +15 XP |
| Compléter un Pomodoro | +50 XP |

---

## 💾 Stockage

Toutes les données sont sauvegardées dans `localStorage` avec le préfixe `org_`.

- `org_tasks` — Tâches
- `org_habits` — Habitudes et completions
- `org_xp` — Points d'expérience
- `org_theme` — Préférence thème clair/sombre
- `org_page` — Dernière page visitée

---

## 📤 Export

Cliquez sur l'icône **téléchargement** dans la barre du haut pour exporter vos données en JSON.

---

## 🧰 Stack technique

- **React 18** + **Vite 5**
- **Recharts** pour les graphiques
- **Lucide React** pour les icônes
- **CSS variables** pour le theming (aucun framework CSS)
- **100% frontend** — aucun backend, aucune API

---

## 🎨 Design System

| Variable | Valeur sombre | Valeur claire |
|----------|---------------|---------------|
| `--bg` | `#0F0F11` | `#F7F7F5` |
| `--card` | `#1F1F23` | `#FFFFFF` |
| `--accent` | `#5E6AD2` | `#5E6AD2` |
| `--text` | `#E4E4E7` | `#18181B` |
| Typo | Outfit (Google Fonts) | Outfit |

---

*Organize — Fait avec ❤️ pour la productivité*
