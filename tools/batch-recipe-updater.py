from ArgsUtils import ArgsUtils
from LogUtils import LogUtils
from MealieApi import MealieApi
from models.Recipe import Recipe
from models.RecipeSettings import RecipeSettings
from RecipeBatchProcessor import RecipeBatchProcessor


def parseArgs():
    parser = ArgsUtils.initialiseParser(scriptUsesMealieApi=True)
    return parser.parse_args()


# Function can be updated to filter Recipes using any logic
def filterRecipes(recipe: Recipe) -> bool:
    hasTag = False

    for tag in recipe.tags:
        if (tag.slug == "parse-ingredients" or
            tag.slug == "missing-ingredients"):
            hasTag = True

    return not hasTag


def noOp(logger, api: MealieApi, recipe: Recipe, isDryRun: bool):
    logger.info(f"No-Op; doing nothing with recipe {recipe.slug}")


def updateSettings(logger, api: MealieApi, recipe: Recipe, isDryRun: bool):
    logger.info(f"Updating recipe '{recipe.slug}'")

    disableAmount = False

    if recipe.ingredients:
        for ingredient in recipe.ingredients:
            if (ingredient.quantity <= 0 or
                not ingredient.food or
                not ingredient.isFood or
                ingredient.disableAmount):
                disableAmount = True
                break
    else:
        disableAmount = True

    newSettings = RecipeSettings(
            disableAmount=disableAmount,
            public=True,
            showNutrition=True,
            showAssets=True,
            landscapeView=False,
            disableComments=False,
            locked=False
        )

    hasChanged = recipe.settings != newSettings

    if not hasChanged:
        logger.info("No settings changes required")
        return

    logger.debug(f"Settings to update:\n{recipe.settings.diff(newSettings)}")

    if isDryRun:
        logger.warning("[DRY RUN] Would've updated recipe settings")
        return None

    api.updateRecipeSettings(recipe.slug, newSettings)


def addTags(logger, api: MealieApi, recipe: Recipe, tagSlugs: list[str], isDryRun: bool):
    logger.info(f"Adding tags to recipe '{recipe.slug}'")
    logger.debug(f"Tags: {tagSlugs}")

    tags = api.getAllTags()
    matchedSlugs = []
    newTags = []

    for tag in tags:
        if tag.slug in tagSlugs:
            matchedSlugs.append(tag.slug)

            if tag in recipe.tags:
                logger.info(f"Recipe already has tag '{tag.slug}'")
            else:
                newTags.append(tag)

    if len(matchedSlugs) != len(tagSlugs):
        unmatchedSlugs = []

        for slug in tagSlugs:
            if slug not in matchedSlugs:
                unmatchedSlugs.append(slug)

        logger.warning(f"Unable to match all slugs with tags. Unmatched slugs: {unmatchedSlugs}")

    if len(newTags) == 0:
        logger.info("No tag changes required")
        return

    newRecipeTags = recipe.tags + newTags

    logger.debug(f"Adding tags: {newTags}")

    if isDryRun:
        logger.warning("[DRY RUN] Would've updated recipe tags")
        return

    api.tagRecipe(recipe.slug, newRecipeTags)


def removeCategories(logger, api: MealieApi, recipe: Recipe, categorySlugs: list[str], isDryRun: bool):
    logger.info(f"Removing categories from recipe '{recipe.slug}'")
    logger.debug(f"Categories: {categorySlugs}")

    categories = api.getAllCategories()
    matchedSlugs = []
    categoriesToRemove = []

    for category in categories:
        if category.slug in categorySlugs:
            matchedSlugs.append(category.slug)

            if category in recipe.categories:
                categoriesToRemove.append(category)
            else:
                logger.info(f"Recipe already doesn't have category '{category.slug}'")

    if len(matchedSlugs) != len(categorySlugs):
        unmatchedSlugs = []

        for slug in categorySlugs:
            if slug not in matchedSlugs:
                unmatchedSlugs.append(slug)

        logger.warning(f"Unable to match all slugs with categories. Unmatched slugs: {unmatchedSlugs}")

    if len(categoriesToRemove) == 0:
        logger.info("No category changes required")
        return

    newRecipeCategories = [item for item in recipe.categories if item not in categoriesToRemove]

    logger.debug(f"Removing categories: {categoriesToRemove}")
    logger.debug(f"Remaining categories: {newRecipeCategories}")

    if isDryRun:
        logger.warning("[DRY RUN] Would've updated recipe categories")
        return

    api.categoriseRecipe(recipe.slug, newRecipeCategories)


# Generic action that can be modified to do pretty much anything on a given Recipe
def do(logger, mealieApi: MealieApi, recipe: Recipe, isDryRun: bool):
    logger.info(f"Processing recipe '{recipe.slug}'")

    categoriesToTransfer = [
        "lunch",
        "breakfast",
        "dinner",
        "snack",
        "sauce",
        "soup",
    ]

    for category in recipe.categories:
        if category.slug in categoriesToTransfer:
            logger.info(f"Transferring category '{category.slug}'")
            addTags(logger, mealieApi, recipe, [category.slug], isDryRun)
            removeCategories(logger, mealieApi, recipe, [category.slug], isDryRun)


def execute():
    args = parseArgs()
    logger = LogUtils.initialiseLogger(args.verbosity, filename="batch-recipe-updater.log")

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; recipes will not be modified")

    mealieApi = MealieApi(args.url, args.token, args.caPath, args.cacheDuration)
    processor = RecipeBatchProcessor(mealieApi)

    # tagSlugs = ["missing-spice-ratios"]
    # categorySlugs = ["goodfood"]

    processor.executeOnAllRecipes(
        # action=lambda r: addTags(logger, mealieApi, r, tagSlugs, args.dryRun),
        # action=lambda r: removeCategories(logger, mealieApi, r, categorySlugs, args.dryRun),
        # action=lambda r: updateSettings(logger, mealieApi, r, args.dryRun),
        action=lambda r: do(logger, mealieApi, r, args.dryRun),
        # action=lambda r: noOp(logger, mealieApi, r, args.dryRun),
        testFunction=None)
        # testFunction=filterRecipes)

    logger.info("Processing completed!")


if __name__ == "__main__":
    execute()
