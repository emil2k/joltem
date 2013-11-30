#!/usr/bin/env bats

REPOSITORY="$BATS_TMPDIR/test"

setup() {
    git clone ssh://emil@joltem.local:222/1 $REPOSITORY
    cd $REPOSITORY
    ls -alh $REPOSITORY
}

teardown() {
    rm -rf $REPOSITORY
}

mock_commit() {
    touch $REPOSITORY/FILE.txt
    date > $REPOSITORY/FILE.txt
    git add FILE.txt
    git commit -m "Modified FILE.txt on $(date)!"
}

@test "clone, commit, and push to s/2" {
    git checkout -b s/2 origin/s/2
    mock_commit
    git push origin s/2
}

