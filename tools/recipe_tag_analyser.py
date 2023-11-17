import json
import logging

from ArgsUtils import ArgsUtils
from datetime import timedelta
from enum import StrEnum
from LogUtils import LogUtils
from MealieApi import MealieApi
from models.CategorySummary import CategorySummary
from models.Recipe import Recipe, RecipeTag


class FlagTagSlugs(StrEnum):
    MissingBbqTag = "missing-bbq-tag"
    MissingSpiceRatios = "missing-spice-ratios"
    MissingServingSize = "missing-serving-size"
    MissingFreezableTag = "missing-freezable-tag"
    MissingParseIngredients = "missing-parsed-ingredients"
    MissingSauceTag = "missing-sauce-tag"
    MissingSaladTag = "missing-salad-tag"
    MissingProteinTags = "missing-protein-tags"
    MissingInstructions = "missing-instructions"
    MissingInstructionImages = "missing-instruction-images"
    MissingNutritionFacts = "missing-nutrition-facts"
    MissingTools = "missing-tools"
    MissingMealTypeCategory = "missing-meal-type-category"
    MissingCountryTag = "missing-country-tag"
    MissingIngredients = "missing-ingredients"
    MissingDescription = "missing-description"
    MissingCookTime = "missing-cook-time"
    MissingPrepTime = "missing-prep-time"
    MissingTotalTime = "missing-total-time"
    MissingImage = "missing-image"
    MissingRating = "missing-rating"
    Duplicate = "duplicate"


class TagValidationResultCode(StrEnum):
    OK = "OK"
    Unknown = "UNKNOWN"
    Conflict = "CONFLICT"
    Missing = "MISSING"


class TagValidationResult():
    tagName: str
    code: TagValidationResultCode
    reason: str

    def __init__(self, tagName: str, code: TagValidationResultCode, reason: str = None) -> None:
        self.tagName = tagName
        self.code = code
        self.reason = reason


def parseArgs():
    parser = ArgsUtils.initialiseParser(scriptUsesMealieApi=True)
    return parser.parse_args()


# Returns tag if slug exists, otherwise returns None
def getTagFromSlug(slug: str | FlagTagSlugs, tags: list[RecipeTag]) -> RecipeTag:
    return next(filter(lambda t: t.slug == slug, tags), None)


# validatedTag and realTag are mutually exclusive: if one exists, the other shouldn't
def checkMutuallyExclusiveTags(recipe: Recipe,
                               validatedTag: RecipeTag,
                               realTags: list[RecipeTag],
                               isMandatory: bool = False) -> TagValidationResult:
    foundTags: list[RecipeTag] = []

    for tag in realTags:
        if tag in recipe.tags:
            foundTags.append(tag)

    if (validatedTag in recipe.tags and
        len(foundTags) > 0):
        tagsText = ", ".join(t.name for t in foundTags)
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but also found tag(s): '{tagsText}'"
        )

    if (validatedTag not in recipe.tags and
        len(foundTags) == 0):
        if isMandatory:
            return TagValidationResult(
                tagName=validatedTag.name,
                code=TagValidationResultCode.Missing,
                reason="Couldn't find corresponding tag(s) on recipe"
            )
        else:
            return TagValidationResult(
                tagName=validatedTag.name,
                code=TagValidationResultCode.Unknown,
                reason=f"Tag '{validatedTag.name}' might need to be present"
            )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


# Checks if a recipe field is defined
def checkField(recipe: Recipe,
               validatedTag: RecipeTag,
               fieldName: str):
    if (validatedTag in recipe.tags and
        recipe.__getattribute__(fieldName)):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has field '{fieldName}' set"
            f" to: {recipe.__getattribute__(fieldName)}"
        )

    if (validatedTag not in recipe.tags and
        not recipe.__getattribute__(fieldName)):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' should be present"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateBbqTag(recipe: Recipe, tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingBbqTag, tags)
    realTag = getTagFromSlug("bbq", tags)

    return checkMutuallyExclusiveTags(recipe, validatedTag, [realTag])


def validateSpiceRatiosTag(logger: logging.Logger,
                           recipe: Recipe,
                           tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingSpiceRatios, tags)

    hasSpiceSection = False

    for ingredient in recipe.ingredients:
        if ingredient.title and ingredient.title == "Spice Mix":
            logger.debug(f"Detected ingredient title: {ingredient.title}")
            hasSpiceSection = True

    if (validatedTag in recipe.tags and
        hasSpiceSection):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has Spice Ratios"
        )

    if (validatedTag not in recipe.tags and
        not hasSpiceSection):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Unknown,
            reason=f"Tag '{validatedTag.name}' might need to be present"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateServingSizeTag(recipe: Recipe,
                           tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingServingSize, tags)
    return checkField(recipe, validatedTag, "recipeYield")


def validateFreezableTag(recipe: Recipe, tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingFreezableTag, tags)
    realTag = getTagFromSlug("freezable", tags)

    return checkMutuallyExclusiveTags(recipe, validatedTag, [realTag])


def validateParseIngredientsTag(logger: logging.Logger,
                                recipe: Recipe,
                                tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingParseIngredients, tags)

    if (validatedTag in recipe.tags and
        not recipe.settings.disableAmount):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe's 'Disable Ingredient Amounts'"
            "setting is false"
        )

    hasAllFoods = True

    for ingredient in recipe.ingredients:
        if not ingredient.food:
            logger.debug(f"Detected ingredient without Food: {ingredient.title}")
            hasAllFoods = False
            break

    if (validatedTag in recipe.tags and
        hasAllFoods):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has parsed ingredients"
        )

    if (validatedTag not in recipe.tags and
        not hasAllFoods):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Unknown,
            reason=f"Tag '{validatedTag.name}' might need to be present"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateSauceTag(recipe: Recipe,
                     tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingSauceTag, tags)
    realTag = getTagFromSlug("sauce", tags)

    return checkMutuallyExclusiveTags(recipe, validatedTag, [realTag])


def validateSaladTag(recipe: Recipe,
                     tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingSaladTag, tags)
    realTag = getTagFromSlug("salad", tags)

    return checkMutuallyExclusiveTags(recipe, validatedTag, [realTag])


def validateProteinTags(recipe: Recipe,
                        tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingProteinTags, tags)

    # Add more protein types as necessary
    proteinTagSlugs = [
        "beef",
        "chicken",
        "cod",
        "haddock",
        "halloumi",
        "lobster",
        "pork",
        "salmon",
        "sausage",
        "shrimp",
        "tilapia",
        "tofu",
        "turkey",
        "veal",
        "vegetarian"
    ]

    proteinTags = []

    for tag in tags:
        if tag.slug in proteinTagSlugs:
            proteinTags.append(tag)

    return checkMutuallyExclusiveTags(recipe, validatedTag, proteinTags, isMandatory=True)


def validateInstructionsTag(logger: logging.Logger,
                            recipe: Recipe,
                            tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingInstructions, tags)

    hasSteps = len(recipe.instructions) > 0
    allStepsOk = True

    for step in recipe.instructions:
        if not step.title and not step.text:
            logger.debug(f"Detected instruction step without title/text: {step}")
            allStepsOk = False
            break

    if (validatedTag in recipe.tags and
        hasSteps and
        allStepsOk):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has valid instructions"
        )

    if (validatedTag not in recipe.tags and
        not hasSteps):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' should be present; recipe has no instructions"
        )

    if (validatedTag not in recipe.tags and
        not allStepsOk):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' should be present; recipe has invalid instructions"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateInstructionImagesTag(logger: logging.Logger,
                                 recipe: Recipe,
                                 tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingInstructionImages, tags)

    hasAllStepImages = True

    for step in recipe.instructions:
        if not step.text or "<img" not in step.text:
            logger.debug(f"Detected instruction step without image: {step}")
            hasAllStepImages = False
            break

    if (validatedTag in recipe.tags and
        hasAllStepImages):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has instruction images"
        )

    if (validatedTag not in recipe.tags and
        not hasAllStepImages):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Unknown,
            reason=f"Tag '{validatedTag.name}' might need to be present"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateNutritionFactsTag(recipe: Recipe,
                              tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingNutritionFacts, tags)

    hasAllFields = True

    for key in recipe.nutrition.__dict__:
        if not recipe.nutrition.__getattribute__(key):
            hasAllFields = False
            break

    if (validatedTag in recipe.tags and
        hasAllFields):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has Nutrition Facts"
        )

    if (validatedTag not in recipe.tags and
        not hasAllFields):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' should be present"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateToolsTag(recipe: Recipe,
                     tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingTools, tags)

    hasTools = len(recipe.tools) > 0

    if (validatedTag in recipe.tags and
        hasTools):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has tools"
        )

    if (validatedTag not in recipe.tags and
        not hasTools):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' should be present; recipe has no tools"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateMealTypeCategoryTag(recipe: Recipe,
                                tags: list[RecipeTag],
                                categories: list[CategorySummary]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingMealTypeCategory, tags)

    # Add more meal types as necessary
    mealTypeCategorySlugs = [
        "breakfast",
        "dessert",
        "dinner",
        "sauce",
        "vinaigrette"
    ]

    foundCategories: list[CategorySummary] = []

    for category in categories:
        if category.slug in mealTypeCategorySlugs and category in recipe.categories:
            foundCategories.append(category)

    if (validatedTag in recipe.tags and
        len(foundCategories) > 0):
        text = ", ".join(t.name for t in foundCategories)
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but also found category(ies): '{text}'"
        )

    if (validatedTag not in recipe.tags and
        len(foundCategories) == 0):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' needs to be present"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateCountryTag(recipe: Recipe,
                       tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingCountryTag, tags)

    # Add more countries as necessary
    countryTagSlugs = [
        "canada",
        "belgium"
    ]

    countryTags = []

    for tag in tags:
        if tag.slug in countryTagSlugs:
            countryTags.append(tag)

    return checkMutuallyExclusiveTags(recipe, validatedTag, countryTags, isMandatory=True)


def validateIngredientsTag(recipe: Recipe,
                           tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingIngredients, tags)
    hasIngredients = len(recipe.ingredients) > 0
    allIngredientsOk = True

    for ingredient in recipe.ingredients:
        if recipe.settings.disableAmount:
            if not ingredient.note:
                allIngredientsOk = False
                break
        else:
            if not ingredient.food or ingredient.quantity <= 0:
                allIngredientsOk = False
                break

    if (validatedTag in recipe.tags and
        hasIngredients and
        allIngredientsOk):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Conflict,
            reason=f"Tag '{validatedTag.name}' is present but recipe has valid ingredient(s)"
        )

    if (validatedTag not in recipe.tags and
        not hasIngredients):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' should be present; recipe has no ingredient"
        )

    if (validatedTag not in recipe.tags and
        not allIngredientsOk):
        return TagValidationResult(
            tagName=validatedTag.name,
            code=TagValidationResultCode.Missing,
            reason=f"Tag '{validatedTag.name}' should be present; recipe has invalid ingredient(s)"
        )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateDescriptionTag(recipe: Recipe,
                           tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingDescription, tags)
    return checkField(recipe, validatedTag, "description")


def validateCookTimeTag(recipe: Recipe,
                        tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingCookTime, tags)
    return checkField(recipe, validatedTag, "performTime")


def validatePrepTimeTag(recipe: Recipe,
                        tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingPrepTime, tags)
    return checkField(recipe, validatedTag, "prepTime")


def validateTotalTimeTag(recipe: Recipe,
                         tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingTotalTime, tags)
    return checkField(recipe, validatedTag, "totalTime")


def validateImageTag(recipe: Recipe,
                     tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingImage, tags)
    return checkField(recipe, validatedTag, "image")


# Duplicate recipes should have link(s) to its other equivalent recipe(s) in the Extras section
def validateDuplicateTag(recipe: Recipe,
                         tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.Duplicate, tags)

    if validatedTag in recipe.tags:
        extras = {k: v for k, v in recipe.extras.items() if k.startswith('duplicate')}

        allUrls = True
        for key in extras:
            if not extras[key]:
                allUrls = False
                break

        if len(extras) == 0:
            return TagValidationResult(
                tagName=validatedTag.name,
                code=TagValidationResultCode.Missing,
                reason="Missing 'duplicate' entry in API Extras"
            )
        elif not allUrls:
            return TagValidationResult(
                tagName=validatedTag.name,
                code=TagValidationResultCode.Missing,
                reason="Not all API Extras have URLs"
            )

    return TagValidationResult(validatedTag.name, TagValidationResultCode.OK)


def validateRatingTag(recipe: Recipe,
                     tags: list[RecipeTag]) -> TagValidationResult:
    validatedTag = getTagFromSlug(FlagTagSlugs.MissingRating, tags)
    return checkField(recipe, validatedTag, "rating")


def analyseRecipeTags(logger: logging.Logger,
                      recipe: Recipe,
                      tagsToValidate: list[RecipeTag],
                      allTags: list[RecipeTag],
                      allCategories: list[CategorySummary]) -> list[TagValidationResult]:
    logger.info("Analysing tags")

    results: list[TagValidationResult] = []

    for tag in tagsToValidate:
        logger.debug(f"Validating tag '{tag.name}'")

        result = None
        match tag.slug:
            case FlagTagSlugs.MissingBbqTag:
                result = validateBbqTag(recipe, allTags)
            case FlagTagSlugs.MissingSpiceRatios:
                result = validateSpiceRatiosTag(logger, recipe, allTags)
            case FlagTagSlugs.MissingServingSize:
                result = validateServingSizeTag(recipe, allTags)
            case FlagTagSlugs.MissingFreezableTag:
                result = validateFreezableTag(recipe, allTags)
            case FlagTagSlugs.MissingParseIngredients:
                result = validateParseIngredientsTag(logger, recipe, allTags)
            case FlagTagSlugs.MissingSauceTag:
                result = validateSauceTag(recipe, allTags)
            case FlagTagSlugs.MissingSaladTag:
                result = validateSaladTag(recipe, allTags)
            case FlagTagSlugs.MissingProteinTags:
                result = validateProteinTags(recipe, allTags)
            case FlagTagSlugs.MissingInstructions:
                result = validateInstructionsTag(logger, recipe, allTags)
            case FlagTagSlugs.MissingInstructionImages:
                result = validateInstructionImagesTag(logger, recipe, allTags)
            case FlagTagSlugs.MissingNutritionFacts:
                result = validateNutritionFactsTag(recipe, allTags)
            case FlagTagSlugs.MissingTools:
                result = validateToolsTag(recipe, allTags)
            case FlagTagSlugs.MissingMealTypeCategory:
                result = validateMealTypeCategoryTag(recipe, allTags, allCategories)
            case FlagTagSlugs.MissingCountryTag:
                result = validateCountryTag(recipe, allTags)
            case FlagTagSlugs.MissingIngredients:
                result = validateIngredientsTag(recipe, allTags)
            case FlagTagSlugs.MissingDescription:
                result = validateDescriptionTag(recipe, allTags)
            case FlagTagSlugs.MissingCookTime:
                result = validateCookTimeTag(recipe, allTags)
            case FlagTagSlugs.MissingPrepTime:
                result = validatePrepTimeTag(recipe, allTags)
            case FlagTagSlugs.MissingTotalTime:
                result = validateTotalTimeTag(recipe, allTags)
            case FlagTagSlugs.MissingImage:
                result = validateImageTag(recipe, allTags)
            case FlagTagSlugs.Duplicate:
                result = validateDuplicateTag(recipe, allTags)
            case FlagTagSlugs.MissingRating:
                result = validateRatingTag(recipe, allTags)

        if result:
            results.append(result)

    return results


def execute():
    args = parseArgs()
    logger = LogUtils.initialiseLogger(args.verbosity, filename="recipe-tag-analyser.log")

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; file system will not be modified")

    logger.debug(f"URL: {args.url}")
    logger.info("Analysing recipe tags")

    mealieApi = MealieApi(args.url, args.token, args.caPath, cacheDuration=timedelta(hours=12))

    recipes = mealieApi.getAllRecipes()
    recipes.sort(key=lambda r: r.slug)

    allTags = mealieApi.getAllTags()
    allCategories = mealieApi.getAllCategories()

    tagsToValidate = []

    for slug in FlagTagSlugs:
        tag = getTagFromSlug(slug.value, allTags)
        if not tag:
            logger.warning(f"Mealie doesn't have tag slug '{slug}'. Skipping validation.")
            continue
        tagsToValidate.append(tag)

    report = {}

    for recipe in recipes:
        logger.info(f"Processing recipe {recipe.slug}")

        results = analyseRecipeTags(logger, recipe, tagsToValidate, allTags, allCategories)

        issues = list(filter(lambda r: r.code != TagValidationResultCode.OK, results))

        if len(issues) > 0:
            report[recipe.slug] = {
                "issues": issues
            }

    logger.info("Writing output file")

    if args.dryRun:
        logger.warning("[DRY RUN] Would've written report file")
    else:
        with open("tags-report.json", mode="w", encoding="utf-8") as jsonFile:
            jsonFile.write(
                json.dumps(report, default=lambda o: o.__dict__, indent=2, ensure_ascii=False)
            )

    logger.info("Processing completed!")


if __name__ == "__main__":
    execute()
