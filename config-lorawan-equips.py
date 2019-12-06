import csv
import click
import requests
import json
import uuid
import logging
import sys
from requests.auth import HTTPBasicAuth

format_type = '%(asctime)-15s %(message)s'
logging.basicConfig(filename='errors.log', filemode='w', format=format_type)
url_ws = 'http://localhost:8442'
config_path = './codec_manifest.json'


@click.command()
@click.option('--box_id', required=True, help='enter the Wattsense boxId')
@click.option('--username', required=True, help='enter the username to access the api')
@click.option('--password', required=True, help='enter the password to access the api')
@click.option('--publish', required=True, type=click.Choice(['False', 'True'], case_sensitive=False),
              help='if the push is yes, the created config will be pushed to the device, otherwise no')
@click.option('--filepath', required=True,
              help='give the csv file path that will contains:wattsenseBoxId,name,devEUI,appKey,appEUI,codecId')
# // Load and process CSV file
def load_csv(filepath, box_id, username, password, publish):
    codec_store = read_codec_config(config_path)
    create_new_draft_config(box_id, username, password)
    network_id = check_create_network(box_id, username, password)
    with open(filepath, 'r') as csvFile:
        reader = csv.reader(csvFile)
        next(csvFile, None)
        equip_list = create_lorawan_equipments_properties(reader, box_id, username, password, codec_store)
        assign_equipments_to_network(box_id, network_id, equip_list, username, password)
        print("The equipments are created", format(box_id))
    csvFile.close()

    if publish == 'True':
        publish_revision(box_id, username, password)
    print("The complete config is published for the boxID", format(box_id))


# POST equipment (and create a new draft)
def create_lorawan_equipments_properties(reader, box_id, username, password, codec_store):
    equip_list = []
    for row in reader:
        body = get_equipment_body(row)
        to_post = url_ws + '/api/devices/' + box_id + '/configs/draft/equipments'
        r = requests.post(to_post,
                          auth=HTTPBasicAuth(username, password),
                          json=body)
        if r.status_code != 201:
            logging.error('Equipment Creation Issue %s', format(r.json()))
            # print("Issue in POST : {}".format(r.status_code))
            return equip_list  # here add it in the log file

        data = r.json()
        equipment_id = data["equipmentId"]
        equip_list.append(equipment_id)
        codec_id = row[4]
        post_properties(codec_id, equipment_id, box_id, username, password, codec_store)
    return equip_list


def post_properties(codec_id, equipment_id, box_id, username, password, codec_sotre):
    to_post = url_ws + '/api/devices/' + box_id + '/configs/draft/properties'
    properties = codec_sotre[codec_id]
    for p_codec in properties:
        body = get_property_body(equipment_id, p_codec)
        r = requests.post(to_post,
                          auth=HTTPBasicAuth(username, password),
                          json=body)
        if r.status_code != 201:
            logging.error('Property Creation Issue %s', format(r.json()))



def publish_revision(box_id, username, password):
    to_put = url_ws + '/api/devices/' + box_id + '/configs/draft'
    body = {
        "publish": True,
        "notes": "automatically published from the script",
    }
    r = requests.put(to_put,
                     auth=HTTPBasicAuth(username, password),
                     json=body)
    if r.status_code != 200:
        print('Error in publishing the config, check error logs')
        logging.error('Revision Publish Issue %s', format(r.json()))
        sys.exit(1)



def get_properties_for_codec_id(json_data, codec_id):
    return json_data[codec_id]


def read_codec_config(file_path):
    with open(file_path) as json_file:
        return json.load(json_file)


# // Activate these properties for a device
#
# // integrate it to create webhooks for a device
def get_equipment_body(row):
    name = row[0]
    dev_eui = row[1]
    app_key = row[2]
    app_eui = row[3]
    codec_id = row[4]
    return {"name": name,
            "description": "auto generated lorawan equipment",
            "config": {"protocol": "LORAWAN_V1_0", "devEUI": dev_eui, "codecId": codec_id, "appEUI": app_eui,
                       "activationMethod": {"type": "OTAA", "version": "V1_0", "appKey": app_key}
                       }
            }


def create_new_draft_config(box_id, username, password):
    to_post = url_ws + '/api/devices/' + box_id + '/configs/'
    r = requests.post(to_post,
                      auth=HTTPBasicAuth(username, password),
                      json={})
    if r.status_code == 404 or r.status_code > 409:
        logging.error('Draft Config Creation Issue %s', format(r.json()))
        print('Error in creating draft config, check error logs')
        sys.exit(1)


def check_create_network(box_id, username, password):
    to_get = url_ws + '/api/devices/' + box_id + '/configs/draft/networks?protocol=LORAWAN_V1_0'
    r = requests.get(to_get,
                     auth=HTTPBasicAuth(username, password))

    if r.status_code == 200 and len(r.json()) != 0:
        return r.json()[0]['networkId']




    network_request = {
        "name": "lorawan network for EU",
        "description": "auto generated lorawan network",
        "config": {
            "protocol": "LORAWAN_V1_0",
            "regionConfig": {
                "name": "EUROPE",
                "frequencyPlanId": "EU_863_870"
            },
        },
    }
    to_post = url_ws + '/api/devices/' + box_id + '/configs/draft/networks'
    r = requests.post(to_post,
                      auth=HTTPBasicAuth(username, password),
                      json=network_request)
    if r.status_code != 201:
        logging.error('Network Creation Issue %s', format(r.json()))
        print('Error in creating network info, check error logs')
        sys.exit(1)
    else:
        return r.json()['networkId']


def assign_equipments_to_network(box_id, network_id, equips_list, username, password):
    network_request = {
        "name": "lorawan network for EU",
        "description": "auto generated lorawan network",
        "equipments": equips_list,
        "config": {
            "protocol": "LORAWAN_V1_0",
            "regionConfig": {
                "name": "EUROPE",
                "frequencyPlanId": "EU_863_870"
            },
        },
    }

    to_put = url_ws + '/api/devices/' + box_id + '/configs/draft/networks/' + network_id
    r = requests.put(to_put,
                     auth=HTTPBasicAuth(username, password),
                     json=network_request)
    if r.status_code != 200:
        print('Error in assigning network info, check error logs')
        logging.error('Network Assignment Issue %s', format(r.json()))
        sys.exit(1)


def get_property_body(equipment_id, codec_property_id):
    return {
        "equipmentId": equipment_id,
        "name": "property-" + codec_property_id,
        "slug": equipment_id.lower() + "-" + codec_property_id.replace('.', '-') + "-" + uuid.uuid4().hex,
        "description": "auto generated lorawan property",
        "accessType": "REMOTE_READ_ONLY",
        "config": {
            "protocol": "LORAWAN_V1_0", "codecPropertyId": codec_property_id
        }
    }


def try_to_get(row, index):
    try:
        return row[index]
    except IndexError:
        return ''


if __name__ == "__main__":
    load_csv()
