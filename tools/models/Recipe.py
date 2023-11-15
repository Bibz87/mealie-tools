import datetime
from models.CategorySummary import CategorySummary
from models.Nutrition import Nutrition
from models.RecipeAsset import RecipeAsset
from models.RecipeComment import RecipeComment
from models.RecipeIngredient import RecipeIngredient
from models.RecipeNote import RecipeNote
from models.RecipeSettings import RecipeSettings
from models.RecipeStep import RecipeStep
from models.RecipeTag import RecipeTag
from models.RecipeTool import RecipeTool
from pydantic import UUID4


class Recipe:
    id: UUID4

    userId: UUID4
    groupId: UUID4

    name: str
    slug: str = ""
    image = None
    recipeYield: str

    totalTime: str = None
    prepTime: str = None
    cookTime: str = None
    performTime: str = None

    description: str = ""
    categories: list[CategorySummary] = []
    tags: list[RecipeTag] = []
    tools: list[RecipeTool] = []
    rating: int
    orgUrl: str

    dateAdded: datetime.date
    dateUpdated: datetime.datetime

    createdAt: datetime.datetime
    updateAt: datetime.datetime
    lastMade: datetime.datetime

    ingredients: list[RecipeIngredient] = []
    instructions: list[RecipeStep] = []
    nutrition: Nutrition

    settings: RecipeSettings = None
    assets: list[RecipeAsset] = []
    notes: list[RecipeNote] = []
    extras: dict = {}
    isOcrRecipe: bool = False

    comments: list[RecipeComment] = []

    def __init__(self,
                 id: UUID4 = None,

                 userId: UUID4 = None,
                 groupId: UUID4 = None,

                 name: str = None,
                 recipeYield: str = None,
                 rating: int = None,
                 orgUrl: str = None,
                 dateAdded: datetime.date = None,
                 dateUpdated: datetime.datetime = None,
                 createdAt: datetime.datetime = None,
                 updateAt: datetime.datetime = None,
                 lastMade: datetime.datetime = None,
                 slug: str = "",
                 image = None,

                 totalTime: str = None,
                 prepTime: str = None,
                 cookTime: str = None,
                 performTime: str = None,

                 description: str = "",
                 categories: list[CategorySummary] = [],
                 tags: list[RecipeTag] = [],
                 tools: list[RecipeTool] = [],

                 ingredients: list[RecipeIngredient] = [],
                 instructions: list[RecipeStep] = [],
                 nutrition: Nutrition = None,

                 settings: RecipeSettings = None,
                 assets: list[RecipeAsset] = [],
                 notes: list[RecipeNote] = [],
                 extras: dict = {},
                 isOcrRecipe: bool = False,

                 comments: list[RecipeComment] = []):
        self.id = id

        self.userId = userId
        self.groupId = groupId

        self.name = name
        self.slug = slug
        self.image = image
        self.recipeYield = recipeYield

        self.totalTime = totalTime
        self.prepTime = prepTime
        self.cookTime = cookTime
        self.performTime = performTime

        self.description = description
        self.categories = categories
        self.tags = tags
        self.tools = tools
        self.rating = rating
        self.orgUrl = orgUrl

        self.dateAdded = dateAdded
        self.dateUpdated = dateUpdated

        self.createdAt = createdAt
        self.updateAt = updateAt
        self.lastMade = lastMade

        self.ingredients = ingredients
        self.instructions = instructions
        self.nutrition = nutrition

        self.settings = settings
        self.assets = assets
        self.notes = notes
        self.extras = extras
        self.isOcrRecipe = isOcrRecipe

        self.comments = comments

    def __str__(self):
        return self.slug

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def from_json(json_dct):
        categories = []
        for item in json_dct.get("recipeCategory"):
            category = CategorySummary.from_json(item)
            categories.append(category)

        tags = []
        for item in json_dct.get("tags"):
            tool = RecipeTag.from_json(item)
            tags.append(tool)

        tools = []
        for item in json_dct.get("tools"):
            tool = RecipeTool.from_json(item)
            tools.append(tool)

        instructions = []
        for item in json_dct.get("recipeInstructions"):
            step = RecipeStep.from_json(item)
            instructions.append(step)

        notes = []
        for item in json_dct.get("notes"):
            note = RecipeNote.from_json(item)
            notes.append(note)

        comments = []
        for item in json_dct.get("comments"):
            comment = RecipeComment.from_json(item)
            comments.append(comment)

        assets = []
        for item in json_dct.get("assets"):
            asset = RecipeAsset.from_json(item)
            assets.append(asset)

        ingredients = []
        for item in json_dct.get("recipeIngredient"):
            ingredient = RecipeIngredient.from_json(item)
            ingredients.append(ingredient)

        return Recipe(
          id = json_dct.get("id"),

          userId = json_dct.get("userId"),
          groupId = json_dct.get("groupId"),

          name = json_dct.get("name"),
          recipeYield = json_dct.get("recipeYield"),
          rating = json_dct.get("rating"),
          orgUrl = json_dct.get("orgUrl"),
          dateAdded = json_dct.get("dateAdded"),
          dateUpdated = json_dct.get("dateUpdated"),
          createdAt = json_dct.get("createdAt"),
          updateAt = json_dct.get("updateAt"),
          lastMade = json_dct.get("lastMade"),
          slug = json_dct.get("slug"),
          image = json_dct.get("image"),

          totalTime = json_dct.get("totalTime"),
          prepTime = json_dct.get("prepTime"),
          cookTime = json_dct.get("cookTime"),
          performTime = json_dct.get("performTime"),

          description = json_dct.get("description"),
          categories = categories,
          tags = tags,
          tools = tools,

          ingredients = ingredients,
          instructions = instructions,
          nutrition = Nutrition.from_json(json_dct.get("nutrition")),

          settings = RecipeSettings.from_json(json_dct.get("settings")),
          assets = assets,
          notes = notes,
          extras = json_dct.get("extras"),
          isOcrRecipe = json_dct.get("isOcrRecipe"),

          comments = comments
          )
