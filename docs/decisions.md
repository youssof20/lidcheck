# Decisions

- 2026-10-31: Exclude the supplied brief, archives, extracted photos and row-level patient data from Git because the brief requires it.
- 2026-10-31: Use country plus folder number for Eyes-defy-anemia because the archive document maps these to the spreadsheet Number field.
- 2026-10-31: Accept the user-supplied Kaggle CP-AnemiC mirror for exploratory research; the original Mendeley release was removed at the author's request and the mirror's reported Apache license does not establish original consent.
- 2026-10-31: Retain CP-AnemiC's historical threshold for replication and distinguish it from WHO 2024 age-specific thresholds.
- 2026-10-31: Use a fixed nearest-neighbor 96-pixel square analysis grid in both languages to avoid browser resampling differences; retain a larger preview for inspection.
- 2026-10-31: Do not publish patient photographs, including segmentation examples; report overlap distributions instead.
- 2026-10-31: Read labels from spreadsheets rather than assuming the Word document contains values; the document explicitly describes the mapping.
- 2026-10-31: Parse decimal commas in Italy Hgb values and exclude the documented missing value; numeric coercion alone would discard valid labels.
- 2026-10-31: Remove PNG iCCP metadata when loading masks because supplied color-profile checksums are broken; retain image-data validation.
- 2026-10-31: Retain conservative quality thresholds after reviewing measured distributions; they reject extreme corruption and do not claim to detect all segmentation failures.
- 2026-10-31: Treat CP patient identity as unverified and keep its model demo-only because record IDs and duplicate clustering cannot prove independent subjects.
- 2026-10-31: Export raw-color adult logistic regression as the primary model fixed by the vertical slice; normalization comparisons do not select the deployed model post hoc.
- 2026-10-31: Use aggregate Dice distributions because no patient image is permitted in the repository.
- 2026-10-31: Report the stronger adult demographics baseline openly because it limits the evidence that the photo contributes independent signal.
- 2026-10-31: Keep volunteer study status uncollected and exercise analysis using synthetic temporary fixtures because no consented study records were supplied.
- 2026-10-31: Omit the optional CNN, offline installation and Arabic stretch items until the required benchmark and app are complete.
- 2026-10-31: Make the repository public only after the user's explicit confirmation following the automatic approval block.
- 2026-10-31: The first app deployment follows the audit and trained vertical slice; the empty-repository deployment was delayed by private repository settings.
