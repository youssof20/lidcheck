# Experiment protocol

Registered 2026-10-31 before training. The initial audit establishes country plus Number as the Eyes-defy-anemia patient key. CP-AnemiC IMAGE_ID identifies a record; independent identity linkage is unavailable. Duplicate and near-duplicate records remain in the same split group.

## Hypotheses

- H1. Under simulated lighting shifts, models using in-photo normalization lose less AUROC than models using raw color.
- H2. Sclera-referenced normalization helps when sclera is visible and is not applicable to cropped images. Report where it cannot run.
- H3. Cross-dataset transfer lowers AUROC relative to within-dataset cross-validation. Quantify the drop.
- H4. Rejecting low-quality photos and abstaining on uncertain scores lowers the error rate on the photos that remain.
- H5. The synthetic stress test predicts real instability: feature drift across synthetic shifts correlates with feature drift across real lighting conditions in the volunteer study.

## Splits and metrics

Stratified patient-grouped five-fold cross-validation repeats ten times, with seed 20261031 plus the repetition. Three inner grouped folds choose L2 logistic regression C from 0.1, 1 and 10 by AUROC. Platt calibration uses inner out-of-fold scores. The screening threshold is the highest inner threshold reaching at least 90% sensitivity. An abstention half-width is chosen from 0, 0.05, 0.10 and 0.15 by inner error, subject to at least half of eligible photos being answered. Quality gates use only image measurements. Continuous thresholds fitted from distributions are fitted on outer training data only.

Report pooled repeated out-of-fold AUROC, AUPRC, sensitivity at 90% specificity, specificity at 90% sensitivity, Brier score and ten-bin expected calibration error. For confidence intervals, average repeat predictions per patient and draw 2,000 patient-cluster bootstrap resamples. This avoids treating repeated predictions as independent patients. Bootstrap intervals are percentile 95% intervals. Report coverage separately when a method is unavailable. Compare methods on the common eligible subset as well as their native coverage. Do not replace unavailable reference patches with gray-world values.

Use majority and demographics-only baselines. Demographics preprocessing is fitted inside each training fold. Age, sex and site are included when present. Do not pool child and adult accuracy. CP results are exploratory because patient identity and mirror provenance cannot be independently established.

## Shipping bar

A population model is validated-in-prototype only if its lower 95% out-of-fold AUROC bound is at least 0.70 and specificity at 90% sensitivity is at least 0.50. Otherwise show "Demo only, not validated". These criteria do not establish clinical validation. CP provenance prevents child population support even if numerical criteria pass. Reference detection is heuristic and cannot establish anatomical identity.

## Failure definition

Normalization did not help if normalized and raw AUROC confidence intervals overlap at every shift level. Report missing methods and rejected-photo fractions. Do not count a missing prediction as a correct answer.

## Lighting and transfer

Apply shifts in linear RGB to the complete photo before segmentation: temperatures 2700, 3500, 4500, 5500, 6500 and 7500 K at half and full strength; exposure 0.4, 0.6, 1, 1.4 and 2; mixed warm/cool horizontal lighting; sensor noise at 0.005, 0.015 and 0.03; JPEG quality 90 and 60; synthetic glare. Temperature gains are an RGB illuminant approximation, not a spectral camera simulation. Normalize gains to equal luminance. Train unshifted and augmentation models without exposing held-out patients to fitting. Evaluate each outer held-out group under each shift. Transfer fits source data only; target labels never select parameters.

## Labels and study

Use Eyes sex-specific adult thresholds (12 g/dL female, 13 male); report fixed 11 and 13 g/dL sensitivity analyses. Record minors separately if present. Retain CP historical 11 g/dL labels for replication; WHO 2024 uses 10.5 g/dL at 6-23 months. Report a secondary age-specific relabeling when ages are available.

The volunteer study has no hemoglobin labels. Report participant count, within-person score standard deviation, ICC with participant bootstrap intervals, quality rejection and synthetic/real feature drift correlation per method. Use two photos under each of six lighting conditions. Synthetic dummy records test software only and never count as study evidence.
