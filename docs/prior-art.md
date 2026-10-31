# Prior work and source checks

Checked on 2026-10-31. A verified paper is not evidence that this implementation reproduces its findings.

| Work | Verified source | Scope |
|---|---|---|
| Patel, AnemiaVision | https://arxiv.org/abs/2604.22964 | Smartphone conjunctiva and nail photographs, EfficientNet-B3 and a web system. |
| Wemyss et al., 2023 | https://doi.org/10.1371/journal.pone.0281736 | Card-free conjunctiva, sclera and lip colorimetry in Ghana. |
| Wemyss et al., 2025 | https://doi.org/10.1088/1361-6579/adab4d | Smartphone eye colorimetry in pregnant women in India; limited specificity after transfer. |
| Mannino et al., 2018 | https://doi.org/10.1038/s41467-018-07262-2 | Fingernail color and metadata without external calibration equipment. |
| Collings et al., 2016 | https://doi.org/10.1371/journal.pone.0153286 | Conjunctival erythema index with an in-frame calibration card; validation differs from training. |
| Dimauro et al., 2023 | https://iris.cnr.it/retrieve/1ef6c36e-bf95-4cf4-8fcd-d18bcb3bbc7b/1-s2.0-S1746809422009430-main.pdf | Sclera and blood-vessel color, Biomedical Signal Processing and Control, article 104489. DOI 10.1016/j.bspc.2022.104489. |
| Appiahene et al., 2023 | https://opus.lib.uts.edu.au/handle/10453/177704 | CP-AnemiC dataset paper. DOI 10.1016/j.medntd.2023.100244. |
| Fuentes-Beingolea et al., 2025 | https://doi.org/10.3991/ijoe.v21i07.54439 | Conjunctival preprocessing on CP-AnemiC and Eyes-defy-anemia. |

AnemiaVision is the closest verified application lead in the brief. Lidcheck uses a small exported model and runs image processing in the browser. Its training data limitations and evaluation outputs are recorded here. Its scores are not directly comparable to AnemiaVision's private validation set.

Wemyss 2023 already used card-free reference regions. Lidcheck compares this method family against unnormalized color; it does not claim invention of sclera referencing.

Wemyss 2025 tested transfer to another population. That failure to retain specificity motivates separate populations and a transfer stress test here. This project does not reproduce its pregnancy cohort.

Mannino used nail photographs and camera metadata. Lidcheck evaluates lower-eyelid color, excludes EXIF metadata from inference, and does not estimate a clinical hemoglobin value.

Collings used a calibration card. Lidcheck asks what in-photo reference methods can achieve without one, while reporting synthetic lighting sensitivity.

Dimauro's work and the supplied archive document describe controlled illumination and scleral analysis. Lidcheck uses deterministic masks with overlap measurements against the provided segmentations. The acquired device images do not validate ordinary handheld capture.

Appiahene supplies the child-dataset method and provenance lead. The supplied mirror has duplicated files and unverified independent patient linkage. Lidcheck groups matching copies and labels CP results exploratory.

Fuentes-Beingolea evaluates preprocessing and learned classifiers. Lidcheck adds a shared Python/TypeScript implementation and tests corruption before segmentation. A claim that the paper omitted every kind of shift test has not been verified and is not made.

## Unverified leads

The brief's Dimauro 2018 IEEE Access citation lacks a title/DOI. Moreno 2024 iJOE, IJACSA 2026 volume 17(8), Zhang BPANet, and Singh 2025 transformer study remain unverified and are not used as evidence. The exact live DataPort citation list is unverified because automated access was blocked; `data/README.md` records the list in the supplied archive instead. The archive's Maglietta paper was marked under submission; final bibliographic metadata is unverified.

## Thresholds and sibling methods

WHO's current source is https://www.who.int/publications/i/item/9789240088542 and its guideline PDF https://iris.who.int/bitstream/handle/10665/376196/9789240088542-eng.pdf. It distinguishes ages 6-23 months from 24-59 months. CP's historical threshold is retained for replication, not described as current WHO policy.

The brief's Taylor/BiliCam lead remains unverified and is not used to justify this pipeline. A calibration-card jaundice method would not establish accuracy for eyelid pallor.
