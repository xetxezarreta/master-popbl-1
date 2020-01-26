from flask import request, jsonify, abort
from flask import current_app as app
from .models import Delivery
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType
import traceback
from . import Session
from .BLConsul import BLConsul
from .config import Config
import requests

from .delivery_logic import DeliveryLogic

bl_consul = BLConsul.get_instance()

logic = DeliveryLogic()

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

@app.route('/delivery/health', methods=['HEAD', 'GET'])
def health_check():
  #  print("Health check on delivery")
    return "OK", 200


# Crea un objeto delivery que contiene la referencia que lo une a un pedido, asi como su estado y su descripcion
# El estado sera en un principio "en proceso"
# La descripcion estara en blanco
@app.route('/delivery/create_delivery', methods=['POST'])
def create_delivery():
    session = Session()

    status = False

    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    print("Contenido del request:\n")
    print(content)

    try:

        temdel = Delivery(
            ref=content['orderId'],
            status=content['status'],
            description=content['description']
        )
        session.add(temdel)
        session.commit()

    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
        status = False

    response = jsonify(status)
    session.close()
    print(response)

    if not response:  # if response == False
        return {"success": False}
    else:
        return {"success": True}


# Se modifica el valor del estado de una delivery mediente la referencia
@app.route('/delivery/update_delivery', methods=['POST'])
def update_delivery():
    session = Session()

    status = False

    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    print("Contenido del request:\n")
    print(content)

    deli = session.query(Delivery).filter_by(ref=content['orderId']).first()

    print("Contenido de la query")
    print(deli)

    if deli:
        # Updatear
        deli.status = content['status']
        session.add(deli)
        session.commit()
        status = True
    else:

        status = False

    response = jsonify(status)
    session.close()
    print(response)

    if not response:  # if response == False
        return {"success": False}
    else:
        return {"success": True}


# El usuario añade a uno de los pedidos referenciados la descripcion necesaria para que seudiese realizar la entrega
# El pedido debe existir en la base de datos y tener su status como finalizado o ready
@app.route('/delivery/info_delivery', methods=['POST'])
def info_delivery():
    session = Session()

    status = False

    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    print("Contenido del request:\n")
    print(content)

    deli = session.query(Delivery).filter_by(ref=content['orderId']).first()

    print("Contenido de la query")
    print(deli)

    if deli:
        # Updatear
        deli.description = content['description']
        session.add(deli)
        session.commit()
        status = True
    else:

        status = False

    response = jsonify(status)
    session.close()
    print(response)

    if not response:  # if response == False
        return {"success": False}
    else:
        return {"success": True}


# Error Handling #######################################################################################################
@app.errorhandler(UnsupportedMediaType)
def unsupported_media_type_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(BadRequest)
def bad_request_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(NotFound)
def resource_not_found_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(InternalServerError)
def server_error_handler(e):
    return get_jsonified_error(e)


def get_jsonified_error(e):
    traceback.print_tb(e.__traceback__)
    return jsonify({"error_code": e.code, "error_message": e.description}), e.code
