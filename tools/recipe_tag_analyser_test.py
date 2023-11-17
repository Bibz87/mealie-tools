import unittest

from models.Recipe import Recipe, RecipeTag
from recipe_tag_analyser import TagValidationResultCode, checkField, checkMutuallyExclusiveTags


class TestMutuallyExclusiveTags(unittest.TestCase):
    def test_whenBothTagsThenConflict(self):
        # Arrange
        expectedResult = TagValidationResultCode.Conflict
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        realTags = [
            RecipeTag("bar", "real-tag", "Real Tag")
        ]
        recipe = Recipe()
        recipe.tags = [validatedTag, *realTags]

        # Act
        result = checkMutuallyExclusiveTags(recipe, validatedTag, realTags)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")

    def test_whenValidatedTagOnlyThenOK(self):
        # Arrange
        expectedResult = TagValidationResultCode.OK
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        realTags = [
            RecipeTag("bar", "real-tag", "Real Tag")
        ]
        recipe = Recipe()
        recipe.tags = [validatedTag]

        # Act
        result = checkMutuallyExclusiveTags(recipe, validatedTag, realTags)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")

    def test_whenAnyRealTagOnlyThenOK(self):
        # Arrange
        expectedResult = TagValidationResultCode.OK
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        realTags = [
            RecipeTag("bar", "real-tag", "Real Tag"),
            RecipeTag("ca", "canada", "Canada"),
            RecipeTag("us", "usa", "USA"),
        ]
        recipe = Recipe()
        recipe.tags = [*realTags]

        # Act
        result = checkMutuallyExclusiveTags(recipe, validatedTag, realTags)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")

    def test_whenNoTagsAndOptionalThenUnknown(self):
        # Arrange
        expectedResult = TagValidationResultCode.Unknown
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        realTags = [
            RecipeTag("bar", "real-tag", "Real Tag")
        ]
        recipe = Recipe()
        recipe.tags = []

        # Act
        result = checkMutuallyExclusiveTags(recipe, validatedTag, realTags)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")

    def test_whenNoTagsAndMandatoryThenMissing(self):
        # Arrange
        expectedResult = TagValidationResultCode.Missing
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        realTags = [
            RecipeTag("bar", "real-tag", "Real Tag")
        ]
        recipe = Recipe()
        recipe.tags = []

        # Act
        result = checkMutuallyExclusiveTags(recipe, validatedTag, realTags, isMandatory=True)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")


class TestField(unittest.TestCase):
    def test_whenTagAndFieldThenConflict(self):
        # Arrange
        expectedResult = TagValidationResultCode.Conflict
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        fieldName = "recipeYield"
        recipe = Recipe()
        recipe.tags = [validatedTag]
        recipe.__setattr__(fieldName, "foo servings")

        # Act
        result = checkField(recipe, validatedTag, fieldName)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")

    def test_whenTagOnlyThenOK(self):
        # Arrange
        expectedResult = TagValidationResultCode.OK
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        fieldName = "recipeYield"
        recipe = Recipe()
        recipe.tags = [validatedTag]

        # Act
        result = checkField(recipe, validatedTag, fieldName)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")

    def test_whenFieldOnlyThenOK(self):
        # Arrange
        expectedResult = TagValidationResultCode.OK
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        fieldName = "recipeYield"
        recipe = Recipe()
        recipe.tags = []
        recipe.__setattr__(fieldName, "foo servings")

        # Act
        result = checkField(recipe, validatedTag, fieldName)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")

    def test_whenNeitherThenMissing(self):
        # Arrange
        expectedResult = TagValidationResultCode.Missing
        validatedTag = RecipeTag("foo", "validated-tag", "Validated Tag")
        fieldName = "recipeYield"
        recipe = Recipe()
        recipe.tags = []

        # Act
        result = checkField(recipe, validatedTag, fieldName)

        # Assert
        self.assertEqual(result.code, expectedResult, f"Expected code to be: {expectedResult}")
