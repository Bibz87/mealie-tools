import argparse
import re
import shutil
import click
from itertools import zip_longest
import json
import logging
import os
from PIL import Image
from slugify import slugify
import sys
import time

from ColoredLogFormatter import ColoredLogFormatter

lastCategoryFileName = "last-category.json"


def parseArgs():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-v",
        "--verbosity",
        help="verbosity level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO")
    parser.add_argument(
        "-d",
        "--dryRun",
        help="No-op; will not modify file system",
        action="store_true")

    parser.add_argument(
        "-i",
        "--inputPath",
        help="path where files to be process are located",
        required=True)

    parser.add_argument(
        "-o",
        "--outputPath",
        help="path where processed files will be copied to",
        required=True)

    parser.add_argument(
        "--ocrDataPath",
        help="path where OCR data files are located",
        required=True)

    return parser.parse_args()


def initLogger(verbosity):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, verbosity))

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(ColoredLogFormatter())
    logger.addHandler(consoleHandler)

    fileHandler = logging.FileHandler('goodfood-scans-organiser.log', encoding="utf-8")
    fileLogFormat = logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s')
    fileHandler.setFormatter(fileLogFormat)
    logger.addHandler(fileHandler)

    logger.info("Logger initialised")

    return logger


def loadCategory(logger):
    logger.debug("Attempting to load category from file")

    if os.path.exists(lastCategoryFileName):
        with open(lastCategoryFileName, encoding="utf-8") as jsonFile:
            return json.load(jsonFile)

    return None


def validateCategory(logger, category):
    logger.debug("Validating category")

    if category:
        if click.confirm(f"Category is '{category['name']}'. Is that OK?", default=True):
            return category
    else:
        logger.warning("Category not defined. Prompting for category.")

    while True:
        categoryName = click.prompt("Please input the category name")

        if click.confirm(f"Category is '{categoryName}'. Is that OK?", default=True):
            slug = slugify(categoryName)
            break

    newCategory = {
        "name": categoryName,
        "slug": slug
    }

    return newCategory


def saveCategory(logger, category, isDryRun):
    if isDryRun:
        logger.warning("[DRY RUN] Would've saved category")
        return

    logger.debug("Saving category")

    with open(lastCategoryFileName, mode="w", encoding="utf-8") as jsonFile:
        jsonFile.write(json.dumps(category, indent=2))


def createFolder(logger, path, isDryRun):
    if isDryRun:
        logger.warning(f"[DRY RUN] Would've created folder {path}")
        return

    logger.info(f"Creating folder '{path}'")
    os.makedirs(path)


def findTitleCandidates(logger, ocrDataFilePath):
    logger.info("Attempting to automatically find recipe title")

    tsv = loadOcrData(logger, ocrDataFilePath)

    # Algorithm based on Mealie's: [1]
    # [1]: https://github.com/mealie-recipes/mealie/blob/4af9eec89dd0b309ebea752d715add3fe0980b3d/frontend/components/Domain/Recipe/RecipeOcrEditorPage/RecipeOcrEditorPage.vue#L223C6-L223C6 # noqa
    filtered = [a for a in tsv if a["level"] == 2 or a["level"] == 5]
    blocks = [[]]
    blockNum = 1

    for i, element in enumerate(filtered):
        if i != 0 and filtered[i - 1]["blockNum"] != element["blockNum"]:
            blocks.append([])
            blockNum = element["blockNum"]

        blocks[blockNum - 1].append(element)

    candidates = []

    # The bigger and higher in the page the block is, the higher the score
    for block in blocks:
        blockDefinition = block[0]
        blockSizeScore = blockDefinition["height"] * blockDefinition["width"]

        if blockDefinition["top"] != 0:
            topModifier = 1 / blockDefinition["top"]
        else:
            topModifier = 1

        blockScore = blockSizeScore * topModifier / len(block)
        blockText = "".join(map(lambda e: e["text"], block))

        if blockText != "":
            filter = [e for e in block if e["level"] == 5 and e["conf"] >= 40]
            text = " ".join(map(lambda e: e["text"].strip(), filter))
            candidates.append({
                "score": blockScore,
                "text": text
            })

    candidates.sort(key=lambda e: e["score"], reverse=True)
    titleCandidates = list(map(lambda e: e["text"], candidates))

    logger.debug(f"Found candidates: {titleCandidates}")
    return titleCandidates


def loadOcrData(logger, ocrDataFilePath):
    logger.info("Loading OCR data")

    with open(ocrDataFilePath, encoding="utf-8") as ocrDataFile:
        ocrData = json.load(ocrDataFile)

    return ocrData


def cleanTitles(logger, titles):
    logger.debug("Cleaning titles")

    # List of hard-coded OCR fixes
    replacements = [
        ("Le choix de Nick | ", ""),
        ("Sain + Sensé: ", ""),
        ("Sain + SensÃ©: ", ""),
        ("Sain + Sense: ", ""),
        ("goodfood", ""),
        ("goodjood", ""),
        ("marche", ""),
        ("|", ""),
        ("_", ""),
        ("—", ""),
        ("good", ""),
        ("food", ""),
        ("’", "'"),
        ("`", "'"),
        ("facon", "façon"),
        ("poelé", "poêlé"),
        ("poele", "poêlé"),
        ("poéle", "poêlé"),
        ("poélé", "poêlé"),
        ("poeélé", "poêlé"),
        (" a ", " à "),
        ("roti", "rôti"),
        (" ala ", " à la "),
        ("cotelettes", "côtelettes"),
        ("fume", "fumé"),
        ("hache", "haché"),
        ("pore", "porc"),
        ("fraiche", "fraîche"),
        ("grille", "grillé"),
        ("glace", "glacé"),
        ("epice", "épicé"),
        ("thai", "thaï"),
        ("péche", "pêche"),
        ("laniere", "lanière"),
        ("legume", "légume"),
        ("marine", "mariné"),
        ("mais", "maïs"),
        ("cremeux", "crémeux"),
        ("« ", "«"),
        (" »", "»"),
        ("puree", "purée"),
        (" 4 ", " à "),
        ("croute", "croûte"),
        ("perle", "perlé"),
        ("seche", "séché"),
        ("creme", "crème"),
        ("vege", "végé")
    ]

    cleanedTitles = []

    for title in titles:
        for r in replacements:
            title = re.sub(r'(?i)(\s*|^)' + re.escape(r[0]), lambda m: m[1] + r[1], title)

        title = re.sub(" {2,}", " ", title)
        title = title.strip()

        if title != "":
            cleanedTitles.append(title)

    return cleanedTitles


def organiseScans(logger, inputPath, outputPath, ocrDataPath, category, isDryRun):
    logger.info(f"Organising scans in '{inputPath}'")

    scans = os.listdir(inputPath)

    if "_DONE" in scans:
        scans.remove("_DONE")

    scanCount = len(scans)

    logger.debug(f"Found {scanCount} scans: {scans}")

    results = {
        "scans": scans
    }

    pairs = grouper(scans, 2)
    duplicates = []
    processedScanCount = 1

    for pair in pairs:
        logger.info(
            f"Processing scans {processedScanCount} & {processedScanCount + 1} of {scanCount}"
        )

        frontFilename = pair[0]
        ocrFilename = f"{os.path.basename(os.path.splitext(frontFilename)[0])}.json"
        ocrFilePath = f"{ocrDataPath}/{ocrFilename}"

        logger.debug(f"Front filename: {frontFilename}")
        logger.debug(f"Back filename: {pair[1]}")

        try:
            titleCandidates = findTitleCandidates(logger, ocrFilePath)
        except Exception as e:
            logger.warning(f"Error occurred during title analysis: {e}")
            titleCandidates = []

        recipe = processRecipeTitle(logger, titleCandidates)

        recipePath = f"{outputPath}/{recipe['slug']}"

        if os.path.exists(recipePath):
            logger.warning(
                f"[DUPLICATE] Duplicate folder for recipe '{recipe['name']}'; Appending timestamp."
            )
            duplicates.append(recipe['slug'])
            recipePath += time.strftime("%Y%m%d-%H%M%S")
            processedScanCount += 2
            logger.debug(f"New path: {recipePath}")

        createFolder(logger, path=recipePath, isDryRun=isDryRun)
        createMetadata(
            logger,
            filePath=f"{recipePath}/metadata.json",
            category=category,
            recipe=recipe,
            isDryRun=isDryRun
        )
        createOcrData(logger, ocrFilePath, recipePath, isDryRun)
        convertScan(logger, frontFilename, "Front", inputPath, recipePath, isDryRun)
        convertScan(logger, pair[1], "Back", inputPath, recipePath, isDryRun)

        processedScanCount += 2

    results["duplicates"] = duplicates

    return results


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def capitalise(string: str):
    return string[0].upper() + string[1:]


def buildRecipeTitle(logger, titleCandidates):
    for i, element in enumerate(titleCandidates):
        print(f"[{i}] {element}")

    while True:
        try:
            sequenceText = click.prompt(
                f"Input string number sequence (0 to {len(titleCandidates) - 1})"
            )

            numbers = list(map(int, sequenceText.split()))

            builtTitle = ""

            for n in numbers:
                builtTitle += " "
                builtTitle += titleCandidates[n]

            builtTitle = capitalise(builtTitle.strip())

            if click.confirm(f"Resulting title would be '{builtTitle}'. Is that OK?", default=True):
                break

        except Exception as e:
            logger.error(f"An error occurred when processing number sequence: {e}")

    return builtTitle


def editRecipeTitle(logger, candidate):
    logger.debug(f"Editing recipe title: {candidate}")

    while True:
        title = click.edit(candidate)

        if title:
            title = title.strip()

            if click.confirm(
                f"New recipe title is '{title}'. Is that OK?",
                default=True
            ):
                return title


def correctRecipeTitle(logger, candidate, titleCandidates):
    if click.confirm("Rebuild title before editing?", default=False):
        candidate = buildRecipeTitle(logger, titleCandidates)

    return editRecipeTitle(logger, candidate)


def promptRecipeTitle():
    while True:
        title = click.prompt("Please input recipe name")

        if click.confirm(f"Recipe is '{title}'. Is that OK?", default=False):
            return title


def processRecipeTitle(logger, titleCandidates):
    logger.debug("Processing recipe title")

    if titleCandidates:
        titleCandidates = cleanTitles(logger, titleCandidates)

        candidate = capitalise(titleCandidates[0])

        if click.confirm(f"Recipe title is '{candidate}'. Is that OK?", default=True):
            title = candidate
        else:
            title = correctRecipeTitle(logger, candidate, titleCandidates)
    else:
        title = promptRecipeTitle()

    recipe = {
        "name": title,
        "slug": slugify(title)
    }

    logger.debug(f"Recipe: '{recipe}'")

    return recipe


def createMetadata(logger, filePath, category, recipe, isDryRun):
    logger.info("Creating recipe metadata")

    metadata = {
        "categories": [
            "Goodfood",
            category["name"]
        ],
        "settings": {
            "public": True,
            "showNutrition": True,
            "showAssets": True,
            "landscapeView": False,
            "disableComments": False,
            "disableAmount": True,
            "locked": False
        },
        "tags": [
            "Missing Image ⚠️",
            "Missing Total Time ⚠️",
            "Missing Prep Time ⚠️",
            "Missing Cook Time ⚠️",
            "Missing Description ⚠️",
            "Missing Ingredients ⚠️",
            "Missing Country Category ⚠️",
            "Missing Type Category ⚠️",
            "Missing Tags ⚠️",
            "Missing Protein Tags ⚠️",
            "Missing Salad Tag ⚠️",
            "Missing Sauce Tag ⚠️",
            "Missing Tools ⚠️",
            "Missing Nutrition Facts ⚠️",
            "Missing Instructions ⚠️",
            "Missing Freezable Tag ⚠️",
        ],
        "title": recipe["name"],
        "servings": "2 portions"
    }

    if isDryRun:
        logger.warning(f"[DRY RUN] Would've created metadata {filePath} with content: {metadata}")
        return

    with open(filePath, mode="w", encoding="utf-8") as jsonFile:
        jsonFile.write(json.dumps(metadata, indent=2))


def createOcrData(logger, ocrFilePath, recipePath, isDryRun):
    logger.info("Copying OCR data")

    if isDryRun:
        logger.warning(f"[DRY RUN] Would've copied OCR data file '{ocrFilePath}'")
        return

    shutil.copy2(ocrFilePath, f"{recipePath}/ocr-front.json")


def convertScan(logger, fileName, newName, inputFolder, outputFolder, isDryRun):
    newFilename = f"{newName}.png"
    logger.info(f"Converting scan '{fileName}' to '{newFilename}'")

    inputPath = f"{inputFolder}/{fileName}"
    outputPath = f"{outputFolder}/{newFilename}"

    logger.debug(f"From: {inputPath}")
    logger.debug(f"To: {outputPath}")

    if isDryRun:
        logger.warning(f"[DRY RUN] Would've converted scan {fileName} to {outputPath}")
        return

    logger.debug("Converting scan")
    image = Image.open(inputPath)
    image.save(outputPath)

    logger.debug("Flagging original file as processed")
    processedPath = f"{inputFolder}/_DONE"
    if not os.path.exists(processedPath):
        os.mkdir(processedPath)
    os.rename(inputPath, f"{processedPath}/{fileName}")


def logExecutionReport(logger, results):
    logger.info("----- Execution report -----")
    logger.info(f"  Scan count: {len(results['scans'])}")
    logger.info(f"  Duplicates count: {len(results['duplicates'])}")

    if results["duplicates"]:
        logger.info(f"  Duplicates: {results['duplicates']}")

    logger.info("----------------------------")


def execute():
    args = parseArgs()
    logger = initLogger(args.verbosity)

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; file system will not be modified")

    logger.debug(f"Input path: {args.inputPath}")
    logger.debug(f"Output path: {args.outputPath}")
    logger.debug(f"OCR data path: {args.ocrDataPath}")

    category = loadCategory(logger)
    category = validateCategory(logger, category)
    logger.debug(f"Category: '{category}'")

    saveCategory(logger, category, args.dryRun)

    results = organiseScans(
        logger,
        args.inputPath,
        args.outputPath,
        args.ocrDataPath,
        category,
        args.dryRun
    )

    logExecutionReport(logger, results)


if __name__ == "__main__":
    execute()
