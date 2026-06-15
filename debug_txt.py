import os
import tempfile
from pathlib import Path
from ebook_manager.parsers.txt_parser import TxtParser
from ebook_manager.models import BookMeta

with tempfile.TemporaryDirectory() as tmpdir:
    path = os.path.join(tmpdir, "large.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("开头标题\n")
        for i in range(100):
            f.write(f"这是第{i}行的内容，非常非常长的一行内容。" * 5 + "\n")

    parser = TxtParser()

    sample_size = parser.sample_size
    print(f"sample_size: {sample_size} bytes")

    with open(path, "rb") as f:
        raw_data = f.read(sample_size)

    print(f"raw_data length: {len(raw_data)} bytes")

    text = parser._decode_text(raw_data)
    print(f"text length: {len(text)} chars")

    lines = text.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]

    print(f"number of lines: {len(lines)}")
    print(f"number of non-empty lines: {len(non_empty_lines)}")
    if non_empty_lines:
        print(f"first line: '{non_empty_lines[0]}'")

    meta = BookMeta()
    meta.title = "large"

    print(f"\nbefore _extract_from_first_lines, meta.title: '{meta.title}'")
    parser._extract_from_first_lines(non_empty_lines, meta, has_good_title=False, has_good_author=False)
    print(f"after _extract_from_first_lines, meta.title: '{meta.title}'")

    print("\n=== 检查条件 ===")
    has_good_title = False
    found_explicit_title = False
    first_line = non_empty_lines[0] if non_empty_lines else ""
    print(f"has_good_title: {has_good_title}")
    print(f"found_explicit_title: {found_explicit_title}")
    print(f"not has_good_title: {not has_good_title}")
    print(f"not found_explicit_title: {not found_explicit_title}")
    print(f"condition: {not has_good_title and not found_explicit_title}")
    print(f"first_line: '{first_line}'")
    print(f"len(first_line) < 200: {len(first_line) < 200}")
