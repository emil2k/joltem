""" For loading dummy data after vagrant up runs. """

from joltem.libs import mixer


def initialize_data():
    """ Initialize dummy data.

    A project, repository, and users.

    """
    description = "This is a platform to openly collaborate with others to " \
                  "build and launch a startup. We have rethinked the way " \
                  "companies are formed based on the idea that an openly " \
                  "developed startup has major advantages over its closed " \
                  "counterparts."
    project = mixer.blend(
        'project.project', name="joltem", title="Joltem",
        description=description, total_shares=1000000, impact_shares=850000,
        exchange_periodicity=12, exchange_magnitude=25)
    mixer.blend(
        'git.repository', project=project, name="Test repository",
        description="An empty repository for you to play with.")
    admin = mixer.blend('joltem.user', username='emil', first_name='Emil',
                        is_superuser=True, is_staff=True,
                        password='123')
    project.admin_set.add(admin)
    project.save()
    first_names = ('Becky', 'Bob', 'Ian', 'Jill', 'Kate', 'Will')
    mixer.cycle(6).blend('joltem.user',
                         first_name=(first_name for first_name in first_names),
                         username=mixer.MIX.first_name(lambda x: x.lower()),
                         password='123')
    mixer.blend('project.equity', user=admin, project=project,
                shares=150000)


if __name__ == "__main__":
    initialize_data()
