import os
from joltem.models import User


def update_keys():
    """
    Update gitolite key directory
    """
    gitolite_admin_directory = os.path.dirname(os.path.realpath(__file__))+"/gitolite-admin/"
    gitolite_keys_log_file_path = gitolite_admin_directory+"keys.log"
    with open(gitolite_keys_log_file_path, 'w') as keys_log:
        users = User.objects.all()
        for user in users:
            print "Processing keys for %s" % user
            for key in user.authentication_set.all():
                # Find file paths
                print "Processing key #%d:\n%s\n" % (key.id, key.key)
                file_name = "%s@%s.pub" % (user.username, key.id)
                file_path = os.path.dirname(os.path.realpath(__file__))+"/keydir/"+file_name
                with open(file_path, 'w') as f:
                    f.write(key.key)
                print "Wrote file, is closed %s." % f.closed
                # Put record in keys log
                keys_log.write("%d : %s\n%s\n***\n" % (key.id, user.username, key.key))
    print "Wrote keys log, is closed %s." % keys_log.closed
    # Commit and push changes
    from subprocess import call
    print "\n*** Commit keys changes\n."
    call("git --git-dir=%s.git --work-tree=%s commit -v -am 'Keys changes.'" % (gitolite_admin_directory, gitolite_admin_directory), shell=True)
    print "\n*** Push permission changes.\n"
    call("git --git-dir=%s.git --work-tree=%s push -v" % (gitolite_admin_directory, gitolite_admin_directory), shell=True)
