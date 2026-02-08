"""
FileReader - input 폴더의 파일을 읽고 요약하는 유틸리티

지원 형식: .txt, .md, .csv, .tsv, .pdf, .json
토큰 예산: 파일당 최대 2000자 (~500토큰)
"""

import csv
import json
from pathlib import Path

MAX_CONTENT_CHARS = 2000
MAX_CSV_ROWS = 20
MULTI_FILE_BUDGET = 4000


class FileInfo:
    """개별 파일의 메타데이터 + 내용"""

    def __init__(self, path, file_type, content, summary):
        self.path = str(path)
        self.name = Path(path).name
        self.file_type = file_type
        self.content = content
        self.summary = summary


EXTENSION_MAP = {
    ".txt": "text", ".md": "text", ".log": "text",
    ".csv": "csv", ".tsv": "csv",
    ".pdf": "pdf",
    ".json": "json",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".gif": "image", ".bmp": "image",
}


class FileReader:
    """input 폴더 스캔 및 파일 읽기"""

    @classmethod
    def scan_folder(cls, folder_path):
        folder = Path(folder_path)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            return []

        files = []
        for p in sorted(folder.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                try:
                    files.append(cls.read_file(p))
                except Exception:
                    files.append(FileInfo(str(p), "unknown", "", f"{p.name}: 읽기 실패"))
        return files

    @classmethod
    def read_file(cls, filepath):
        filepath = Path(filepath)
        ext = filepath.suffix.lower()
        file_type = EXTENSION_MAP.get(ext, "unknown")

        readers = {
            "text": cls._read_text,
            "csv": cls._read_csv,
            "pdf": cls._read_pdf,
            "json": cls._read_json,
            "image": cls._read_image,
        }
        return readers.get(file_type, cls._read_unknown)(filepath, file_type)

    @classmethod
    def _read_text(cls, path, file_type):
        text = path.read_text(encoding="utf-8", errors="replace")
        truncated = text[:MAX_CONTENT_CHARS]
        if len(text) > MAX_CONTENT_CHARS:
            truncated += "..."
        return FileInfo(path, file_type, truncated, f"{path.name}: 텍스트 ({len(text)}자)")

    @classmethod
    def _read_csv(cls, path, file_type):
        lines = []
        total_rows = 0
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                total_rows = i
                if i <= MAX_CSV_ROWS:
                    lines.append(" | ".join(row))
        content = "\n".join(lines)[:MAX_CONTENT_CHARS]
        summary = f"{path.name}: CSV ({total_rows}행, 상위 {min(MAX_CSV_ROWS, total_rows)}행 표시)"
        return FileInfo(path, file_type, content, summary)

    @classmethod
    def _read_pdf(cls, path, file_type):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)
            full = "\n\n".join(pages)
            truncated = full[:MAX_CONTENT_CHARS]
            if len(full) > MAX_CONTENT_CHARS:
                truncated += "..."
            return FileInfo(path, file_type, truncated, f"{path.name}: PDF ({len(reader.pages)}페이지)")
        except ImportError:
            return FileInfo(path, file_type, "", f"{path.name}: PDF (PyPDF2 미설치로 읽기 불가)")

    @classmethod
    def _read_json(cls, path, file_type):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        return FileInfo(path, file_type, text[:MAX_CONTENT_CHARS], f"{path.name}: JSON")

    @classmethod
    def _read_image(cls, path, file_type):
        return FileInfo(path, "image", "[이미지 파일]", f"{path.name}: 이미지 (텍스트 추출 불가)")

    @classmethod
    def _read_unknown(cls, path, file_type):
        return FileInfo(path, "unknown", "", f"{path.name}: 지원하지 않는 형식")

    @classmethod
    def build_manifest(cls, file_infos):
        """파일 목록 요약문 (프롬프트용)"""
        if not file_infos:
            return "(파일 없음)"
        return "\n".join(f"- {fi.summary}" for fi in file_infos)

    @classmethod
    def get_content(cls, file_infos, filenames=None):
        """특정 파일들의 내용을 토큰 예산 내에서 반환합니다."""
        selected = file_infos if filenames is None else [
            fi for fi in file_infos if fi.name in filenames
        ]
        parts = []
        total = 0
        for fi in selected:
            if not fi.content:
                continue
            remaining = MULTI_FILE_BUDGET - total
            if remaining <= 0:
                break
            chunk = fi.content[:remaining]
            parts.append(f"=== {fi.name} ===\n{chunk}")
            total += len(chunk)
        return "\n\n".join(parts) if parts else "(파일 내용 없음)"
