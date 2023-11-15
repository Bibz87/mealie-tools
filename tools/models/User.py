from pydantic import UUID4


class User:
    id: UUID4
    username: str
    admin: bool

    def __init__(self,
                 id: UUID4,
                 username: str,
                 admin: bool):
        self.id = id
        self.username = username
        self.admin = admin

    @staticmethod
    def from_json(json_dct):
      return User(
         id = json_dct["id"],
         username = json_dct["username"],
         admin = json_dct["admin"]
         )
