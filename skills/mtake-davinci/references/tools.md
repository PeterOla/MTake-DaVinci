# Use the toolkit on your own film

Commands below use “mtake.py” as shorthand for “python /path/to/the/installed/skill/scripts/mtake.py”. For setup and complete Windows and macOS/Linux commands see [setup](setup.md).

1. Run **mtake.py new my-film**. Edit production.md and project.json in that folder. Plan and approve the camera before detailed modelling. Each output folder is separate from the installed skill.
2. Render silent constant-frame-rate H.264 MP4 shots from Blender or your editor. Use the project's even pixel dimensions and integer fps for every shot. Place them in shots/. In project.json set title, size, fps and ordered shots, e.g. [{"clip":"shots/opening.mp4","frames":150}]. A five-second shot is 150 frames at 30 fps. The simple assembler accepts MP4 sources carrying a frame count. In a full editing suite export the combined cut there and use review on it directly.
3. List every important model in subjects with id, kind "model", reference (real photo), rights, read (what establishes likeness), model, neutral, on, off, roi and min_changed. Use project-relative file paths. roi is [left, top, right, bottom] as fractions of the frame; min_changed is the visible fraction expected to change inside that box when only this subject is hidden. Use a matched render with a fixed camera, seed and backdrop. At least 90% of all materially changed pixels should fall inside the chosen region including its contact shadow. For an evidence graphic use kind "graphic", reference, rights, read, source (editable page, map, data or original media) and on. Review its appearance manually. Use **mtake.py art my-film** before animating.
4. Set stems.voice, stems.music and stems.effects to three 48 kHz stereo PCM WAVs, pre-balanced, printed from zero to picture end. An intentionally unused stem can be silence. Place UTF-8 SRT at the captions path or use null for an explicitly captionless deliverable. Burned-in captions are authored in the source pictures; the assembler also muxes a selectable track. Disable selectable captions on players that display them over already burned-in text.
5. List effect cues with name, frame and end (exclusive). Count event starts separately from continuing tails. Add accents for story-critical drops. Each needs name, frame, speech_free as [start,exclusive_end], floor_dbfs and rise_ratio keyed by music and effects. Measure thresholds against the actual score, then check visually. A music floor of −28 dBFS and an attack ratio of 1.3 suit the supplied dry example; dense sustained music needs different criteria or an isolated accent print and a manual waveform comparison. Optionally add roi, min_picture_change and pixel_step at a visible onset. A moving camera can also produce a pixel change. Confirm the actual cause by watching.
6. **mtake.py assemble my-film my-film/cut-v1.mp4** sums the stems at unity, checks lengths/headroom, concatenates the declared shots and writes an H.264/AAC stereo movie. It refuses to overwrite a previous master. Run **mtake.py review my-film my-film/cut-v1.mp4 --report my-film/review/v1.json**. A nonzero exit reports a detected failure. Project and candidate should describe the same cut. An arbitrary video alone cannot establish how many effects were in an editable mix.
7. Read the per-ten-second measured RMS dBFS, including the final partial window, and effect-onset counts. For delivery loudness run an EBU R128/true-peak analysis on the encoded file as well. The RMS table doesn't measure integrated LUFS. Compare the export fingerprint, print phone mono, and screen for first-watch comprehension.

~~~sh
ffmpeg -hide_banner -i cut-v1.mp4 -map 0:a:0 -af ebur128=peak=true -f null -
ffmpeg -i cut-v1.mp4 -vn -af "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=180,lowpass=f=6500" phone-listen.wav
~~~

The sample's generated project.json is a filled, working specification. All times are zero-based display frames. @ 30 fps, a marked contact on frame 58 begins at 1.9333 seconds. The measurement checks the before/on-frame difference and a speech-free interval; it cannot authenticate subjective likeness, presence, or the story. Keep a written screening note beside the technical report.

## Register the source before the cut exists

At camera planning, add a scene object like the following to scenes. The subject name identifies one specific appearance. Keep the approval as a real production decision. For related scenes with different views of the same model, give the appearances separate ids and point them to the same editable source.

~~~json
{"id":"bench","camera_sheet":"art/camera.svg","subjects":["standing tile"],
 "approval":{"by":"Example author","basis":"Teaching fixture; approved continuous pull to the gap."}}
~~~

After entering the matching subjects and inspecting their photo, neutral view and final linework, run **mtake.py art my-film** and **mtake.py lock-art my-film --reviewer "Artist name"**. This works before any shot is rendered. Add materials, external textures and the production drawing script to the subject's optional dependencies array. The lock records fingerprints for these files and the camera sheet.

At edit time, each shot refers to its scene. For every planned subject include a checkpoint at the frame shown by its production on/off evidence. Frame numbers here are local to the shot, counted from zero:

~~~json
{"clip":"shots/opening.mp4","frames":150,"scene":"bench",
 "art_frames":[{"subject":"standing tile","frame":102}]}
~~~

The default assembler refuses a stale or absent art lock and checks the **actual encoded frame** against the reference on pixels where that subject disappears. Review repeats the comparison. A missing subject, changed mesh, swapped drawing or wrong camera frame now has a test. If you deliberately change the shot, capture matched proof again, inspect it and renew the lock. It records a review decision; it cannot certify who personally authored an object.
