from __future__ import annotations

import hashlib
import io
import json
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import numpy as np
import pandas as pd
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_data() -> pd.DataFrame:
    records = []
    for archive, dataset in [("dataset anemia.zip", "eyes"), ("cp-anemic.zip", "cp")]:
        path = ROOT / "data" / archive
        if not path.exists():
            raise FileNotFoundError(f"Place {archive} in data/")
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if not n.startswith("__MACOSX")]
            if dataset == "eyes":
                for country in ["India", "Italy"]:
                    sheet = next(n for n in names if n.endswith(f"{country}.xlsx"))
                    frame = pd.read_excel(io.BytesIO(z.read(sheet)))
                    for _, row in frame.iterrows():
                        if pd.isna(row.get("Number")):
                            continue
                        number = int(row.Number)
                        prefix = f"dataset anemia/{country}/{number}/"
                        photos = [n for n in names if n.startswith(prefix) and n.endswith(".jpg")]
                        if len(photos) != 1:
                            raise ValueError(f"Ambiguous patient mapping: {prefix}")
                        masks = [n for n in names if n.startswith(prefix) and n.endswith(".png")]
                        mask = next((n for n in masks if n.endswith("_forniceal_palpebral.png")),
                                    next((n for n in masks if n.endswith("_palpebral.png")), ""))
                        hb = pd.to_numeric(str(row.Hgb).replace(",", "."), errors="coerce")
                        sex = str(row.Gender).strip().upper()
                        threshold = 13.0 if sex == "M" else 12.0
                        records.append(dict(dataset=dataset, patient=f"{country}-{number}",
                                            site=country, archive=archive, image=photos[0], mask=mask,
                                            hb=hb, age=row.Age, sex=sex, threshold=threshold))
            else:
                sheet = next(n for n in names if n.endswith(".xlsx"))
                frame = pd.read_excel(io.BytesIO(z.read(sheet)))
                for _, row in frame.iterrows():
                    key = str(row.IMAGE_ID).strip()
                    photos = [n for n in names if Path(n).stem == key and n.endswith(".png")]
                    if len(photos) != 1:
                        raise ValueError(f"Ambiguous CP image mapping: {key}")
                    records.append(dict(dataset=dataset, patient=key, site=row.HOSPITAL,
                                        archive=archive, image=photos[0], mask="", hb=row.HB_LEVEL,
                                        age=row["Age(Months)"], sex=str(row.GENDER)[0].upper(),
                                        threshold=11.0))
    df = pd.DataFrame(records)
    df["label"] = np.where(df.hb.notna(), (df.hb < df.threshold).astype(int), np.nan)
    return df


def read_image(row: pd.Series, size: int = 96, mask: bool = False) -> np.ndarray:
    with zipfile.ZipFile(ROOT / "data" / row.archive) as z:
        raw = z.read(row["mask" if mask else "image"])
        if raw.startswith(b"\x89PNG"):
            # Some supplied masks have invalid iCCP checksums; retain image-data CRC checks.
            chunks, pos = [raw[:8]], 8
            while pos < len(raw):
                length = struct.unpack(">I", raw[pos:pos + 4])[0]
                chunk = raw[pos:pos + length + 12]
                if raw[pos + 4:pos + 8] != b"iCCP":
                    chunks.append(chunk)
                pos += length + 12
            raw = b"".join(chunks)
        with Image.open(io.BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            pixels = np.asarray(im)
    h, w = pixels.shape[:2]
    ys = np.minimum((np.arange(size) * h / size).astype(int), h - 1)
    xs = np.minimum((np.arange(size) * w / size).astype(int), w - 1)
    return pixels[ys[:, None], xs[None, :]]


def archive_checksums() -> dict:
    return {p.name: hashlib.file_digest(p.open("rb"), "sha256").hexdigest()
            for p in sorted((ROOT / "data").glob("*.zip"))}


def archive_document() -> str:
    with zipfile.ZipFile(ROOT / "data/dataset anemia.zip") as z:
        doc = z.read("dataset anemia/Dataset anemia.docx")
    with zipfile.ZipFile(io.BytesIO(doc)) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return "\n".join("".join(p.itertext()) for p in root.findall(".//w:p", ns))
