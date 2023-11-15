import datetime
from pydantic import UUID4


class IngredientUnit:
    id: UUID4
    createdAt: datetime.datetime
    updateAt: datetime.datetime

    name: str
    description: str = ""
    extras: dict = {}

    fraction: bool = True
    abbreviation: str = ""
    useAbbreviation: bool = False

    def __init__(self,
                 id: UUID4,
                 createdAt: datetime.datetime,
                 updateAt: datetime.datetime,

                 name: str,
                 description: str = "",
                 extras: dict = {},

                 fraction: bool = True,
                 abbreviation: str = "",
                 useAbbreviation: bool = False):
        self.id = id
        self.createdAt = createdAt
        self.updateAt = updateAt
        self.name = name
        self.description = description
        self.extras = extras
        self.fraction = fraction
        self.abbreviation = abbreviation
        self.useAbbreviation = useAbbreviation

    @staticmethod
    def from_json(json_dct):
        if not json_dct:
            return None

        return IngredientUnit(
            id = json_dct.get("id"),
            createdAt = json_dct.get("createdAt"),
            updateAt = json_dct.get("updateAt"),
            name = json_dct.get("name"),
            description = json_dct.get("description"),
            extras = json_dct.get("extras"),
            fraction = json_dct.get("fraction"),
            abbreviation = json_dct.get("abbreviation"),
            useAbbreviation = json_dct.get("useAbbreviation")
            )


class IngredientLabel:
    id: UUID4
    groupId: UUID4
    name: str
    color: str = "#E0E0E0"

    def __init__(self,
                 id: UUID4,
                 groupId: UUID4,
                 name: str,
                 color: str = "#E0E0E0"):
        self.id = id
        self.groupId = groupId
        self.name = name
        self.color = color

    @staticmethod
    def from_json(json_dct):
        if not json_dct:
            return None

        return IngredientLabel(
            id = json_dct.get("id"),
            groupId = json_dct.get("groupId"),
            name = json_dct.get("name"),
            color = json_dct.get("color"),
            )


class IngredientFood:
    id: UUID4
    label: IngredientLabel = None
    createdAt: datetime.datetime
    updateAt: datetime.datetime

    labelId: UUID4 = None

    def __init__(self,
                 id: UUID4,
                 createdAt: datetime.datetime,
                 updateAt: datetime.datetime,
                 label: IngredientLabel = None,

                 labelId: UUID4 = None):
        self.id = id
        self.createdAt = createdAt
        self.updateAt = updateAt
        self.label = label
        self.labelId = labelId

    @staticmethod
    def from_json(json_dct):
        if not json_dct:
            return None

        return IngredientFood(
            id = json_dct.get("id"),
            createdAt = json_dct.get("createdAt"),
            updateAt = json_dct.get("updateAt"),
            label = IngredientLabel.from_json(json_dct.get("label")),
            labelId = json_dct.get("labelId"),
            )


class RecipeIngredient:
    title: str
    originalText: str
    disableAmount: bool = True

    quantity: float = 1
    unit: IngredientUnit
    food: IngredientFood
    note: str = ""

    isFood: bool = None
    display: str = ""

    def __init__(self,
                 title: str,
                 originalText: str,
                 unit: IngredientUnit,
                 food: IngredientFood,
                 disableAmount: bool = True,

                 quantity: float = 1,
                 note: str = "",

                 isFood: bool = None,
                 display: str = ""):
        self.title = title
        self.originalText = originalText
        self.unit = unit
        self.food = food
        self.disableAmount = disableAmount
        self.quantity = quantity
        self.note = note
        self.isFood = isFood
        self.display = display

    @staticmethod
    def from_json(json_dct):
        return RecipeIngredient(
            title = json_dct.get("title"),
            originalText = json_dct.get("originalText"),
            unit = IngredientUnit.from_json(json_dct.get("unit")),
            food = IngredientFood.from_json(json_dct.get("food")),
            disableAmount = json_dct.get("disableAmount"),
            quantity = json_dct.get("quantity"),
            note = json_dct.get("note"),
            isFood = json_dct.get("isFood"),
            display = json_dct.get("display"),
            )
