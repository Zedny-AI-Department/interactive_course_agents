import fitz
from typing import List

from src.models import ExtractedImage


class FileProcessingService:
    """A service that handles pdf processing tools."""

    def __init__(self):
        pass

    def extract_images_from_pdf(self, pdf_bytes: bytes) -> List[ExtractedImage]:
        """
        Extract images from a PDF given as bytes.
        Returns a list of ExtractedImage with image data and metadata.
        """
        images_list = []

        # Open PDF in memory
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        image_index = 1
        for page_number in range(len(pdf_doc)):
            page = pdf_doc[page_number]
            images = page.get_images(full=True)

            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                images_list.append(
                    ExtractedImage(
                        image_index=image_index,
                        image_bytes=image_bytes,
                        file_extension=image_ext,
                    )
                )
                image_index += 1
        pdf_doc.close()
        return images_list
