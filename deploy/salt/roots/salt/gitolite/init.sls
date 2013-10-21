git:
  user:
    - present
    - groups:
      - git-data
    - createhome: True
    - require:
      - group: git-data
  group:
    - present
    - name: git-data

ssh dir:
  file:
    - directory
    - name: /home/git/.ssh
    - mode: 700
    - user: git
    - group: git
    - require:
      - user: git

ssh secret:
  file:
    - managed
    - name: /home/git/.ssh/id_rsa
    - source: salt://gitolite/id_rsa
    - user: git
    - group: git
    - mode: 600
    - require:
      - file: ssh dir

ssh pub:
  file:
    - managed
    - name: /home/git/.ssh/id_rsa.pub
    - source: salt://gitolite/id_rsa.pub
    - user: git
    - group: git
    - mode: 644
    - require:
      - file: ssh dir

gitolite bin folder:
  file:
    - directory
    - name: /home/git/bin
    - user: git
    - group: git
    - require:
      - user: git

gitolite:
  git:
    - latest
    - name: git://github.com/sitaramc/gitolite
    - target: /home/git/gitolite_src
    - rev: master
    - user: git
    - require:
      - user: git
  cmd:
    - wait
    - name: "gitolite_src/install -ln &&
             bin/gitolite setup -pk /home/git/.ssh/id_rsa.pub"
    - user: git
    - cwd: /home/git
    - watch:
      - git: gitolite
    - require:
      - file: gitolite bin folder
