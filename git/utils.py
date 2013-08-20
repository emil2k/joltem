
def get_branch_reference(branch_name):
    """
    Get a branch reference name from it's regular branch name
    """
    # todo write a test for this function
    return "refs/heads/%s" % branch_name


def walk_branch(pygit_repository, branch_oid):
    """
    Walk a single branch
    """
    # todo write test for this function
    from pygit2 import GIT_SORT_TOPOLOGICAL
    previous_first_parent_oid = None
    for commit in pygit_repository.walk(branch_oid, GIT_SORT_TOPOLOGICAL):
        if previous_first_parent_oid is None or commit.oid == previous_first_parent_oid:
            previous_first_parent_oid = commit.parents[0].oid if len(commit.parents) else None
            yield commit


def get_checkout_oid(pygit_repository, topic_branch_oid, parent_branch_oid):
    """
    Get the Oid for the initial commit a topic branch was checked out from a parent branch
    """
    topic_commit_oids = (c.oid for c in walk_branch(pygit_repository, topic_branch_oid))
    parent_commit_oids = [c.oid for c in walk_branch(pygit_repository, parent_branch_oid)]

    checkout_id = None
    previous_in_parent = False
    for commit_oid in topic_commit_oids:
        in_parent = commit_oid in parent_commit_oids
        if not previous_in_parent and in_parent:
            checkout_id = commit_oid
        previous_in_parent = in_parent

    return checkout_id