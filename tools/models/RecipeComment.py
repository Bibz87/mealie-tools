import datetime
from models.User import User
from pydantic import UUID4


class RecipeComment:
    text: str

    id: UUID4
    recipeId: UUID4
    createdAt: datetime.datetime
    updateAt: datetime.datetime
    userId: UUID4
    user: User

    def __init__(self,
                 text: str,

                 id: UUID4,
                 recipeId: UUID4,
                 createdAt: datetime.datetime,
                 updateAt: datetime.datetime,
                 userId: UUID4,
                 user: User):
        self.text = text
        self.id = id
        self.recipeId = recipeId
        self.createdAt = createdAt
        self.updateAt = updateAt
        self.userId = userId
        self.user = user

    @staticmethod
    def from_json(json_dct):
      return RecipeComment(
         text = json_dct["text"],
         id = json_dct["id"],
         recipeId = json_dct["recipeId"],
         createdAt = json_dct["createdAt"],
         updateAt = json_dct["updateAt"],
         userId = json_dct["userId"],
         user = User.from_json(json_dct["user"]),
         )
