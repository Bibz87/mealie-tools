class RecipeNote:
    title: str
    text: str

    def __init__(self, title: str, text: str):
        self.title = title
        self.text = text

    @staticmethod
    def from_json(json_dct):
      return RecipeNote(
         title = json_dct["title"],
         text = json_dct["text"]
         )
