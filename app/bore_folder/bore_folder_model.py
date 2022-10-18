from viktor.api_v1 import EntityList


class BoreFolder:
    def __init__(self, bore_entities: EntityList, folder_name: str):
        self._bore_entities = bore_entities
        self.name = folder_name
