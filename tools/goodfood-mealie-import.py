import argparse
import json
import logging
import os
import shutil
import sys

from MealieApi import MealieApi
from ColoredLogFormatter import ColoredLogFormatter


def parseArgs():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-v",
        "--verbosity",
        help="Verbosity level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO")
    parser.add_argument(
        "-d",
        "--dryRun",
        help="No-op; will not modify file system",
        action="store_true")

    parser.add_argument(
        "-u",
        "--url",
        help="URL to Mealie instance",
        required=True)

    parser.add_argument(
        "-t",
        "--token",
        help="Mealie API token",
        required=True)

    parser.add_argument(
        "-c",
        "--caPath",
        help="Path to CA bundle used to verify server TLS certificate",
        default=None)

    parser.add_argument(
        "-i",
        "--inputPath",
        help="Path where sorted recipe files are located",
        required=True)

    parser.add_argument(
        "-o",
        "--outputPath",
        help="Path where processed recipes will be moved to",
        required=True)

    return parser.parse_args()


def initLogger(verbosity):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, verbosity))

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(ColoredLogFormatter())
    logger.addHandler(consoleHandler)

    fileHandler = logging.FileHandler('goodfood-mealie-importer.log', encoding="utf-8")
    fileLogFormat = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] %(message)s')
    fileHandler.setFormatter(fileLogFormat)
    logger.addHandler(fileHandler)

    logger.info("Logger initialised")

    return logger


def importRecipes(logger, mealieApi, inputPath, outputPath, isDryRun):
    logger.info(f"Importing recipes from '{inputPath}'")

    recipeNames = os.listdir(inputPath)

    results = {
        "foundRecipes": recipeNames
    }

    recipeCount = len(recipeNames)

    logger.info(f"Found {recipeCount} recipes")
    logger.debug(f"Recipes: {recipeNames}")

    duplicates = []
    importedRecipes = []
    processedRecipeCount = 1

    for recipeName in recipeNames:
        logger.info(f"Importing recipe {processedRecipeCount} of {recipeCount}: {recipeName}")

        recipePath = f"{inputPath}/{recipeName}"
        metadata = loadMetadata(logger, recipePath)
        recipeTitle = metadata["title"]
        recipeExists = mealieApi.hasRecipe(recipeTitle)

        if recipeExists:
            logger.warning("[DUPLICATE] Recipe already exists in Mealie. Skipping.")
            duplicates.append(recipeTitle)
            processedRecipeCount += 1
            continue

        categories = processCategories(logger, mealieApi, metadata["categories"], isDryRun)
        tags = processTags(logger, mealieApi, metadata["tags"], isDryRun)

        recipeSlug = createRecipe(logger, mealieApi, f"{recipePath}/Front.png", isDryRun)
        addBackImage(logger, mealieApi, recipeSlug, f"{recipePath}/Back.png", isDryRun)

        newSlug = renameRecipe(logger, mealieApi, recipeSlug, metadata, isDryRun)
        categoriseRecipe(logger, mealieApi, newSlug, categories, isDryRun)
        tagRecipe(logger, mealieApi, newSlug, tags, isDryRun)
        updateRecipeServings(logger, mealieApi, newSlug, metadata["servings"], isDryRun)

        moveFolder(logger, recipePath, f"{outputPath}", isDryRun)

        importedRecipes.append(recipeTitle)
        processedRecipeCount += 1

    results["duplicates"] = duplicates
    results["importedRecipes"] = importedRecipes

    return results


def processCategories(logger, mealieApi, categorieNames, isDryRun):
    logger.info("Processing recipe categories")

    categories = []

    for categoryName in categorieNames:
        category = mealieApi.getCategory(categoryName)

        if not category:
            if isDryRun:
                logger.warning(f"[DRY RUN] Would've created Mealie category {categoryName}")
            else:
                category = mealieApi.createCategory(categoryName)

        categories.append(category)

    return categories


def processTags(logger, mealieApi, tagNames, isDryRun):
    logger.info("Processing recipe tags")

    tags = []

    for tagName in tagNames:
        tag = mealieApi.getTag(tagName)

        if not tag:
            if isDryRun:
                logger.warning(f"[DRY RUN] Would've created Mealie tag {tagName}")
            else:
                tag = mealieApi.createTag(tagName)

        tags.append(tag)

    return tags


def loadMetadata(logger, recipePath):
    logger.info("Loading recipe metadata")

    with open(f"{recipePath}/metadata.json") as metadataFile:
        metadata = json.load(metadataFile)

    logger.debug(f"Metadata: {metadata}")

    return metadata


def createRecipe(logger, mealieApi, imagePath, isDryRun):
    logger.info("Importing recipe into Mealie")

    if isDryRun:
        logger.warning(f"[DRY RUN] Would've imported recipe into Mealie from {imagePath}")
        return None

    recipeSlug = mealieApi.createRecipeWithOcr(imagePath)

    return recipeSlug


def addBackImage(logger, mealieApi, recipeSlug, imagePath, isDryRun):
    logger.info("Adding back image to recipe")

    if isDryRun:
        logger.warning(
            f"[DRY RUN] Would've added back image '{imagePath}'"
        )
        return

    mealieApi.addRecipeAsset(recipeSlug, imagePath, MealieApi.AssetIcon.Image)


def renameRecipe(logger, mealieApi, slug, metadata, isDryRun):
    logger.info("Renaming recipe")

    newName = metadata["title"]

    if isDryRun:
        logger.warning(
            f"[DRY RUN] Would've renamed recipe to {newName}"
        )
        return

    return mealieApi.renameRecipe(slug, newName)


def categoriseRecipe(logger, mealieApi, slug, categories, isDryRun):
    logger.info("Categorising recipe")

    if isDryRun:
        logger.warning(
            f"[DRY RUN] Would've categorised recipe with {categories}"
        )
        return

    mealieApi.categoriseRecipe(slug, categories)


def tagRecipe(logger, mealieApi, slug, tags, isDryRun):
    logger.info("Tagging recipe")

    if isDryRun:
        logger.warning(
            f"[DRY RUN] Would've tagged recipe with {tags}"
        )
        return

    mealieApi.tagRecipe(slug, tags)


def updateRecipeServings(logger, mealieApi, slug, servingsText, isDryRun):
    logger.info("Updating recipe servings")

    if isDryRun:
        logger.warning(
            f"[DRY RUN] Would've updated recipe servings with '{servingsText}'"
        )
        return

    mealieApi.updateRecipeServings(slug, servingsText)


def moveFolder(logger, sourcePath, targetPath, isDryRun):
    createFolder(logger, targetPath, isDryRun)

    if isDryRun:
        logger.warning(f"[DRY RUN] Would've moved folder from '{sourcePath}' to '{targetPath}'")
        return

    logger.info("Moving folder")
    shutil.move(sourcePath, targetPath)


def createFolder(logger, path, isDryRun):
    if isDryRun:
        logger.warning(f"[DRY RUN] Would've created folder {path}")
        return

    if os.path.exists(path):
        return

    logger.info(f"Creating folder '{path}'")
    os.makedirs(path)


def logExecutionReport(logger, results):
    logger.info("----- Execution report -----")
    logger.info(f"  Found recipes count: {len(results['foundRecipes'])}")
    logger.info(f"  Duplicates count: {len(results['duplicates'])}")

    if results["duplicates"]:
        logger.info(f"  Duplicates: {results['duplicates']}")

    logger.info(f"  Imports count: {len(results['importedRecipes'])}")

    if results["importedRecipes"]:
        logger.info(f"  Imported recipes: {results['importedRecipes']}")

    logger.info("----------------------------")


def execute():
    args = parseArgs()
    logger = initLogger(args.verbosity)

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; Mealie will not be modified")

    logger.debug(f"URL: {args.url}")
    logger.debug(f"Input path: {args.inputPath}")
    logger.debug(f"Output path: {args.outputPath}")

    mealieApi = MealieApi(args.url, args.token, args.caPath)

    results = importRecipes(
        logger,
        mealieApi,
        args.inputPath,
        args.outputPath,
        args.dryRun
    )

    logExecutionReport(logger, results)


if __name__ == "__main__":
    execute()
