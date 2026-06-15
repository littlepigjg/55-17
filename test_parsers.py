import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ebook_manager.models import BookMeta
from ebook_manager.parsers import (
    ParserFactory,
    BaseParser,
    EpubParser,
    MobiParser,
    PdfParser,
    Azw3Parser,
    Fb2Parser,
    TxtParser,
)
from ebook_manager.config import ParserConfig
from ebook_manager.metadata_parser import MetadataParser
from ebook_manager.scanner import BookshelfScanner


def test_imports():
    print("✓ 所有模块导入成功")
    print(f"  - BaseParser: {BaseParser}")
    print(f"  - EpubParser: {EpubParser}")
    print(f"  - MobiParser: {MobiParser}")
    print(f"  - PdfParser: {PdfParser}")
    print(f"  - Azw3Parser: {Azw3Parser}")
    print(f"  - Fb2Parser: {Fb2Parser}")
    print(f"  - TxtParser: {TxtParser}")
    print(f"  - ParserFactory: {ParserFactory}")
    print(f"  - ParserConfig: {ParserConfig}")
    print(f"  - MetadataParser: {MetadataParser}")
    print(f"  - BookshelfScanner: {BookshelfScanner}")


def test_factory():
    factory = ParserFactory()
    print("\n✓ ParserFactory 创建成功")

    extensions = factory.get_supported_extensions()
    print(f"  支持的扩展名: {sorted(extensions)}")

    assert ".epub" in extensions
    assert ".mobi" in extensions
    assert ".pdf" in extensions
    assert ".azw3" in extensions
    assert ".fb2" in extensions
    assert ".txt" in extensions
    print("✓ 所有格式都已注册")


def test_config():
    config = ParserConfig()
    print("\n✓ ParserConfig 创建成功")

    enabled = config.get_enabled_formats()
    print(f"  启用的格式: {enabled}")

    assert config.is_format_enabled("epub")
    assert config.is_format_enabled("mobi")
    assert config.is_format_enabled("pdf")
    assert config.is_format_enabled("azw3")
    assert config.is_format_enabled("fb2")
    assert config.is_format_enabled("txt")
    print("✓ 所有格式默认都启用")

    sample_size = config.get_txt_sample_size()
    print(f"  TXT采样大小: {sample_size} bytes ({sample_size//1024} KB)")
    assert sample_size == 10 * 1024
    print("✓ TXT采样大小正确")


def test_txt_parser():
    print("\n--- 测试 TXT 解析器 ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "测试书籍 - 测试作者.txt"
        test_file.write_text("""书名：测试书籍
作者：测试作者
标签：科幻, 冒险
简介：这是一本测试用的书籍。

第一章 开始
故事从这里开始...
""", encoding="utf-8")

        parser = TxtParser()
        meta = parser.parse(str(test_file))

        print(f"  书名: {meta.title}")
        print(f"  作者: {meta.author}")
        print(f"  标签: {meta.tags}")
        print(f"  格式: {meta.file_format}")
        print(f"  文件大小: {meta.file_size}")

        assert meta.title == "测试书籍"
        assert meta.author == "测试作者"
        assert "科幻" in meta.tags
        assert meta.file_format == "txt"
        assert meta.file_size > 0
        print("✓ TXT解析器测试通过")


def test_fb2_parser():
    print("\n--- 测试 FB2 解析器 ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.fb2"
        fb2_content = '''<?xml version="1.0" encoding="UTF-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">
  <description>
    <title-info>
      <book-title>测试书籍</book-title>
      <author>
        <first-name>测试</first-name>
        <last-name>作者</last-name>
      </author>
      <genre>sf</genre>
      <genre>fantasy</genre>
      <lang>zh</lang>
      <annotation>
        <p>这是一本测试用的书。</p>
      </annotation>
      <date>2024</date>
    </title-info>
    <document-info>
      <isbn>1234567890</isbn>
    </document-info>
    <publish-info>
      <publisher>测试出版社</publisher>
      <year>2024</year>
    </publish-info>
  </description>
  <body>
    <section>
      <title>第一章</title>
      <p>内容...</p>
    </section>
  </body>
</FictionBook>
'''
        test_file.write_text(fb2_content, encoding="utf-8")

        parser = Fb2Parser()
        meta = parser.parse(str(test_file))

        print(f"  书名: {meta.title}")
        print(f"  作者: {meta.author}")
        print(f"  出版社: {meta.publisher}")
        print(f"  出版日期: {meta.publish_date}")
        print(f"  语言: {meta.language}")
        print(f"  ISBN: {meta.isbn}")
        print(f"  标签: {meta.tags}")
        print(f"  描述: {meta.description[:30]}...")
        print(f"  格式: {meta.file_format}")

        assert meta.title == "测试书籍"
        assert "测试" in meta.author and "作者" in meta.author
        assert meta.publisher == "测试出版社"
        assert meta.language == "zh"
        assert meta.isbn == "1234567890"
        assert "sf" in meta.tags
        assert meta.file_format == "fb2"
        print("✓ FB2解析器测试通过")


def test_corrupted_file():
    print("\n--- 测试损坏文件处理 ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "corrupted.epub"
        test_file.write_bytes(b"This is not a valid epub file")

        parser = EpubParser()
        meta = parser.parse(str(test_file))

        print(f"  书名(回退到文件名): {meta.title}")
        print(f"  格式: {meta.file_format}")
        print(f"  文件大小: {meta.file_size}")

        assert meta.title == "corrupted"
        assert meta.file_format == "epub"
        print("✓ 损坏文件降级策略工作正常")


def test_unsupported_format():
    print("\n--- 测试不支持的格式 ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.docx"
        test_file.write_text("test")

        factory = ParserFactory()
        parser = factory.get_parser(str(test_file))
        assert parser is None
        print("✓ 不支持的格式返回None")

        meta = factory.parse(str(test_file))
        assert meta.title == "test"
        assert meta.file_format == "docx"
        print("✓ 不支持的格式使用降级策略")


def test_metadata_parser_backward_compat():
    print("\n--- 测试向后兼容性 ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("测试内容", encoding="utf-8")

        parser = MetadataParser()
        meta = parser.parse(str(test_file))

        assert meta.title == "test"
        assert meta.file_format == "txt"
        print("✓ MetadataParser 向后兼容")


def test_scanner():
    print("\n--- 测试扫描器 ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "book1.epub").write_text("fake")
        Path(tmpdir, "book2.mobi").write_text("fake")
        Path(tmpdir, "book3.pdf").write_text("fake")
        Path(tmpdir, "book4.azw3").write_text("fake")
        Path(tmpdir, "book5.fb2").write_text("fake")
        Path(tmpdir, "book6.txt").write_text("fake")
        Path(tmpdir, "book7.docx").write_text("fake")

        scanner = BookshelfScanner()
        files = scanner.scan_directory(tmpdir, recursive=False)
        print(f"  扫描到 {len(files)} 个支持的文件")

        assert len(files) == 6
        print("✓ 扫描器正确识别所有支持的格式")

        assert scanner.is_supported_file(str(Path(tmpdir) / "book1.epub"))
        assert not scanner.is_supported_file(str(Path(tmpdir) / "book7.docx"))
        print("✓ is_supported_file 工作正常")


def test_disable_format():
    print("\n--- 测试禁用格式 ---")

    config = ParserConfig()
    config.set_format_enabled("txt", False)

    factory = ParserFactory()
    factory.refresh()

    extensions = factory.get_supported_extensions()
    print(f"  禁用txt后支持的扩展名: {sorted(extensions)}")

    assert ".txt" not in extensions
    print("✓ 禁用格式功能正常")

    config.set_format_enabled("txt", True)
    factory.refresh()
    assert ".txt" in factory.get_supported_extensions()
    print("✓ 重新启用格式功能正常")


def test_txt_performance():
    print("\n--- 测试TXT大文件性能 ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "large.txt"

        import time
        start_time = time.time()

        with open(test_file, "w", encoding="utf-8") as f:
            for i in range(10000):
                f.write(f"这是第{i}行的内容。" * 10 + "\n")

        write_time = time.time() - start_time
        file_size = test_file.stat().st_size
        print(f"  创建 {file_size/1024/1024:.2f} MB 的文件，耗时 {write_time:.2f}s")

        start_time = time.time()
        parser = TxtParser()
        meta = parser.parse(str(test_file))
        parse_time = time.time() - start_time

        print(f"  解析耗时: {parse_time:.4f}s")
        print(f"  解析结果书名: {meta.title}")
        print(f"  文件大小: {meta.file_size}")

        assert meta.file_size == file_size
        assert parse_time < 1.0
        print("✓ TXT大文件解析性能正常（仅读取前10KB）")


def main():
    print("=" * 60)
    print("电子书解析器架构测试")
    print("=" * 60)

    try:
        test_imports()
        test_factory()
        test_config()
        test_txt_parser()
        test_fb2_parser()
        test_corrupted_file()
        test_unsupported_format()
        test_metadata_parser_backward_compat()
        test_scanner()
        test_disable_format()
        test_txt_performance()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
