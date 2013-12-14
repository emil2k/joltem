""" For loading dummy data after vagrant up runs. """

from joltem.libs import mixer


def initialize_data():
    """ Initialize dummy data.

    A project, repository, and users.

    """
    project = mixer.blend('project.project', name="joltem", title="Joltem")
    mixer.blend(
        'git.repository', project=project, name="Test repository",
        description="An empty repository for you to play with.")
    admin = mixer.blend('joltem.user', username='emil', first_name='Emil',
                        is_superuser=True, is_staff=True,
                        password='123')
    project.admin_set.add(admin)
    project.save()
    usernames = ('becky', 'bob', 'ian', 'jill', 'kate', 'will')
    first_names = ('Becky', 'Bob', 'Ian', 'Iill', 'Kate', 'Will')
    mixer.cycle(6).blend('joltem.user',
                         username=(username for username in usernames),
                         first_names=(first_name for first_name in first_names),
                         password='123')


if __name__ == "__main__":
    initialize_data()
