import csv
import click
import requests
import json
import uuid
from requests.auth import HTTPBasicAuth

url_ws = 'http://localhost:8442'
config_path = './codec_manifest.json'


@click.command()
@click.option('--box_id', required=True, help='enter the Wattsense boxId')
@click.option('--username', required=True, help='enter the username to access the api')
@click.option('--password', required=True, help='enter the password to access the api')
@click.option('--push', required=True, type=click.Choice(['yes', 'no'], case_sensitive=False),
              help='if the push is yes, the created config will be pushed to the device, otherwise no')
@click.option('--filepath', required=True,
              help='give the csv file path that will contains:wattsenseBoxId,name,devEUI,appKey,appEUI,codecId')

# // Load and process CSV file
def load_csv(filepath, box_id, username, password, push):
    codec_store = read_codec_config(config_path)
    create_new_draft_config(box_id,username,password)
    check_create_network(box_id,username,password)
    with open(filepath, 'r') as csvFile:
        reader = csv.reader(csvFile)
        next(csvFile, None)
        create_lorawan_equipments_properties(reader, box_id, username, password, codec_store)
    csvFile.close()




def create_lorawan_equipments_properties(reader, box_id, username, password, codec_store):
    # POST equipment (and create a new draft)
    for row in reader:
        body = get_equipment_body(row)
        print("created : {}".format(body))
        toPost = url_ws + '/api/devices/' + box_id + '/configs/draft/equipments'
        print("Posting to:{}", format(toPost))
        r = requests.post(toPost,
                          auth=HTTPBasicAuth(username, password),
                          json=body)
        if r.status_code != 201:
            print("Issue in POST : {}".format(r.status_code))
            # here add it in the log file
        else:
            data = r.json()
            equipment_id = data["equipmentId"]
            codec_id = row[4]
            print("equipmentID:{}", format(equipment_id))
            print("codecID: {}", format(codec_id))
            post_properties(codec_id, equipment_id, box_id, username, password, codec_store)


def post_properties(codec_id, equipment_id, box_id, username, password, codec_sotre):
    toPost = url_ws + '/api/devices/' + box_id + '/configs/draft/properties'
    properties = codec_sotre[codec_id]
    for p_codec in properties:
        print("prop Codec: {}", format(p_codec))
        body = get_property_body(equipment_id, p_codec)
        r = requests.post(toPost,
                          auth=HTTPBasicAuth(username, password),
                          json=body)
        if r.status_code != 201:
            print("Issue in property POST : {}".format(r.reason))
        else:
            print("Done properties")


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
        print("Issue in creating new draft: {}{}",format(r.json()),format(r.status_code))


def check_create_network(box_id, username, password):
    to_get = url_ws + '/api/devices/' + box_id + '/configs/draft/networks?protocol=LORAWAN_V1_0'
    r = requests.get(to_get,
                     auth=HTTPBasicAuth(username, password))

    if r.status_code != 200:
        print("Issue in network Get : {}".format(r.reason))

    print("network code: {}",format(r.status_code))

    if len(r.json()) != 0:
        return

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
        print("Issue in network creation POST : {}".format(r.reason))
    else:
        print("Done Network")
    return


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
