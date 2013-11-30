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

@test "clone, commit, and push to s/1" {
    git checkout -b s/1 origin/s/1
    mock_commit
    git push origin s/1
}

@test "clone, commit, and push to s/2" {
    git checkout -b s/2 origin/s/2
    mock_commit
    git push origin s/2
}

@test "clone, commit to s/1 and s/2, and push both" {
    git checkout -b s/1 origin/s/1
    mock_commit
    git checkout -b s/2 origin/s/2
    mock_commit
    git push --all
}



