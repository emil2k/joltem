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

@test "clone, commit, and push to master" {
    mock_commit
    git push origin master
}
