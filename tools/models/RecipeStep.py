from pydantic import UUID4


class IngredientReferences:
    referenceId: UUID4

    def __init__(self, referenceId: UUID4):
        self.referenceId = referenceId

    @staticmethod
    def from_json(json_dct):
        return IngredientReferences(json_dct.get("referenceId"))


class RecipeStep:
    id: UUID4
    title: str = ""
    text: str
    ingredientReferences: list[IngredientReferences] = []

    def __init__(self,
                 id: UUID4,
                 text: str,
                 title: str = "",
                 ingredientReferences: list[IngredientReferences] = []):
        self.id = id
        self.text = text
        self.title = title
        self.ingredientReferences = ingredientReferences

    @staticmethod
    def from_json(json_dct):
        return RecipeStep(
            id = json_dct.get("id"),
            text = json_dct.get("text"),
            title = json_dct.get("title"),
            ingredientReferences = json_dct.get("ingredientReferences"),
            )
