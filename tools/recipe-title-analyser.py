import csv
from datetime import timedelta
import json

from ArgsUtils import ArgsUtils
from LogUtils import LogUtils
from MealieApi import MealieApi
from thefuzz import fuzz


def parseArgs():
    parser = ArgsUtils.initialiseParser(scriptUsesMealieApi=True)
    return parser.parse_args()


def execute():
    args = parseArgs()
    logger = LogUtils.initialiseLogger(args.verbosity, filename="recipe-title-analyser.log")

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; file system will not be modified")

    logger.debug(f"URL: {args.url}")
    logger.info("Analysing recipe titles")

    mealieApi = MealieApi(args.url, args.token, args.caPath, args.cacheDuration)

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

    if args.dryRun:
        logger.warning("[DRY RUN] Would've written report and ratios files")
    else:
        with open("title-report.json", mode="w", encoding="utf-8") as jsonFile:
            jsonFile.write(json.dumps(report, indent=2))

        with open("title-ratios.tsv", mode="w", encoding="utf-8", newline="") as tsvFile:
            dw = csv.DictWriter(tsvFile, sorted(ratios[0].keys()), delimiter='\t')
            dw.writeheader()
            dw.writerows(ratios)

    logger.info("Processing completed!")


if __name__ == "__main__":
    execute()
