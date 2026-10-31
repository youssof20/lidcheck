# Data

Keep the two supplied archives in this directory. The loader reads archives directly; it does not extract photos to a public folder.

| Dataset | Archive | Source | Terms |
|---|---|---|---|
| Eyes-defy-anemia | `dataset anemia.zip` | https://ieee-dataport.org/documents/eyes-defy-anemia, DOI 10.21227/t5s2-4j73 | The supplied document provides the data free and requests the citations below. The live DataPort page could not be read by the verifier. No photo redistribution. |
| CP-AnemiC mirror | `cp-anemic.zip` | https://www.kaggle.com/datasets/karankumar4090/cp-anemic-dataset-same | User reports Apache 2.0 on Kaggle. Original Mendeley release https://data.mendeley.com/datasets/m53vz6b7fx/1 was removed at the author's request. Original academic-use terms and mirror relicensing authority are unverified. Local exploratory research only; no redistribution. |

`uv run python scripts/verify_data.py` prints archive checksums and checks mappings. Recorded hashes are in `results/checksums.json`. `uv run lidcheck audit` writes aggregate counts and the hemoglobin histogram. Row-level labels, duplicate links and intermediate features stay in ignored `data/interim/`.

Eyes keys are country plus the spreadsheet Number. The archive document explicitly maps folder names to Number. Decimal commas in the Italy Hgb column are parsed as decimal points; `_` is missing. Gender and age are present. Original JPEGs are distinct from hand-segmented PNGs. Masks with broken iCCP metadata are read after removing that color-profile chunk; image-data CRC checks remain enabled.

CP IMAGE_ID is an image-record key, not independently verified patient identity. Byte-identical and perceptually similar copies are joined into connected groups before splitting, including transitive matches. Perceptual distance is a candidate grouping rule, not evidence that two people are identical. The sampled CP images contain the segmented conjunctiva on black, without usable sclera or skin. The sampled Eyes images include sclera and surrounding skin. Reference-patch availability is measured separately by the heuristic. Do not infer that every bright neutral patch is sclera.

## Citation list supplied with Eyes-defy-anemia

The DataPort page was blocked to the verifier. This list is transcribed from `Dataset anemia.docx`, not represented as a verified copy of the current web page:

- R. Maglietta, M. E. Griseta, F. Clemente, A. Guarini, G. Dimauro, Advances in the Automated Diagnosis of Anemia: a shared Eyes-defy-anemia dataset and a novel non-invasive system with machine learning, under submission.
- G. Dimauro, D. Caivano, P. Di Pilato, A. Dipalma, M.G. Camporeale, A Systematic Mapping Study on Research in Anemia Assessment with Non-Invasive Devices. Appl. Sci. 2020, 10, 4804. DOI 10.3390/app10144804.
- G. Dimauro and L. Simone, Novel Biased Normalized Cuts Approach for the Automatic Segmentation of the Conjunctiva, Electronics 2020, 9, 997. DOI 10.3390/electronics9060997.

CP source paper: Appiahene et al., CP-AnemiC: A conjunctival pallor dataset and benchmark for anemia detection in children. Medicine in Novel Technology and Devices, DOI 10.1016/j.medntd.2023.100244.
