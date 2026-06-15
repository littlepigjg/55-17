import logging
import os
import re
from pathlib import Path

from .base import BaseParser
from ..config import ParserConfig
from ..models import BookMeta

logger = logging.getLogger(__name__)


class TxtParser(BaseParser):
    """TXT 纯文本格式解析器

    TXT文件没有标准元数据，通过以下方式推测：
    1. 从文件名提取书名和作者（常见模式：书名 - 作者.txt）
    2. 读取文件前10KB，从首行和内容推测元数据
    3. 限制读取大小，避免大文件占用内存
    """

    SUPPORTED_EXTENSIONS = (".txt",)

    _sample_size: int = None

    def __init__(self):
        config = ParserConfig()
        self._sample_size = config.get_txt_sample_size()

    @property
    def sample_size(self) -> int:
        return self._sample_size

    def _parse(self, file_path: str) -> BookMeta:
        meta = BookMeta()

        title_from_filename, author_from_filename = self._extract_from_filename(file_path, meta)
        self._extract_from_content(file_path, meta, title_from_filename, author_from_filename)

        return meta

    def _extract_from_filename(self, file_path: str, meta: BookMeta) -> tuple[bool, bool]:
        stem = Path(file_path).stem
        has_good_title = False
        has_good_author = False

        patterns = [
            r"^(.+?)\s*[-_]\s*(.+)$",
            r"^(.+?)\s*【(作者|著)[:：]\s*(.+?)】",
            r"^(.+?)\s*\((作者|著)[:：]\s*(.+?)\)",
            r"^(.+?)\s*by\s+(.+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, stem, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    title = groups[0].strip()
                    author = groups[-1].strip()
                    if title:
                        meta.title = title
                        has_good_title = True
                    if author:
                        meta.author = author
                        has_good_author = True
                    return has_good_title, has_good_author

        if stem and not meta.title:
            meta.title = stem

        return has_good_title, has_good_author

    def _extract_from_content(self, file_path: str, meta: BookMeta, has_good_title: bool = False, has_good_author: bool = False):
        try:
            file_size = os.path.getsize(file_path)
            read_size = min(file_size, self._sample_size)

            with open(file_path, "rb") as f:
                raw_data = f.read(read_size)

            text = self._decode_text(raw_data)
            if not text:
                return

            lines = text.splitlines()
            non_empty_lines = [line.strip() for line in lines if line.strip()]

            if not non_empty_lines:
                return

            self._extract_from_first_lines(non_empty_lines, meta, has_good_title, has_good_author)

        except Exception as e:
            logger.warning(f"读取TXT文件内容失败: {file_path}, {e}")

    def _decode_text(self, data: bytes) -> str:
        if not data:
            return ""

        if data.startswith(b"\xef\xbb\xbf"):
            return data.decode("utf-8-sig", errors="ignore")
        if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
            return data.decode("utf-16", errors="ignore")

        text = self._try_decode_utf8_safe(data)
        if text is not None:
            return text

        fallback_encodings = ["gbk", "gb2312", "big5", "cp1252", "latin-1"]
        for encoding in fallback_encodings:
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue

        return data.decode("utf-8", errors="ignore")

    @staticmethod
    def _try_decode_utf8_safe(data: bytes) -> str | None:
        try:
            text = data.decode("utf-8")
            if TxtParser._is_plausible_utf8(text):
                return text
        except (UnicodeDecodeError, UnicodeError):
            pass

        for truncate in range(1, 4):
            if len(data) <= truncate:
                break
            try:
                text = data[:-truncate].decode("utf-8")
                if TxtParser._is_plausible_utf8(text):
                    return text
            except (UnicodeDecodeError, UnicodeError):
                continue

        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return None

    @staticmethod
    def _is_plausible_utf8(text: str) -> bool:
        if not text:
            return False

        control_chars = sum(1 for c in text if ord(c) < 32 and c not in "\t\n\r")
        if len(text) > 0 and control_chars / len(text) > 0.1:
            return False

        return True

    def _extract_from_first_lines(self, lines: list, meta: BookMeta, has_good_title: bool = False, has_good_author: bool = False):
        if not lines:
            return

        first_line = lines[0]

        explicit_title_patterns = [
            r"^书名[：:]\s*(.+)$",
            r"^title[：:]\s*(.+)$",
            r"^《(.+?)》",
        ]

        found_explicit_title = False
        for pattern in explicit_title_patterns:
            match = re.match(pattern, first_line, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if title and len(title) < 200:
                    meta.title = title
                    found_explicit_title = True
                    break

        if not has_good_title and not found_explicit_title:
            if first_line and len(first_line) < 200:
                meta.title = first_line.strip()

        if not has_good_author:
            for i in range(1, min(10, len(lines))):
                line = lines[i]
                author_match = re.match(
                    r"^(作者|著者|author)\s*[:：]?\s*(.+)$",
                    line,
                    re.IGNORECASE,
                )
                if author_match:
                    author = author_match.group(2).strip()
                    if author and len(author) < 100:
                        meta.author = author
                        break

                if re.match(r"^内容简介|简介|序|前言|第[一二三四五六七八九十\d]+章|Chapter\s+\d+", line):
                    break

        for i in range(1, min(20, len(lines))):
            line = lines[i]
            tag_match = re.match(r"^(标签|分类|题材|类型)[:：]\s*(.+)$", line, re.IGNORECASE)
            if tag_match:
                tags_str = tag_match.group(2)
                tags = re.split(r"[,，、;；\s]+", tags_str)
                for tag in tags:
                    tag = tag.strip()
                    if tag and tag not in meta.tags:
                        meta.tags.append(tag)
