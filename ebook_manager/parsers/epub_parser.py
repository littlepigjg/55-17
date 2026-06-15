import zipfile
import xml.etree.ElementTree as ET
from typing import Optional

from .base import BaseParser
from ..models import BookMeta

EPUB_CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
EPUB_METADATA_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "opf": "http://www.idpf.org/2007/opf",
}


class EpubParser(BaseParser):
    SUPPORTED_EXTENSIONS = (".epub",)

    def _parse(self, file_path: str) -> BookMeta:
        meta = BookMeta()
        with zipfile.ZipFile(file_path, "r") as zf:
            opf_path = self._find_opf_path(zf)
            if not opf_path:
                return meta
            opf_content = zf.read(opf_path).decode("utf-8", errors="ignore")
            root = ET.fromstring(opf_content)
            self._extract_epub_metadata(root, meta)
            cover_path = self._find_epub_cover(zf, root, opf_path)
            if cover_path:
                meta.cover_path = cover_path
        return meta

    def _find_opf_path(self, zf: zipfile.ZipFile) -> Optional[str]:
        try:
            container = zf.read("META-INF/container.xml").decode("utf-8")
            root = ET.fromstring(container)
            rootfile = root.find(".//c:rootfile", EPUB_CONTAINER_NS)
            if rootfile is not None:
                return rootfile.get("full-path")
        except Exception:
            pass
        return None

    def _extract_epub_metadata(self, root: ET.Element, meta: BookMeta):
        for elem in root.iter():
            tag = elem.tag
            if isinstance(tag, str):
                if tag.endswith("}title") or tag == "title":
                    if not meta.title:
                        meta.title = (elem.text or "").strip()
                elif tag.endswith("}creator") or tag == "creator":
                    if not meta.author:
                        meta.author = (elem.text or "").strip()
                elif tag.endswith("}publisher") or tag == "publisher":
                    if not meta.publisher:
                        meta.publisher = (elem.text or "").strip()
                elif tag.endswith("}date") or tag == "date":
                    if not meta.publish_date:
                        meta.publish_date = (elem.text or "").strip()
                elif tag.endswith("}language") or tag == "language":
                    if not meta.language:
                        meta.language = (elem.text or "").strip()
                elif tag.endswith("}identifier") or tag == "identifier":
                    text = (elem.text or "").strip()
                    if "isbn" in text.lower() and not meta.isbn:
                        meta.isbn = text
                elif tag.endswith("}description") or tag == "description":
                    if not meta.description:
                        meta.description = (elem.text or "").strip()
                elif tag.endswith("}subject") or tag == "subject":
                    if elem.text and elem.text.strip() not in meta.tags:
                        meta.tags.append(elem.text.strip())

    def _find_epub_cover(self, zf, root, opf_path: str) -> Optional[str]:
        try:
            manifest = root.find(".//{http://www.idpf.org/2007/opf}manifest")
            if manifest is not None:
                for item in manifest:
                    props = item.get("properties", "")
                    href = item.get("href", "")
                    if "cover-image" in props:
                        return href
            metadata = root.find(".//{http://www.idpf.org/2007/opf}metadata")
            if metadata is not None:
                for meta_elem in metadata:
                    if meta_elem.get("name") == "cover":
                        cover_id = meta_elem.get("content")
                        if manifest is not None and cover_id:
                            for item in manifest:
                                if item.get("id") == cover_id:
                                    return item.get("href")
        except Exception:
            pass
        return None
