from ArgsUtils import ArgsUtils
from LogUtils import LogUtils
from datetime import timedelta
from MealieApi import MealieApi
from slugify import slugify


tagNames = [
    "Duplicate ⚠️",
    "Missing BBQ Tag ⚠️",
    "Missing Cook Time ⚠️",
    "Missing Country Tag ⚠️",
    "Missing Description ⚠️",
    "Missing Freezable Tag ⚠️",
    "Missing Image ⚠️",
    "Missing Ingredients ⚠️",
    "Missing Instruction Images ⚠️",
    "Missing Instructions ⚠️",
    "Missing Meal Type Category ⚠️",
    "Missing Meat Cut Ingredient ⚠️",
    "Missing Nutrition Facts ⚠️",
    "Missing Parsed Ingredients ⚠️",
    "Missing Prep Time ⚠️",
    "Missing Protein Tags ⚠️",
    "Missing Rating ⚠️",
    "Missing Salad Tag ⚠️",
    "Missing Sauce Tag ⚠️",
    "Missing Serving Size ⚠️",
    "Missing Spice Ratios ⚠️",
    "Missing Tools ⚠️",
    "Missing Total Time ⚠️",
]


def parseArgs():
    parser = ArgsUtils.initialiseParser(scriptUsesMealieApi=True)
    return parser.parse_args()


def execute():
    args = parseArgs()
    logger = LogUtils.initialiseLogger(args.verbosity, filename="flag-tags-seeder.log")

    if args.dryRun:
        logger.warning("[DRY RUN] Running script in dry run mode; Mealie will not be modified")

    logger.debug(f"URL: {args.url}")
    logger.info("Seeding flag tags")

    mealieApi = MealieApi(args.url, args.token, args.caPath, cacheDuration=timedelta(hours=12))

    allTags = mealieApi.getAllTags()

    for name in tagNames:
        slug = slugify(name)
        tag = next(filter(lambda t: t.slug == slug, allTags), None)

        if tag:
            logger.warning(f"Mealie already has tag '{slug}'")

            if tag.name != name:
                logger.warning(f"Tag name difference detected. Updating tag with new name '{name}'")

                if args.dryRun:
                    logger.warning(f"[DRY RUN] Would've updated tag {slug}")
                    continue

                mealieApi.updateTag(tag.id, name)
        else:
            logger.info(f"Creating tag '{name}'")

            if args.dryRun:
                logger.warning(f"[DRY RUN] Would've created tag {name}")
                continue

            mealieApi.createTag(name)

    logger.info("Processing completed!")


if __name__ == "__main__":
    execute()
