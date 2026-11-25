# Vault Wars

CS246/346 Artificial Intelligence group project at AUA. Five AI brains run rival banks on the real road network of central Yerevan, and we compare how they do.

See `CLAUDE.md` for the rules and decisions, and `STEPS.md` for build progress.

## Setup

You need Python 3.12. Clone the repo outside OneDrive (we use `C:\dev\vault-wars`) and create the virtual environment outside OneDrive too, for example in `C:\venvs\vault-wars` on Windows.

Windows (PowerShell):

```
py -3.12 -m venv C:\venvs\vault-wars
C:\venvs\vault-wars\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

macOS or Linux:

```
python3.12 -m venv ~/venvs/vault-wars
source ~/venvs/vault-wars/bin/activate
pip install -r requirements.txt
pytest
```

## Folders

* `engine/` game rules and simulation
* `brains/` one file per brain
* `experiments/` batch runner and statistics
* `app/` replay viewer and dashboard
* `data/` cached maps and layouts (committed)
* `docs/` assignment and deliverables
* `tests/` unit tests

Map data from OpenStreetMap contributors.
