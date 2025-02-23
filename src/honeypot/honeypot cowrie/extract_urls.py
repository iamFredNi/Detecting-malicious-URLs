import os
import subprocess
import boto3
import uuid
from datetime import datetime, timedelta

# Configurer la connexion à DynamoDB
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = 'eu-west-3'
DYNAMODB_TABLE_NAME = 'TABLE_NAME'

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Définir la date du jour
date_today = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

# Définir le chemin du fichier de logs de Cowrie pour la date courante
log_file_path = f'/home/cowrie/cowrie/var/log/cowrie/cowrie.json.{date_today}'

# Commande grep pour extraire les URLs dans cowrie.json
grep_command = f'grep -aiE "wget http|curl http" {log_file_path}'

# Fonction pour insérer les données dans DynamoDB
def upload_to_dynamodb(urls):
    for url in urls:
        log_entry = json.loads(url)
        item = {
            'id': str(uuid.uuid4()),  # Génère un identifiant unique pour chaque enregistrement
            'date': date_today,
            'source': 'HONEY_POT',
            'source_name': log_entry.get('src_ip', 'N/A'),
            'url': log_entry.get('input').split(';')[1]  # Nettoyer les espaces autour de l'URL
        }
        # Insérer l'élément dans DynamoDB
        table.put_item(Item=item)
    print(f"{len(urls)} URLs insérées dans DynamoDB pour la date {date_today}.")


# Exécuter les commandes grep et écrire les résultats dans le fichier de sortie
result= subprocess.run(grep_command, shell=True, stdout=subprocess.PIPE, text=True)
extracted_urls = result.stdout.splitlines()

# Vérifier si des URLs ont été trouvées et les uploader dans DynamoDB
if extracted_urls:
    upload_to_dynamodb(extracted_urls)
else:
    print(f"Aucune URL trouvée dans les logs pour la date {date_today}.")
