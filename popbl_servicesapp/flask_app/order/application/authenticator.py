from .api_client import ApiClient
import jwt, json


class Authenticator:
    __instance = None
    public_key = None
    
    def __new__(cls):
        if Authenticator.__instance is None:
            Authenticator.__instance = object.__new__(cls)
        return Authenticator.__instance

    def __init__(self):
        # Get public key from auth service
        self.public_key = ApiClient.auth_get_pubkey()
        Authenticator.__instance = self

    
    def authenticate(self, recv_jwt):
        try:
            decoded = jwt.decode(recv_jwt, self.public_key, algorithms='RS256')
            print("Authenticated as " + decoded["name"])
            return True, decoded
        except jwt.ExpiredSignatureError:
            print("ExpiredSignatureError")
            return False , None
        except jwt.DecodeError:
            print("ExpiredSignatureError")
            return False , None
        except Exception:
            return False , None


    def check_permission(self, dec_jwt, permission):
        perms = json.loads(dec_jwt["perms"])
        if permission in perms:
            return True
        else:
            return False