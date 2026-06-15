import unittest
import tempfile
import os
import struct

from ebook_manager.parsers.azw3_parser import Azw3Parser
from ebook_manager.models import BookMeta


class TestAzw3Parser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_supports_azw3_extension(self):
        self.assertTrue(Azw3Parser.supports("book.azw3"))
        self.assertTrue(Azw3Parser.supports("book.AZW3"))
        self.assertTrue(Azw3Parser.supports("book.azw"))
        self.assertFalse(Azw3Parser.supports("book.mobi"))

    def _create_minimal_pdb_header(self, name: bytes, record_count: int = 1) -> bytes:
        header = bytearray(78)
        name_padded = name[:31].ljust(32, b"\x00")
        header[0:32] = name_padded
        header[60:64] = struct.pack(">I", 78 + 8 * record_count)
        return bytes(header)

    def _create_mobi_header(self, title: bytes, encoding: int = 65001) -> bytes:
        mobi = bytearray(200)
        mobi[0:4] = b"BOOK"
        mobi[4:8] = struct.pack(">I", 200)
        mobi[12:16] = struct.pack(">I", encoding)
        mobi[20:24] = struct.pack(">I", len(title))
        return bytes(mobi)

    def test_corrupted_file_fallback(self):
        path = os.path.join(self.temp_dir, "test.azw3")
        with open(path, "wb") as f:
            f.write(b"This is not a valid azw3 file")

        parser = Azw3Parser()
        meta = parser.parse(path)

        self.assertEqual(meta.title, "test")
        self.assertEqual(meta.file_format, "azw3")
        self.assertGreater(meta.file_size, 0)

    def test_empty_file(self):
        path = os.path.join(self.temp_dir, "empty.azw3")
        with open(path, "wb") as f:
            pass

        parser = Azw3Parser()
        meta = parser.parse(path)

        self.assertEqual(meta.title, "empty")
        self.assertEqual(meta.file_format, "azw3")

    def test_short_file(self):
        path = os.path.join(self.temp_dir, "short.azw3")
        with open(path, "wb") as f:
            f.write(b"short")

        parser = Azw3Parser()
        meta = parser.parse(path)

        self.assertEqual(meta.title, "short")
        self.assertEqual(meta.file_format, "azw3")

    def test_minimal_valid_structure(self):
        path = os.path.join(self.temp_dir, "minimal.azw3")

        title = b"Test Book"
        pdb_header = self._create_minimal_pdb_header(title)
        mobi_header = self._create_mobi_header(title)

        with open(path, "wb") as f:
            f.write(pdb_header)
            for i in range(1):
                f.write(struct.pack(">II", 78 + len(mobi_header), 0))
            f.write(mobi_header)

        parser = Azw3Parser()
        meta = parser.parse(path)

        self.assertEqual(meta.title, "Test Book")
        self.assertEqual(meta.file_format, "azw3")

    def test_parser_never_raises(self):
        path = os.path.join(self.temp_dir, "weird.azw3")

        weird_data = b"\x00\x01\x02\x03\xff\xfe\xfd" * 100
        with open(path, "wb") as f:
            f.write(weird_data)

        parser = Azw3Parser()
        try:
            meta = parser.parse(path)
            self.assertIsInstance(meta, BookMeta)
        except Exception as e:
            self.fail(f"Azw3Parser.parse raised {type(e).__name__}: {e}")


if __name__ == "__main__":
    unittest.main()
