
def get_branch_reference(branch_name):
    """
    Get a branch reference name from it's regular branch name
    """
    return "refs/heads/%s" % branch_name