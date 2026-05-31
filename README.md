# OSINT-Intel Discord Bot

Bot Discord propulsé par **HuggingFace Inference API** avec le skill **OSINT-Intel** intégré et **recherche web DuckDuckGo** en temps réel.

Conçu pour fournir des analyses de renseignement stratégique structurées directement dans Discord, avec création automatique de fils (threads) pour chaque analyse.

---

## Fonctionnalités

- 5 modes d'analyse : OSINT / EXPRESS / FORECAST / UPDATE / CALIBRATION
- Recherche web temps réel via DuckDuckGo (gratuit, sans clé API)
- Citations de sources automatiques dans les réponses
- Création automatique d'un thread Discord par analyse
- Mémoire de session par utilisateur (suivi de dossiers multi-tours)
- Commandes slash Discord (`/osint`, `/reset_session`, `/osint_help`)

---

## Stack technique

| Composant | Technologie |
|---|---|
| LLM | HuggingFace Inference API (Mistral, Llama, Qwen...) |
| Recherche web | DuckDuckGo (`ddgs`) — gratuit, sans clé |
| Bot Discord | discord.py 2.x — slash commands |
| Hébergement | Compatible tout serveur Python (testé sur AlwaysData) |

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-compte/osint-intel-bot.git
cd osint-intel-bot
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditez `.env` et renseignez vos valeurs :

```env
HF_TOKEN=hf_votre_token_huggingface
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
DISCORD_TOKEN=votre_token_discord
```

---

## Obtenir un token HuggingFace (gratuit)

1. Créez un compte sur [huggingface.co](https://huggingface.co)
2. **Settings → Access Tokens → New token**
3. Nom : `osint-bot`, rôle : **Read**, cochez **Make calls to Inference Providers**
4. Copiez le token généré (`hf_...`)

### Modèles recommandés

| Modèle | Qualité | Accès |
|---|---|---|
| `meta-llama/Llama-3.1-8B-Instruct` | ★★★★☆ | Licence Meta à accepter* |
| `Qwen/Qwen2.5-72B-Instruct` | ★★★★★ | Libre |
| `mistralai/Mistral-7B-Instruct-v0.3` | ★★★☆☆ | Libre (plus rapide) |

*Pour Llama : acceptez la licence sur [huggingface.co/meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)

---

## Créer le bot Discord

1. Allez sur [discord.com/developers/applications](https://discord.com/developers/applications) → **New Application**
2. Onglet **Bot** → copiez le **Token** → activez **Message Content Intent**
3. Onglet **OAuth2 → URL Generator** :
   - Scopes : `bot` + `applications.commands`
   - Permissions : `Send Messages`, `Read Message History`, `Use Slash Commands`, `Create Public Threads`, `Send Messages in Threads`
4. Ouvrez l'URL générée → ajoutez le bot à votre serveur

---

## Lancer le bot

```bash
python bot.py
```

---

## Commandes disponibles

| Commande | Description |
|---|---|
| `/osint [requête]` | Analyse OSINT complète (mode auto-détecté) |
| `/osint [requête] mode:OSINT` | Analyse terrain complète — 11 étapes |
| `/osint [requête] mode:EXPRESS` | Synthèse rapide — 4 blocs |
| `/osint [requête] mode:FORECAST` | Prédiction probabilisée (Superforecasting) |
| `/osint [requête] mode:UPDATE` | Mise à jour bayésienne sur dossier actif |
| `/osint [requête] mode:CALIBRATION` | Scoring de prédictions passées |
| `/reset_session` | Réinitialise l'historique de conversation |
| `/osint_help` | Aide et guide d'utilisation |

---

## Exemples d'utilisation

```
/osint Situation actuelle en Iran

/osint Signaux faibles autour de la politique énergétique française mode:OSINT

/osint Probabilité d'une récession en zone euro d'ici 12 mois mode:FORECAST

/osint Nouveau signal sur dossier X : [information] mode:UPDATE
```

---

## Structure du projet

```
osint-intel-bot/
├── bot.py              # Bot principal (Discord + HuggingFace + threads)
├── osint_skill.py      # System prompt et formats OSINT-Intel
├── web_search.py       # Module de recherche DuckDuckGo
├── requirements.txt    # Dépendances Python
├── .env.example        # Modèle de configuration (sans les vraies clés)
├── .gitignore          # Exclut .env et fichiers sensibles
└── README.md           # Ce fichier
```

---

## Déploiement sur AlwaysData (gratuit)

1. Créez un compte sur [alwaysdata.com](https://www.alwaysdata.com) (plan gratuit 100 Mo)
2. Uploadez tous les fichiers via FTP/SFTP dans un dossier `osint-bot/`
3. En SSH : `pip install -r requirements.txt --user`
4. Panneau AlwaysData → **Avancé → Services** → commande : `python ~/osint-bot/bot.py`
5. Démarrez le service — le bot est en ligne 24h/24

---

## Limitations HuggingFace (tier gratuit)

- File d'attente possible sur les grands modèles aux heures de pointe
- Environ 1 000 requêtes/jour
- Pour un usage intensif : HuggingFace PRO (9$/mois) ou déploiement local

---

## Garde-fous éthiques

- Sources ouvertes uniquement
- Un acteur peut être analysé, jamais ciblé dans une recommandation opérationnelle
- Les scénarios sont des possibles, pas des prédictions
- Ce bot éclaire la décision, il ne sert pas à construire des récits trompeurs

---

## Licence

MIT — libre d'utilisation, de modification et de redistribution.
