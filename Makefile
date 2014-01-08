ENV = $(shell echo $${VDIR:-.env})
SETTINGS ?= joltem.settings.local

all: $(ENV)
	$(ENV)/bin/python manage.py $(ARGS) --settings=$(SETTINGS)

.PHONY: clean
# target: clean - Clean temporary files
clean:
	@find $(CURDIR) -name "*.py[co]" -delete
	@find $(CURDIR) -name "*.orig" -delete
	@find $(CURDIR) -name "*.deb" -delete
	@rm -rf build

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
	$(ENV)/bin/python manage.py test --settings=joltem.settings.jenkins --with-coverage --with-xunit --cover-xml --cover-package=joltem,task,solution,project,git,help,gateway,account

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
	$(ENV)/bin/python $(CURDIR)/manage.py shell_plus --settings=$(SETTINGS) || $(ENV)/bin/python $(CURDIR)/manage.py shell --settings=$(SETTINGS)

.PHONY: static
# target: static - Compile project static
static: $(ENV)
	@mkdir -p $(CURDIR)/static
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

.PHONY: deb
# target: deb - Compile deb package
PREFIX=/usr/lib/joltem
PACKAGE_VERSION?=$(shell git describe --abbrev=0 --tags `git rev-list master --tags --max-count=1`)
PACKAGE_POSTFIX?=
PACKAGE_NAME?="joltem-web"
PACKAGE_MAINTAINER="Emil Davtyan <emil2k@gmail.com>"
PACKAGE_URL="http://joltem.com"
FPM=fpm
deb: build
	@$(FPM) -s dir -t deb -a all \
	    --name $(PACKAGE_NAME) \
	    --version $(PACKAGE_VERSION)$(PACKAGE_POSTFIX) \
	    --maintainer $(PACKAGE_MAINTAINER) \
	    --url $(PACKAGE_URL) \
	    --deb-user root \
	    --deb-group root \
	    -C $(CURDIR)/build \
	    -d "python2.7" \
	    -d "python-virtualenv" \
	    -d "nginx-full" \
	    -d "supervisor" \
	    --config-files /etc/supervisor/conf.d/joltem.conf \
	    --config-files /etc/nginx/sites-enabled/joltem.conf \
	    --before-install $(CURDIR)/deploy/debian/preinst \
	    --after-install $(CURDIR)/deploy/debian/postinst \
	    usr etc

.PHONY: build
# target: build - Prepare structure for deb package
build: clean static
	@mkdir -p $(CURDIR)/build$(PREFIX)/log
	@touch $(CURDIR)/build$(PREFIX)/log/.placeholder
	@mkdir -p $(CURDIR)/build$(PREFIX)/run
	@touch $(CURDIR)/build$(PREFIX)/run/.placeholder
	@mkdir -p $(CURDIR)/build$(PREFIX)/build
	@cp -r account gateway git help joltem project solution task static Changelog Makefile manage.py requirements.txt wsgi.py $(CURDIR)/build$(PREFIX)/build/.
	@mkdir -p $(CURDIR)/build/etc/supervisor/conf.d
	@cp $(CURDIR)/deploy/debian/supervisor.ini $(CURDIR)/build/etc/supervisor/conf.d/joltem.conf
	@mkdir -p $(CURDIR)/build/etc/nginx/sites-enabled
	@cp $(CURDIR)/deploy/debian/nginx.conf $(CURDIR)/build/etc/nginx/sites-enabled/joltem.conf
	@cp $(CURDIR)/deploy/debian/uwsgi.ini $(CURDIR)/build$(PREFIX)/uwsgi.ini

$(ENV): requirements.txt
	[ -d $(ENV) ] || virtualenv --no-site-packages $(ENV)
	$(ENV)/bin/pip install -M -r requirements.txt -i http://pypi.joltem.com/simple
