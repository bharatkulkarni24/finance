"""Set or reset a member's login password directly in the database.

Useful for first-time setup (seeded admin accounts start with no password)
or for resetting a forgotten password.

Usage (from the project root):

    python scripts/set_password.py "Govindrao Kulkarni" "YourPassword123"
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash

from core.database import get_conn


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    name, password = sys.argv[1], sys.argv[2]
    conn = get_conn()
    cur = conn.execute(
        'UPDATE members SET password=? WHERE name=?',
        (generate_password_hash(password), name),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        print(f'No member named "{name}" found.')
        sys.exit(1)
    print(f'Password set for "{name}".')


if __name__ == '__main__':
    main()
