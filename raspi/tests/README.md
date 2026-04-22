# Raspi tests

This folder uses `unittest`.

Run the suite from the `raspi` directory:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Test files should stay focused on one behavior area each, and shared test setup should go in `tests/__init__.py` instead of being duplicated in every file.
