.PHONY: serve test audit

# Start the mock client API on http://127.0.0.1:8099
serve:
	python -m uvicorn mock_api.server:app --host 127.0.0.1 --port 8099 --reload

# Run the acceptance suite (offline; add RUN_AI_TESTS=1 for the live test)
test:
	python -m pytest -q

# Peek at the side effects your skill has produced against a running server
audit:
	@curl -s http://127.0.0.1:8099/_audit | python -m json.tool
