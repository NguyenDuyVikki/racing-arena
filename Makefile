# Racing Arena Makefile

.PHONY: help server client clean install

help:
	@echo "Racing Arena - Available commands:"
	@echo "  make server      - Start the Racing Arena server"
	@echo "  make client      - Start a Racing Arena client"
	@echo "  make install     - Install the package"
	@echo "  make clean       - Clean up generated files"

server:
	@echo "Starting Racing Arena Server..."
	python main.py --mode server

client:
	@echo "Starting Racing Arena Client..."
	python main.py --mode client

install:
	@echo "Installing Racing Arena..."
	pip install .

clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
