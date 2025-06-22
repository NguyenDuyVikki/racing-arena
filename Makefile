# Racing Arena Makefile

.PHONY: help server client test test-client clean install dev-install

help:
	@echo "Racing Arena - Available commands:"
	@echo "  make server      - Start the Racing Arena server"
	@echo "  make client      - Start a Racing Arena client"
	@echo "  make test        - Run unit tests"
	@echo "  make test-client - Run automated test clients"
	@echo "  make install     - Install the package"
	@echo "  make dev-install - Install in development mode"
	@echo "  make clean       - Clean up generated files"

server:
	@echo "Starting Racing Arena Server..."
	python race.py server

client:
	@echo "Starting Racing Arena Client..."
	python race.py

test:
	@echo "Running unit tests..."
	python tests/test_game.py

test-client:
	@echo "Running automated test clients..."
	@echo "Make sure the server is running first!"
	python tests/test_client.py

install:
	@echo "Installing Racing Arena..."
	pip install .

dev-install:
	@echo "Installing Racing Arena in development mode..."
	pip install -e .

clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
