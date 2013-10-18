packages:
  pkgrepo:
    - managed
    - name: deb http://ppa.launchpad.net/xav0989/libgit2/ubuntu precise main
    - keyid: 797674B4
    - keyserver: keyserver.ubuntu.com
  pkg:
    - installed
    - names:
      - git
      - python-dev
      - libgit2-0
      - libgit2-dev
    - require:
      - pkgrepo: packages

pip:
  pkg:
    - installed
    - name: python-pip

virtualenv:
  pip:
    - installed
    - require:
      - pkg: pip

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
      - pkg: packages
      - pip: virtualenv
      - file: /var/www/joltem_venv
