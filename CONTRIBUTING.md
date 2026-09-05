# Contributing

Contributions should preserve these invariants:

- no automatic trade or transfer;
- no broker credential handling;
- no leverage, short-selling or derivative recommendation path;
- no specific-security recommendation in the reference core;
- scenario numbers remain labelled as assumptions;
- tests and documentation are updated with every model change.

Run:

```bash
PYTHONPATH=src python -m pytest -q
python tools/static_audit.py
python formal/bounded_model_check.py
```
