#!/usr/bin/env bats

REPOSITORY="$BATS_TMPDIR/test"

setup() {
    git clone ssh://emil@joltem.local:222/1 $REPOSITORY
}

teardown() {
    rm -rf $REPOSITORY
}

@test "clone empty repository" {
    test -d $REPOSITORY
}
