from models import seed_db


def seed():
    seed_db()
    print('Seeded sample members (if none existed)')


if __name__ == '__main__':
    seed()
