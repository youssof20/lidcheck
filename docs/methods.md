# Methods

## Data and splits

`io.py` reads the supplied archives directly. `audit.py` joins the country and Number key for Eyes and the IMAGE_ID key for CP. It reports missing labels, dimensions and exact duplicate counts. A perceptual hash uses the low-frequency DCT of a grayscale thumbnail. Exact matches or Hamming distance at most four form connected split groups. All members remain in the same fold. The private index records group membership; only aggregate audit outputs are committed. CP groups are a conservative image-based proxy for patient identity.

`models.py` uses a standard scaler fitted on each training partition and L2 logistic regression. Inner grouped folds select regularization, fit a sigmoid calibration to held-out base-model scores, and choose the screening threshold and abstention band. `benchmark.py` repeats outer grouped splits as specified in the registered protocol. Mean repeated predictions produce the reported cluster-bootstrap point estimate and intervals. Pooled repeated prediction metrics are also saved separately. Calibration and threshold selection use inner data only; outer labels are never used for fitting. The inner score used to fit the calibration sigmoid also selects its threshold; an additional calibration-selection nesting level is not used.

Baseline comparisons include training-fold prevalence, demographics-only logistic regression with age/sex/site, and fixed-configuration gradient boosting. The prevalence baseline uses probabilities, so its pooled AUROC need not be exactly one half. Secondary Ridge hemoglobin regression and alternate label thresholds are in `label_sensitivity.csv`. No hemoglobin estimate is exported to the app.

## Shared image measurements

Python and TypeScript use the same nearest-neighbor square grid. The long-side preview is limited in the browser before sampling. JPEG decoding and browser color management may differ; exact parity is asserted on shared RGB inputs, not on every browser codec. EXIF orientation is applied before sampling. The model assumes sRGB.

The segmentation converts sRGB to linear RGB, then D65 CIELab. Candidate pixels have a* above 12 and L* between 20 and 90, excluding saturated white and very dark pixels. Square morphological opening and closing use a one-pixel radius and zero padding. Four-connected labeling retains the first largest component on ties. Hand masks do not supply features. They measure Dice and IoU after alignment to the same grid. Color and shape rules do not guarantee anatomical correctness.

Quality measures are ROI fraction, largest-component cohesion, luminance Laplacian variance within the ROI, clipped-pixel fraction within the ROI, and whole-photo glare fraction. Whole-photo glare counts highlights excluded by segmentation, preventing the mask from hiding them. Fixed conservative thresholds are stored in `configs/default.yaml` and the exported manifest. The audit distributions were inspected and the conservative thresholds retained; no outcome-driven threshold search was performed. They reject extreme failures but do not detect every low-overlap mask. `quality.csv` reports each failed check separately; failures can overlap. The registered performance evaluation includes all finite feature vectors and separately reports gated risk-coverage.

## Normalization and features

All transformations operate in linear RGB before computing color summaries. None means no channel normalization, not omission of the sRGB transfer function. Chromaticity divides by the channel sum. Gray-world divides by whole-photo channel means while retaining mean intensity. White-patch divides by each channel's high percentile. Sclera divides by a median bright, near-neutral candidate patch. Skin divides by a median warm-colored border candidate patch. Reference methods return unavailable when too few candidate pixels exist; they never silently fall back. CP reference methods are disabled because sampled images are presegmented crops. Skin candidates may be absent on Eyes despite surrounding tissue being visible.

| Feature | Reason |
|---|---|
| Median L* and L* interquartile range | Overall lightness and within-mask variation |
| Median a* and a* interquartile range | Red-green color and variation |
| Median b* and b* interquartile range | Yellow-blue color and variation |
| Median linear red/green | Relative red intensity |
| Median log red/green | Erythema-style color contrast |
| Median saturation and saturation interquartile range | Color strength and variation |

`tests/parity/` contains generated RGB arrays with expected masks, quality, normalized pixels and features. Masks match exactly; features use the tolerance fixed in the brief. Dark, structured-eye and random-texture cases exercise empty and fragmented regions. Export tests check that scaler, logistic weights and sigmoid calibration reproduce Python probabilities.

## Stress and uncertainty

`stress.py` shifts the whole analysis image before segmentation. Temperature is an approximate RGB illuminant gain normalized to equal luminance. It is not a physical spectral rendering model. Fixed seeded noise, JPEG recompression, mixed lighting, exposure and glare share the same altered input across methods. Augmentation adds warm, cool and exposure variants of training patients only. Their group identifiers remain unchanged in inner fitting. Unshifted and augmented models are tested on outer held-out patients. Each shift reports available predictions, patient-cluster AUROC intervals and gate rejection. Methods with different availability require the common-subset results and coverage tables, not an unconditional ranking.

The quality gate and inner-selected probability band define abstention. Risk-coverage curves sweep bands on held-out predictions descriptively; this sweep does not tune the app. The app's visible score interval spans the final model and models from the first outer repetition. It visualizes model disagreement and is not a patient-specific clinical confidence interval. Training density bands are descriptive fitted-score histograms and are labeled as training data.

## Volunteer analysis

The browser study mode exports no photos and renders no health result. Each available normalization has a fitted research score and feature vector. A fixed set of exposure and equal-luminance warm/cool gains produces per-photo synthetic feature drift. This small study perturbation set differs from the full benchmark stress grid and is recorded in `study.ts`. Drift is the root mean square displacement in the shared feature coordinates; features have different units, so comparisons are within a normalization method.

`consistency.py` excludes synthetic records, detects duplicate participant/condition/shot keys, and uses complete condition means with both shots for the absolute-agreement ICC(A,1). It reports participant-bootstrap intervals, within-person score variability, quality rejection, and Spearman correlation of synthetic and real feature drift. Missing references remain missing. Synthetic dummy records test the analysis in a temporary directory and never enter the published study results.

## Privacy and deployment

The Vite build embeds the model and English strings in local JavaScript. Source Sans 3 is self-hosted with its OFL license. The production CSP forbids network connections. Photo decoding uses a canvas without persistent storage. Camera tracks stop on capture, cancellation and page exit. Study downloads use a Blob URL revoked after activation. The native camera may retain its own photo, which the app cannot delete. Playwright blocks all requests after load and completes a synthetic check and clinician-summary flow; CI repeats that test without the datasets.
