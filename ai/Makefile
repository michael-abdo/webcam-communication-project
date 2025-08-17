.PHONY: install test lint train predict clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	flake8 src/
	black src/ --check

format:
	black src/
	isort src/

train-ft:
	python -m src.cli.train --detector f_t

train-dide:
	python -m src.cli.train --detector di_de

train-ensemble:
	python -m src.cli.train --detector ensemble

predict:
	python -m src.cli.predict --input $(INPUT)

setup-data:
	python scripts/download_data.py
	python scripts/validate_data.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/