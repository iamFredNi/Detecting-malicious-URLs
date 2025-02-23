import random
from pysafebrowsing import SafeBrowsing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests
import boto3
import time 
import logging
from src.shared.custom_logger import CustomFormatter
from src.shared.services.dynamodb_accessor import DynamoDbAccessor
from src.shared.services.secret_manager_accessor import SecretManagerAccessor
from src.shared.models.collected_site import CollectedSite, SourceType
import os

import requests

# Configuration AWS
S3_BUCKET_NAME = "phishing-browser-screenshots"
AWS_REGION = "eu-west-3"

# Configuration of the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

database = DynamoDbAccessor()

GOOGLE_KEY, VIRUS_TOTAL_KEY = SecretManagerAccessor.get_checker_api_secrets()
MAX_QUERY_VIRUS_TOTAL = 500
nb_query_virus_total = 0

google_api = SafeBrowsing(GOOGLE_KEY)

def is_url_accessible(site :  CollectedSite) -> bool:
    """
    Vérifie si une URL est accessible et ne retourne pas un code HTTP 404 ou 403.

    Args:
        url (str): URL à vérifier.

    Returns:
        bool: True si l'URL est accessible, False sinon.
    """
     # Charger le site
    url = site.url
    if site.source == SourceType.CRAWLER:
        url = f"https://{site.url}"
    try:
        response = requests.head(url, timeout=10)  # Vérifie uniquement les headers
        if response.status_code in (404, 526):
            logger.warning(f"URL inaccessible : {url} (Code HTTP: {response.status_code})")
            return False
        return True
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la vérification de l'URL {url} : {e}")
        return False

def all_results_unrated(last_analysis_results):
    """
    Vérifie si tous les résultats dans 'last_analysis_results' sont 'unrated'.

    Args:
        last_analysis_results (dict): Dictionnaire contenant les résultats de l'analyse.

    Returns:
        bool: True si tous les résultats sont 'unrated', False sinon.
    """
    for engine in last_analysis_results.values():
        if engine.get('result') != 'unrated':
            return False
    return True

def reanalyse_domain(api_key, domain_id):
    url = f"https://www.virustotal.com/api/v3/domains/{domain_id}/analyse"

    headers = {
        "x-apikey": VIRUS_TOTAL_KEY,
        "accept": "application/json"
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        # Successfully reanalysed the domain
        result = response.json()
        return result
    else:
        # Handle errors
        return {
            "error": f"Failed to reanalyse domain. Status code: {response.status_code}",
            "details": response.text
        }

# Fonction pour vérifier un domaine avec VirusTotal
def is_malicious_virustotal(site :  CollectedSite) -> bool:
    domain = site.url
    if site.source is not SourceType.CRAWLER:
        domain = site.url.replace("https://", "").replace("http://", "")
    global nb_query_virus_total
    # URL de l'API VirusTotal pour la recherche par domaine
    URL = f"https://www.virustotal.com/api/v3/domains/{domain}"

    # Effectuer la requête GET vers l'API VirusTotal
    response = requests.get(URL, headers={
        "x-apikey": VIRUS_TOTAL_KEY
    })
    nb_query_virus_total += 1

    # Vérifier si la requête est réussie (code HTTP 200)
    if response.status_code == 200:
        # Analyser la réponse JSON
        data = response.json()

        # Vérifier la catégorie de la menace
        if 'data' in data:
            # L'élément 'attributes' contient les informations du domaine
            threat_info = data['data']['attributes']['last_analysis_stats']
            
            malicious = threat_info.get('malicious', 0)
            suspicious = threat_info.get('suspicious', 0)

            # Si le nombre de rapports malveillants est supérieur à 0, le domaine est malveillant
            if malicious > 0 or suspicious>0:
                return True

            threat_info_engine = data['data']['attributes']['last_analysis_results']

            if(all_results_unrated(threat_info_engine)):
                logger.warning(f"Aucun scan n'a probablement été fait sur ce domain : {domain}")

        return False
    else:
        print(f"Erreur lors de la requête : {response.status_code}")
        return False


def is_malicious_google(site : CollectedSite) -> bool:
    url = site.url
    if site.source == SourceType.CRAWLER:
        url = f"https://{site.url}"

    # Check the domain with the Google API
    try:
        result = google_api.lookup_urls([url])
    except Exception as e:
        logger.warning("Google API quota exceeded. Skipping")
    
    # Vérifier le statut de la réponse
    if url in result:
        threat_info = result[url]
        
        # Si le statut est "ok", cela signifie que le domaine est sûr
        return threat_info['malicious']
    
    return False


def update_domain_database(site: CollectedSite, flag_value: bool):
    # TODO update flag in database
    site.is_safe = flag_value
    database.update_collected_site(site)

def upload_to_s3(file_path: str, bucket_name: str, s3_key: str):
    """
    Upload un fichier vers un bucket S3.

    Args:
        file_path (str): Chemin local du fichier.
        bucket_name (str): Nom du bucket S3.
        s3_key (str): Clé S3 (chemin du fichier dans le bucket).

    Returns:
        bool: True si l'upload est réussi, False sinon.
    """
    s3_client = boto3.client('s3', region_name=AWS_REGION)

    try:
        s3_client.upload_file(file_path, bucket_name, s3_key)
        print(f"Fichier uploadé avec succès : s3://{bucket_name}/{s3_key}")
        return True
    except (BotoCoreError, ClientError) as e:
        print(f"Erreur lors de l'upload vers S3 : {e}")
        return False

def handle_malicious_domain(site : CollectedSite):   
    
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_file = f"{site.url.replace('.', '_').replace('https://', '').replace('http://', '')}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_file)
    s3_key = f"screenshots/{screenshot_file}"  # Chemin dans S3

    try:
        # Configuration du navigateur
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")  # Ignore les erreurs SSL
        chrome_options.add_argument("--allow-insecure-localhost")   # Autorise les connexions non sécurisées
        chrome_options.add_argument("--disable-web-security")       # Désactive certaines sécurités web
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())  # Faudra verifier le chemin ChromeDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Désactiver navigator.webdriver
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
            """
        })

        # Charger le site
        url = site.url
        if site.source == SourceType.CRAWLER:
            url = f"https://{site.url}"
        print(f"Prise du screenshot pour : {url}")
        driver.set_page_load_timeout(20)
        driver.get(url)

        # Pause aléatoire pour éviter les détections
        time.sleep(random.uniform(5, 8))

        # Prendre le screenshot
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot enregistré localement : {screenshot_path}")

        # Upload vers S3
        upload_success = upload_to_s3(screenshot_path, S3_BUCKET_NAME, s3_key)
        if upload_success:
            print(f"Screenshot uploadé avec succès sur S3 : {s3_key}")
            site.screenshot = f"https://{S3_BUCKET_NAME}.s3.eu-west-3.amazonaws.com/{s3_key}"
        else:
            print("L'upload du screenshot vers S3 a échoué.")

        # Set the flag verified in the database
        update_domain_database(site, False)
    except WebDriverException as e:
        print(f"Erreur Selenium : {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

    # Nettoyer le fichier local après l'upload
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
        print("Fichier local supprimé après l'upload.")

def verify_urls() -> None:
    
    # TODO: Retrieve the domain from the database
    # The domain is urrently a list of string, in the future, it will be a list of obj Data
    # ===================
    # TODO: TO REMOVE
    # file_path = "malicious_domain.txt"
    # domains = open(file_path, 'r')
    # ===================
    
    collected_sites = database.get_all_collected_sites()
    collected_sites = CollectedSite.sort_collected_sites(collected_sites)
    for site in collected_sites:
        if site.is_safe is not None or is_url_accessible(site) is False:
            continue
        # Check with google
        if is_malicious_google(site):
            logger.warning(f"Malicious domain with Google : {site.url}")
            handle_malicious_domain(site)
        elif nb_query_virus_total < MAX_QUERY_VIRUS_TOTAL :
            if is_malicious_virustotal(site):
                logger.warning(f"Malicious domain with Virus Total : {site.url}")
                handle_malicious_domain(site)
            else:
                # Safe website
                logger.info(f"Domain {site.url} is safe.")
                update_domain_database(site, True)
                
            # Wait 5 secondes for the limit of 5 for 1 minute
            logger.info("Wait the cooldown of Virus Total...")    
            time.sleep(5)
        # Else case => we don't update in database because we cannot verified with virus total
        


if __name__ == "__main__":
    verify_urls()
