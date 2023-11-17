import json
import os

from ArgsUtils import ArgsUtils
from LogUtils import LogUtils
from MealieOcr import MealieOcr


def parseArgs():
    parser = ArgsUtils.initialiseParser()

    parser.add_argument(
        "-i",
        "--inputPath",
        help="Path where recipes to be processed are located")

    return parser.parse_args()


def analyseImage(logger, mealieOcr: MealieOcr, imagePath, outputFilePath, isDryRun) -> list[MealieOcr.OcrChunk]:
    logger.debug(f"Analysing image: {imagePath}")
    logger.debug(f"Output file path: {outputFilePath}")

    ocrData: list[MealieOcr.OcrChunk] = None

    if os.path.exists(outputFilePath) and os.stat(outputFilePath).st_size > 0:
        logger.warning(f"OCR data for '{imagePath}' already exists. Reading data from file.")
        with open(outputFilePath, encoding="utf-8") as ocrDataFile:
            ocrData = json.load(ocrDataFile, object_hook=MealieOcr.OcrChunk.Encoder.decode)
    else:
        logger.info(f"OCR data for '{imagePath}' doesn't exist. Analysing image.")

        with open(imagePath, "rb") as image:
            ocrData = mealieOcr.runOcrOnFile(image.read())

        if isDryRun:
            logger.warning(
                f"[DRY RUN] Would've created OCR data file '{outputFilePath}'"
            )
            return ocrData

        with open(outputFilePath, mode="w", encoding="utf-8") as jsonFile:
            jsonFile.write(json.dumps(ocrData, cls=MealieOcr.OcrChunk.Encoder, indent=2))

    return ocrData


def extractOcrBlocks(logger, mealieOcr:MealieOcr, ocrData: list[MealieOcr.OcrChunk], ocrBlocksFilePath: str, isDryRun: bool):
    logger.info("Extracting OCR blocks")

    blocks = mealieOcr.extractBlocks(ocrData)

    if isDryRun:
        logger.warning(
            f"[DRY RUN] Would've created OCR blocks file '{ocrBlocksFilePath}'"
        )
        return

    with open(ocrBlocksFilePath, mode="w", encoding="utf-8") as jsonFile:
        jsonFile.write(json.dumps(blocks, cls=MealieOcr.OcrChunk.Encoder, indent=2))


def analyseRecipes(logger, mealieOcr: MealieOcr, inputPath, isDryRun):
    logger.info(f"Analysing recipes in '{inputPath}'")

    recipeSlugs = os.listdir(inputPath)
    recipeCount = len(recipeSlugs)

    logger.debug(f"Found {recipeCount} recipes: {recipeSlugs}")

    toAnalyse = ["front", "back"]
    processedRecipeCount = 1

    for recipeSlug in recipeSlugs:
        logger.info(
            f"Processing recipe {processedRecipeCount} of {recipeCount}"
        )

        for item in toAnalyse:
            imagePath = f"{inputPath}/{recipeSlug}/{item.capitalize()}.png"
            ocrDataFilePath = f"{inputPath}/{recipeSlug}/ocr-{item}.json"
            ocrBlocksFilePath = f"{inputPath}/{recipeSlug}/ocr-blocks-{item}.json"

            ocrData = analyseImage(logger, mealieOcr, imagePath, ocrDataFilePath, isDryRun)

            if not ocrData:
                logger.error(
                    "Something went wrong when analysing image. Skipping block extraction."
                    )
                continue

            extractOcrBlocks(logger, mealieOcr, ocrData, ocrBlocksFilePath, isDryRun)

        processedRecipeCount += 1


def execute():
    args = parseArgs()
    logger = LogUtils.initialiseLogger(args.verbosity, filename="goodfood-recipes-analyser.log")

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; file system will not be modified")

    logger.debug(f"Input path: {args.inputPath}")

    mealieOcr = MealieOcr()

    analyseRecipes(
        logger,
        mealieOcr,
        args.inputPath,
        args.dryRun
    )

    logger.info("Done!")


if __name__ == "__main__":
    execute()
