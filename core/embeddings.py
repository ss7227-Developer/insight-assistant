"""
embeddings.py
Initializes and returns a BedrockEmbeddings client.
Adapted from Financial_chatbot/vector_store_manager.py.
"""

import boto3
from langchain_community.embeddings import BedrockEmbeddings

import config


def get_embeddings() -> BedrockEmbeddings:
    """Return a Bedrock embeddings client using credentials from config."""
    session = boto3.Session(
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    )
    bedrock_client = session.client(service_name="bedrock-runtime")
    return BedrockEmbeddings(
        client=bedrock_client,
        model_id=config.EMBEDDING_MODEL_ID,
    )
