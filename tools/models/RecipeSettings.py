class RecipeSettings:
    public: bool = False
    showNutrition: bool = False
    showAssets: bool = False
    landscapeView: bool = False
    disableComments: bool = True
    disableAmount: bool = True
    locked: bool = False

    def __init__(self,
                 public: bool = False,
                 showNutrition: bool = False,
                 showAssets: bool = False,
                 landscapeView: bool = False,
                 disableComments: bool = True,
                 disableAmount: bool = True,
                 locked: bool = False):
        self.public = public
        self.showNutrition = showNutrition
        self.showAssets = showAssets
        self.landscapeView = landscapeView
        self.disableComments = disableComments
        self.disableAmount = disableAmount
        self.locked = locked

    def __eq__(self, other):
        if isinstance(other, RecipeSettings):
            properties = vars(self)

            for p in properties:
                mine = getattr(self, p)
                theirs = getattr(other, p)

                if mine != theirs:
                    return False

            return True
        return NotImplemented

    @staticmethod
    def from_json(json_dct):
        return RecipeSettings(
          public = json_dct.get("public"),
          showNutrition = json_dct.get("showNutrition"),
          showAssets = json_dct.get("showAssets"),
          landscapeView = json_dct.get("landscapeView"),
          disableComments = json_dct.get("disableComments"),
          disableAmount = json_dct.get("disableAmount"),
          locked = json_dct.get("locked")
          )

    def to_json(self) -> dict:
        return {
            "public": self.public,
            "showNutrition": self.showNutrition,
            "showAssets": self.showAssets,
            "landscapeView": self.landscapeView,
            "disableComments": self.disableComments,
            "disableAmount": self.disableAmount,
            "locked": self.locked,
        }

    def diff(self, other: "RecipeSettings") -> str:
        output = ""

        properties = vars(self)

        for p in properties:
            mine = getattr(self, p)
            theirs = getattr(other, p)

            if mine != theirs:
                output += f"{p}: {mine} -> {theirs}\n"

        return output

