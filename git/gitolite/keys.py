import os
from joltem.models import User


def update_keys():
    """
    Update gitolite key directory
    """
    users = User.objects.all()
    for user in users:
        print "Processing keys for %s" % user
        for key in user.authentication_set.all():
            print "Processing key #%d:\n%s\n" % (key.id, key.key)
            file_name = "%s@%s.pub" % (user.username, key.id)
            file_path = os.path.dirname(os.path.realpath(__file__))+"/gitolite/keydir/"+file_name
            with open(file_path, 'w') as f:
                f.write(key.key)
            print "Wrote file, is closed %s." % f.closed