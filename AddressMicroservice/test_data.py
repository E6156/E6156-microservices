import AddressValidation.DataObject as DataObject
from AddressValidation.DataObject import AddressDynamoDB as AddressDynamoDB
import json


def t1():
    resp = AddressDynamoDB.post_address({'deliver_point_barcode': '123', 'xxx': 'yyy'})
    print("Result = ", json.dumps(resp, indent=2))
    resp = AddressDynamoDB.get_address('123')
    print("Result = ", json.dumps(resp, indent=2))

def t2():
    resp = AddressDynamoDB.post_address({'xxx': 'yyy'})
    print("Result = ", json.dumps(resp, indent=2))
    resp = AddressDynamoDB.get_address({'deliver_point_barcode': '456'})
    print("Result = ", json.dumps(resp, indent=2))


t1()
t2()