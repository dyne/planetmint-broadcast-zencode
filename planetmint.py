import json
import base58
from hashlib import sha3_256
from cryptoconditions.types.ed25519 import Ed25519Sha256
from cryptoconditions import ZenroomSha256, Fulfillment
from zenroom import zencode_exec
from planetmint_driver import Planetmint


class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return json.JSONEncoder.default(self, obj)

def broadcast_tx(asset, metadata, ed_public_key, data, keys, script):
    # Execute one time the script and capture the output

    # Run script in zenroom
    version = "2.0"
    zenData = {"output": data}
    try:
        zenData["asset"] = asset["data"]
    except:
        pass
    try:
        zenData["result"] = metadata["data"]
    except:
        pass

    def format_return(success, **kwargs):
        return {
            "success": success,
            "zenroom": {
                "data": zenData,
                "keys": keys,
            },
            **kwargs
        }

    zen_result = zencode_exec(script, data=json.dumps(zenData),
                                      keys=json.dumps(keys))

    if not zen_result.output:
        return format_return(False, error=zen_result.logs)

    zenroomscpt = ZenroomSha256(script=script, data=data, keys=keys)
    # CRYPTO-CONDITIONS: generate the condition uri
    condition_uri_zen = zenroomscpt.condition.serialize_uri()

    # CRYPTO-CONDITIONS: construct an unsigned fulfillment dictionary
    unsigned_fulfillment_dict_zen = {
        'type': zenroomscpt.TYPE_NAME,
        'public_key': base58.b58encode(ed_public_key).decode(),
    }
    output = {
        'amount': '1',
        'condition': {
            'details': unsigned_fulfillment_dict_zen,
            'uri': condition_uri_zen,

        },
        'public_keys': [ed_public_key,],
    }
    input_ = {
        'fulfillment': None,
        'fulfills': None,
        'owners_before': [ed_public_key,]
    }
    metadata.update({
        "result": json.loads(zen_result.output)
    })

    token_creation_tx = {
        'operation': 'CREATE',
        'asset': asset,
        'metadata': metadata,
        'outputs': [output,],
        'inputs': [input_,],
        'version': version,
        'id': None,
    }


    # JSON: serialize the transaction-without-id to a json formatted string
    message = json.dumps(
        token_creation_tx,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )

    if not zenroomscpt.validate(message=message):
        return format_return(False,
                error="Validation failed on the server")

    message = json.loads(message)
    fulfillment_uri_zen = zenroomscpt.serialize_uri()

    message['inputs'][0]['fulfillment'] = fulfillment_uri_zen
    tx = message
    tx['id'] = None
    json_str_tx = json.dumps(
        tx,
        sort_keys=True,
        skipkeys=False,
        separators=(',', ':')
    )
    # SHA3: hash the serialized id-less transaction to generate the id
    shared_creation_txid = sha3_256(json_str_tx.encode()).hexdigest()
    message['id'] = shared_creation_txid

    # `https://example.com:9984`
    plntmnt = Planetmint("https://test.ipdb.io")
    sent_transfer_tx = plntmnt.transactions.send_commit(message)

    # decode fulfillment and put it into the result
    ff = Fulfillment.from_uri(fulfillment_uri_zen)
    ff_encoded = json.loads(json.dumps(ff.asn1_dict, cls=BytesEncoder))

    # In a zenroom cryptocondition try to decode keys and data into dict
    try:
        for k,v in ff_encoded["zenroomSha256"].items():
            if k == "keys" or k == "data":
                ff_encoded["zenroomSha256"][k] = json.loads(v)
    except:
        pass
    return format_return(True, tx=sent_transfer_tx,
            zenroom_fulfillment=ff_encoded)
