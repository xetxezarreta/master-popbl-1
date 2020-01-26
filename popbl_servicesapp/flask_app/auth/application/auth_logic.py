import bcrypt
from OpenSSL import crypto
import os
from . import Session
from .models import User, Permission
import jwt
import json


class AuthLogic:

    __instance = None
    
    def __new__(cls):
        if AuthLogic.__instance is None:
            AuthLogic.__instance = object.__new__(cls)
        return AuthLogic.__instance


    def generate_keys(self):

        if os.path.isfile('./private_key.pem') and os.path.isfile('./public_key.pem'):
            with open('./public_key.pem', 'rb') as f:
                self.public_key = f.read()

            with open('./private_key.pem', 'rb') as f:
                self.private_key = f.read()

        else:
            print("KEYS not found, creating new ones")
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 2048)

            with open('private_key.pem', 'wb') as f:
                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey=key))

            with open('public_key.pem', 'wb') as f:
                f.write(crypto.dump_publickey(crypto.FILETYPE_PEM, pkey=key))

            self.public_key = crypto.dump_publickey(
                crypto.FILETYPE_PEM, pkey=key)
            self.private_key = crypto.dump_privatekey(
                crypto.FILETYPE_PEM, pkey=key)

    def get_hashed_password(self, password):
        b_password = password.encode()
        salt = bcrypt.gensalt()

        return bcrypt.hashpw(b_password, salt)

    def generate_jwt(self, user, permissions):
        payload = {
            "sub": 1,
            "name": user,
            "perms": json.dumps([p.permission for p in permissions])
        }

        jwt_encoded = jwt.encode(payload, self.private_key, algorithm="RS256")
        return jwt_encoded

    def create_client(self, user, password):
        session = Session()

        if session.query(User).filter_by(name=user).count() != 0:
            print("ERROR: the user already exist")
            return False

        hashed_password = self.get_hashed_password(password)

        client = User(name=user, password=hashed_password,
                      rol=User.ROL_CLIENT)
        session.add(client)
        session.commit()
        session.close()

        return True

    def authenticate(self, user, password):
        session = Session()
        client = session.query(User).filter_by(name=user).first()

        if not client:
            print("ERROR: there is no user")
            return False, None

        hashed_input_password = self.get_hashed_password(password)

        if hashed_input_password != hashed_input_password:
            print("Incorrect password")
            return False, None

        # Generate jwt
        jwt = self.generate_jwt(user, client.permissions)
        return True, jwt

    def get_public_key(self):
        return self.public_key

    def init_permissions(self):
        session = Session()

        if session.query(Permission).count() != 0:
            print("INFO: basic permissions already defined")
            return

        print("WARNING: Basic permissions not defined, adding them!")
        p = Permission(rol=User.ROL_ADMIN, permission=Permission.C_ALL)
        session.add(p)
        p = Permission(rol=User.ROL_ADMIN, permission=Permission.R_ALL)
        session.add(p)
        p = Permission(rol=User.ROL_ADMIN, permission=Permission.U_ALL)
        session.add(p)
        p = Permission(rol=User.ROL_ADMIN, permission=Permission.D_ALL)
        session.add(p)

        p = Permission(rol=User.ROL_CLIENT, permission=Permission.C_OWN_ORDER)
        session.add(p)
        p = Permission(rol=User.ROL_CLIENT, permission=Permission.R_OWN_ORDER)
        session.add(p)
        p = Permission(rol=User.ROL_CLIENT, permission=Permission.U_OWN_ORDER)
        session.add(p)
        p = Permission(rol=User.ROL_CLIENT, permission=Permission.D_OWN_ORDER)
        session.add(p)

        session.commit()
        session.close()
        print("INFO: Basic permissions added correctly!")
