# OSDU SPI Skills — Test Runner
# ==============================
# Six-layer test framework for cross-platform validation.
#
# Usage:
#   make test                        Fast tests: L0 + L1 + L2 (no AI calls)
#   make lint                        L1: Structure validation
#   make unit                        L2: Trigger eval dry-run
#   make test-apm                    L0: APM install dry-run per target
#   make test-triggers CLI=copilot   L3: Live trigger accuracy
#   make test-sessions CLI=copilot   L4: Multi-turn session tests
#   make test-benchmark S=brain      L5: Skill value comparison
#   make test-all                    Full matrix (L0–L4, both CLIs)
#   make report                      Test inventory
#
# Options:
#   S=skill-name     Target a specific skill
#   CLI=copilot|claude  Target CLI for live tests (default: copilot)
#   DEBUG=1          Show response captures in session tests

SCRIPTS := tests/scripts
CLI ?= copilot
DEBUG_FLAG := $(if $(DEBUG),--debug,)
CLAUDE_FLAG := $(if $(filter claude,$(CLI)),--use-claude,)

.PHONY: test test-apm lint unit pytest deploy test-triggers test-sessions test-benchmark test-all report test-skill help doctor

help: ## Show this help
	@echo "OSDU SPI Skills — Test Runner"
	@echo "=============================="
	@echo ""
	@echo "Quick start:"
	@echo "  make test                        L0 + L1 + L2 (fast, no AI)"
	@echo "  make test-triggers CLI=copilot   L3: Live trigger eval"
	@echo "  make test-sessions CLI=claude    L4: Session tests"
	@echo "  make test-all                    Full matrix"
	@echo ""
	@echo "Individual layers:"
	@echo "  make test-apm                    L0: APM install dry-run (all targets)"
	@echo "  make lint                        L1: Structure validation"
	@echo "  make unit                        L2: Trigger eval dry-run"
	@echo "  make test-triggers CLI=X         L3: Live trigger accuracy"
	@echo "  make test-sessions CLI=X         L4: Multi-turn session tests"
	@echo "  make test-benchmark S=X          L5: Skill value comparison"
	@echo ""
	@echo "Utility:"
	@echo "  make report                      Test inventory"
	@echo "  make test-skill S=brain          All layers for one skill"
	@echo "  make doctor                      Check CLI dependencies"
	@echo "  make pytest                      Run pytest unit tests"
	@echo ""
	@echo "Options:"
	@echo "  CLI=copilot|claude    Target CLI (default: copilot)"
	@echo "  S=skill-name          Target a specific skill"
	@echo "  DEBUG=1               Show tmux pane output in L4"

# =============================================================================
# Fast tests (run after every change)
# =============================================================================

test: test-apm lint unit pytest

# =============================================================================
# L0: APM verification
# =============================================================================

test-apm:
	@echo ""
	@echo "=== L0: APM Verification ==="
	@# Validate plugin.json is parseable and has required fields
	@python3 -c "import json; d=json.load(open('plugin.json')); \
		assert d.get('name'), 'missing name'; \
		assert d.get('agents'), 'missing agents'; \
		assert d.get('skills'), 'missing skills'; \
		assert d.get('mcpServers'), 'missing mcpServers'; \
		print('  plugin.json: valid')"
	@# Validate all agent files exist
	@for f in agents/*.md; do [ -f "$$f" ] && echo "  agent: $$f" || echo "  MISSING: $$f"; done
	@# Validate all skill directories have SKILL.md
	@for d in skills/*/; do \
		if [ -f "$$d/SKILL.md" ]; then echo "  skill: $$d"; \
		elif [ ! -f "$$d/*.md" ] && [ "$$(basename $$d)" != "osdu-shared" ]; then echo "  WARN: $$d missing SKILL.md"; fi; \
	done
	@# Validate commands exist
	@for f in commands/*.md; do [ -f "$$f" ] && echo "  command: $$f"; done
	@echo "[L0] Package structure verified"

# =============================================================================
# L1: Structure validation
# =============================================================================

lint:
	@echo ""
	@echo "=== L1: Structure Validation ==="
	@uv run $(SCRIPTS)/validate.py

# =============================================================================
# L2: Trigger eval dry-run (validates eval set balance and format)
# =============================================================================

unit:
ifdef S
	@echo ""
	@echo "=== L2: Trigger Eval — $(S) ==="
	@eval_file="tests/evals/triggers/$(S).json"; \
	skill_path=""; \
	if [ -d "skills/$(S)" ]; then skill_path="skills/$(S)"; \
	elif [ -f "agents/$(S).md" ]; then skill_path="agents/$(S).md"; fi; \
	if [ -n "$$skill_path" ]; then \
		uv run $(SCRIPTS)/run_trigger_eval.py \
			--eval-set $$eval_file --skill-path $$skill_path --dry-run; \
	else echo "  skill not found: $(S)"; fi
else
	@echo ""
	@echo "=== L2: Trigger Evals ==="
	@for evalfile in $$(ls tests/evals/triggers/*.json 2>/dev/null); do \
		skill=$$(basename $$evalfile .json); \
		printf "  %-25s " "$$skill"; \
		skill_path=""; \
		if [ -d "skills/$$skill" ]; then skill_path="skills/$$skill"; \
		elif [ -f "agents/$$skill.md" ]; then skill_path="agents/$$skill.md"; fi; \
		if [ -n "$$skill_path" ]; then \
			uv run $(SCRIPTS)/run_trigger_eval.py \
				--eval-set $$evalfile --skill-path $$skill_path \
				--dry-run 2>&1 | grep -o '[0-9]* positive.*' || echo "error"; \
		else echo "skill not found"; fi; \
	done
	@echo ""
endif

# =============================================================================
# Deploy: symlink source to platform directories for live testing
# =============================================================================

deploy:
	@echo ""
	@echo "=== Deploy: Creating platform directories ==="
	@echo "  (Local equivalent of 'apm install' — symlinks source to platform dirs)"
	@mkdir -p .github .claude
	@# Copilot: agents + skills in .github/
	@if [ ! -e .github/agents ]; then ln -sf ../agents .github/agents; echo "  .github/agents -> agents/"; fi
	@if [ ! -e .github/skills ]; then ln -sf ../skills .github/skills; echo "  .github/skills -> skills/"; fi
	@# Claude Code: agents + skills + commands in .claude/
	@if [ ! -e .claude/agents ]; then ln -sf ../agents .claude/agents; echo "  .claude/agents -> agents/"; fi
	@if [ ! -e .claude/skills ]; then ln -sf ../skills .claude/skills; echo "  .claude/skills -> skills/"; fi
	@if [ ! -e .claude/commands ]; then ln -sf ../commands .claude/commands; echo "  .claude/commands -> commands/"; fi
	@echo "[deploy] Platform symlinks created"

# =============================================================================
# L3: Live trigger accuracy (requires AI)
# =============================================================================

test-triggers: deploy
ifdef S
	@echo "=== L3: Triggers — $(S) ($(CLI)) ==="
	@uv run $(SCRIPTS)/run_trigger_eval.py \
		--eval-set tests/evals/triggers/$(S).json \
		--skill-path skills/$(S) \
		$(CLAUDE_FLAG) --verbose
else
	@echo "=== L3: Triggers — all skills ($(CLI)) ==="
	@for evalfile in $$(ls tests/evals/triggers/*.json 2>/dev/null); do \
		skill=$$(basename $$evalfile .json); \
		printf "  %-25s " "$$skill"; \
		skill_path=""; \
		if [ -d "skills/$$skill" ]; then skill_path="skills/$$skill"; \
		elif [ -f "agents/$$skill.md" ]; then skill_path="agents/$$skill.md"; fi; \
		if [ -n "$$skill_path" ]; then \
			uv run $(SCRIPTS)/run_trigger_eval.py \
				--eval-set $$evalfile --skill-path $$skill_path \
				$(CLAUDE_FLAG) 2>&1 | tail -1; \
		else echo "skill not found"; fi; \
	done
endif

# =============================================================================
# L4: Session tests (multi-turn, requires AI + tmux)
# =============================================================================

test-sessions: deploy
ifdef S
	@echo "=== L4: Session — $(S) ($(CLI)) ==="
	@uv run $(SCRIPTS)/session_test.py \
		--scenario $$(ls tests/evals/scenarios/*$(S)*.json 2>/dev/null | head -1) \
		--cli $(CLI) --verbose $(DEBUG_FLAG)
else
	@echo "=== L4: Sessions — all ($(CLI)) ==="
	@for scenario in $$(ls tests/evals/scenarios/*.json 2>/dev/null); do \
		name=$$(basename $$scenario .json); \
		echo ""; \
		echo "--- $$name ---"; \
		uv run $(SCRIPTS)/session_test.py \
			--scenario $$scenario \
			--cli $(CLI) --verbose $(DEBUG_FLAG) 2>&1 | tail -15; \
	done
endif

# =============================================================================
# L5: Skill value comparison (benchmark)
# =============================================================================

test-benchmark:
ifndef S
	@echo "Usage: make test-benchmark S=skill-name"
	@echo "Example: make test-benchmark S=brain"
	@exit 1
endif
	@mkdir -p tests/benchmarks
	@uv run $(SCRIPTS)/compare_skill.py \
		--skill $(S) \
		--scenario $$(ls tests/evals/scenarios/*$(S)*.json 2>/dev/null | head -1) \
		--cli $(CLI) --verbose \
		--save-to tests/benchmarks/

# =============================================================================
# Full matrix (both CLIs)
# =============================================================================

test-all: test
	@$(MAKE) test-triggers CLI=copilot
	@$(MAKE) test-triggers CLI=claude
	@$(MAKE) test-sessions CLI=copilot
	@$(MAKE) test-sessions CLI=claude

# =============================================================================
# All layers for one skill
# =============================================================================

test-skill:
ifndef S
	@echo "Usage: make test-skill S=skill-name"
	@exit 1
endif
	@uv run $(SCRIPTS)/test_skill.py $(S)

# =============================================================================
# Pytest: unit tests
# =============================================================================

pytest:
	@echo ""
	@echo "=== Pytest: Unit Tests ==="
	@uv run --with pytest --with rich pytest tests/unit/ -v --tb=short

# =============================================================================
# Test inventory / report
# =============================================================================

report:
	@uv run $(SCRIPTS)/test_skill.py --inventory

# =============================================================================
# Doctor: check dependencies
# =============================================================================

doctor:
	@uv run $(SCRIPTS)/check_deps.py
