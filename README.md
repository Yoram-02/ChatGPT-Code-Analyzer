# ChatGPT Code Analyzer

Une application GUI puissante pour l'analyse automatisée de code source utilisant ChatGPT. Analysez vos projets locaux ou GitHub avec des prompts personnalisés et obtenez des rapports détaillés en Markdown.

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macOS%20%7C%20linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🚀 Fonctionnalités

- **Sources multiples** : Analysez des dépôts locaux ou clonez directement depuis GitHub
- **Interface intuitive** : GUI PyQt5 avec contrôles de progression en temps réel
- **Analyse intelligente** : Filtrage automatique des fichiers pertinents (ignore `node_modules`, `.git`, etc.)
- **Gros fichiers supportés** : Division automatique en chunks pour les fichiers volumineux
- **Sauvegarde progressive** : Résultats sauvegardés au format Markdown après chaque fichier
- **Prompts personnalisables** : Configurez votre propre analyse selon vos besoins
- **Reprise d'analyse** : Continuez une analyse interrompue automatiquement

## 📋 Prérequis

- Python 3.7+
- Google Chrome installé
- Compte ChatGPT (gratuit ou payant)
- Connexion internet stable

## 🛠️ Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-username/chatgpt-code-analyzer.git
cd chatgpt-code-analyzer
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer l'application

```bash
python main.py
```

## 🎯 Utilisation

### Interface principale

1. **Sélection de source** :
   - **Local** : Choisissez un dossier de projet sur votre machine
   - **GitHub** : Entrez l'URL d'un dépôt public (ex: `https://github.com/user/repo`)

2. **Configuration du prompt** :
   - Utilisez le prompt par défaut ou personnalisez selon vos besoins

3. **Authentification** :
   - Cochez "Attendre la connexion utilisateur" pour vous connecter manuellement à ChatGPT
   - Un navigateur s'ouvrira automatiquement sur chat.openai.com

4. **Fichier de sortie** :
   - Spécifiez le nom du fichier Markdown de résultats
   - Par défaut : `resultats_chatgpt.md`

5. **Lancement** :
   - Cliquez sur "Start Analysis"
   - Connectez-vous à ChatGPT dans le navigateur qui s'ouvre
   - L'analyse démarre automatiquement après connexion

### Fichiers analysés

L'outil analyse automatiquement les fichiers avec ces extensions :
- **Code** : `.js`, `.ts`, `.jsx`, `.tsx`, `.py`, `.php`, `.java`, `.cs`, `.rb`, `.go`
- **Config** : `.json`, `.env`, `.yml`, `.yaml`, `.dockerfile`
- **Web** : `.html`, `.htm`, `.css`, `.scss`, `.sass`, `.vue`
- **Scripts** : `.sh`, `.bash`

**Dossiers ignorés** : `node_modules`, `.git`, `.github`, `.vscode`, `.idea`, `dist`, `build`, `__pycache__`, etc.

## 📊 Format de sortie

Les résultats sont sauvegardés dans un fichier Markdown structuré :

```markdown
# Analyse du code source par ChatGPT

## src/
### main.js
**Chemin complet:** `src/main.js`
**Analyse:**
[Résultats de l'analyse ChatGPT]
---
```

## 🔧 Configuration avancée

### Personnalisation des filtres

Modifiez les extensions et dossiers dans `main_window.py` :

```python
'relevant_extensions': {
    ".js", ".ts", ".py", ".php",  # Ajoutez vos extensions
},
'ignored_folders': {
    'node_modules', '.git', 'custom_folder'  # Ajoutez vos exclusions
}
```

### Taille des chunks

Ajustez la taille maximale des chunks dans `analyzer_worker.py` :

```python
self.max_chunk_size = 8000  # Caractères par chunk
```

## 🛠️ Dépannage

### Le navigateur ne se lance pas
```bash
# Vérifiez Chrome
google-chrome --version
# Ou chromium-browser --version

# Réinstallez ChromeDriver
pip uninstall webdriver-manager
pip install webdriver-manager
```

### Erreur de connexion ChatGPT
- Vérifiez votre connexion internet
- Assurez-vous d'être connecté à ChatGPT dans le navigateur
- Videz le cache de Chrome si nécessaire

### Fichiers non analysés
- Vérifiez que les extensions sont dans `relevant_extensions`
- Confirmez que les dossiers ne sont pas dans `ignored_folders`

## 🏗️ Architecture

```
chatgpt-code-analyzer/
├── main.py                 # Point d'entrée
├── main_window.py         # Interface GUI principale
├── workers/
│   └── analyzer_worker.py # Logique d'analyse (thread)
├── utils/
│   ├── browser_utils.py   # Utilitaires navigateur
│   ├── markdown_utils.py  # Gestion Markdown
│   └── file_utils.py      # Utilitaires fichiers
├── gui/
│   └── styles.py          # Styles PyQt5
└── requirements.txt       # Dépendances
```



## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## ⚠️ Avertissement

Cet outil utilise l'interface web de ChatGPT via automation. L'utilisation intensive peut violer les conditions d'utilisation d'OpenAI. Utilisez de manière responsable et respectez les limites de taux.

---

⭐ **N'oubliez pas de mettre une étoile si ce projet vous aide !** ⭐