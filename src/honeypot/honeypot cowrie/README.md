# Cowrie Honeypot sur Google Cloud Compute Engine

## Description du projet

Ce projet consiste à déployer un **honeypot** Cowrie sur une machine virtuelle (VM) sur **Google Cloud Compute Engine**. Cowrie est un honeypot interactif conçu pour simuler **un serveur SSH/Telnet vulnérable**, permettant de capturer les tentatives de connexion malveillantes, les commandes exécutées par les attaquants, ainsi que les fichiers téléchargés.

## Objectifs du projet

- Capturer les attaques sur les services SSH et Telnet.
- Obtenir des **URL malveillantes** utilisées par les attaquants pour télécharger des scripts ou du code malveillant.

## Prerequis

Avant de commencer, assurez-vous d'avoir :

1. **Un compte Google Cloud** avec un projet actif.
2. **Compute Engine VM** avec un OS ( debian ou ubuntu ) 
3. Internet access to download necessary dependencies.

## Étapes de mise en place

### 1. Création de la VM sur Google Cloud Compute Engine

- Connectez-vous à votre compte **Google Cloud** et accédez à la **console Compute Engine**.
- Créez une nouvelle instance avec les spécifications suivantes :
    - **Type de machine** : e2-micro (ou équivalent).
    - **Système d'exploitation** : Ubuntu 20.04 LTS (ou plus récent)
    - Activez les ports **22 (SSH), 23 (Telnet)** et **33333(ou un autre > 1024)** pour se connecter en ssh au honeypot.Dans le reste du projet nous utiliserons le port 33333
  
### 2. Connexion à la VM

Pour la premiere connexion :

- **Premiere option**: 
```bash
  gcloud compute ssh <nom-de-votre-instance>
```
- **Deuxieme option**: cliquer sur le bouton ssh dans la comsole compute engine

**NB**: Après avoir activé le honeypot toutes les futures connection à l'instance se ferons sur le port **33333**


### 3. Modification du port de connextion ssh

Ouvrez le file de configuration de ssh et remplacez le port 22 par 33333:
```bash
  sudo nano /etc/ssh/sshd_config
  sudo systemctl restart ssh
  sudo systemctl status ssh
```

### 4. Installation de cowrie

- Installer les dépendances python
```bash
  sudo apt update
  sudo apt-get install git python3-virtualenv libssl-dev libffi-dev build-essential libpython3-dev python3-minimal authbind virtualenv
```
- Créer l'utilisateur cowrie sans mot de passe
```bash
    sudo useradd -m -s /bin/bash cowrie
    sudo passwd -d cowrie  
    su - cowrie
```
- Télécharger cowrie
```bash
  git clone https://github.com/cowrie/cowrie
```
- Configurer un environement virtuel: Nécessarie pour créer un espace isolé pour installer des paquets et des dépendances spécifiques du projet
```bash
  cd cowrie
  virtualenv cowrie-env
  source cowrie-env/bin/activate
  pip install --upgrade pip
  pip install --upgrade -r requirements.txt
```

- Activer Telnet: par defaut cowrie desactive telnet
```bash
 cp etc/cowrie.cfg.dist cowrie.cfg

 [Telnet]
 Enable = true
```
- Configurer les Iptables pour rediriger le traffic sur les ports 22  et 23  vers les ports 2222 et 2223 de cowrie .
```bash
sudo iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port 2222
sudo iptables -t nat -A PREROUTING -p tcp --dport 23 -j REDIRECT --to-port 2223
```
**NB**: Exécutez ces comandes en tant que root

- Lancez cowrie:
```bash
  bin/cowrie start
```

- **Logs**:
  - Pour voir les logs en live:
```bash
     tail -f /var/log/cowrie/cowrie.log
```
  - Pour consuler tous les logs d'un jour spéfique:

```bash
     cd  /var/log/cowrie/
```
  - Pour avoir plus d'info sur les logs consultez les files **cowrie.json**

### 5. Analyse 

Le repertoire ```~/cowrie/var/log/cowrie```  contient les logs depuis le lancement de l'honeypot, pour chaque journée on a deux file cowrie.log.date et cowrie.json.date


### 6. Transfert des urls vers aws

le script extract_urls.py extrait chaque jour a 10h (grace a cron) les url du jour precedent et charge un fichier .txt sur dynamoDB
```bash
  0 10 * * * /usr/bin/python3 /home/dongueyann2002/extract_urls.py
```


