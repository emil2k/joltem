ENV = $(shell echo $${VDIR:-.env})
SETTINGS ?= chefenv

.PHONY: clean
# target: clean - Clean temporary files
clean:
	@rm -f *.py[co]
	@rm -f *.orig
	@rm -f */*.py[co]
	@rm -f */*.orig
 
.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile | sed -e 's/^# target: //g'

.PHONY: lint
# target: lint - Code audit
lint: $(ENV)
	@rm -rf pylama.report
	pylama . -r pylama.report

.PHONY: run
# target: run - Run Django development server
run: $(ENV)
	$(ENV)/bin/python $(CURDIR)/manage.py runserver --settings=joltem.settings.$(SETTINGS)

.PHONY: db
# target: db - Prepare database
db: $(ENV)
	$(ENV)/bin/python $(CURDIR)/manage.py syncdb --settings=joltem.settings.$(SETTINGS) --noinput
	$(ENV)/bin/python $(CURDIR)/manage.py migrate --settings=joltem.settings.$(SETTINGS) --noinput

.PHONY: shell
# target: shell - Prepare database
shell: $(ENV)
	$(ENV)/bin/python $(CURDIR)/manage.py shell_plus --settings=joltem.settings.$(SETTINGS)

$(ENV): requirements.txt
	virtualenv --no-site-packages $(ENV)
	$(ENV)/bin/pip install -M -r requirements.txt
	touch $(ENV)

test: $(ENV)
	$(ENV)/bin/python manage.py test --settings=joltem.settings.test --failfast
