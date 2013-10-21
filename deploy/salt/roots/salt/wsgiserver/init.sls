supervisord conf:
  file:
    - managed
    - name: /etc/supervisor/conf.d/django_gunicorn.conf
    - source: salt://wsgiserver/supervisord.conf

gunicorn conf:
  file:
    - managed
    - name: /var/www/gunicorn.conf.py
    - source: salt://wsgiserver/gunicorn.conf.py
    - user: vagrant
    - group: vagrant

supervisor:
  pkg:
    - installed

django_gunicorn:
  supervisord:
    - running
    - watch:
      - file: supervisord conf
      - file: gunicorn conf
    - require:
      - pkg: supervisor
