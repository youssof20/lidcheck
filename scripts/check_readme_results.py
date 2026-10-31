import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(summary: dict) -> str:
    lines = [
        "<!-- results:start -->",
        "",
        "Repeated grouped cross-validation. Intervals use patient-cluster bootstrap resampling.",
        "",
        "| Dataset / method | Images | AUROC (95% interval) | Specificity at 90% sensitivity |",
        "|---|---:|---:|---:|",
    ]
    for key, result in summary["benchmark"].items():
        if result["status"] != "evaluated":
            lines.append(f"| {key} | {result['n']} | {result['status']} | Not applicable |")
            continue
        auc = result["metrics"]["auroc"]
        spec = result["metrics"]["specificity_at_90_sensitivity"]
        lines.append(
            f"| {key} | {result['n']} | {auc['value']:.3f} ({auc['low']:.3f}-{auc['high']:.3f}) | {spec['value']:.3f} ({spec['low']:.3f}-{spec['high']:.3f}) |"
        )
    lines.extend(
        [
            "",
            f"Adult model: {summary['populations']['older']}. Child model: {summary['populations']['child']}.",
            "",
            "CP figures are exploratory: grouping is based on image-record keys and duplicate clusters, not independently verified patient identity.",
        ]
    )
    for row in summary["audit"]:
        lines.append(
            f"{row['dataset']}: {row['images']} images, {row['missing_hb']} missing hemoglobin labels, {row['exact_duplicates']} byte-identical duplicates beyond the first copy, {row['groups']} split groups."
        )
    seg = summary["segmentation"]
    lines.extend(
        [
            "",
            f"Segmentation: mean Dice {seg['mean_dice']:.3f}, mean IoU {seg['mean_iou']:.3f}, n={seg['n']}. The quality gate cannot identify every poor mask.",
            "",
        ]
    )
    for row in summary["baselines"]:
        if row["model"] == "demographics":
            image = summary["benchmark"][row["dataset"] + "/none"]["metrics"]["auroc"]["value"]
            lines.append(
                f"{row['dataset']} demographics-only AUROC is {row['auroc']:.3f}; raw-image AUROC is {image:.3f}. "
                + (
                    "Demographics match or exceed the image model."
                    if row["auroc"] >= image
                    else "The image model has a higher point estimate; this is not a test of superiority."
                )
            )
    for dataset, result in summary.get("stress", {}).items():
        lines.extend(
            [
                "",
                f"{dataset} raw-color stress AUROC ranges from {result['raw_min']:.3f} to {result['raw_max']:.3f}.",
            ]
        )
        failed = [r["method"] for r in result["comparisons"] if r["overlap_all"]]
        lines.append(
            "Normalization did not help by the registered overlap rule for: "
            + (", ".join(failed) if failed else "none of the evaluated methods")
            + ". Other methods require shift-specific interpretation; overlap is not an equivalence test."
        )
    lines.extend(
        [
            "",
            f"Volunteer study: {summary['study']['status']}; {summary['study']['participants']} participants. No stability or H5 result is claimed.",
            "",
            "![Grouped ROC](results/figures/roc_grouped_cv.png)",
            "",
            "ROC curves show raw-color held-out discrimination with cluster bootstrap bands. The table above contains AUROC intervals and operating-point metrics.",
            "",
            "![Calibration](results/figures/calibration.png)",
            "",
            "The reliability diagram compares observed labels with mean repeated held-out scores. The histogram shows where scores concentrate.",
        ]
    )
    for dataset in ["eyes", "cp"]:
        m = summary["benchmark"][dataset + "/none"]["metrics"]
        b = m["brier"]
        e = m["ece"]
        lines.append(
            f"{dataset}: Brier {b['value']:.3f} ({b['low']:.3f}-{b['high']:.3f}); ECE {e['value']:.3f} ({e['low']:.3f}-{e['high']:.3f})."
        )
    if "stress" in summary:
        lines.extend(
            [
                "",
                "![Lighting stress](results/figures/lighting_stress.png)",
                "",
                "The figure shows full-strength temperature and exposure shifts for models trained on unshifted photos. Half-strength casts, noise, JPEG, glare, mixed light and augmented-training results are in the stress table with intervals and rejection rates.",
            ]
        )
    lines.extend(
        [
            "",
            "![Risk and coverage](results/figures/risk_coverage.png)",
            "",
            "Error rate is plotted against the fraction of photos answered as the abstention band widens. This is a descriptive held-out curve; it does not select the deployed band.",
        ]
    )
    if "cross_dataset" in summary:
        lines.extend(
            [
                "",
                "![Cross-dataset transfer](results/figures/cross_dataset.png)",
                "",
                "The matrix compares raw-color transfer with within-dataset cross-validation. Population, acquisition and mirror provenance differ, so these are shift tests.",
            ]
        )
        for row in summary["cross_dataset"]:
            if row["method"] == "none" and row["status"] == "evaluated":
                lines.append(
                    f"{row['source']} to {row['target']}: AUROC {row['value']:.3f} ({row['low']:.3f}-{row['high']:.3f}), n={row['n']}."
                )
    lines.extend(["", "<!-- results:end -->"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary = json.loads((ROOT / "results/summary.json").read_text())
    path = ROOT / "README.md"
    original = path.read_text(encoding="utf-8")
    start = original.index("<!-- results:start -->")
    end = original.index("<!-- results:end -->") + len("<!-- results:end -->")
    updated = original[:start] + render(summary) + original[end:]
    if args.check:
        if updated != original:
            raise SystemExit("README results differ from results/summary.json")
    else:
        path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
