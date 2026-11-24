# Install and check the software

If your agent already discovered this skill, installation is complete. Run Python against scripts/mtake.py in this directory and install dependencies from the adjacent requirements.txt. The installer and repository-root paths below apply to a downloaded checkout. You can keep the production project anywhere writable.

## What is required

| Job | Software | Check |
| --- | --- | --- |
| Run the example, assemble and measure new films | Python 3.11 or later, NumPy and Pillow; the requirements file includes tested-compatible version ranges. | python --version and the doctor command below |
| Encode picture, decode audio and inspect the actual MP4 | FFmpeg and ffprobe on PATH, with libx264, AAC and mov_text support | doctor reports the programs and encoder availability |
| Use the directing instructions | An agent that reads a SKILL.md directory, or a human reading the same Markdown. | Ask it to show the five discovery checks and to plan a shot before drawing. |

Python and FFmpeg are separate installations. On Windows use the Python installer or launcher (py -3.12 is an example) and an FFmpeg build that includes ffprobe. Put the build's bin folder on PATH and reopen the terminal. On macOS with Homebrew use “brew install python ffmpeg”. On Debian/Ubuntu use a system providing Python 3.11+ and “sudo apt install python3-venv ffmpeg”. Install Git or download the GitHub release ZIP to obtain the files. [Python](https://www.python.org/downloads/) · [FFmpeg downloads by platform](https://ffmpeg.org/download.html) · [Pillow installation](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html)

From the repository root on **Windows PowerShell**:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r skills/mtake-davinci/requirements.txt
.\.venv\Scripts\python.exe skills/mtake-davinci/scripts/mtake.py doctor
.\.venv\Scripts\python.exe skills/mtake-davinci/scripts/mtake.py demo build/the-gap
~~~

On **macOS or Linux**:

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/mtake-davinci/requirements.txt
.venv/bin/python skills/mtake-davinci/scripts/mtake.py doctor
.venv/bin/python skills/mtake-davinci/scripts/mtake.py demo build/the-gap
~~~

Install for the current user's agent with “python install.py” from the repo root, or “python install.py --project /path/to/film” for one project. This copies the complete skill to .agents/skills/mtake-davinci under the chosen scope. Use --dest with a different host's skills parent, for example ~/.codex/skills. Start a new agent session in the intended project and invoke $mtake-davinci. A host that ignores skills can read the same SKILL.md and run the same tools. On Windows substitute the Python launcher or the virtual-environment executable in any “python” example. [Codex skill directories](https://developers.openai.com/codex/skills/)

The skill can live in a read-only directory. Build each film in a separate writable folder. To update an installation, back up local edits, move the old skill aside, and rerun the installer from the desired release. The installer refuses to merge over an existing copy. The demo runs offline once the software is installed; the sample voice, source photograph, font and editable mesh ship with it.

## Production tools to choose for a new story

Use Blender for poseable humans, architecture, materials, real lenses, reusable sets and imported OBJ/glTF/FBX assets. Save the editable .blend plus external textures and record versions. A CPU is sufficient for the supplied example. Complex production renders benefit from a suitable GPU. Use an editor such as Kdenlive or a DAW such as Audacity for picture edits, takes, spotting and stem prints. A real microphone, an authorised voice artist or an optional local TTS engine provides new narration. Keep the generated/recorded voice out of the effects and music prints. Optional Pocket TTS and Piper have their own installation requirements, voices, language coverage and licences. Check the actual model before distributing a new voice. [Blender](https://www.blender.org/download/) · [Kdenlive](https://kdenlive.org/download/) · [Audacity](https://www.audacityteam.org/download/) · [Pocket TTS](https://github.com/kyutai-labs/pocket-tts) · [Piper](https://github.com/OHF-Voice/piper1-gpl)

If a command cannot find FFmpeg, run ffmpeg -version and ffprobe -version in the same shell. If the sample asks for Pillow or NumPy, call the executable inside the virtual environment where pip installed them. If a render folder already exists, choose a fresh folder name. If your editor exports variable frame rate or a different stem length, print a constant-frame-rate MP4 and full-length aligned WAVs before using the portable assembler.
