# MTake DaVinci

An installable directing skill and production toolkit for original vertical illustrated films. Give an agent a story and it can plan what the audience discovers, build photo-grounded 3D linework, move a camera through one consistent set, direct narration around the score, and review the encoded film. The package includes the production method, editable templates and working picture and sound tools.

**[Watch The Gap, a nine-second example with sound](https://github.com/PeterOla/MTake-DaVinci/releases/download/v0.1.0/the-gap.mp4)** · **[See its real reference, neutral model and final drawing](skills/mtake-davinci/examples/the-gap/source-board.jpg)** · **[Read the skill](skills/mtake-davinci/SKILL.md)**

The download also includes [eight editable Halifax models in architectural linework](skills/mtake-davinci/assets/models/README.md) and [three original felt-piano cues from the production](skills/mtake-davinci/assets/sounds/README.md). Start with the existing house, roads, lamp, bed or steamship when one fits your new film.

## Install

Get Python 3.11+, Git and FFmpeg with ffprobe. Clone the repository, then install the skill in your agent's user skill directory:

~~~sh
git clone https://github.com/PeterOla/MTake-DaVinci.git
cd MTake-DaVinci
python install.py
~~~

On Windows, py -3.12 can replace python. Use “python install.py --project /path/to/your/film” for a project-only install. The installer copies the entire package, including its resources, and preserves any existing installation. Open a new agent session. For the Python environment, dependencies, platform-specific commands and optional Blender, editing and voice tools, follow [software setup](skills/mtake-davinci/references/setup.md).

**Try asking:** “Use $mtake-davinci to make a 45-second illustrated film about how a lighthouse lens turns a small lamp into a visible signal. Show me the story chain, the narration and the continuous camera sheet before drawing.”

## Make your first cut

From the repo root, with the Python environment from setup active:

~~~sh
python -m pip install -r skills/mtake-davinci/requirements.txt
python skills/mtake-davinci/scripts/mtake.py doctor
python skills/mtake-davinci/scripts/mtake.py demo build/the-gap
~~~

Open **build/the-gap/the-gap.mp4**. Inside the same folder are three separate stereo stems, a silent shot, SRT captions, the model, the photo and the measured export review. Once the dependencies are installed, this example runs offline, without an API key, GPU or voice-model download.

For your own project, run “python skills/mtake-davinci/scripts/mtake.py new my-film” and follow [make and check a different film](skills/mtake-davinci/references/tools.md). The new project carries agent instructions, a continuity record and an editable timeline. The skill guides an agent through research, direction and original artwork. The assembler takes the resulting shots, speech, music and effects.

A fresh agent used the same instructions for a second subject. See its [35-second bicycle-reflector plan and camera sheet](skills/mtake-davinci/examples/reflector/README.md) and [what the release checks caught](VALIDATION.md).

## What travels with the skill

| Production stage | Resources |
| --- | --- |
| Find the story, write and time narration | [Five storytelling decisions and measured pacing](skills/mtake-davinci/references/story.md) · [Production and continuity record](skills/mtake-davinci/templates/production.md) |
| Stage a camera move and build the world once | [Camera, locations and maps](skills/mtake-davinci/references/camera.md) · [Worked overhead movement sheet](skills/mtake-davinci/examples/the-gap/camera.svg) |
| Make recognisable editable artwork | [Reference-to-model workflow](skills/mtake-davinci/references/art.md) · [Reusable components](skills/mtake-davinci/references/components.md) |
| Direct motion, weight and consequences | [Motion and illustrated effects](skills/mtake-davinci/references/motion.md) · [Editable model and worked scene](skills/mtake-davinci/examples/the-gap/README.md) |
| Place the voice, captions, score and sound effects | [Narration around beat drops, SFX and stereo/mono review](skills/mtake-davinci/references/sound.md) |
| Study references, catch regressions and deliver | [Frame and sound study method](skills/mtake-davinci/references/study.md) · [Export review](skills/mtake-davinci/references/review.md) |

## Licence

Original toolkit material is released under [MIT](LICENSE). The reference photograph is public domain. The bundled font carries its own SIL Open Font License. The voice takes, font and photograph are documented in [credits and provenance](skills/mtake-davinci/CREDITS.md). Commercial music, game footage and private study films are not distributed.

For contributions, include the failure a proposed change addresses, a reproducible example and any asset credits. Run “python -m unittest discover -s tests” from the repository root in the prepared environment.
