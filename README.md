# ☁️ NEXUS CLOUD - Orchestrateur IaaS

Un mini-cloud privé complet permettant de déployer, gérer et monitorer des instances virtuelles (Ubuntu/Debian) en quelques secondes.

---

## ✨ Points Forts

*   **🚀 Provisioning Turbo :** Déploiement en ~30 secondes (Optimisation Cloud-init & Netplan).
*   **🔒 Sécurité Avancée :** Gestion automatique des clés SSH et expiration forcée des mots de passe.
*   **📊 Monitoring Réel :** Tableau de bord temps réel (CPU Différentiel, RAM RSS).
*   **🎨 Interface Moderne :** Design Glassmorphism, entièrement responsive.
*   **🔌 Mode Offline :** Toutes les librairies (Bootstrap, Chart.js) sont incluses. Aucune connexion internet requise pour l'interface.

---

## 🛠️ Installation
1. Cloner le dépôt

```bash
git clone [https://github.com/schawil/nexus-cloud.git]
cd nexus-cloud
```

2. Lancer l'installation automatique

```bash
Ce script installe KVM, configure le réseau et télécharge les images Cloud officielles (Ubuntu & Debian).

chmod +x setup.sh  
sudo ./setup.sh
```

> Note : Une fois l'installation terminée, il est conseillé de redémarrer votre session pour appliquer les droits de groupe.

3. Démarrer le serveur
```bash
sudo python3 app.py
```

Ouvrez votre navigateur sur : [http://localhost:5000]

🔑 Guide de Connexion SSH

NEXUS Cloud génère les clés SSH côté serveur pour garantir la sécurité.

Lors de la création d'une VM, choisissez "Générer une clé".

Votre navigateur va télécharger un fichier (ex: ma-cle-projet).

Ce fichier se trouve dans votre dossier Téléchargements (~/Downloads).

Pour vous connecter :

Ouvrez un terminal et tapez :

## 1. Sécuriser la clé (Obligatoire pour que SSH l'accepte)
```bash
chmod 600 ~/Downloads/ma-cle-projet
```
## 2. Connexion
```bash
ssh -i ~/Downloads/ma-cle-projet admin@ADRESSE_IP
```

> L'adresse IP est affichée sur le Dashboard une fois la VM démarrée.
> admin ici doit être remplacé par le nom de l'utilisateur créé.

🏗️ Architecture Technique

Backend : Python Flask + Libvirt API.

Hyperviseur : KVM / QEMU (Format qcow2 avec Backing Files).


Frontend : HTML5, Bootstrap 5 (Local), Chart.js (Local).

Orchestration : Cloud-init (User Data & Meta Data injection via ISO).


## Auteur

*   [@schawil](github.com) - Initial commit & Mainteneur

