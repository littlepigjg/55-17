import xml.etree.ElementTree as ET
import logging
from pathlib import Path

from .base import BaseParser
from ..models import BookMeta

logger = logging.getLogger(__name__)

FB2_NS = "http://www.gribuser.ru/xml/fictionbook/2.0"


class Fb2Parser(BaseParser):
    """FB2 (FictionBook) 格式解析器

    FB2是俄罗斯流行的电子书格式，基于XML。
    元数据存储在<description>标签中，包含<title-info>和<document-info>。
    """

    SUPPORTED_EXTENSIONS = (".fb2",)

    def _parse(self, file_path: str) -> BookMeta:
        meta = BookMeta()
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            description = self._find_element(root, "description")
            if description is None:
                logger.debug(f"未找到description元素: {file_path}")
                return meta

            title_info = self._find_element(description, "title-info")
            if title_info is not None:
                self._extract_title_info(title_info, meta)

            document_info = self._find_element(description, "document-info")
            if document_info is not None:
                self._extract_document_info(document_info, meta)

            publish_info = self._find_element(description, "publish-info")
            if publish_info is not None:
                self._extract_publish_info(publish_info, meta)

        except ET.ParseError as e:
            logger.warning(f"FB2 XML解析失败: {file_path}, {e}")
        except Exception as e:
            logger.warning(f"FB2解析失败: {file_path}, {e}")

        return meta

    def _find_element(self, parent: ET.Element, tag_name: str) -> ET.Element | None:
        ns_tag = f"{{{FB2_NS}}}{tag_name}"
        elem = parent.find(ns_tag)
        if elem is not None:
            return elem
        for child in parent:
            if child.tag.endswith(f"}}{tag_name}") or child.tag == tag_name:
                return child
        return None

    def _find_all_elements(self, parent: ET.Element, tag_name: str) -> list:
        ns_tag = f"{{{FB2_NS}}}{tag_name}"
        elems = parent.findall(ns_tag)
        if elems:
            return elems
        result = []
        for child in parent:
            if child.tag.endswith(f"}}{tag_name}") or child.tag == tag_name:
                result.append(child)
        return result

    def _extract_title_info(self, title_info: ET.Element, meta: BookMeta):
        book_title = self._find_element(title_info, "book-title")
        if book_title is not None and book_title.text:
            meta.title = book_title.text.strip()

        authors = self._find_all_elements(title_info, "author")
        author_names = []
        for author in authors:
            first_name = self._find_element(author, "first-name")
            last_name = self._find_element(author, "last-name")
            middle_name = self._find_element(author, "middle-name")

            name_parts = []
            if first_name is not None and first_name.text:
                name_parts.append(first_name.text.strip())
            if middle_name is not None and middle_name.text:
                name_parts.append(middle_name.text.strip())
            if last_name is not None and last_name.text:
                name_parts.append(last_name.text.strip())

            if name_parts:
                author_names.append(" ".join(name_parts))

        if author_names:
            meta.author = ", ".join(author_names)

        genres = self._find_all_elements(title_info, "genre")
        for genre in genres:
            if genre.text and genre.text.strip() not in meta.tags:
                meta.tags.append(genre.text.strip())

        lang = self._find_element(title_info, "lang")
        if lang is not None and lang.text:
            meta.language = lang.text.strip()

        src_lang = self._find_element(title_info, "src-lang")
        if not meta.language and src_lang is not None and src_lang.text:
            meta.language = src_lang.text.strip()

        annotation = self._find_element(title_info, "annotation")
        if annotation is not None:
            meta.description = self._extract_text(annotation).strip()

        date_elem = self._find_element(title_info, "date")
        if date_elem is not None and date_elem.text:
            meta.publish_date = date_elem.text.strip()

    def _extract_document_info(self, doc_info: ET.Element, meta: BookMeta):
        isbn_elem = self._find_element(doc_info, "isbn")
        if isbn_elem is not None and isbn_elem.text:
            meta.isbn = isbn_elem.text.strip()

    def _extract_publish_info(self, publish_info: ET.Element, meta: BookMeta):
        publisher = self._find_element(publish_info, "publisher")
        if publisher is not None and publisher.text:
            if not meta.publisher:
                meta.publisher = publisher.text.strip()

        year = self._find_element(publish_info, "year")
        if year is not None and year.text:
            if not meta.publish_date:
                meta.publish_date = year.text.strip()

        isbn_elem = self._find_element(publish_info, "isbn")
        if isbn_elem is not None and isbn_elem.text:
            if not meta.isbn:
                meta.isbn = isbn_elem.text.strip()

    def _extract_text(self, elem: ET.Element) -> str:
        texts = []
        if elem.text:
            texts.append(elem.text)
        for child in elem:
            if child.text:
                texts.append(child.text)
            if child.tail:
                texts.append(child.tail)
        return " ".join(t.strip() for t in texts if t.strip())
