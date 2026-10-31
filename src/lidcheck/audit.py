import hashlib
import io
import zipfile

import numpy as np
import pandas as pd
from PIL import Image
from scipy.fft import dctn

from lidcheck.io import ROOT, archive_checksums, archive_document, load_data, write_json


def run() -> pd.DataFrame:
    df = load_data()
    rows = []
    hashes = []
    for _, row in df.iterrows():
        with zipfile.ZipFile(ROOT / "data" / row.archive) as z:
            raw = z.read(row.image)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        small = np.asarray(im.resize((32, 32)).convert("L"), dtype=float)
        coeff = dctn(small, norm="ortho")[:8, :8].ravel()[1:]
        bits = coeff > np.median(coeff)
        hashes.append(bits)
        rows.append(
            dict(
                dataset=row.dataset,
                patient=row.patient,
                width=im.width,
                height=im.height,
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        )
    detail = pd.DataFrame(rows)
    df = df.merge(detail, on=["dataset", "patient"], validate="one_to_one")
    parent = list(range(len(df)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    pairs = []
    digests = df.sha256.to_numpy()
    hash_array = np.array(hashes)
    for i in range(len(df)):
        distances = np.count_nonzero(hash_array[:i] != hash_array[i], axis=1)
        for j in range(i):
            distance = int(distances[j])
            if digests[i] == digests[j] or distance <= 4:
                parent[find(i)] = find(j)
                pairs.append(dict(first=i, second=j, distance=distance))
    df["group"] = [f"cluster-{find(i)}" for i in range(len(df))]
    interim = ROOT / "data/interim"
    interim.mkdir(parents=True, exist_ok=True)
    df.to_csv(interim / "index.csv", index=False)
    pd.DataFrame(pairs).to_csv(interim / "duplicate_pairs.csv", index=False)
    summary = []
    for name, part in df.groupby("dataset"):
        summary.append(
            dict(
                dataset=name,
                images=len(part),
                patients=part.patient.nunique(),
                groups=part.group.nunique(),
                missing_hb=int(part.hb.isna().sum()),
                positive=int(part.label.sum()),
                negative=int((part.label == 0).sum()),
                hb_min=float(part.hb.min()),
                hb_median=float(part.hb.median()),
                hb_max=float(part.hb.max()),
                dimensions="; ".join(
                    sorted(set(f"{r.width}x{r.height}" for r in part.itertuples()))
                ),
                exact_duplicates=int(part.sha256.duplicated().sum()),
                near_duplicate_links=sum(df.iloc[p["first"]].dataset == name for p in pairs),
                masks=int((part["mask"] != "").sum()),
                reference_visibility="sampled images: sclera and skin visible"
                if name == "eyes"
                else "sampled images: conjunctiva on black; no reference region",
                patient_key="country + Number"
                if name == "eyes"
                else "IMAGE_ID; one image per record, identity unverified",
            )
        )
    table = pd.DataFrame(summary)
    (ROOT / "results/tables").mkdir(parents=True, exist_ok=True)
    table.to_csv(ROOT / "results/tables/data_audit.csv", index=False)
    write_json(ROOT / "results/checksums.json", archive_checksums())
    (interim / "archive_document.txt").write_text(archive_document(), encoding="utf-8")
    from lidcheck.plotting import audit_figure

    audit_figure(df)
    print(table.to_string(index=False))
    return df
