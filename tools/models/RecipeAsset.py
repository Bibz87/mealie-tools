class RecipeAsset:
    name: str
    icon: str
    fileName: str

    def __init__(self,
                 name: str,
                 icon: str,
                 fileName: str):
        self.name = name
        self.icon = icon
        self.fileName = fileName

    @staticmethod
    def from_json(json_dct):
      return RecipeAsset(
         name = json_dct["name"],
         icon = json_dct["icon"],
         fileName = json_dct["fileName"]
         )
