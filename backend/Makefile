.PHONY: test test-unit test-cov install run clean

install:
	pip install -r requirements.txt

test:
	python -m pytest test_reminders.py

test-unit:
	python -m pytest test_reminders.py -v

test-cov:
	python -m pytest test_reminders.py --cov=icloud_service --cov-report=html --cov-report=term

run:
	python icloud_service.py

clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -type f -name '*.pyc' -delete
