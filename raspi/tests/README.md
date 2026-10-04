# Raspi tests

This folder uses `unittest`.

Install `pip install -r requirements-test.txt` for the focused test dependencies,
or install those alongside the engine requirements. API tests use temporary
settings and mocked discovery; they do not pair devices or contact Home Assistant.

Run the suite from the `raspi` directory:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Test files should stay focused on one behavior area each, and shared test setup should go in `tests/__init__.py` instead of being duplicated in every file.
