from typing import Dict, Any
import pypdf
from io import BytesIO
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from datetime import datetime
from app.core.exceptions import PDFException
from app.core.logger import logger
import os
from app.config.config import app_settings

from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image


if app_settings.NLTK_DATA_PATH:
    os.environ["NLTK_DATA"] = app_settings.NLTK_DATA_PATH


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
                        logger.info(f"Page {page_num + 1} needs OCR")
                        needs_ocr = True
                        break
                    full_text += page_text + "\n"
                except Exception as e:
                    logger.error(f"Text extraction failed on page {page_num + 1}: {e}")
                    raise PDFException(f"Failed to extract text: {e}")

            if needs_ocr:
                logger.info("Falling back to OCR for entire PDF...")
                full_text = PDFProcessor._ocr_pdf(pdf_file)

            if not full_text.strip():
                raise ValueError("No text could be extracted from the PDF")

            try:
                sentences = sent_tokenize(full_text)
                tokens = word_tokenize(full_text)
                tagged = pos_tag(tokens)
                entities = ne_chunk(tagged)
            except Exception as e:
                logger.error(f"NLTK processing failed: {e}")
                raise PDFException(f"Text processing failed: {e}")

            return {
                "text_content": full_text,
                "num_pages": len(reader.pages),
                "metadata": reader.metadata or {},
                "document_type": document_type,
                "processed_date": datetime.now().isoformat(),
                "analysis": {
                    "num_sentences": len(sentences),
                    "num_words": len(tokens),
                    "entities": PDFProcessor._extract_entities(entities),
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
                logger.error(f"OCR failed on page {i + 1}: {e}")
        return text

    @staticmethod
    def _extract_entities(chunked) -> Dict[str, list]:
        entities = {
            "PERSON": [],
            "ORGANIZATION": [],
            "GPE": [],
            "DATE": [],
            "MONEY": [],
        }

        for chunk in chunked:
            if hasattr(chunk, "label"):
                entity_type = chunk.label()
                if entity_type in entities:
                    entity_text = " ".join(token for token, _ in chunk.leaves())
                    if entity_text not in entities[entity_type]:
                        entities[entity_type].append(entity_text)
        return entities

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
    #                     logger.warning(f"Page {page_num + 1} has no extractable text")
    #                 full_text += page_text + "\n"
    #             except Exception as e:
    #                 logger.error(
    #                     f"Error extracting text from page {page_num + 1}: {str(e)}"
    #                 )
    #                 raise PDFException(
    #                     f"Failed to extract text from page {page_num + 1}: {str(e)}"
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

    @staticmethod
    def _extract_entities(chunked) -> Dict[str, list]:
        """Extract named entities from chunked text"""
        entities = {
            "PERSON": [],
            "ORGANIZATION": [],
            "GPE": [],  # Geo-Political Entities
            "DATE": [],
            "MONEY": [],
        }

        for chunk in chunked:
            if hasattr(chunk, "label"):
                entity_type = chunk.label()
                if entity_type in entities:
                    entity_text = " ".join([token for token, pos in chunk.leaves()])
                    if entity_text not in entities[entity_type]:
                        entities[entity_type].append(entity_text)

        return entities
