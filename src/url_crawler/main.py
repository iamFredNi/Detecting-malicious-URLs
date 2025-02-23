import socket
import time
import requests
import ipaddress
import logging
import socket
import csv
import threading
import queue
import certstream
import sys
import os
from src.shared.custom_logger import CustomFormatter
from src.shared.services.dynamodb_accessor import DynamoDbAccessor
from src.shared.models.collected_site import CollectedSite, SourceType
from pysafebrowsing import SafeBrowsing


# Configuration of the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

db_accessor = DynamoDbAccessor()

malicious_prefix = []
shared_queue = queue.Queue()

"""
==============================================
ASN PART
==============================================
"""


def load_malicious_asn():
    logger.info("Chargement du fichier contenant les ASN.")
    try:
        with open("malicious_asn.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            # Load all ASN from the file
            return [row[0] for row in list(reader)][1:] 
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du fichier des ASN : {e}")
        exit(1)


# Fonction pour récupérer les préfixes IPv4 associés à un ASN (via RIPE sans clé API)
def get_ipv4_prefix_from_asn(asn):
    try:
        # Get all prefixes of the ASN
        url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Return all prefixes of this ASN
            prefixes = [
                prefix['prefix'] for prefix in data['data']['prefixes']
                if ":" not in prefix['prefix']  # Exclure les adresses IPv6 (qui contiennent ":")
            ]
            return prefixes
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des préfixes pour ASN {asn}: {e}")
    return []



def is_ip_in_range(ip: str, ip_range: str) -> bool:
    """
    Vérifie si une adresse IP appartient à une plage d'adresses IP en format CIDR.

    Args:
    ip (str): L'adresse IP à vérifier.
    ip_range (str): La plage d'adresses IP au format CIDR (ex: "192.168.0.0/24").

    Returns:
    bool: True si l'adresse IP est dans la plage, sinon False.
    """
    try:
        network = ipaddress.ip_network(ip_range, strict=False)
        ip_addr = ipaddress.ip_address(ip)
        return ip_addr in network
    except ValueError as e:
        logger.error(f"Erreur adresse IP : {ip}, {e}")
        return False


def is_ip_in_asn(ip : str) -> bool:
    for prefix in malicious_prefix:
        if is_ip_in_range(ip, prefix):
            return True
    
    return False


def load_malicious_prefix_from_asn(malicious_asn):
    global malicious_prefix
    logger.info("Récupération des prefixes IPs à partir des ASN")
    # Get all Ips from the malicious host
    for asn in malicious_asn:
        logger.info(f"Chargement de l'ASN {asn}")
        if asn:
            prefixes = get_ipv4_prefix_from_asn(asn)
            malicious_prefix = malicious_prefix + prefixes

"""
==============================================
DOMAIN PART
==============================================
"""

def get_ip_from_domain(domain):
    try:
        # Get the ip of the domain 
        ip = socket.gethostbyname(domain)
        return ip
    except socket.error as e:
        logger.error(f"Erreur lors de la récupération de l'IP pour {domain}: {e}")
    return None



def analyze_domain(domain):
    domain_ip = get_ip_from_domain(domain)
    if domain_ip and is_ip_in_asn(domain_ip):
        # Enregistrement du domaine malicieux dans le fichier 'malicious_domain.txt'
        with open("malicious_domain.txt", "a") as file:
            file.write(f"{domain}\n")
        
        logger.warning(f"Le domaine {domain} avec l'IP {domain_ip} est malicieux.")
        logger.info(f"Ecriture du domaine {domain} en base de données.")
        write_domain_in_db(domain)
    else:
        logger.info(f"Le domaine {domain} n'est pas considéré comme malicieux.")

def write_domain_in_db(domain):
    collected_site = CollectedSite.from_urls(
        [domain], 
        SourceType.CRAWLER, 
        "URL_Crawler"
    )[0]
    
    db_accessor.write(collected_site)


"""
==============================================
CONSUMER
==============================================
"""

def consumer():
    while True:
        # Get the first element
        domain = shared_queue.get()
        if domain is None:  # Condition d'arrêt
            break

        logger.info(f"CONSUMER : Récupération du domaine {domain} dans la queue")
        analyze_domain(domain)


"""
==============================================
PRODUCER
==============================================
"""

# Liste des préfixes à ignorer
excluded_prefixes = ["webmail", "webdisk", "cpanel", "autodiscover", "ftp", "mail", "smtp", "phpmyadmin", "*.", "cpcalendar", "cpcontact" ]

exclude_words=["event.join", "ww25","verifier-azure", "galaxy-dev", "galaxy", "amplifyapp", "mongodb", "sandbox", "microsoft-int", "windows-int", "herozerogame", "test"]

phishing_keywords = [
    # challeges : List de mots clés - prouvé que c'est un signe de phising - analyse de mots clés
    
    "connexion", "securiser", "compte", "verifier",  "confirmer",
    "banque", "soutien", "informations", "facturation", "amende", "acheminement", "macarte", "maladie", "abonnement"
    "aide", "livraison", "colis", "paiement", "mobilite", 
    "urgent.", "urgent-",".urgent", "-urgent","suspicion", "attention", 
    "avertissement","leboncoin", "allegro", "vinted", ".antai", "-antai", "laposte", "indemnite", "parcel", "consignes",
    "impaye", "-vitale", ".vitale" ,"-gouv", "stationement", "-gouv", "rappel", "retard", "-ameli",".ameli", "regularisation", 
    "credit-agricole", "banque-populaire", "credit.agricole", "banque.postale", "banque-postale", "caisse-epargne",
    "caisse.epargne", "-cic.", ".cic-", ".cic.", "-cic-", ".lcl-", "-lcl.", "-lcl-", "societe-generale", "societe.generale", "-bnp", ".bnp", 
    "bnpparibas", "banquepopulaire", "bnp.paribas" , "banquepopulaire", "Gumtree", "Milanuncios", "Subito", "2ememain", 
    "Marktplaats", "Blocket", "Anibis", "Kijiji", "MercadoLibre", "Segundamano", "cartevitale", "infraction", "shipment",
    "-sante", ".sante", "dossier-", "dossier.", "relai", "chronopost", "contravention", "cocaine", "heroine", "-mdma",
    ".mdma", "fentany","canadapost", ".ups-", "-ups-", "-ups.", "-dhl.", ".dhl.", "-dhl-", ".dhl-", "-dpd.", ".dpd.", "-dpd-", ".dpd-", "fedex"

    "netflix", 'burger-king', "burgerking", "airbnb", "-blablacar", "snapchat", "instagram", "-facebook", "facebook-", "telegram"
    "whatsapp", "-amex", "amex-", "binance", "banxo-", "-banxo", "blablacar-", "applecare", "apple-care", "-icloud", "icloud-", "-paypal", "paypal-", 
    "-google", "google-", "microsoft-", "-microsoft", "-windows", "windows-", "-antivirus", "antivirus-", "stationnement", "coinbase",
    "-amazon", "amazon-", "googlepay", "-axa", "axa-", "-samsung","samsung-", "-nike", "nike-", "adidas-", "-adidas", "discord-", "-discord", 
    "action-logement", "action.logement", "actionlogement", "allocation", "-caf-", "-caf.", ".caf-" ,
    "carrefour", "e-leclerc", "intermarche", "lnfraction",
     
    # États-Unis
    "bank-of-america", "bank.of.america", "bankofamerica", "bank.of-america","bank-of.america",
    "jpmorgan-chase", "jpmorgan.chase", "jpmorganchase",
    "wells-fargo", "wells.fargo", "wellsfargo",
    "citibank", 
    "us-bank", "us.bank", "usbank", 
    "pnc-bank", "pnc.bank", "pncbank",
    "capital-one", "capital.one", "capitalone", 
    "td-bank", "td.bank", "tdbank", 
    "goldman-sachs", "goldman.sachs", "goldmansachs", 
    "morgan-stanley", "morgan.stanley", "morganstanley",

    # Canada
    "royal-bank-of-canada", "royal.bank.of.canada", "royalbankofcanada", "royal.bank-of-canada", "royal-bank.of-canada", "royal-bank-of.canada", 
    ".rbc", "-rbc", 
    "toronto-dominion", "toronto.dominion", "torontodominion",
    "scotiabank", 
    "bank-of-montreal", "bank.of.montreal", "bankofmontreal", "-bmo.", "-bmo-", ".bmo.", 
    "canadian-imperial", "canadian.imperial", "canadianimperial", 
    ".cibc", "-cibc", 
    "national-bank-of-canada", "national.bank.of.canada", "nationalbankofcanada",
    "desjardins", 
    "hsbc-canada", "hsbc.canada", "hsbccanada", 
    "laurentian-bank", "laurentian.bank", "laurentianbank",

    # Allemagne
    "deutsche-bank", "deutsche.bank", "deutschebank", 
    "commerzbank", 
    "dz-bank", "dz.bank", "dzbank", 
    "-kfw", ".kfw",
    "ing-diba", "ing.diba", "ingdiba",

    # Royaume-Uni
    ".hsbc", "-hsbc", 
    "barclays", 
    "lloyds-bank", "lloyds.bank", "lloydsbank", 
    "natwest", 
    "standard-chartered", "standard.chartered", "standardchartered",

    # Italie
    "unicredit", 
    "intesa-sanpaolo", "intesa.sanpaolo", "intesasanpaolo", 
    "banca-monte-dei-paschi", "banca.monte.dei.paschi", "bancamontedeipaschi", 
    "banco-bpm", "banco.bpm", "bancobpm",

    # Espagne
    "banco-santander", "banco.santander", "bancosantander", 
    ".bbva", "-bbva",  
    "caixabank", 
    ".bankia", "-bankia", 

    # Suisse
    ".ubs", "-ubs", 
    "credit-suisse", "credit.suisse", "creditsuisse", 
    "julius-baer", "julius.baer", "juliusbaer", 
    "raiffeisen-schweiz", "raiffeisen.schweiz", "raiffeisenschweiz"
]

def should_exclude(domain: str) -> bool:
    """
    Vérifie si le domaine doit être exclu, soit parce qu'il commence par un préfixe indésirable,
    soit parce qu'il contient un mot indésirable.

    Args:
    domain (str): Le domaine à vérifier.

    Returns:
    bool: True si le domaine doit être exclu, sinon False.
    """
    # Vérifie si le domaine commence par un préfixe exclu
    if any(domain.startswith(prefix) for prefix in excluded_prefixes):
        return True

    # Vérifie si le domaine contient un mot indésirable
    if any(word.lower() in domain.lower() for word in exclude_words):
        return True

    return False

# Fonction pour vérifier si le domaine contient un mot-clé de phishing
def contains_phishing_keyword(domain):
    return any(keyword.lower() in domain.lower() for keyword in phishing_keywords)

# Fonction appelée à chaque fois qu'un nouveau certificat est détecté
def print_certificates(message, context):
    try:
        # Récupérer les domaines du certificat
        domains = message['data']['leaf_cert']['all_domains']
        
        # Ouvrir le fichier en mode append pour ajouter les nouveaux domaines
        with open('domains.txt', 'a') as f:
            for domain in domains:
                # Vérifier si le domaine doit être exclu ou s'il contient un mot-clé de phishing
                if not should_exclude(domain) and contains_phishing_keyword(domain):
                    f.write(f"{domain}\n")
                    logger.info("PRODUCER : Ajout du domaine %s dans la queue"%domain)
                    shared_queue.put(domain)
    except KeyError as e:
        # Ignorer si les informations du certificat ne contiennent pas de domaine
        logger.error(f"Erreur lors du producer: {e}")

def producer():
    # Connexion à CertStream en utilisant l'URL WebSocket publique
    certstream.listen_for_events(print_certificates, url='wss://certstream.calidog.io/')



if __name__ == "__main__":
    logger.info("Début du programme")
    # Load the ASN
    malicious_asn = load_malicious_asn()
    load_malicious_prefix_from_asn(malicious_asn)

    # Create consumer thread
    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)

    # Start threads
    producer_thread.start()
    consumer_thread.start()

