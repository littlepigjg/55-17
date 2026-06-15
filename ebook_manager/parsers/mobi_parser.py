from .base import BaseParser
from ..models import BookMeta


class MobiParser(BaseParser):
    SUPPORTED_EXTENSIONS = (".mobi",)

    def _parse(self, file_path: str) -> BookMeta:
        meta = BookMeta()
        with open(file_path, "rb") as f:
            header = f.read(132)
            if len(header) < 132:
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

            self._extract_exth_metadata(f, mobi_start, mobi_header, codec, meta)

        return meta

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

                    if record_length < 8:
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
