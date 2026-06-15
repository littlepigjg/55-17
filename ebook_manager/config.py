import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "enabled_formats": {
        "epub": True,
        "mobi": True,
        "pdf": True,
        "azw3": True,
        "fb2": True,
        "txt": True,
    },
    "txt_sample_size_kb": 10,
    "scan_skip_unsupported": True,
}


class ParserConfig:
    _instance = None
    _config: Dict[str, Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self._config = DEFAULT_CONFIG.copy()
        config_path = self._get_config_path()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                self._merge_config(user_config)
                logger.info(f"已加载配置文件: {config_path}")
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}，使用默认配置")

    @staticmethod
    def _get_config_path() -> str:
        home = Path.home()
        config_dir = home / ".ebook_manager"
        return str(config_dir / "parser_config.json")

    def _merge_config(self, user_config: Dict[str, Any]):
        if "enabled_formats" in user_config:
            self._config["enabled_formats"].update(user_config["enabled_formats"])
        if "txt_sample_size_kb" in user_config:
            self._config["txt_sample_size_kb"] = user_config["txt_sample_size_kb"]
        if "scan_skip_unsupported" in user_config:
            self._config["scan_skip_unsupported"] = user_config["scan_skip_unsupported"]

    def is_format_enabled(self, format_name: str) -> bool:
        return self._config["enabled_formats"].get(format_name, False)

    def get_txt_sample_size(self) -> int:
        return self._config["txt_sample_size_kb"] * 1024

    def should_skip_unsupported(self) -> bool:
        return self._config["scan_skip_unsupported"]

    def get_enabled_formats(self) -> Dict[str, bool]:
        return self._config["enabled_formats"].copy()

    def set_format_enabled(self, format_name: str, enabled: bool):
        self._config["enabled_formats"][format_name] = enabled

    def save_config(self):
        config_path = self._get_config_path()
        try:
            config_dir = os.path.dirname(config_path)
            os.makedirs(config_dir, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到: {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
