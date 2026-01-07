# policy

Python project scaffold.

## Development

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run training:

```bash
python src/policy/train.py
```
