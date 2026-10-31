# Lighting consistency capture protocol

Check with the hackathon committee whether ethics review applies before recruiting anyone. Use adult volunteers who can give written consent. Do not collect hemoglobin labels or give health results. The study evaluates repeated-photo stability only.

Open the app with `#study`. Obtain signed consent before photography. Store consent separately from anonymous measurements. Assign a code with no name or contact details. Record the phone model. Take two photos for each condition: window daylight, open shade, warm bulb (about 2700 K), cool LED (5000-6500 K), dim room, and mixed window plus lamp. These temperatures describe intended lighting; without a meter they are estimates.

Use automatic camera settings, flash off, with the phone 10-15 cm away. Ask the volunteer to look up and gently pull down the lower lid. Stop if the eye feels sore. Keep the same eye, phone and distance throughout. Check that the marked region covers the inner eyelid before saving measurements. Keep rejected photos' quality measurements so rejection is counted.

Download the JSON after the session. It contains anonymous feature vectors, quality measurements, model scores, condition, shot and phone model. It contains no image. Do not use the synthetic example as a volunteer record. The analysis excludes records marked synthetic. Delete source photos from the camera roll, recently deleted folder and any synchronized copies after extraction; the browser cannot delete photos saved by the camera application. The app retains photos only in memory while processing.

Run `uv run lidcheck consistency --study data/study.json`. Participant-condition means require both shots for the complete-case ICC analysis. Preserve missing conditions as missing. Report the number excluded from complete-case analysis. Do not call stability accuracy. H5 requires matched synthetic and real feature drift for the same volunteers.
