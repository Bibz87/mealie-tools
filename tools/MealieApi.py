from enum import StrEnum
import logging
import os
import pathlib
import requests
from requests_cache import CachedSession, NEVER_EXPIRE, ExpirationTime
from slugify import slugify
from models.CategorySummary import CategorySummary
from models.Recipe import Recipe
from models.RecipeSettings import RecipeSettings
from models.RecipeTag import RecipeTag


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class MealieApi():
    class AssetIcon(StrEnum):
        File = "mdi-file"
        PDF = "mdi-file-pdf-box"
        Image = "mdi-file-image"
        Code = "mdi-code-json"
        Recipe = "mdi-silverware-fork-knife"

    def __init__(
            self,
            url: str,
            token: str,
            caCertPath: str = None,
            cacheDuration: ExpirationTime = NEVER_EXPIRE):
        self.logger = logging.getLogger("mealie")
        self.url = url
        self.token = token
        self.requestVerify = caCertPath if caCertPath else True
        self.session = CachedSession("mealie-api-cache", expire_after=cacheDuration)

        if cacheDuration == NEVER_EXPIRE:
            self.session.cache.clear()

        self.logger.info("Mealie API initialised")

    def hasCategory(self, categoryName: str) -> bool:
        self.logger.debug(f"Checking if category '{categoryName}' exists")

        category = self.getCategory(categoryName)

        return category is not None

    def getCategory(self, categoryName: str) -> CategorySummary:
        self.logger.debug(f"Getting category '{categoryName}'")

        slug = slugify(categoryName)
        url = f"{self.url}/api/organizers/categories/slug/{slug}"
        r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify)

        if r.status_code == 200:
            return CategorySummary.from_json(r.json())

        return None

    def getAllCategories(self) -> list[CategorySummary]:
        self.logger.debug("Getting all categories")

        url = f"{self.url}/api/organizers/categories"
        r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify)

        page = 1
        totalPages = 1 # Small number to reduce loop count in case of logic error

        categories = []

        while page <= totalPages:
            params = {
                "page": page
            }
            r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify, params=params)
            response = r.json()
            totalPages = response["total_pages"]

            for rawCategory in response["items"]:
                category = CategorySummary.from_json(rawCategory)
                categories.append(category)

            page += 1

        return categories

    def createCategory(self, categoryName: str) -> CategorySummary:
        self.logger.debug(f"Creating category '{categoryName}'")

        url = f"{self.url}/api/organizers/categories"
        data = {
            "name": categoryName
        }

        r = self.session.post(url, auth=BearerAuth(self.token), json=data, verify=self.requestVerify)
        r.raise_for_status()

        return CategorySummary.from_json(r.json())

    def getTag(self, tagName: str) -> RecipeTag:
        self.logger.debug(f"Getting tag '{tagName}'")

        slug = slugify(tagName)
        url = f"{self.url}/api/organizers/tags/slug/{slug}"
        r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify)

        if r.status_code == 200:
            return RecipeTag.from_json(r.json())

        return None

    def getAllTags(self) -> list[RecipeTag]:
        self.logger.debug("Getting all tags")

        url = f"{self.url}/api/organizers/tags"
        r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify)

        page = 1
        totalPages = 1 # Small number to reduce loop count in case of logic error

        tags = []

        while page <= totalPages:
            params = {
                "page": page
            }
            r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify, params=params)
            response = r.json()
            totalPages = response["total_pages"]

            for rawTag in response["items"]:
                tag = RecipeTag.from_json(rawTag)
                tags.append(tag)

            page += 1

        return tags

    def createTag(self, tagName: str) -> RecipeTag:
        self.logger.debug(f"Creating tag '{tagName}'")

        url = f"{self.url}/api/organizers/tags"
        data = {
            "name": tagName
        }

        r = self.session.post(url, auth=BearerAuth(self.token), json=data, verify=self.requestVerify)
        r.raise_for_status()

        return RecipeTag.from_json(r.json())

    def hasRecipe(self, recipeTitle: str) -> bool:
        self.logger.debug(f"Checking if recipe '{recipeTitle}' exists")

        slug = slugify(recipeTitle)
        url = f"{self.url}/api/recipes/{slug}"
        r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify)

        return r.status_code == 200

    def getRecipe(self, recipeTitle: str) -> Recipe:
        self.logger.debug(f"Getting recipe '{recipeTitle}'")

        slug = slugify(recipeTitle)
        url = f"{self.url}/api/recipes/{slug}"
        r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify)

        if r.status_code == 200:
            return Recipe.from_json(r.json())

        return None

    def getAllRecipes(self) -> list[Recipe]:
        self.logger.debug(f"Getting all recipes")

        url = f"{self.url}/api/recipes"

        page = 1
        totalPages = 1 # Small number to reduce loop count in case of logic error

        slugs = []

        while page <= totalPages:
            params = {
                "page": page
            }
            r = self.session.get(url, auth=BearerAuth(self.token), verify=self.requestVerify, params=params)
            response = r.json()
            totalPages = response["total_pages"]

            for item in response["items"]:
                slugs.append(item["slug"])

            page += 1

        recipes: list[Recipe] = []

        for slug in slugs:
            recipe = self.getRecipe(slug)
            recipes.append(recipe)

        return recipes

    def createRecipeWithOcr(self, imagePath: str, setThumbnail: bool = True) -> str:
        self.logger.debug(f"Creating recipe with OCR with image '{imagePath}'")

        extension = pathlib.Path(imagePath).suffix

        with open(imagePath, 'rb') as imageFile:

            url = f"{self.url}/api/recipes/create-ocr"
            data = {
                "extension": (None, extension),
                "makefilerecipeimage": (None, setThumbnail),
                "file": imageFile
            }

            r = self.session.post(
                url,
                auth=BearerAuth(self.token),
                files=data,
                verify=self.requestVerify
            )
            r.raise_for_status()

        return r.json()

    def addRecipeAsset(self, recipeSlug: str, imagePath: str, icon: AssetIcon = AssetIcon.File) -> None:
        self.logger.debug(f"Adding asset '{imagePath}' to recipe slug '{recipeSlug}'")

        fileName = os.path.basename(os.path.splitext(imagePath)[0])
        extension = pathlib.Path(imagePath).suffix

        with open(imagePath, 'rb') as imageFile:

            url = f"{self.url}/api/recipes/{recipeSlug}/assets"
            data = {
                "name": (None, fileName),
                "extension": (None, extension),
                "icon": (None, icon),
                "file": imageFile
            }

            r = self.session.post(
                url,
                auth=BearerAuth(self.token),
                files=data,
                verify=self.requestVerify
            )
            r.raise_for_status()

    def renameRecipe(self, recipeSlug: str, newName: str) -> str:
        self.logger.debug(f"Renaming recipe '{recipeSlug}' with new name: {newName}")

        newSlug = slugify(newName)

        url = f"{self.url}/api/recipes/{recipeSlug}"
        data = {
            "name": newName,
            "slug": newSlug
        }

        r = self.session.patch(url, auth=BearerAuth(self.token), json=data, verify=self.requestVerify)
        r.raise_for_status()

        return newSlug

    def categoriseRecipe(self, recipeSlug: str, categories: list[CategorySummary]) -> None:
        self.logger.debug(f"Categorising recipe '{recipeSlug}' with categories: {categories}")

        url = f"{self.url}/api/recipes/{recipeSlug}"
        data = {
            "recipeCategory": [c.to_json() for c in categories]
        }

        r = self.session.patch(url, auth=BearerAuth(self.token), json=data, verify=self.requestVerify)
        r.raise_for_status()

    def tagRecipe(self, recipeSlug: str, tags: list[RecipeTag]) -> None:
        self.logger.debug(f"Tagging recipe '{recipeSlug}' with tags: {tags}")

        url = f"{self.url}/api/recipes/{recipeSlug}"
        data = {
            "tags": [t.to_json() for t in tags]
        }

        r = self.session.patch(url, auth=BearerAuth(self.token), json=data, verify=self.requestVerify)
        r.raise_for_status()

    def updateRecipeServings(self, recipeSlug: str, servingsText: str) -> None:
        self.logger.debug(f"Updating recipe '{recipeSlug}' with servings: {servingsText}")

        url = f"{self.url}/api/recipes/{recipeSlug}"
        data = {
            "recipeYield": servingsText
        }

        r = self.session.patch(url, auth=BearerAuth(self.token), json=data, verify=self.requestVerify)
        r.raise_for_status()

    def updateRecipeSettings(self, recipeSlug: str, settings: RecipeSettings) -> None:
        self.logger.debug(f"Updating recipe '{recipeSlug}' with settings: {settings}")

        url = f"{self.url}/api/recipes/{recipeSlug}"
        data = {
            "settings": settings.to_json()
        }

        r = self.session.patch(url, auth=BearerAuth(self.token), json=data, verify=self.requestVerify)
        r.raise_for_status()

    def runOcrOnFile(self, filePath: str):
        self.logger.debug(f"Running OCR on '{filePath}'")

        with open(filePath, 'rb') as file:

            url = f"{self.url}/api/ocr/file-to-tsv"
            data = {
                "file": file
            }

            r = self.session.post(
                url,
                auth=BearerAuth(self.token),
                files=data,
                verify=self.requestVerify
            )
            r.raise_for_status()

        return r.json()
