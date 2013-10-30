libgit2 from source code:
  pkg:
    - installed
    - names:
      - git
      - gcc
      - make
      - cmake
  git:
    - latest
    - name: git://github.com/libgit2/libgit2.git
    - rev: v0.19.0
    - target: {{ pillar['libgit2_src_dir'] }}
    - require:
      - pkg: libgit2 from source code
  file:
    - directory
    - name: {{ pillar['libgit2_build_dir'] }}
    - require:
      - git: libgit2 from source code
  cmd:
    - wait
    - name: >
              cmake .. &&
              cmake --build . &&
              cmake --build . --target install &&
              pwd > /etc/ld.so.conf.d/libgit.conf &&
              ldconfig
    - cwd: {{ pillar['libgit2_build_dir'] }}
    - watch:
      - git: libgit2 from source code
    - require:
      - file: libgit2 from source code
