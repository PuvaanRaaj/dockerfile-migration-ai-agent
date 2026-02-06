PYTHON ?= python3
VENV ?= .venv

.PHONY: setup agent agent-write agent-apply validate-knowledge

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

agent:
	./bin/agent --target "$(TARGET)" --task "$(TASK)" --mode propose

agent-write:
	./bin/agent --target "$(TARGET)" --task "$(TASK)" --mode propose --write

agent-apply:
	./bin/agent --target "$(TARGET)" --task "$(TASK)" --mode apply

validate-knowledge:
	./bin/agent --list-reference-groups
	$(VENV)/bin/python -m agent.validate_knowledge
