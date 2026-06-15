import struct
import logging
from .base import BaseParser
from ..models import BookMeta

logger = logging.getLogger(__name__)


class Azw3Parser(BaseParser):
    """AZW3 (KF8) 格式解析器

    AZW3基于MOBI格式，但使用KF8（Kindle Format 8）头部结构。
    KF8文件包含两个MOBI头部：旧版MOBI头部和KF8头部。
    """

    SUPPORTED_EXTENSIONS = (".azw3", ".azw")

    MOBI_HEADER_MAGIC = b"BOOKMOBI"
    KF8_HEADER_MAGIC = b"TEXTREAD"

    def _parse(self, file_path: str) -> BookMeta:
        meta = BookMeta()
        with open(file_path, "rb") as f:
            header = f.read(78)
            if len(header) < 78:
                logger.debug(f"文件太小，不是有效的AZW3文件: {file_path}")
                return meta

            if not self._is_valid_pdb_header(header):
                logger.debug(f"无效的PDB头部: {file_path}")
                return meta

            mobi_start = int.from_bytes(header[60:64], "big")
            f.seek(mobi_start)
            mobi_header = f.read(200)
            if len(mobi_header) < 24:
                return meta

            encoding = int.from_bytes(mobi_header[12:16], "big")
            codec = "utf-8" if encoding == 65001 else "cp1252"

            f.seek(0)
            palm_name = f.read(32).split(b"\x00")[0]
            try:
                meta.title = palm_name.decode(codec).strip()
            except Exception:
                meta.title = palm_name.decode("utf-8", errors="ignore").strip()

            kf8_mobi_start = self._find_kf8_header(f, mobi_start, mobi_header)
            if kf8_mobi_start is not None:
                f.seek(kf8_mobi_start)
                kf8_header = f.read(200)
                if len(kf8_header) >= 24:
                    self._extract_exth_metadata(
                        f, kf8_mobi_start, kf8_header, codec, meta
                    )
            else:
                self._extract_exth_metadata(
                    f, mobi_start, mobi_header, codec, meta
                )

        return meta

    def _is_valid_pdb_header(self, header: bytes) -> bool:
        name = header[0:32]
        try:
            name_str = name.split(b"\x00")[0].decode("ascii", errors="ignore")
            return bool(name_str)
        except Exception:
            return False

    def _find_kf8_header(self, f, mobi_start: int, mobi_header: bytes) -> int | None:
        try:
            mobi_length = int.from_bytes(mobi_header[4:8], "big")
            exth_flag = int.from_bytes(mobi_header[128:132], "big")

            if exth_flag & 0x40:
                exth_start = mobi_start + mobi_length
                f.seek(exth_start)
                exth_header = f.read(12)
                if len(exth_header) >= 12 and exth_header[0:4] == b"EXTH":
                    record_count = int.from_bytes(exth_header[8:12], "big")
                    pos = exth_start + 12

                    for _ in range(record_count):
                        f.seek(pos)
                        record_header = f.read(8)
                        if len(record_header) < 8:
                            break

                        record_type = int.from_bytes(record_header[0:4], "big")
                        record_length = int.from_bytes(record_header[4:8], "big")

                        if record_length < 8 or record_length > 100000:
                            break

                        if record_type == 2000:
                            f.seek(pos + 8)
                            data = f.read(record_length - 8)
                            if len(data) >= 4:
                                kf8_offset = int.from_bytes(data[0:4], "big")
                                return kf8_offset

                        pos += record_length

            first_record_offset = int.from_bytes(mobi_header[112:116], "big")
            if first_record_offset > 0:
                return first_record_offset

        except Exception as e:
            logger.debug(f"查找KF8头部失败: {e}")

        return None

    def _extract_exth_metadata(
        self, f, mobi_start: int, mobi_header: bytes, codec: str, meta: BookMeta
    ):
        try:
            mobi_length = int.from_bytes(mobi_header[4:8], "big")
            exth_flag = int.from_bytes(mobi_header[128:132], "big")

            if exth_flag & 0x40:
                exth_start = mobi_start + mobi_length
                f.seek(exth_start)
                exth_header = f.read(12)
                if len(exth_header) < 12:
                    return

                exth_magic = exth_header[0:4]
                if exth_magic != b"EXTH":
                    return

                record_count = int.from_bytes(exth_header[8:12], "big")
                pos = exth_start + 12

                for _ in range(record_count):
                    f.seek(pos)
                    record_header = f.read(8)
                    if len(record_header) < 8:
                        break

                    record_type = int.from_bytes(record_header[0:4], "big")
                    record_length = int.from_bytes(record_header[4:8], "big")

                    if record_length < 8 or record_length > 100000:
                        break

                    data = f.read(record_length - 8)

                    try:
                        text = data.decode(codec, errors="ignore").strip()
                    except Exception:
                        text = data.decode("utf-8", errors="ignore").strip()

                    self._map_exth_record(record_type, text, meta)

                    pos += record_length
        except Exception:
            pass

    @staticmethod
    def _map_exth_record(record_type: int, value: str, meta: BookMeta):
        if not value:
            return

        exth_type_map = {
            100: "author",
            101: "publisher",
            106: "publish_date",
            109: "description",
            103: "isbn",
            524: "language",
            200: "title",
        }

        field = exth_type_map.get(record_type)
        if field and hasattr(meta, field):
            if not getattr(meta, field):
                setattr(meta, field, value)

        if record_type == 105 and value not in meta.tags:
            meta.tags.append(value)
