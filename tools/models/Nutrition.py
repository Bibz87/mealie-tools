class Nutrition:
    calories: str
    fatContent: str
    proteinContent: str
    carbohydrateContent: str
    fiberContent: str
    sodiumContent: str
    sugarContent: str

    def __init__(self,
                 calories: str,
                 fatContent: str,
                 proteinContent: str,
                 carbohydrateContent: str,
                 fiberContent: str,
                 sodiumContent: str,
                 sugarContent: str):
        self.id = id
        self.calories = calories
        self.fatContent = fatContent
        self.proteinContent = proteinContent
        self.carbohydrateContent = carbohydrateContent
        self.fiberContent = fiberContent
        self.sodiumContent = sodiumContent
        self.sugarContent = sugarContent

    @staticmethod
    def from_json(json_dct):
      return Nutrition(
         calories = json_dct["calories"],
         fatContent = json_dct["fatContent"],
         proteinContent = json_dct["proteinContent"],
         carbohydrateContent = json_dct["carbohydrateContent"],
         fiberContent = json_dct["fiberContent"],
         sodiumContent = json_dct["sodiumContent"],
         sugarContent = json_dct["sugarContent"],
         )
