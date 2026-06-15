import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

from ..models import BookMeta

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """所有解析器的基类"""

    SUPPORTED_EXTENSIONS: tuple = ()

    @classmethod
    def supports(cls, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS

    def parse(self, file_path: str) -> BookMeta:
        try:
            meta = self._parse(file_path)
        except Exception as e:
            logger.warning(f"解析 {file_path} 失败: {e}，使用降级策略")
            meta = self._fallback_parse(file_path)

        meta.file_path = file_path
        meta.file_format = self._get_format(file_path)
        meta.file_size = self._get_file_size(file_path)

        if not meta.title:
            meta.title = Path(file_path).stem

        return meta

    @abstractmethod
    def _parse(self, file_path: str) -> BookMeta:
        pass

    def _fallback_parse(self, file_path: str) -> BookMeta:
        return BookMeta()

    def _get_format(self, file_path: str) -> str:
        return Path(file_path).suffix.lower().lstrip(".")

    @staticmethod
    def _get_file_size(file_path: str) -> int:
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
