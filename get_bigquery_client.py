import tomllib
from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
import pandas as pd

# Acessa o arquivo secrets.toml
SECRETS_FILE = ".streamlit/secrets.toml"


def get_bigquery_client():
    try:
        with open(SECRETS_FILE, "rb") as f:
            secrets = tomllib.load(f)
        
        gcp_credentials = secrets.get("gcp_service_account")
        if not gcp_credentials:
            raise FileNotFoundError("Credenciais 'gcp_service_account' não encontradas em secrets.toml.")
        
        credentials = service_account.Credentials.from_service_account_info(gcp_credentials)
        project_id = gcp_credentials["project_id"]

        client = bigquery.Client(
            credentials=credentials,
            project=project_id
        )

        # Cria o dataset reference
        default_dataset = bigquery.DatasetReference(project_id, "DELIVERY")

        # Configura QueryJobConfig com dataset padrão
        client._default_query_job_config = bigquery.QueryJobConfig(default_dataset=default_dataset)

        return client
    except Exception as e:
        print(f"Erro ao carregar credenciais: {e}")
        return None
# Exemplo de uso
