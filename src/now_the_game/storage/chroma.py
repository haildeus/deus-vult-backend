from enum import Enum

import chromadb
from pydantic import BaseModel, Field, field_validator, model_validator

from .storage_config import storage_config


class SupportedMetaFields(Enum):
    peer_id = "peer_id"
    chat_id = "chat_id"
    message_id = "message_id"
    date = "date"


class ValidMetadataEntry(BaseModel):
    key: SupportedMetaFields
    value: str

    @field_validator("key")
    def validate_key(cls, v):
        if v not in SupportedMetaFields:
            raise ValueError(f"Metadata field {v} is not supported")
        return v


class ChromaAddRequest(BaseModel):
    """
    Used to pass an array of documents to the ChromaDB client.
    """

    documents: list[str] = Field(
        ...,
        description="Chroma can tokenize or we can do embeddings ourself",
    )
    metadata: list[ValidMetadataEntry] = Field(
        ...,
        description="Filtering and grouping on metadata",
    )
    ids: list[str] = Field(
        ...,
        description="Unique identifiers for each document. \
        Made with chat_id+message_id",
    )

    @field_validator("metadata")
    def validate_metadata(cls, v):
        for meta in v:
            if meta.keys() not in SupportedMetaFields:
                raise ValueError(f"Metadata field {meta.keys()} is not supported")
        return v

    @model_validator(mode="after")
    def validate_lengths(self):
        if len(self.documents) != len(self.metadata) or len(self.documents) != len(
            self.ids
        ):
            raise ValueError("Documents, metadata, and ids must be of equal length")


class VectorStore:
    def __init__(self):
        self.client = chromadb.Client()
        self.config = storage_config

        self.default_collection_name = self.config.chroma_collection_default_name

    async def get_default_collection(self):
        return self.client.get_or_create_collection(self.default_collection_name)

    async def add(self, request: ChromaAddRequest):
        self.client.add(request.documents, request.metadata, request.ids)

    async def query(self, query: str, n_results: int = 10):
        if n_results <= 0:
            raise ValueError("n_results must be greater than 0")

        return self.client.query(query, n_results)
