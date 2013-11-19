{{ pillar['website_venv_dir'] }}:
  file:
    - directory
    - user: joltem
    - group: joltem
    - makedirs: True
  virtualenv:
    - managed
    - no_site_packages: True
    - distribute: True
    - requirements: {{ pillar['website_requirements_path'] }}
    - index_url: {{ pillar['website_pypi_url'] }}
    - user: joltem
    - no_chown: True
    - require:
      - pip: virtualenv
      - file: {{ pillar['website_venv_dir'] }}

django settings:
  file:
    - managed
    - name: {{ pillar['website_settings_path'] }}
    - source: salt://website/local.py.template
    - template: jinja

django-admin collectstatic:
  module:
    - run
    - name: django.collectstatic
    - bin_env: {{ pillar['website_venv_dir'] }}
    - settings_module: joltem.settings.local
    - pythonpath: {{ pillar['website_src_dir'] }}
    - noinput: True
    - require:
      - virtualenv: {{ pillar['website_venv_dir'] }}
      - file: django settings

django-admin migrate:
  module:
    - run
    - name: django.syncdb
    - bin_env: {{ pillar['website_venv_dir'] }}
    - settings_module: joltem.settings.local
    - pythonpath: {{ pillar['website_src_dir'] }}
    - migrate: True
    - require:
      - virtualenv: {{ pillar['website_venv_dir'] }}
      - file: django settings

django initial data:
  cmd:
    - run
    - cwd: {{ pillar['website_src_dir'] }}
    - name: >
              source {{ pillar['website_venv_activate_path'] }} &&
              python -m joltem.libs.factories
    - require:
      - module: django-admin migrate
