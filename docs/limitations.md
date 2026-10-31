# Limitations

Eyes-defy-anemia photographs were acquired with controlled lighting and an attachment. The exported model was evaluated on those images, not on ordinary handheld phone photos. Passing the numerical prototype bar does not establish clinical validation.

Children and adults are separate populations. CP-AnemiC is a user-supplied Kaggle mirror of a removed Mendeley release. The reported mirror license does not establish original consent or relicensing authority. IMAGE_ID identifies records but cannot prove that different records belong to different people. Exact and perceptual matching reduces known duplication leakage; it cannot exclude all repeated patients. Duplicate groups can contain conflicting labels. This limits every CP and cross-dataset result.

Reference detection uses color and position, not anatomical ground truth. Scleral pigmentation, skin pigmentation, contact lenses, inflammation, phone processing and unusual white balance can change measurements. A user must confirm the detected eyelid region. The quality gate does not reliably detect every wrong region.

Repeated cross-validation reuses the same small cohorts. Intervals describe patient sampling conditional on the fitted procedure. They do not include the full uncertainty of moving to another camera or clinical population. The displayed interval is a spread of fold-model scores, not a confidence interval for a person's health.

Synthetic illuminant changes approximate RGB gains; they do not simulate camera spectral sensitivity or every automatic white-balance algorithm. Perturbations are applied to the fixed analysis grid, which changes the interpretation of sensor noise and JPEG artifacts compared with full-resolution camera capture. Raw color means unnormalized color converted to linear RGB for shared feature calculations.

Heuristic skin references may be unavailable even when skin is physically present. Coverage and performance must be read together. Neither rejected photos nor missing reference patches count as correct predictions. No hemoglobin estimate is displayed to users.

No real volunteer study has been collected during the build. Dummy records validate the analysis software only. The planned study has no hemoglobin labels and cannot estimate diagnostic accuracy. Check the hackathon committee's ethics-review requirements before recruitment.

The app cannot erase images retained by the native camera or a cloud photo backup. Browser memory is cleared on retake; this is not a forensic secure-erasure guarantee. The app makes no processing network requests after its static assets load.
