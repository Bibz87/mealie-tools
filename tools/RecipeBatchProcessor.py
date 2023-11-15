import logging
from typing import Callable
from MealieApi import MealieApi
from models.Recipe import Recipe


class RecipeBatchProcessor():
    def __init__(self, api: MealieApi):
        self.logger = logging.getLogger("recipe-batch-processor")
        self.api = api

    def executeOnAllRecipes(
            self,
            action: Callable[[Recipe], None],
            testFunction: Callable[[Recipe], bool] = None
          ):

        if not action:
            raise ValueError("Action must be defined")

        recipes = self.api.getAllRecipes()
        recipes = list(filter(testFunction, recipes))

        self.logger.debug(f"Filtered recipes: {recipes}")

        for recipe in recipes:
            action(recipe)

        self.logger.info(f"{len(recipes)} recipe(s) updated")
