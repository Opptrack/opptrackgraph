from typing import Dict, Any
import re
from io import BytesIO
from datetime import datetime

import pypdf
from pdf2image import convert_from_bytes
import pytesseract

from app.core.exceptions import PDFException
from app.core.logger import logger


class PDFProcessor:
    @staticmethod
    def extract_info(pdf_file: bytes, document_type: str) -> Dict[str, Any]:
        if not pdf_file:
            raise ValueError("PDF file is empty or invalid")

        try:
            reader = pypdf.PdfReader(stream=BytesIO(pdf_file))
            if len(reader.pages) == 0:
                raise ValueError("PDF file has no pages")

            full_text = ""
            needs_ocr = False

            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if not page_text or not page_text.strip():
                        logger.info("Page %s needs OCR", page_num + 1)
                        needs_ocr = True
                        break
                    full_text += page_text + "\n"
                except Exception as e:
                    logger.error(
                        "Text extraction failed on page %s: %s",
                        page_num + 1,
                        str(e),
                    )
                    raise PDFException(f"Failed to extract text: {e}")

            if needs_ocr:
                logger.info("Falling back to OCR for entire PDF...")
                full_text = PDFProcessor._ocr_pdf(pdf_file)

            if not full_text.strip():
                raise ValueError("No text could be extracted from the PDF")

            # Basic text stats without NLTK
            sentences = [s for s in re.split(r"(?<=[.!?])\s+", full_text.strip()) if s]
            tokens = re.findall(r"\b\w+\b", full_text)

            return {
                "text_content": full_text,
                "num_pages": len(reader.pages),
                "metadata": reader.metadata or {},
                "document_type": document_type,
                "processed_date": datetime.now().isoformat(),
                "analysis": {
                    "num_sentences": len(sentences),
                    "num_words": len(tokens),
                    "entities": PDFProcessor._empty_entities(),
                },
            }
        except Exception as e:
            logger.error(f"PDF Processing error: {e}", exc_info=True)
            raise

    @staticmethod
    def _ocr_pdf(pdf_file: bytes) -> str:
        images = convert_from_bytes(pdf_file, dpi=300)
        text = ""
        for i, img in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(img)
                text += page_text + "\n"
            except Exception as e:
                logger.error("OCR failed on page %s: %s", i + 1, str(e))
        return text

    @staticmethod
    def _empty_entities() -> Dict[str, list]:
        return {
            "PERSON": [],
            "ORGANIZATION": [],
            "GPE": [],
            "DATE": [],
            "MONEY": [],
        }

    # @staticmethod
    # def extract_info(pdf_file: bytes, document_type: str) -> Dict[str, Any]:
    #     """
    #     Extract and analyze information from a PDF file using NLTK
    #     """
    #     if not pdf_file:
    #         raise ValueError("PDF file is empty or invalid")

    #     try:
    #         reader = pypdf.PdfReader(stream=BytesIO(pdf_file))
    #         if len(reader.pages) == 0:
    #             raise ValueError("PDF file has no pages")

    #         # Extract text from all pages
    #         full_text = ""
    #         for page_num, page in enumerate(reader.pages):
    #             try:
    #                 page_text = page.extract_text()
    #                 if not page_text:
    #                     logger.warning(
    #                         "Page %s has no extractable text", page_num + 1
    #                     )
    #                 full_text += page_text + "\n"
    #             except Exception as e:
    #                 logger.error(
    #                     "Error extracting text from page %s: %s",
    #                     page_num + 1,
    #                     str(e),
    #                 )
    #                 raise PDFException(
    #                     "Failed to extract text from page %s: %s"
    #                     % (page_num + 1, str(e))
    #                 )

    #         if not full_text.strip():
    #             raise ValueError("No text could be extracted from the PDF")

    #         # Process text with NLTK
    #         try:
    #             sentences = sent_tokenize(full_text)
    #             tokens = word_tokenize(full_text)
    #             tagged = pos_tag(tokens)
    #             entities = ne_chunk(tagged)
    #         except Exception as e:
    #             logger.error(f"Error during NLTK processing: {str(e)}")
    #             raise PDFException(f"Text processing failed: {str(e)}")

    #         # Extract key information based on document type
    #         extracted_info = {
    #             "text_content": full_text,
    #             "num_pages": len(reader.pages),
    #             "metadata": reader.metadata or {},
    #             "document_type": document_type,
    #             "processed_date": datetime.now().isoformat(),
    #             "analysis": {
    #                 "num_sentences": len(sentences),
    #                 "num_words": len(tokens),
    #                 "entities": PDFProcessor._extract_entities(entities),
    #             },
    #         }

    #         return extracted_info
    #     except Exception as e:
    #         logger.error(f"PDF Processing error: {str(e)}", exc_info=True)
    #         raise

    # Note: entity extraction removed with NLTK; returning empty categories
