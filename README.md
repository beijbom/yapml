# YetAnotherMachineLearningPlatform

An open-source full-stack Machine Learning Platform build on Modal.

## Developers

### Run once

* Install the `uv` python manager <https://docs.astral.sh/uv/getting-started/installation/>
* Create a modal account <https://modal.com/>
* Configure your modal account `uv run modal config`
* Add the `src/` folder to your PYTHONPATH. E.g. `export PYTHONPATH=path/to/this/repo/src`

### Run dev server

`uv run modal serve -m src.yamlp.yamlp`

### Deploy to prod

`uv run modal deploy -m src.yamlp.yamlp`

### Run tests

`uv run pytest`
