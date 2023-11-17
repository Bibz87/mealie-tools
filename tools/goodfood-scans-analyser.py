from itertools import zip_longest
import json
import os

from ArgsUtils import ArgsUtils
from LogUtils import LogUtils
from MealieApi import MealieApi


def parseArgs():
    parser = ArgsUtils.initialiseParser(scriptUsesMealieApi=True)

    parser.add_argument(
        "-i",
        "--inputPath",
        help="Path where scans to be processed are located",
        required=True)

    parser.add_argument(
        "-o",
        "--outputPath",
        help="Path where OCR data files will be saved to",
        required=True)

    return parser.parse_args()


def analyseScans(logger, mealieApi, inputPath, outputPath, isDryRun):
    logger.info(f"Analysing scans in '{inputPath}'")

    if not os.path.exists(outputPath):
        os.makedirs(outputPath)

    scans = os.listdir(inputPath)

    # Exclude already analyzed scans
    if "_DONE" in scans:
        scans.remove("_DONE")

    scanCount = len(scans)

    logger.debug(f"Found {scanCount} scans: {scans}")

    results = {
        "scans": scans
    }

    pairs = grouper(scans, 2) # Group front and back scans together
    skips = []
    processedScanCount = 1

    for pair in pairs:
        logger.info(
            f"Processing scans {processedScanCount} & {processedScanCount + 1} of {scanCount}"
        )

        inputFile = pair[0]
        outputFilename = os.path.basename(os.path.splitext(inputFile)[0])
        outputFilePath = f"{outputPath}/{outputFilename}.json"

        logger.debug(f"Input file: {inputFile}")
        logger.debug(f"Output file path: {outputFilePath}")

        if os.path.exists(outputFilePath):
            logger.warning(
                f"[DUPLICATE] OCR data for '{inputFile}' already exists. Skipping."
            )
            skips.append(inputFile)
            skips.append(pair[1])
            processedScanCount += 2
            continue

        ocrData = mealieApi.runOcrOnFile(f"{inputPath}/{inputFile}")

        if isDryRun:
            logger.warning(
                f"[DRY RUN] Would've created OCR data file '{outputFilePath}'"
            )
            continue

        with open(outputFilePath, mode="w", encoding="utf-8") as jsonFile:
            jsonFile.write(json.dumps(ocrData, indent=2))

        processedScanCount += 2

    results["skips"] = skips

    return results


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def logExecutionReport(logger, results):
    logger.info("----- Execution report -----")
    logger.info(f"  Scan count: {len(results['scans'])}")
    logger.info(f"  Skipped scans count: {len(results['skips'])}")

    if results["skips"]:
        logger.info(f"  Skipped scans: {results['skips']}")

    logger.info("----------------------------")


def execute():
    args = parseArgs()
    logger = LogUtils.initialiseLogger(args.verbosity, filename="goodfood-scans-analyser.log")

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; file system will not be modified")

    logger.debug(f"URL: {args.url}")
    logger.debug(f"Input path: {args.inputPath}")
    logger.debug(f"Output path: {args.outputPath}")

    mealieApi = MealieApi(args.url, args.token, args.caPath)

    results = analyseScans(
        logger,
        mealieApi,
        args.inputPath,
        args.outputPath,
        args.dryRun
    )

    logExecutionReport(logger, results)


if __name__ == "__main__":
    execute()
