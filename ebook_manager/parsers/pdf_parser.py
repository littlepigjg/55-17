from .base import BaseParser
from ..models import BookMeta


class PdfParser(BaseParser):
    SUPPORTED_EXTENSIONS = (".pdf",)

    def _parse(self, file_path: str) -> BookMeta:
        meta = BookMeta()
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            info = reader.metadata
            if info:
                meta.title = self._clean_pdf_field(info.title)
                meta.author = self._clean_pdf_field(info.author)
                meta.publisher = self._clean_pdf_field(
                    info.get("/Publisher", info.get("/Producer", ""))
                )
                meta.publish_date = self._clean_pdf_field(info.get("/CreationDate", ""))
                meta.language = self._clean_pdf_field(info.get("/Language", ""))
                meta.description = self._clean_pdf_field(
                    info.get("/Subject", info.get("/Keywords", ""))
                )
                isbn_val = self._clean_pdf_field(info.get("/ISBN", ""))
                if isbn_val:
                    meta.isbn = isbn_val
        except ImportError:
            pass
        except Exception:
            pass
        return meta

    @staticmethod
    def _clean_pdf_field(value) -> str:
        if not value:
            return ""
        s = str(value)
        if s.startswith("/"):
            s = s[1:]
        for prefix in ["D:", "d:"]:
            if s.startswith(prefix):
                s = s[len(prefix):]
                break
        try:
            s = s.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
        return s.strip()
