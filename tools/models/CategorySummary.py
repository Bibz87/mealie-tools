from pydantic import UUID4

class CategorySummary:
    id: UUID4
    slug: str
    name: str

    def __init__(self, id: UUID4, slug: str, name: str):
        self.id = id
        self.slug = slug
        self.name = name

    def __str__(self):
        return self.slug

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, CategorySummary):
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
      return CategorySummary(
         id = json_dct["id"],
         slug = json_dct["slug"],
         name = json_dct["name"]
         )

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
        }
