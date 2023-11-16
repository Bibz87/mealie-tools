import json
import pytesseract
from io import BytesIO
from PIL import Image

# Class reverse-engineered and adapted from Mealie's OCR code
class MealieOcr:

    class OcrChunk:
        # Type of detected structure
        # 1 = a page
        # 2 = a block
        # 3 = a paragraph
        # 4 = a line
        # 5 = a word
        level: int = 0
        page_num: int = 0   # Page on which the word was found
        block_num: int = 0  # Detected block within page
        par_num: int = 0    # Paragraph number within block
        line_num: int = 0   # Line number within paragraph
        word_num: int = 0   # Word number within line
        left: int = 0       # Word's X position from the left of the image, in pixels
        top: int = 0        # Word's Y position from the left of the image, in pixels
        width: int = 0      # Width of the word in the image, in pixels
        height: int = 0     # Height of the word in the image, in pixels
        conf: float = 0.0   # Confidence level Tesseract got the word right
        text: str = ""      # Word detected by Tesseract. Will be empty if line is structure

        def __str__(self) -> str:
            return self.text

        def __repr__(self) -> str:
            return self.__str__()

        class Encoder(json.JSONEncoder):
            def default(self, obj):
                return {
                        "level": obj.level,
                        "pageNum": obj.page_num,
                        "blockNum": obj.block_num,
                        "parNum": obj.par_num,
                        "lineNum": obj.line_num,
                        "wordNum": obj.word_num,
                        "left": obj.left,
                        "top": obj.top,
                        "width": obj.width,
                        "height": obj.height,
                        "conf": obj.conf,
                        "text": obj.text,
                    }

            def decode(dct):
                ocrChunk = MealieOcr.OcrChunk()

                ocrChunk.level = dct["level"]
                ocrChunk.page_num = dct["pageNum"]
                ocrChunk.block_num = dct["blockNum"]
                ocrChunk.par_num = dct["parNum"]
                ocrChunk.line_num = dct["lineNum"]
                ocrChunk.word_num = dct["wordNum"]
                ocrChunk.left = dct["left"]
                ocrChunk.top = dct["top"]
                ocrChunk.width = dct["width"]
                ocrChunk.height = dct["height"]
                ocrChunk.conf = dct["conf"]
                ocrChunk.text = dct["text"]

                return ocrChunk

    def image_to_tsv(self, image_data, lang=None):
        if lang is not None:
            return pytesseract.image_to_data(Image.open(BytesIO(image_data)), lang=lang)

        return pytesseract.image_to_data(Image.open(BytesIO(image_data)))

    def format_tsv_output(self, tsv: str) -> list[OcrChunk]:
        lines = tsv.split("\n")
        titles = [t.strip() for t in lines[0].split("\t")]
        response: list[MealieOcr.OcrChunk] = []

        for i in range(1, len(lines)):
            if lines[i] == "":
                continue

            line = MealieOcr.OcrChunk()
            for key, value in zip(titles, lines[i].split("\t"), strict=False):
                if isinstance(getattr(line, key), str):
                    setattr(line, key, value.strip())
                elif isinstance(getattr(line, key), float):
                    setattr(line, key, float(value.strip()))
                elif isinstance(getattr(line, key), int):
                    setattr(line, key, int(value.strip()))
                else:
                    continue

            if isinstance(line, MealieOcr.OcrChunk):
                response.append(line)

        return response

    def runOcrOnFile(self, file: bytes, lang=None) -> list[OcrChunk]:
        tsv = self.image_to_tsv(file, lang)
        return self.format_tsv_output(tsv)

    def extractBlocks(self, ocrData: list[OcrChunk]) -> list[list[OcrChunk]]:
        # Only keep block definitions (level 2) and their words (level 5)
        filtered = [a for a in ocrData if a.level == 2 or a.level == 5]
        blocks = [[MealieOcr.OcrChunk]]
        blockNum = 1

        for i, element in enumerate(filtered):
            if i != 0 and filtered[i - 1].block_num != element.block_num:
                blocks.append([])
                blockNum = element.block_num

            blocks[blockNum - 1].append(element)

        return blocks
