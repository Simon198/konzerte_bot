import sys

from models.user import User
from repository import session


def main():
    if len(sys.argv) != 2:
        print("Usage: python turn_admin <user-id>")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
    except ValueError:
        print("Error: Argument must be an integer.")
        return

    db_user = session.get(User, user_id)
    if db_user is None:
        print("Error: The user does not exist")
        return

    db_user.is_admin = True
    session.commit()
    print(f"User {user_id} is now an admin")


if __name__ == "__main__":
    main()
