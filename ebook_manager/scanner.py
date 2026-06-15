import os
import logging
from pathlib import Path
from typing import List

from .config import ParserConfig

logger = logging.getLogger(__name__)


class BookshelfScanner:
    def __init__(self):
        self._progress_callback = None
        self._config = ParserConfig()

    def set_progress_callback(self, callback):
        self._progress_callback = callback

    def _notify_progress(self, current: int, total: int, file_path: str):
        if self._progress_callback:
            self._progress_callback(current, total, file_path)

    def scan_directory(self, directory: str, recursive: bool = True) -> List[str]:
        directory = Path(directory)
        if not directory.is_dir():
            return []
        return self._collect_files(directory, recursive)

    def scan_directories(self, directories: List[str], recursive: bool = True) -> List[str]:
        all_files = []
        for d in directories:
            all_files.extend(self.scan_directory(d, recursive))
        return all_files

    def _collect_files(self, directory: Path, recursive: bool) -> List[str]:
        result = []
        try:
            entries = list(directory.iterdir())
        except PermissionError:
            logger.warning(f"无法访问目录: {directory}")
            return result

        total = len(entries)
        for i, entry in enumerate(entries):
            if entry.is_file():
                if self.is_supported_file(str(entry)):
                    result.append(str(entry.resolve()))
                    self._notify_progress(i + 1, total, str(entry))
                else:
                    if not self._config.should_skip_unsupported():
                        logger.debug(f"跳过不支持的文件: {entry}")
            elif entry.is_dir() and recursive:
                result.extend(self._collect_files(entry, recursive))

        return result

    def is_supported_file(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower().lstrip(".")
        return self._config.is_format_enabled(ext)

    @staticmethod
    def get_file_format(file_path: str) -> str:
        return Path(file_path).suffix.lower().lstrip(".")

    def get_supported_extensions(self) -> List[str]:
        enabled = self._config.get_enabled_formats()
        return [f".{fmt}" for fmt, enabled in enabled.items() if enabled]
