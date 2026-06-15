import unittest
import tempfile
import os

from ebook_manager.scanner import BookshelfScanner


class TestScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_files(self, files: list):
        for name in files:
            path = os.path.join(self.temp_dir, name)
            with open(path, "w") as f:
                f.write("test")

    def test_scan_supported_formats(self):
        self._create_files([
            "book1.epub",
            "book2.mobi",
            "book3.pdf",
            "book4.azw3",
            "book5.fb2",
            "book6.txt",
            "book7.docx",
        ])

        scanner = BookshelfScanner()
        files = scanner.scan_directory(self.temp_dir, recursive=False)

        self.assertEqual(len(files), 6)

    def test_is_supported_file(self):
        scanner = BookshelfScanner()

        self.assertTrue(scanner.is_supported_file("test.epub"))
        self.assertTrue(scanner.is_supported_file("test.mobi"))
        self.assertTrue(scanner.is_supported_file("test.pdf"))
        self.assertTrue(scanner.is_supported_file("test.azw3"))
        self.assertTrue(scanner.is_supported_file("test.fb2"))
        self.assertTrue(scanner.is_supported_file("test.txt"))
        self.assertFalse(scanner.is_supported_file("test.docx"))
        self.assertFalse(scanner.is_supported_file("test.html"))

    def test_get_file_format(self):
        self.assertEqual(BookshelfScanner.get_file_format("book.epub"), "epub")
        self.assertEqual(BookshelfScanner.get_file_format("book.PDF"), "pdf")
        self.assertEqual(BookshelfScanner.get_file_format("path/to/book.mobi"), "mobi")

    def test_scan_empty_directory(self):
        scanner = BookshelfScanner()
        files = scanner.scan_directory(self.temp_dir, recursive=False)
        self.assertEqual(files, [])

    def test_scan_nonexistent_directory(self):
        scanner = BookshelfScanner()
        files = scanner.scan_directory("/nonexistent/path", recursive=False)
        self.assertEqual(files, [])

    def test_scan_recursive(self):
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir)
        with open(os.path.join(self.temp_dir, "top.epub"), "w") as f:
            f.write("test")
        with open(os.path.join(subdir, "nested.txt"), "w") as f:
            f.write("test")

        scanner = BookshelfScanner()
        files = scanner.scan_directory(self.temp_dir, recursive=True)
        self.assertEqual(len(files), 2)

        files_non_recursive = scanner.scan_directory(self.temp_dir, recursive=False)
        self.assertEqual(len(files_non_recursive), 1)

    def test_get_supported_extensions(self):
        scanner = BookshelfScanner()
        extensions = scanner.get_supported_extensions()

        self.assertIn(".epub", extensions)
        self.assertIn(".mobi", extensions)
        self.assertIn(".pdf", extensions)
        self.assertIn(".azw3", extensions)
        self.assertIn(".fb2", extensions)
        self.assertIn(".txt", extensions)

    def test_scan_multiple_directories(self):
        dir2 = tempfile.mkdtemp()
        try:
            with open(os.path.join(self.temp_dir, "a.epub"), "w") as f:
                f.write("test")
            with open(os.path.join(dir2, "b.txt"), "w") as f:
                f.write("test")

            scanner = BookshelfScanner()
            files = scanner.scan_directories([self.temp_dir, dir2], recursive=False)
            self.assertEqual(len(files), 2)
        finally:
            import shutil
            shutil.rmtree(dir2, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
