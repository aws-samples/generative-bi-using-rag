
from streamlit_authenticator.utilities.hasher import Hasher

if __name__ == "__main__":
    password = input("please enter the password: ")
    hashed_passwords = Hasher([password]).generate()
    print("hashed_passwords: ", hashed_passwords[0])
