test:
	python -m unittest discover -s tests -v

run:
	uvicorn gateway:app --host 0.0.0.0 --port 8080

bench:
	python benchmarks/evaluate.py
