

class OcrRequestDTO:

    image: str

    def from_rest_input(self, rest_input: dict) -> "OcrRequestDTO":
        self.image = rest_input.get("image")
        return self