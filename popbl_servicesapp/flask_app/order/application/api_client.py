import requests
import json
from os import environ
from .models import Order, Piece
from .BLConsul import BLConsul

GATEWAY_PORT = environ.get("HAPROXY_PORT")
GATEWAY_ADDRESS = environ.get("HAPROXY_IP")
MACHINE_SERVICE = "machine"
PAYMENT_SERVICE = "payment"
DELIVERY_SERVICE = "delivery"
AUTH_SERVICE = "auth"

CA_CERT = environ.get("RABBITMQ_CA_CERT")

consul = BLConsul.get_instance()

class ApiClient:

    @staticmethod
    def auth_get_pubkey():
        consul_dict = consul.get_service(AUTH_SERVICE)
        print("CONSUL RESPONSE {}".format(consul_dict))
        address = consul_dict['Address']
        port = str(consul_dict['Port'])
        r = requests.get("http://{}:{}/{}/pubkey".format(address, port, AUTH_SERVICE), verify=False)
        if r.status_code == 200:
            content = json.loads(r.content)
            return content["publicKey"].encode("utf-8")
