import unittest
import tempfile
import os
from pathlib import Path

from ebook_manager.parsers.base import BaseParser
from ebook_manager.parsers.txt_parser import TxtParser
from ebook_manager.models import BookMeta


class TestBaseParser(unittest.TestCase):
    def test_base_parser_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseParser()

    def test_supports_method(self):
        class TestParser(BaseParser):
            SUPPORTED_EXTENSIONS = (".test",)

            def _parse(self, file_path):
                return BookMeta()

        self.assertTrue(TestParser.supports("file.test"))
        self.assertTrue(TestParser.supports("file.TEST"))
        self.assertFalse(TestParser.supports("file.txt"))

    def test_parse_calls_fallback_on_error(self):
        class FailingParser(BaseParser):
            SUPPORTED_EXTENSIONS = (".fail",)

            def _parse(self, file_path):
                raise ValueError("Parse error")

        parser = FailingParser()
        with tempfile.NamedTemporaryFile(suffix=".fail", delete=False) as f:
            f.write(b"test")
            file_path = f.name

        try:
            meta = parser.parse(file_path)
            self.assertIsInstance(meta, BookMeta)
            self.assertEqual(meta.file_path, file_path)
            self.assertEqual(meta.file_format, "fail")
        finally:
            os.unlink(file_path)

    def test_parse_fills_common_fields(self):
        class TestParser(BaseParser):
            SUPPORTED_EXTENSIONS = (".test",)

            def _parse(self, file_path):
                meta = BookMeta()
                meta.title = "Test Title"
                meta.author = "Test Author"
                return meta

        parser = TestParser()
        with tempfile.NamedTemporaryFile(suffix=".test", delete=False) as f:
            f.write(b"test content")
            file_path = f.name

        try:
            meta = parser.parse(file_path)
            self.assertEqual(meta.title, "Test Title")
            self.assertEqual(meta.author, "Test Author")
            self.assertEqual(meta.file_path, file_path)
            self.assertEqual(meta.file_format, "test")
            self.assertGreater(meta.file_size, 0)
        finally:
            os.unlink(file_path)

    def test_fallback_title_from_filename(self):
        class EmptyParser(BaseParser):
            SUPPORTED_EXTENSIONS = (".empty",)

            def _parse(self, file_path):
                return BookMeta()

        parser = EmptyParser()
        with tempfile.NamedTemporaryFile(
            prefix="My Book Title.", suffix=".empty", delete=False
        ) as f:
            f.write(b"test")
            file_path = f.name

        try:
            meta = parser.parse(file_path)
            self.assertTrue(meta.title.startswith("My Book Title"))
        finally:
            os.unlink(file_path)


if __name__ == "__main__":
    unittest.main()
