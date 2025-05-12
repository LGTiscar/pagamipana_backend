class OcrRequest:
    def __init__(self, image: str) -> None:
        self.image = image

    def get_image(self) -> str:
        return self.image
