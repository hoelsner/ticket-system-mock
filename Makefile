check: clean validate-bash validate-yaml webapp-compile webapp-complexity-check webapp-bandit-tests ticketsystemmock-compile ticketsystemmock-complexity-check ticketsystemmock-bandit-tests ticketsystemmock-unittest ticketsystemmock-validate-package webapp-unittest n8n-node-test n8n-node-validate-package
test: clean ticketsystemmock-test-coverage webapp-test-coverage

n8n-node-build:
	@cd src/n8n_node && npm run build

n8n-node-stage-dev-package:
	@./scripts/build_n8n_dev_package.bash

n8n-node-test:
	@printf "running n8n node tests... "; \
	tmpfile=$$(mktemp); \
	if cd src/n8n_node && npm test > "$$tmpfile" 2>&1; then \
		rm -f "$$tmpfile"; \
		echo "OK"; \
	else \
		cat "$$tmpfile"; \
		rm -f "$$tmpfile"; \
		exit 1; \
	fi

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

ticketsystemmock-complexity-check:
	@./scripts/ticketsystemmock/complexity.bash

ticketsystemmock-bandit-tests:
	@./scripts/ticketsystemmock/bandit.bash

ticketsystemmock-test-coverage:
	@./scripts/ticketsystemmock/test_coverage.bash
