import boto3

from json import loads
from typing import Tuple


class SecretManagerAccessor:
    """
    The goal of this class is to provide easy-to-use functions
    to access secrets in AWS Secret Manager service.
    """

    @staticmethod
    def get_secret(secret_name) -> str:
        """
        This function is used to retrieve a secret from AWS SM.

        The resource or the IAM user that is using this function must
        own the corresponding permissions to perform this action.

        The return value is always a string, but can correspond to
        a string representation of a JSON object.
        """
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_name)

        return response["SecretString"]

    @staticmethod
    def write_secret(secret_name, secret_string) -> None:
        """
        This function is used to write a secret into AWS SM

        The resource or the IAM user that is using this function must
        own the corresponding permissions to perform this action.
        """
        client = boto3.client("secretsmanager")
        client.put_secret_value(
            SecretId=secret_name, 
            SecretString=secret_string
        )

    @staticmethod
    def get_reddit_api_secrets() -> Tuple[str, str]:
        """
        This function is used to retrieve secrets for accessing the Reddit's API.

        Returns the tuple (REDDIT_APP_ID, REDDIT_APP_SECRET).
        """
        secrets_data = SecretManagerAccessor.get_secret(
            "phishing-brower/prod/reddit-api"
        )
        secrets_data = loads(secrets_data)
        return secrets_data["REDDIT_APP_ID"], secrets_data["REDDIT_APP_SECRET"]

    @staticmethod
    def get_checker_api_secrets() -> Tuple[str, str]:
        """
        This function is used to retrieve secrets for accessing Google and Virus Total API keys.

        Returns the tuple (GOOGLE_API_KEY, VIRUS_TOTAL_API_KEY)
        """

        secrets_data = SecretManagerAccessor.get_secret(
            "phishing-browser/prod/checker_api_keys"
        )
        secrets_data = loads(secrets_data)
        return secrets_data["GOOGLE_API_KEY"], secrets_data["VIRUS_TOTAL_API_KEY"]