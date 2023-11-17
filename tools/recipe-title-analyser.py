import argparse
import csv
from datetime import timedelta
import json
import logging
import sys

from thefuzz import fuzz
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

    return parser.parse_args()


def initLogger(verbosity):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, verbosity))

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(ColoredLogFormatter())
    logger.addHandler(consoleHandler)

    fileHandler = logging.FileHandler('recipe-title-analyser.log', encoding="utf-8")
    fileLogFormat = logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s')
    fileHandler.setFormatter(fileLogFormat)
    logger.addHandler(fileHandler)

    logger.info("Logger initialised")

    return logger


def execute():
    args = parseArgs()
    logger = initLogger(args.verbosity)

    logger.debug(f"URL: {args.url}")
    logger.info("Analysing recipe titles")

    mealieApi = MealieApi(args.url, args.token, args.caPath, cacheDuration=timedelta(hours=12))

    recipes = mealieApi.getAllRecipes()
    recipes.sort(key=lambda r: r.slug)

    ratios = []
    potentialDuplicates = []
    duplicateThreshold = 75 # Change this to tweak duplicate title detection sensitivity

    for recipe in recipes:
        logger.info(f"Processing recipe {recipe.slug}")

        slugKey = "_slug"
        results = {
            slugKey: recipe.slug
        }

        for other in recipes:
            if recipe.id == other.id:
                results[other.slug] = None
                continue

            # Check if recipe has already been compared to other
            if True in (e[slugKey] == other.slug and recipe.slug in e.keys() for e in ratios):
                results[other.slug] = None
                continue

            ratio = fuzz.ratio(recipe.slug, other.slug)
            results[other.slug] = ratio

            if ratio >= duplicateThreshold:
                potentialDuplicates.append((recipe.slug, other.slug))

        logger.debug("Sorting results")
        keys = list(results.keys())
        keys.sort()
        sortedResults = {i: results[i] for i in keys}
        ratios.append(sortedResults)

    logger.info("Writing output files")

    report = {
        "potentialDuplicates": potentialDuplicates
    }

    with open("title-report.json", mode="w", encoding="utf-8") as jsonFile:
        jsonFile.write(json.dumps(report, indent=2))

    with open("title-ratios.tsv", mode="w", encoding="utf-8", newline="") as tsvFile:
        dw = csv.DictWriter(tsvFile, sorted(ratios[0].keys()), delimiter='\t')
        dw.writeheader()
        dw.writerows(ratios)

    logger.info("Processing completed!")


if __name__ == "__main__":
    execute()
