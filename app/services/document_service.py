import subprocess
import os
import tempfile
from pathlib import Path
from typing import List, Union, Tuple
from pypdf import PdfReader, PdfWriter
import re
from io import BytesIO
from PIL import Image
from docx2pdf import convert
import shutil

from app.core.exceptions import (
    LatexValidationError,
    LatexStructureError,
    LatexSyntaxError,
    LatexCompilationError,
    LatexReferenceError,
    LatexConversionError,
)


class DocumentService:
    @staticmethod
    def _find_pdflatex() -> str:
        """
        Find the pdflatex executable path.

        Returns:
            str: Full path to pdflatex executable

        Raises:
            LatexConversionError: If pdflatex is not found
        """
        # Common paths where pdflatex might be installed
        common_paths = [
            "/opt/homebrew/bin/pdflatex",  # Homebrew on Apple Silicon
            "/usr/local/bin/pdflatex",  # Homebrew on Intel Mac
            "/usr/bin/pdflatex",  # System installation
            "/Library/TeX/texbin/pdflatex",  # MacTeX
        ]

        # First try to find it using shutil.which (respects PATH)
        pdflatex_path = shutil.which("pdflatex")
        if pdflatex_path:
            return pdflatex_path

        # If not found in PATH, try common installation paths
        for path in common_paths:
            if Path(path).exists():
                return path

        # If still not found, raise an error with helpful message
        raise LatexConversionError(
            "pdflatex not found. Please install LaTeX (e.g., 'brew install --cask mactex' or 'brew install --cask basictex')"
        )

    @staticmethod
    def latex_to_pdf(name: str, latex_content: str) -> bytes:
        """
        Converts LaTeX content to a PDF file.

        Args:
            name: The name of the document (without extension)
            latex_content: String containing the LaTeX document

        Returns:
            bytes: The generated PDF file content

        Raises:
            LatexConversionError: If PDF generation fails
        """
        # Create a temporary directory to work in
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create paths
            tex_path = Path(temp_dir) / f"{name}.tex"
            pdf_path = Path(temp_dir) / f"{name}.pdf"

            # Write LaTeX content to file
            tex_path.write_text(latex_content)

            try:
                # First verify the LaTeX is valid
                DocumentService.validate_latex(latex_content)

                # Get the full path to pdflatex
                pdflatex_cmd = DocumentService._find_pdflatex()

                # Run pdflatex twice to resolve references
                for _ in range(2):
                    subprocess.run(
                        [
                            pdflatex_cmd,
                            "-interaction=nonstopmode",
                            "-halt-on-error",
                            tex_path.name,
                        ],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                if pdf_path.exists():
                    return pdf_path.read_bytes()
                else:
                    raise LatexConversionError("PDF file was not generated")
            except LatexReferenceError as e:
                # Let LatexReferenceError propagate up
                raise
            except subprocess.CalledProcessError as e:
                raise LatexConversionError(
                    f"LaTeX to PDF conversion failed: {e.stdout}\n{e.stderr}"
                )
            except LatexValidationError as e:
                raise LatexConversionError(f"LaTeX validation failed: {str(e)}")

    @staticmethod
    def concatenate_pdfs(pdfs: List[Union[Path, str, bytes]]) -> bytes:
        """
        Concatenates multiple PDF files into a single PDF.

        Args:
            pdfs: List of PDFs as Path objects, strings, or bytes

        Returns:
            bytes: The concatenated PDF file content

        Raises:
            ValueError: If the list is empty or contains invalid types
        """
        if not pdfs:
            raise ValueError("No files provided.")

        writer = PdfWriter()

        for pdf in pdfs:
            if isinstance(pdf, (str, Path)):
                reader = PdfReader(str(pdf))
            elif isinstance(pdf, bytes):
                stream = BytesIO(pdf)
                stream.seek(0)
                reader = PdfReader(stream)
            else:
                raise ValueError("Invalid file type")

            for page in reader.pages:
                writer.add_page(page)

        output_buffer = BytesIO()
        writer.write(output_buffer)
        return output_buffer.getvalue()

    @staticmethod
    def validate_latex(latex_content: str) -> None:
        """
        Validates if a string contains properly formatted LaTeX.

        Args:
            latex_content: String to validate

        Raises:
            LatexStructureError: If LaTeX structure is invalid (missing documentclass, etc.)
            LatexSyntaxError: If LaTeX syntax is invalid (unmatched braces, etc.)
            LatexCompilationError: If LaTeX compilation fails
            LatexReferenceError: If LaTeX has unresolved references
        """
        # Basic structure checks
        if not latex_content.strip():
            raise LatexStructureError("Empty content")

        if r"\documentclass" not in latex_content:
            raise LatexStructureError("Missing \\documentclass declaration")

        if (
            r"\begin{document}" not in latex_content
            or r"\end{document}" not in latex_content
        ):
            raise LatexStructureError("Missing document environment")

        # Check for undefined references before other checks
        refs = re.findall(r"\\ref\{([^}]+)\}", latex_content)
        labels = re.findall(r"\\label\{([^}]+)\}", latex_content)

        if refs and not set(refs).issubset(set(labels)):
            undefined_refs = set(refs) - set(labels)
            raise LatexReferenceError(
                f"Undefined references: {', '.join(undefined_refs)}"
            )

        # Check for balanced braces
        brace_count = 0
        for char in latex_content:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            if brace_count < 0:
                raise LatexSyntaxError("Unmatched closing brace")
        if brace_count != 0:
            raise LatexSyntaxError("Unmatched opening brace")

        # Check for balanced environments
        environments = re.findall(r"\\begin\{([^}]+)\}", latex_content)
        endings = re.findall(r"\\end\{([^}]+)\}", latex_content)
        if set(environments) != set(endings):
            raise LatexSyntaxError("Unmatched environment begin/end pairs")

        # Dry run with pdflatex
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "validate.tex"
            tex_path.write_text(latex_content)

            try:
                # Get the full path to pdflatex
                pdflatex_cmd = DocumentService._find_pdflatex()

                result = subprocess.run(
                    [
                        pdflatex_cmd,
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        "-draftmode",
                        tex_path.name,
                    ],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    error_log = result.stdout + result.stderr
                    error_match = re.search(r"!(.*?)\n", error_log)
                    error_msg = (
                        error_match.group(1).strip()
                        if error_match
                        else "LaTeX compilation failed"
                    )
                    raise LatexCompilationError(f"LaTeX Error: {error_msg}")

                # Look for unresolved references in the .log file
                log_path = Path(temp_dir) / "validate.log"
                if log_path.exists():
                    log_content = log_path.read_text()
                    if (
                        "LaTeX Warning: Reference" in log_content
                        or "LaTeX Warning: Citation" in log_content
                    ):
                        raise LatexReferenceError(
                            "Unresolved references or citations detected"
                        )

            except subprocess.CalledProcessError as e:
                raise LatexCompilationError(f"Process error: {str(e)}")
            except Exception as e:
                if not isinstance(e, LatexValidationError):
                    raise LatexValidationError(f"Validation error: {str(e)}")

    @staticmethod
    def file_to_pdf(file_path: Union[str, Path]) -> bytes:
        """Converts various file types to PDF."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        # Check file type before attempting conversion
        if suffix not in [".docx", ".jpg", ".jpeg", ".png"]:
            raise ValueError(f"Unsupported file type: {suffix}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            output_path = temp_dir_path / "output.pdf"

            try:
                if suffix == ".docx":
                    return DocumentService._convert_docx(file_path, output_path)
                elif suffix in (".jpg", ".jpeg", ".png"):
                    return DocumentService._convert_image(file_path, output_path)
                else:
                    # This should never be reached due to the check above, but added for completeness
                    raise ValueError(f"Unsupported file type: {suffix}")
            except Exception as e:
                raise RuntimeError(f"Failed to convert {file_path}: {str(e)}")

    @staticmethod
    def _convert_docx(file_path: Path, output_path: Path) -> bytes:
        """Convert DOCX to PDF using docx2pdf."""
        try:
            convert(str(file_path), str(output_path))
            return output_path.read_bytes()
        except Exception as e:
            raise RuntimeError(f"DOCX conversion failed: {str(e)}")

    @staticmethod
    def _convert_image(file_path: Path, output_path: Path) -> bytes:
        """Convert image to PDF using Pillow."""
        try:
            image = Image.open(file_path)
            # Convert to RGB if necessary (required for some PNG files)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.save(output_path, "PDF")
            return output_path.read_bytes()
        except Exception as e:
            raise RuntimeError(f"Image conversion failed: {str(e)}")
