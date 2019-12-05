import csv
import click
import requests
import json
from requests.auth import HTTPBasicAuth

user_x = 'test'
pass_x = 'test'
url_WS = 'https://api.wattsense.com'


@click.command()
@click.option('--username', required=True, help='enter the username to access the api')
@click.option('--password', required=True, help='enter the password to access the api')
@click.option('--push', required=True, type=click.Choice(['yes', 'no'], case_sensitive=False),
              help='if the push is yes, the created config will be pushed to the device, otherwise no')
@click.option('--filepath', required=True,
              help='give the csv file path that will contains:wattsenseBoxId,name,devEUI,appKey,appEUI,codecId')
# // Load the CSV file
def load_csv(filepath, username, password, push):
    with open(filepath, 'r') as csvFile:
        reader = csv.reader(csvFile)
        next(csvFile, None)
        create_lorawan_eqiupments(reader, username, password)
    csvFile.close()
    # activate_streams(device,type)
    # integrate_webhooks(device,type)


# // Based on it create Intent properties for a device

def create_lorawan_eqiupments(reader, username, password):
    # POST equipment (and create a new draft)
    for row in reader:
        box_id = row[0]
        body = get_json_request(row)
        print("created Intent : {}".format(body))
        toPost = url_WS + '/api/devices/' + box_id + '/configs/draft/equipments'
        print("Posting to:{}", format(toPost))
        r = requests.post(toPost,
                          auth=HTTPBasicAuth(username, password),
                          json=body)
        if r.status_code != 201:
            print("Issue in POST Intent : {}".format(r.status_code))
            # here add it in the log file
        else:
            data = r.json()
            equipmentId = data["equipmentId"]



def post_properties(codec_id, equipment_id, box_id, username, password):
    toPost = url_WS + '/api/devices/' + box_id + '/configs/draft/equipments'
    print("Posting to:{}", format(toPost))

    body = get_property_body(equipment_id, codec_id)
    r = requests.post(toPost,
                      auth=HTTPBasicAuth(username, password),
                      json=body)

def get_properties_for_codec_id(json_data, codec_id):
    return json_data[codec_id]






# // Activate these properties for a device
#
# // integrate it to create webhooks for a device
def get_equipment_body(row):
    name = row[1]
    dev_eui = row[2]
    app_key = row[3]
    app_eui = row[4]
    codec_id = row[5]

    return {"name": name,
            "description": "auto generated lorawan equipment",
            "config": {"protocol": "LORAWAN_V1_0", "devEUI": dev_eui, "codecId": codec_id, "appEUI": app_eui,
                       "activationMethod": {"type": "OTAA", "version": "V1_0", "appKey": app_key}
                       }
            }


def get_property_body(equipment_id, codec_property_id):
    return {
                "equipmentId": equipment_id,
                "name": "property",
                "slug": "string",
                "description": "auto generated lorawan property",
                "accessType": "REMOTE_READ_ONLY",
                "config": {
                "protocol": "LORAWAN_V1_0", "codecPropertyId":codec_property_id
                }
                }


def try_to_get(row, index):
    try:
        return row[index]
    except IndexError:
        return ''


if __name__ == "__main__":
    load_csv()
