from ... import Database
from .config import ApiStorageConfig, api_storage_config


class ApiDatabase(Database):
    """API database implementation"""

    def __init__(self, config: ApiStorageConfig):
        super().__init__(config)


api_db = ApiDatabase(api_storage_config)
