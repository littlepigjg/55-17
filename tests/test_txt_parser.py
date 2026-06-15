import unittest
import tempfile
import os
from pathlib import Path

from ebook_manager.parsers.txt_parser import TxtParser
from ebook_manager.config import ParserConfig
from ebook_manager.models import BookMeta


class TestTxtParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_file(self, name: str, content: str, encoding: str = "utf-8") -> str:
        path = os.path.join(self.temp_dir, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return path

    def test_supports_txt_extension(self):
        self.assertTrue(TxtParser.supports("book.txt"))
        self.assertTrue(TxtParser.supports("book.TXT"))
        self.assertFalse(TxtParser.supports("book.epub"))

    def test_title_from_filename_with_dash(self):
        path = self._create_file("三体 - 刘慈欣.txt", "内容...")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "三体")
        self.assertEqual(meta.author, "刘慈欣")

    def test_title_from_filename_with_by(self):
        path = self._create_file("Harry Potter by J.K. Rowling.txt", "Content...")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "Harry Potter")
        self.assertEqual(meta.author, "J.K. Rowling")

    def test_title_from_filename_with_chinese_brackets(self):
        path = self._create_file("盗墓笔记【作者：南派三叔】.txt", "内容...")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "盗墓笔记")
        self.assertEqual(meta.author, "南派三叔")

    def test_title_from_content_explicit(self):
        path = self._create_file("somefile.txt", "书名：平凡的世界\n作者：路遥\n内容...")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "平凡的世界")
        self.assertEqual(meta.author, "路遥")

    def test_title_from_content_first_line(self):
        path = self._create_file("random.txt", "第一行就是书名\n正文内容开始...")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "第一行就是书名")

    def test_title_from_filename_when_good(self):
        path = self._create_file("好书名 - 好作者.txt", "第一行内容\n更多内容...")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "好书名")
        self.assertEqual(meta.author, "好作者")

    def test_tags_extraction(self):
        content = """书名：测试书
作者：测试作者
标签：科幻, 冒险, 悬疑
内容开始...
"""
        path = self._create_file("test.txt", content)
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertIn("科幻", meta.tags)
        self.assertIn("冒险", meta.tags)
        self.assertIn("悬疑", meta.tags)

    def test_sample_size_limit(self):
        config = ParserConfig()
        sample_size = config.get_txt_sample_size()
        self.assertEqual(sample_size, 10 * 1024)

    def test_large_file_performance(self):
        import time

        path = os.path.join(self.temp_dir, "large.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("开头标题\n")
            for i in range(100000):
                f.write(f"这是第{i}行的内容，非常非常长的一行内容。" * 5 + "\n")

        parser = TxtParser()
        start = time.time()
        meta = parser.parse(path)
        elapsed = time.time() - start

        self.assertLess(elapsed, 1.0)
        self.assertEqual(meta.title, "开头标题")
        self.assertGreater(meta.file_size, 1024 * 1024)

    def test_encoding_detection_utf8(self):
        path = self._create_file("utf8.txt", "你好世界\n内容...", encoding="utf-8")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertTrue("你好" in meta.title or "内容" in meta.title)

    def test_encoding_detection_gbk(self):
        path = self._create_file("gbk.txt", "GBK编码测试\n内容...", encoding="gbk")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertTrue(len(meta.title) > 0)

    def test_empty_file(self):
        path = self._create_file("empty.txt", "")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "empty")
        self.assertEqual(meta.file_size, 0)

    def test_file_not_found(self):
        parser = TxtParser()
        meta = parser.parse(os.path.join(self.temp_dir, "nonexistent.txt"))
        self.assertEqual(meta.title, "nonexistent")
        self.assertEqual(meta.file_format, "txt")

    def test_file_format_and_size(self):
        path = self._create_file("test.txt", "Hello World")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.file_format, "txt")
        self.assertGreater(meta.file_size, 0)
        self.assertTrue(meta.file_path.endswith("test.txt"))

    def test_author_stops_at_chapter(self):
        content = """书名：测试
第一章 开始
作者：这个作者不应该被识别
内容...
"""
        path = self._create_file("test.txt", content)
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.author, "")

    def test_underscore_separator(self):
        path = self._create_file("海底两万里_儒勒凡尔纳.txt", "内容...")
        parser = TxtParser()
        meta = parser.parse(path)
        self.assertEqual(meta.title, "海底两万里")
        self.assertEqual(meta.author, "儒勒凡尔纳")


if __name__ == "__main__":
    unittest.main()
