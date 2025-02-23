from unittest import TestCase
from boto3 import client
from moto import mock_aws
from src.shared.services.secret_manager_accessor import SecretManagerAccessor


@mock_aws
class TestSecretManagerAccessor(TestCase):
    def setUp(self):
        sm_client = client("secretsmanager")
        sm_client.create_secret(Name="my-test-secret", SecretString="abcdefg")
        sm_client.create_secret(
            Name="phishing-brower/prod/reddit-api",
            SecretString='{"REDDIT_APP_ID":"app-id","REDDIT_APP_SECRET":"app-secret"}',
        )
        sm_client.create_secret(
            Name="some_secret",
            SecretString='test_value',
        )

    def test_get_secret(self):
        secret = SecretManagerAccessor.get_secret("my-test-secret")
        assert secret == "abcdefg"

    def test_get_reddit_secrets(self):
        app_id, app_secret = SecretManagerAccessor.get_reddit_api_secrets()
        assert app_id == "app-id"
        assert app_secret == "app-secret"

    def test_write_secret(self):
        secret_name = 'some_secret'
        secret_value = 'some_secret_value'
        SecretManagerAccessor.write_secret(secret_name, secret_value)

        secret = SecretManagerAccessor.get_secret(secret_name)
        assert secret == secret_value
        
