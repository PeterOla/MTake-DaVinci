# Component library and editable starters

Look for the **function** you need, e.g. “soft keyed cue with a long decay” or “one continuous pullback showing a missing connection.” Keep catalogue rows with the template's provenance and dimensions. Add your actual sets, performers, props, furniture, street pieces, documents, evidence graphics, typography, effects and sounds as you make films. The release includes the following redistributable starters.

Start with the [eight editable Halifax location and prop models](../assets/models/README.md) and [three original piano prints](../assets/sounds/README.md). The model gallery includes the same timber house in dark and light treatments. You can reproduce either directly from the GLB. The sound library includes the actual early tension build with its space between notes.

| Need | What you can use | Controls / proof |
| --- | --- | --- |
| A real mesh drawn in ink | [Blender starter](../scripts/blender_board.py) imports your licensed OBJ/glTF/GLB, renders neutral, on and off through one camera and saves an editable scene. | Editable source, studio view, camera, material and cavity treatment. Match the approved camera and restage the asset when placing it in production. An isolated import board only proves that the asset can be rendered. |
| Repeat an object through a shot | [Domino mesh builder](../examples/the-gap/make_tile.py) and [shot renderer](../scripts/tabletop.py). | One pivot, real faces and inlays, explicit world axes, continuous camera and a switch-off per instance. The source file survives import into another scene. |
| Light through a layered cloud | [components.py](../scripts/components.py) exports original steam overlays. | Set origin, pixel radius, depth, warm palette, time from 0 to 1 and deterministic seed. Compare early, middle and late frames. Allow the foreground to mask parts of the glowing rear layer. |
| Motion strokes around a fast subject | The same module's motion_marks function. | Two attachment points on the silhouette, actual projected travel angle, dash length, weight, alternating upper/lower phase. Keep the streaks close to the form during a turn. |
| Score and effects | Original felt-note and air-rise generators, the [demo score and dry wood contacts](../scripts/demo.py), and separated voice/music/effects WAVs produced by the demo. | Change pitch, duration, decay, placement, pan or level. Use the source in a new project, choose a fitting instrument, and keep clean stem prints for review. |
| Captions and evidence | [Typeface and licence](../CREDITS.md), [picture caption placement](../scripts/tabletop.py) and a generated SRT. | Set type size from phone pixels, check the full phrase and any highlighted word over the actual picture. |
| Reusable records | [Film plan and continuity](../templates/production.md) and [portable edit specification](../templates/project.json). | Clone for each new film. Keep its source pictures and authorisations beside that film. |

From the repository root, here is an actual Blender artwork handoff:

~~~sh
blender -b --python-exit-code 1 -P skills/mtake-davinci/scripts/blender_board.py -- skills/mtake-davinci/examples/the-gap/domino.obj build/blender-board
python skills/mtake-davinci/scripts/components.py build/component-samples
~~~

On Windows, if Blender is installed outside PATH, run its full executable path in PowerShell with the call operator (&). The default three-quarter framing is an asset audition. Once a mesh is inside the film, re-render enabled/disabled through the production camera, including surrounding geometry and shadows. Preserve the camera and all other subjects when disabling the registered hero at its source.
