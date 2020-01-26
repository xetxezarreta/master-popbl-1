from flask import request, jsonify, abort
from flask import current_app as app
from .business_logic import BusinessLogic
from .BLConsul import BLConsul
from .config import Config
import requests

bl = BusinessLogic.getInstance()


bl_consul = BLConsul.get_instance()

# Get Service from consul by name and return  ##########################################################################
@app.route('/{}/<string:external_service_name>'.format(Config.SERVICE_NAME))
def external_service_response(external_service_name):
    service = bl_consul.get_service(external_service_name)
    service['Name'] = external_service_name
    print(""*50)
    print(external_service_name)
    if service is None:
        ret_message = "The service does not exist or there is no healthy replica"
        status_code = 404
    else:
        ret_message, status_code = call_external_service(service)
    return ret_message, status_code


@app.route('/{}/kv'.format(Config.SERVICE_NAME))
def key_values():
    kv = bl_consul.get_key_value_items()
    return jsonify(kv), 200


@app.route('/{}/catalog'.format(Config.SERVICE_NAME))
def get_catalog():
    catalog = bl_consul.get_service_catalog()
    return jsonify(catalog), 200


@app.route('/{}/replicas'.format(Config.SERVICE_NAME))
def get_replicas():
    replicas = bl_consul.get_service_replicas()
    return jsonify(replicas), 200

def call_external_service(service):
    url = "http://{host}:{port}/{path}".format(
        host=service['Address'],
        port=service['Port'],
        path=service['Name']
    )
    response = requests.get(url)
    if response:
        ret_message = jsonify({
            "caller": Config.SERVICE_NAME,
            "callerURL": "{}:{}".format(Config.IP, Config.PORT),
            "answerer": service['Name'],
            "answererURL": "{}:{}".format(service['Address'], service['Port']),
            "response": response.text,
            "status_code": response.status_code
        })
        status_code = response.status_code
    else:
        ret_message = "Could not get message"
        status_code = 500
    return ret_message, status_code

@app.route('/logger/health', methods=['HEAD', 'GET'])
def health_check():
    # print("Health check on logger")
    return "OK", 200

@app.route('/logger/logs', methods=['GET'])
def get_logs():
    logs = bl.get_logs()
    return jsonify(logs)