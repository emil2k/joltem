ENV = $(shell echo $${VDIR:-.env})
SETTINGS ?= joltem.settings.local

all: $(ENV)
	$(ENV)/bin/python manage.py $(ARGS) --settings=$(SETTINGS)

.PHONY: clean
# target: clean - Clean temporary files
clean:
	@rm -f *.py[co]
	@rm -f *.orig
	@rm -f */*.py[co]
	@rm -f */*/*.orig

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile | sed -e 's/^# target: //g'

.PHONY: lint
# target: lint - Code audit
lint: $(ENV)
	@rm -rf pep8.pylama
	$(ENV)/bin/pip install pylama
	$(ENV)/bin/pip install pylama_pylint
	$(ENV)/bin/pylama . -r pep8.pylama -l pep257,pep8,pyflakes,mccabe || echo
	$(ENV)/bin/pylama . -r pylint.pylama -l pylint -f pylint || echo

ci:
	$(ENV)/bin/pip install coverage
	$(ENV)/bin/python manage.py test --settings=joltem.settings.test --with-coverage --with-xunit --cover-xml --cover-package=joltem,task,solution,project,git,help,gateway,common,account

.PHONY: run
# target: run - Run Django development server
run: $(ENV)
	$(ENV)/bin/python $(CURDIR)/manage.py runserver 0.0.0.0:8000 --settings=$(SETTINGS)

.PHONY: db
# target: db - Prepare database
db: $(ENV)
	$(ENV)/bin/python $(CURDIR)/manage.py syncdb --settings=$(SETTINGS) --noinput
	$(ENV)/bin/python $(CURDIR)/manage.py migrate --settings=$(SETTINGS) --noinput

.PHONY: shell
# target: shell - Run project shell
shell: $(ENV)
	$(ENV)/bin/python $(CURDIR)/manage.py shell_plus --settings=$(SETTINGS)

.PHONY: static
# target: static - Compile project static
static: $(ENV)
	$(ENV)/bin/python $(CURDIR)/manage.py collectstatic --settings=$(SETTINGS) --noinput -c

$(ENV): requirements.txt
	[ -d $(ENV) ] || virtualenv --no-site-packages $(ENV)
	$(ENV)/bin/pip install -M -r requirements.txt -i http://pypi.joltem.com/simple
	touch $(ENV)

.PHONY: test
# target: test - Run project's tests
test: $(ENV)
	$(ENV)/bin/python manage.py test --settings=joltem.settings.test -x

.PHONY: test_joltem
test_joltem: $(ENV) joltem
	$(ENV)/bin/python manage.py test joltem --settings=joltem.settings.test --failfast

.PHONY: test_project
test_project: $(ENV) project
	$(ENV)/bin/python manage.py test project --settings=joltem.settings.test --failfast

.PHONY: test_solution
test_solution: $(ENV) solution
	$(ENV)/bin/python manage.py test solution --settings=joltem.settings.test --failfast

.PHONY: test_task
test_task: $(ENV) task
	$(ENV)/bin/python manage.py test task --settings=joltem.settings.test --failfast

.PHONY: test_git
test_git: $(ENV) git
	$(ENV)/bin/python manage.py test git --settings=joltem.settings.test --failfast

.PHONY: test_help
test_help: $(ENV) help
	$(ENV)/bin/python manage.py test help --settings=joltem.settings.test --failfast

.PHONY: test_account
test_account: $(ENV) account
	$(ENV)/bin/python manage.py test account --settings=joltem.settings.test --failfast

.PHONY: test_gateway
test_gateway: $(ENV) gateway
	DJANGO_SETTINGS_MODULE=joltem.settings.test trial gateway/tests.py
