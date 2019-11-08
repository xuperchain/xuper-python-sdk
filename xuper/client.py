#encoding=utf8
#!/bin/env python
import time
import json
import random
import requests
import ecdsa
from ecdsa.util import sigencode_der, sigdecode_der
import base64
import hashlib
import binascii
import codecs
from pprint import pprint
from collections import OrderedDict, namedtuple
from ecdsa import ellipticcurve, NIST256p, SigningKey, VerifyingKey

TxTemplate = '''
{   "txid":"",
    "tx_inputs": [
    ],
    "tx_outputs": [
    ],
    "desc": "",
    "nonce": "",
    "timestamp": "",
    "version": 1,
    "tx_inputs_ext":[
    ],
    "tx_outputs_ext":[
    ],
    "initiator": "",
    "auth_require": [
    ],
    "initiator_signs": [
    ],
    "auth_require_signs": [
    ]
}
'''

ResTypeEnum = {
    "CPU":0,
    "MEMORY":1,
    "DISK":2,
    "XFEE":3
}

InvokeResponse = namedtuple('InvokeResponse', ['result', 'fee', 'txid'])

def double_sha256(data):
    s1 = hashlib.sha256(data).digest()
    return hashlib.sha256(s1)

def go_style_dumps(data):
    return json.dumps(data,separators=(',',':'),sort_keys=False)
    
def to_bytes(n, length=32, endianess='big'):
    h = b'%x' % n
    s = codecs.decode((b'0'*(len(h) % 2) + h).zfill(length*2), 'hex')
    return s if endianess == 'big' else s[::-1]

class XuperSDK(object):
    """
    XuperSDK is a pure python sdk for xuperchain
    """
    def __init__(self, url, bcname = 'xuper'):
        """
        url is the address of xuperchain http gateway
        bcname is the chain name. e.g. xuper
        """
        self.url = url
        self.bcname = bcname
        self.address = ""
        self.account_name = ""

    def __encodeTx(self, tx, include_sign = False):
        s = ""
        for tx_input in tx['tx_inputs']:
            s += go_style_dumps(tx_input['ref_txid'])   
            s += "\n"
            s += go_style_dumps(tx_input['ref_offset'])
            s += "\n"
            s += go_style_dumps(tx_input['from_addr'])
            s += "\n"
            s += go_style_dumps(tx_input['amount'])
            s += "\n"
            s += go_style_dumps(tx_input.get("frozen_height",0))
            s += "\n"
        s += go_style_dumps(tx['tx_outputs'])
        s += "\n"
        if len(tx['desc']) > 0:
            s += go_style_dumps(tx['desc'])
            s += "\n"
        s += go_style_dumps(tx['nonce'])
        s += "\n"
        s += go_style_dumps(tx['timestamp'])
        s += "\n"
        s += go_style_dumps(tx['version'])
        s += "\n"
        for tx_input_ext in tx['tx_inputs_ext']:
            s += go_style_dumps(tx_input_ext['bucket'])
            s += "\n"
            s += go_style_dumps(tx_input_ext['key'])
            s += "\n"
            if 'ref_txid' in tx_input_ext:
                s += go_style_dumps(tx_input_ext['ref_txid'])
                s += "\n"
            s += go_style_dumps(tx_input_ext.get('ref_offset',0))
            s += "\n"
        for tx_output_ext in tx['tx_outputs_ext']:
            s += go_style_dumps(tx_output_ext['bucket'])
            s += "\n"
            s += go_style_dumps(tx_output_ext['key'])
            s += "\n"
            s += go_style_dumps(tx_output_ext['value'])
            s += "\n"
        if 'contract_requests' not in tx:
            s += "null"  # contract request
            s += "\n"
        else:
            s += go_style_dumps(tx['contract_requests'])
            s += "\n"
        s += go_style_dumps(tx['initiator'])
        s += "\n"
        s += go_style_dumps(tx['auth_require'])
        s += "\n"
        if include_sign:
            s += go_style_dumps(tx['initiator_signs'])  
            s += "\n"
            s += go_style_dumps(tx['auth_require_signs'])
            s += "\n"   
        s += "false\n" #coinbase
        s += "false\n" #autogen 
        return s.encode()

    def __make_txid(self, tx):
        json_multi = self.__encodeTx(tx, True)
        #print(json_multi.decode())
        return double_sha256(json_multi)

    def __my_address(self):
        if self.account_name != "":
            return self.account_name
        else:
            return self.address

    def __my_auth_require(self):
        if self.account_name != "":
            return self.account_name + "/" + self.address
        else:
            return self.address
    
    def sign_tx(self, tx):
        """
        must call read_keys to read private key first
        sign tx with private key, set signature in tx
        """
        raw = self.__encodeTx(tx, False)
        #print(raw.decode())
        s = self.private_key.sign(raw, hashfunc=double_sha256, sigencode=sigencode_der)
        tx['auth_require_signs'][0]['Sign'] = base64.b64encode(s).decode()
        tx['initiator_signs'][0]['Sign'] = base64.b64encode(s).decode()
        txid = self.__make_txid(tx).digest()
        tx['txid'] = base64.b64encode(txid).decode()
    
    def readkeys(self, path):
        """
        read private keys from a directory, which must containser private.key, address and public.key
        """
        self.address = open(path + "/address").read()
        self.private_key_js = open(path + "/private.key").read()
        self.public_key_js = open(path + "/public.key").read()
        sk_obj = json.loads(self.private_key_js)
        X = int(sk_obj['X'])
        Y = int(sk_obj['Y'])
        D = int(sk_obj['D'])
        self.public_key = VerifyingKey.from_public_point(ellipticcurve.Point(NIST256p.curve, X, Y), NIST256p, double_sha256)
        self.private_key = SigningKey.from_secret_exponent(D, NIST256p, double_sha256)
        #print(self.private_key.privkey.public_key.point.x())
        #print(self.private_key.privkey.public_key.point.y())

    def post_tx(self, tx):
        """
        broadcast a tx to xchain node
        """
        payload = {
            'bcname':self.bcname,
            'header':{'logid':'pysdk_post_tx'+str(int(time.time()*1e6)) },
            'txid': tx['txid'],
            'tx': tx
        }   
        #print(json.dumps(payload))
        rsps = requests.post(self.url + "/v1/post_tx", data = json.dumps(payload))
        rsps_obj = json.loads(rsps.content)
        if 'error' in rsps_obj['header']:
            raise Exception(rsps_obj['header'])
        return rsps.content

    def preexec(self, contract, method, args, module="wasm"):
        """
        pre-execute a contract, and get response which contains inputs,outputs and response of contract"
        contract:  contract name
        method: method name
        args: contract args
        module: contract module, default is wasm
        """
        payload = {
            'bcname':self.bcname,
            'header':{'logid':'pysdk_preexec'+str(int(time.time())*1e6)},
            'requests':[
                OrderedDict([
                    ('module_name', module),
                    ('contract_name', contract),
                    ('method_name', method),
                    ('args',OrderedDict([(k,base64.b64encode(args[k]).decode()) for k in sorted(args.keys())])),
                ])
            ],
            'initiator':self.__my_address(),
            'auth_require':[self.__my_auth_require()]
        }
        rsps = requests.post(self.url + "/v1/preexec", data = json.dumps(payload, sort_keys=False))
        rsps_obj = json.loads(rsps.content)
        if 'error' in rsps_obj:
            raise Exception(rsps_obj)
        return rsps.content

    def query_tx(self, txid):
        """
        query a transaction by txid (hex format)
        """
        payload = {
            'bcname':self.bcname,
            'header':{'logid':'pysdk_query_tx'+str(int(time.time()*1e6)) },
            'txid': codecs.encode(codecs.decode(txid, 'hex'), 'base64').decode()
        } 
        rsps = requests.post(self.url + "/v1/query_tx", data = json.dumps(payload))
        rsps_obj = json.loads(rsps.content)
        if 'error' in rsps_obj['header']:
            raise Exception(rsps_obj['header'])
        rsps_obj = json.loads(rsps.content)
        return rsps_obj['tx']
        
    def get_block(self, blockid):
        """
        get a block by blockid (hex format)
        """
        payload = {
            'bcname':self.bcname,
            'header':{'logid':'pysdk_get_block'+str(int(time.time()*1e6)) },
            'blockid': codecs.encode(codecs.decode(blockid, 'hex'), 'base64').decode(),
            'need_content': True
        } 
        rsps = requests.post(self.url + "/v1/get_block", data = json.dumps(payload))
        rsps_obj = json.loads(rsps.content)
        if 'error' in rsps_obj['header']:
            raise Exception(rsps_obj['header'])
        rsps_obj = json.loads(rsps.content)
        print(rsps_obj)
        return rsps_obj['block']

    def invoke(self, contract, method, args, module="wasm"):
        """
        invoke a contract, then the state update will take effect on chain
        contract: contract name
        method: method name
        args:  contract args 
        module: module name, default: wasm
        """
        rsps = self.preexec(contract, method, args, module)
        preexec_result = json.loads(rsps,object_pairs_hook=OrderedDict)
        return_msg = preexec_result['response']['response']
        fee = preexec_result['response']['gas_used']
        if 'outputs' not in preexec_result['response']:
            return [base64.b64decode(x) for x in return_msg], int(fee)
        contract_info = {}
        contract_info['tx_inputs_ext'] = preexec_result['response']['inputs']
        contract_info['tx_outputs_ext'] = preexec_result['response']['outputs']
        contract_info['contract_requests'] = preexec_result['response']['requests']
        contract_requests = contract_info["contract_requests"]
        for req in contract_requests:
            for res_limit in req['resource_limits']:
                if 'type' in res_limit:
                    res_limit['type'] = ResTypeEnum[res_limit['type']]
                if 'limit' in res_limit:
                    res_limit['limit'] = int(res_limit['limit'])
        txid = self.transfer('$', int(fee)+10, '', contract_info)
        return InvokeResponse([base64.b64decode(x) for x in return_msg], int(fee), txid)

    def new_account(self, account_name=None, acl=None):
        """
        create a new contract account
        account_name: name of the contract, should be 16 digits, if it is None, a random account will be generated  
        """
        if account_name == None:
            account_name = str(random.randint(0,9999999999999999)).zfill(16)
        if acl == None:
            acl = {
                "pm": {
                "rule": 1,
                "acceptValue": 1.0
                },
                "aksWeight": {
                self.address: 1.0
                }
            }
        self.invoke('','NewAccount', {'account_name':account_name.encode(), 'acl':json.dumps(acl).encode()},'xkernel')
        return "XC"+account_name+"@"+self.bcname

    def set_account(self, account_name):
        """
        set the account name represented by this SDK instance
        """
        self.account_name = account_name

    def deploy(self, account_name, contract_name, code, init_args, runtime="c"):
        """
        deploy a contract, only C runtime supported
        account_name: account name
        contract_name: contract name
        code: wasm binary
        init_args: init call args
        runtime: runtime for wasm, e.g. "c" or "go"
        """
        runtime_desc = {
            "c":b"\n\x01c",
            "go":b"\n\x02go"
        }
        js_init_args = go_style_dumps(
            OrderedDict([(k,base64.b64encode(init_args[k]).decode()) for k in sorted(init_args.keys())])
        )
        args = {
            'account_name': account_name.encode(),
            'contract_name': contract_name.encode(),
            'contract_code': code,
            'contract_desc': runtime_desc[runtime],
            'init_args':js_init_args.encode()
        }       
        return self.invoke('','Deploy', args, 'xkernel')

    def balance(self, address = None):
        """
        get balance of an address or account
        """
        if address == None:
            address = self.address
        payload = {
            'bcs':[{'bcname':self.bcname}],
            'address': address
        }
        balance_response = requests.post(self.url + "/v1/get_balance", data = json.dumps(payload))
        balance = json.loads(balance_response.content)
        return balance['bcs'][0]['balance']

    def transfer(self, to_address, amount, desc='', contract_info = None):
        """
        transfer token to another address
        to_address: receiver
        amount: how much to be transfered
        desc: note 
        contract_info: only needed when a contract is invoked. using invoke instead, if in that case
        """
        payload = {
            'bcname':self.bcname,
            'address': self.__my_address(),
            'totalNeed': str(amount),
            'header':{'logid':'pysdk_'+str(int(time.time()*1e6)) },
            'needLock': False
        }   
        select_response = requests.post(self.url + "/v1/select_utxos_v2", data = json.dumps(payload))
        selected_obj = json.loads(select_response.content)  
        if 'error' in selected_obj['header']:
            raise Exception(selected_obj['header'])
        tx = json.loads(TxTemplate)
        #pprint(selected_obj)
        tx['tx_inputs'] = selected_obj['utxoList']
        for x in tx['tx_inputs']:
            x['ref_txid'] = x['refTxid']
            x['ref_offset'] = x.get('refOffset', 0)
            x['from_addr'] = base64.b64encode(self.__my_address().encode()).decode()
            del x['refTxid']
            del x['toAddr']
            if 'refOffset' in x:
                del x['refOffset']
        total_selected = int(selected_obj['totalSelected'])
        output_return = total_selected - amount
        tx['tx_outputs'].append(
            {
                'amount':base64.b64encode(to_bytes(amount).lstrip(b'\0')).decode(),
                'to_addr': base64.b64encode(to_address.encode('ascii')).decode()
            }
        )
        if output_return > 0:
            tx['tx_outputs'].append(
                {
                    'amount':base64.b64encode(to_bytes(output_return).lstrip(b'\0')).decode(),
                    'to_addr': base64.b64encode(self.__my_address().encode()).decode()
                }
            )
        tx['desc'] = base64.b64encode(desc.encode()).decode()
        tx['nonce'] = str(int(time.time()*1e6)) 
        tx['timestamp'] = int(time.time()*1e6)
        tx['initiator'] = self.__my_address()
        tx['auth_require'].append(self.__my_auth_require())
        tx['initiator_signs'].append({
            'PublicKey':self.public_key_js,
            'Sign':''
        })
        tx['auth_require_signs'].append({
            'PublicKey':self.public_key_js,
            'Sign':''
        })
        if contract_info != None:
            tx.update(contract_info)
        self.sign_tx(tx)
        #print(json.dumps(tx))
        res = self.post_tx(tx)
        return codecs.encode(codecs.decode(tx['txid'].encode(),'base64'), 'hex').decode()

