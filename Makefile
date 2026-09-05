.PHONY: test audit model-check demo browser-smoke

test:
	PYTHONPATH=src python -m pytest -q

audit:
	python tools/static_audit.py

model-check:
	python formal/bounded_model_check.py --output validation/BOUNDED_MODEL_CHECK_RECEIPT.json

demo:
	PYTHONPATH=src python -m dikwp_valueark demo --workspace .valueark-demo --reset

browser-smoke:
	python tools/browser_smoke.py
