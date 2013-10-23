packages:
  pkg:
    - installed
    - names:
      - git
      - python-dev
      - python-pip
      - gcc
      - make
      - cmake

libgit2:
  git:
    - latest
    - name: git://github.com/libgit2/libgit2.git
    - rev: v0.19.0
    - target: /usr/local/src/libgit2
    - require:
      - pkg: packages
  file:
    - directory
    - name: /usr/local/src/libgit2/build
    - require:
      - git: libgit2
  cmd:
    - wait
    - name: >
              cmake .. &&
              cmake --build . &&
              cmake --build . --target install &&
              pwd > /etc/ld.so.conf.d/libgit.conf &&
              ldconfig
    - cwd: /usr/local/src/libgit2/build
    - watch:
      - git: libgit2
    - require:
      - file: libgit2

virtualenv:
  pip:
    - installed
    - require:
      - pkg: packages

/var/www/joltem_venv:
  file:
    - directory
    - user: vagrant
    - group: vagrant
    - makedirs: True
  virtualenv:
    - managed
    - no_site_packages: True
    - distribute: True
    - requirements: /joltem/requirements_tests.txt
    - user: vagrant
    - no_chown: True
    - require:
      - pip: virtualenv
      - file: /var/www/joltem_venv

/joltem/joltem/settings/local.py:
  file:
    - managed
    - source: salt://django_project/local.py.template

django-admin migrate:
  module:
    - run
    - name: django.syncdb
    - bin_env: /var/www/joltem_venv
    - settings_module: joltem.settings
    - pythonpath: /joltem/
    - migrate: True
    - require:
      - virtualenv: /var/www/joltem_venv
      - file: /joltem/joltem/settings/local.py

django-admin collectstatic:
  module:
    - run
    - name: django.collectstatic
    - bin_env: /var/www/joltem_venv
    - settings_module: joltem.settings
    - pythonpath: /joltem/
    - noinput: True
    - require:
      - module: django-admin migrate
