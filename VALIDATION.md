# What was exercised for v0.1.0

- Installed the skill outside the source tree and built the nine-second vertical example from its own packaged assets. The production record links to the output camera sheet, photo, model, generator, review board, captions, cut and export measurements.
- Imported the sample OBJ and its MTL into Blender in background mode and generated the neutral, ink, disabled and editable .blend outputs. The tabletop renderer reads the same original OBJ; the final cut is an orthographic projection with original score, two speech takes and contact sounds.
- An additional two-shot project goes through the generic assembler. The test checks its actual 20 fps edit boundary, visible subject, stereo stems, captions and per-window effect count.
- Negative controls remove the subject's visible pixels, move the comparison box, substitute a blank encoded shot, change the model after approval, omit a delivery checkpoint, mute music, delay an effect by one frame and place speech on the accent. The corresponding checks must fail. The physics fixture checks that each toppling tile first reaches its neighbour, and that the final gap is too long to cross.
- An independent agent took a different premise to a [35-second camera plan](skills/mtake-davinci/examples/reflector/README.md). Its first run exposed the premature shot-list requirement and broken links in the generated production record. Both were corrected before publication.

To repeat the automated checks from the repo root:

~~~sh
python -m unittest discover -s tests -v
python skills/mtake-davinci/scripts/mtake.py demo build/independent-run
python skills/mtake-davinci/scripts/mtake.py review build/independent-run build/independent-run/the-gap.mp4
~~~

Release checks were exercised on Windows with Python 3.12 and FFmpeg 6.0. The optional Blender transfer was checked in Blender 5.3. macOS and Linux commands are provided; native runs on those systems have not been recorded for this release. The checks verify specified facts about files, frames and audio. A director and a first-time viewer still decide whether the story reads.
