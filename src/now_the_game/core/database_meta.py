from sqlmodel import SQLModel

# Import all models from features
# These imports register the models with SQLModel.metadata


def get_metadata():
    """Return SQLModel metadata with all models registered"""
    return SQLModel.metadata
