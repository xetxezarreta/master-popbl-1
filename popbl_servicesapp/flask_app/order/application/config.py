from os import environ
from dotenv import load_dotenv
import netifaces as ni

# Only needed for developing, on production Docker .env file is used
load_dotenv()


class Config:
    """Set Flask configuration vars from .env file."""
    # Database
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")
    # print(SQLALCHEMY_DATABASE_URI)


    """Set Flask configuration vars from .env file."""
    CONSUL_HOST = environ.get("CONSUL_HOST", "192.168.4.100")
    PORT = int(environ.get("ORDER_PORT", '13002'))
    SERVICE_NAME = environ.get("SERVICE_NAME", "order")
    SERVICE_ID = environ.get("SERVICE_ID", "order1")


    """ Set RabbitMQ env vars """

    RABBITMQ_IP = environ.get("RABBITMQ_IP")
    RABBITMQ_PORT = environ.get("RABBITMQ_PORT")
    RABBITMQ_USER = environ.get("RABBITMQ_USER")
    RABBITMQ_PASS = environ.get("RABBITMQ_PASS")

    CA_CERTS = environ.get("RABBITMQ_CA_CERT")
    KEYFILE = environ.get("RABBITMQ_CLIENT_KEY")
    CERTFILE = environ.get("RABBITMQ_CLIENT_CERT")

    HOST_IP = environ.get("HOST_IP", "")
    IP = None
    __instance = None

    @staticmethod
    def get_instance():
        if Config.__instance is None:
            Config()
        return Config.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Config.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.get_ip()
            Config.__instance = self

    def get_ip(self):
        if(self.HOST_IP):
            self.IP = self.HOST_IP
        else:
            print("HOST IP NOT DEFINED")
            exit(1) 


    @staticmethod
    def get_ip_iface(iface):
        return ni.ifaddresses(iface)[ni.AF_INET][0]['addr']