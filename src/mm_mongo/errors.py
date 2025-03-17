class MongoNotFoundError(Exception):
    def __init__(self, id: object) -> None:
        self.id = id
        super().__init__(f"mongo document not found: {id}")
