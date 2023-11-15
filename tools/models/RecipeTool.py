from pydantic import UUID4
from models.RecipeTag import RecipeTag


class RecipeTool(RecipeTag):
    id: UUID4
    onHand: bool = False

    def __init__(self,
                 id: UUID4,
                 slug: str,
                 name: str,
                 onHand: bool):
        super().__init__(id, slug, name)
        self.id = id
        self.onHand = onHand

    @staticmethod
    def from_json(json_dct):
      return RecipeTool(
         id = json_dct["id"],
         slug = json_dct["slug"],
         name = json_dct["name"],
         onHand = json_dct.get("onHand")
         )
