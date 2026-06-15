import logging
from pathlib import Path
from typing import Dict, Type, Optional

from .base import BaseParser
from .epub_parser import EpubParser
from .mobi_parser import MobiParser
from .pdf_parser import PdfParser
from .azw3_parser import Azw3Parser
from .fb2_parser import Fb2Parser
from .txt_parser import TxtParser
from ..config import ParserConfig
from ..models import BookMeta

logger = logging.getLogger(__name__)


class ParserFactory:
    """解析器工厂类

    根据文件扩展名自动选择合适的解析器。
    支持通过配置文件启用/禁用特定格式。
    """

    def __init__(self):
        self._config = ParserConfig()
        self._parsers: Dict[str, Type[BaseParser]] = {}
        self._register_parsers()

    def _register_parsers(self):
        parser_classes = [
            EpubParser,
            MobiParser,
            PdfParser,
            Azw3Parser,
            Fb2Parser,
            TxtParser,
        ]

        for parser_cls in parser_classes:
            for ext in parser_cls.SUPPORTED_EXTENSIONS:
                fmt = ext.lstrip(".")
                if self._config.is_format_enabled(fmt):
                    self._parsers[ext] = parser_cls
                    logger.debug(f"已注册解析器: {parser_cls.__name__} -> {ext}")

    def get_parser(self, file_path: str) -> Optional[BaseParser]:
        ext = Path(file_path).suffix.lower()
        parser_cls = self._parsers.get(ext)
        if parser_cls is None:
            return None
        return parser_cls()

    def parse(self, file_path: str) -> BookMeta:
        parser = self.get_parser(file_path)
        if parser is None:
            logger.warning(f"不支持的文件格式: {file_path}")
            meta = BookMeta()
            meta.file_path = file_path
            meta.file_format = Path(file_path).suffix.lower().lstrip(".")
            meta.file_size = 0
            meta.title = Path(file_path).stem
            return meta
        return parser.parse(file_path)

    def is_supported(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in self._parsers

    def get_supported_extensions(self) -> list:
        return list(self._parsers.keys())

    def refresh(self):
        self._parsers.clear()
        self._register_parsers()


def get_parser(file_path: str) -> Optional[BaseParser]:
    factory = ParserFactory()
    return factory.get_parser(file_path)


def parse_book(file_path: str) -> BookMeta:
    factory = ParserFactory()
    return factory.parse(file_path)
