"""Shared FAKE helpers for the tests. Nothing here is real PPS content."""

import re
import zlib


def make_pdf(pages: list[list[str]]) -> bytes:
    """Build a tiny valid PDF (one list of text lines per page) by hand,
    so tests do not need any PDF-writing library."""
    n = len(pages)
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n))
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for i, lines in enumerate(pages):
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {5 + 2 * i} 0 R /Resources << /Font << /F1 3 0 R >> >> >>"
            ).encode()
        )
        ops = ["BT", "/F1 12 Tf", "14 TL", "72 720 Td"]
        for line in lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops += [f"({escaped}) Tj", "T*"]
        ops.append("ET")
        stream = "\n".join(ops).encode("latin-1")
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_start = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode() + b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF\n"
    ).encode()
    return bytes(out)


class HashingEmbedder:
    """A tiny FAKE embedder for tests (no model download, instant).

    It hashes each word into one of ``dimension`` slots, so texts that share
    words get similar vectors. Good enough to test plumbing and ranking;
    it is NOT a real semantic model.
    """

    def __init__(self, dimension: int = 64) -> None:
        self._dimension = dimension
        self.query_calls = 0

    @property
    def dimension(self) -> int:
        return self._dimension

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimension
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            vector[zlib.crc32(word.encode()) % self._dimension] += 1.0
        norm = sum(v * v for v in vector) ** 0.5 or 1.0
        return [v / norm for v in vector]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        self.query_calls += 1
        return self._embed(query)
