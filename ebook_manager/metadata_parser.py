import logging
from pathlib import Path

from .models import BookMeta
from .parsers import ParserFactory

logger = logging.getLogger(__name__)


class MetadataParser:
    """元数据解析器（向后兼容包装类）

    新代码建议直接使用 parsers.ParserFactory
    """

    def __init__(self):
        self._factory = ParserFactory()

    def parse(self, file_path: str) -> BookMeta:
        parser = self._factory.get_parser(file_path)
        if parser is None:
            logger.warning(f"不支持的格式: {file_path}")
            meta = BookMeta()
            meta.file_path = file_path
            meta.file_format = Path(file_path).suffix.lower().lstrip(".")
            meta.file_size = 0
            meta.title = Path(file_path).stem
            return meta
        return parser.parse(file_path)
