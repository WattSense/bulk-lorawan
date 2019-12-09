## Batch Lorawan Equipment,Network, Properties Creator

### Installation
``cd <script_dir>``

``pip install`` should do the trick

### Input Parameters
The script has a set of input parameters:

``--box_id`` : The id of the box the lorawan equipments will be configured (The box should be activated)

``--username`` : Wattsense API username
 
`--password` : Wattsense API password

`--filepath` : The path of the CSV that is formatted as: `name,devEUI,appKey,appEUI,codecId` (see `test_data.csv`)

`--pulish` : (`True`/`False`) to push the newly configured lorawan equipments to the Box

### How to Run
Just to configure the equipments (Recommended):

``python3 config-lorawan-equips.py --box_id B1XXX --username test --password test --filepath ./input_data.csv --publish False``

After this you'll have to use the console or Wattsense API to publish the configuration to the box


To Configure and push the configuration:

``python3 config-lorawan-equips.py --box_id B1XXX --username test --password test --filepath ./input_data.csv --publish True``
 
 ### In case of Errors
 There could be cases when there can be configuration issues for an equipment due to wrong devEUI, appKey or appEUI format. In this case,
 the error log will be inserted in the ``errors.log`` file. This will give you detailed description about the errors.