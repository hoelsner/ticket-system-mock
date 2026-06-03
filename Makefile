check: clean validate-bash webapp-compile webapp-complexity-check webapp-bandit-tests webapp-unittest
test: clean webapp-test-coverage

webapp-runserver:
	@cd src/webapp && ./.venv/bin/python3 manage.py runserver 0.0.0.0:8000

webapp-restart-devserver:
	@docker compose restart webapp

clean:
	@./scripts/clean_directories.bash

validate-bash:
	@./scripts/validate_bash.bash

webapp-compile:
	@./scripts/webapp/compile.bash

webapp-complexity-check:
	@./scripts/webapp/complexity.bash

webapp-bandit-tests:
	@./scripts/webapp/bandit.bash

webapp-unittest:
	@./scripts/webapp/unittest.bash

webapp-test-coverage:
	@./scripts/webapp/test_coverage.bash
