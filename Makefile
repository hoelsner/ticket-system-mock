check: clean validate-bash validate-yaml webapp-compile webapp-mypy-check webapp-complexity-check webapp-bandit-tests ticketsystemmock-compile ticketsystemmock-mypy-check ticketsystemmock-complexity-check ticketsystemmock-bandit-tests ticketsystemmock-unittest ticketsystemmock-validate-package webapp-unittest n8n-node-build n8n-node-lint n8n-node-test n8n-node-validate-package
test: clean ticketsystemmock-test-coverage webapp-test-coverage n8n-node-test-coverage
update-devserver: ticketsystemmock-stage-dev-package
	@./scripts/build_n8n_for_devserver.bash
	@$(MAKE) n8n-node-stage-dev-package
	@$(MAKE) webapp-restart-devserver

n8n-node-build:
	@bash ./scripts/n8n_node/compile.bash

n8n-node-lint:
	@bash ./scripts/n8n_node/lint.bash

n8n-node-audit:
	@bash ./scripts/n8n_node/audit.bash

n8n-node-stage-dev-package:
	@./scripts/build_n8n_dev_package.bash

n8n-node-test:
	@bash ./scripts/n8n_node/unittest.bash

n8n-node-test-coverage:
	@bash ./scripts/n8n_node/test_coverage.bash

n8n-node-test-coverage-python-threshold:
	@bash ./scripts/n8n_node/test_coverage_python_threshold.bash

n8n-node-pack:
	@cd src/n8n_node && npm run pack:node

n8n-node-validate-package:
	@./scripts/validate_n8n_package.bash

ticketsystemmock-stage-dev-package:
	@./scripts/build_ticketsystemmock_for_devserver.bash

ticketsystemmock-pack:
	@uv build --sdist src/ticketsystemmock

ticketsystemmock-validate-package:
	@./scripts/validate_ticketsystemmock_package.bash

webapp-runserver:
	@cd src/webapp && ./.venv/bin/python3 manage.py runserver 0.0.0.0:8000

webapp-restart-devserver:
	@docker compose restart webapp

clean:
	@./scripts/clean_directories.bash

validate-bash:
	@./scripts/validate_bash.bash

validate-yaml:
	@bash ./scripts/validate_yaml.bash

webapp-compile:
	@./scripts/webapp/compile.bash

webapp-mypy-check:
	@./scripts/webapp/mypy.bash

webapp-complexity-check:
	@./scripts/webapp/complexity.bash

webapp-bandit-tests:
	@./scripts/webapp/bandit.bash

webapp-unittest:
	@./scripts/webapp/unittest.bash

webapp-test-coverage:
	@./scripts/webapp/test_coverage.bash

ticketsystemmock-unittest:
	@./scripts/ticketsystemmock/unittest.bash

ticketsystemmock-compile:
	@./scripts/ticketsystemmock/compile.bash

ticketsystemmock-mypy-check:
	@./scripts/ticketsystemmock/mypy.bash

ticketsystemmock-complexity-check:
	@./scripts/ticketsystemmock/complexity.bash

ticketsystemmock-bandit-tests:
	@./scripts/ticketsystemmock/bandit.bash

ticketsystemmock-test-coverage:
	@./scripts/ticketsystemmock/test_coverage.bash
