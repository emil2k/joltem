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
	@rm -rf pep8.pylama pylint.pylama
	$(ENV)/bin/pip install pylama
	$(ENV)/bin/pip install pylama_pylint
	$(ENV)/bin/pylama . -r pep8.pylama -l pep257,pep8,pyflakes,mccabe || echo
	$(ENV)/bin/pylama . -r pylint.pylama -l pylint -f pylint || echo

ci:
	$(ENV)/bin/pip install coverage
	$(ENV)/bin/python manage.py test --settings=joltem.settings.test --with-coverage --with-xunit --cover-xml --cover-package=joltem,task,solution,project,git,help,gateway,account

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

.PHONY: test
# target: test - Run project's tests
TEST ?=
test: $(ENV)
	$(ENV)/bin/python manage.py test $(TEST) --settings=joltem.settings.test -x

.PHONY: test_joltem
test_joltem: $(ENV) joltem
	make test TEST=joltem

.PHONY: test_project
test_project: $(ENV) project
	make test TEST=project

.PHONY: test_solution
test_solution: $(ENV) solution
	make test TEST=solution

.PHONY: test_task
test_task: $(ENV) task
	make test TEST=task

.PHONY: test_git
test_git: $(ENV) git
	make test TEST=git

.PHONY: test_help
test_help: $(ENV) help
	make test TEST=help

.PHONY: test_account
test_account: $(ENV) account
	make test TEST=account

.PHONY: test_gateway
test_gateway: $(ENV) gateway
	DJANGO_SETTINGS_MODULE=joltem.settings.test trial gateway/tests.py

.PHONY: celery
# target: celery - Run dev celery worker/beat
celery: $(ENV)
	$(ENV)/bin/celery -A joltem worker -B -l info

.PHONY: update
# target: update - Restart 'joltem_web' process
update:
	sudo supervisorctl restart joltem_web

$(ENV): requirements.txt
	[ -d $(ENV) ] || virtualenv --no-site-packages $(ENV)
	$(ENV)/bin/pip install -M -r requirements.txt -i http://pypi.joltem.com/simple
	touch $(ENV)
