#encoding=utf8
#!/bin/env python

import xuper
import time
import random
import json

pysdk = xuper.XuperSDK("http://localhost:8089", "xuper")
pysdk.readkeys("./data/keys")

#0. 系统状态
print(pysdk.system_status())

#1. 普通转账
txid = pysdk.transfer("bob", 88888, desc="hello world")
print(pysdk.balance("bob"))
print(pysdk.query_tx(txid))

#2. 存证上链(不涉及UTXO，对应xuperunion > v3.4)
#a. 读取文件
with open('./data/evidence/demo.json', 'r') as f:
    data = json.load(f)
#b. 文件反序列化
txid = pysdk.transfer("bob", 0, desc=str(data))
print(pysdk.query_tx(txid))

#2. 创建合约账号
new_account_name = pysdk.new_account()
print("wait acl confirmed....")
time.sleep(4)
print("new account:", new_account_name)

#3. 部署合约
pysdk.transfer(new_account_name, 10000000, desc="start funds")

pysdk.set_account(new_account_name)
contract_name = 'counter'+str(random.randint(100,1000000))
print("contract name:", contract_name)
print("deploying......")
rsps = pysdk.deploy(new_account_name, contract_name, open('./data/wasm/counter.wasm','rb').read(), {'creator':b'baidu'})
print(rsps)

#4. 预执行合约
rsps = pysdk.preexec(contract_name, "get", {"key":b"counter"})
print(rsps.decode())


#5. 调用合约并生效上链
for i in range(5):
        rsps = pysdk.invoke(contract_name, "increase", {"key":b"counter"})
        print(rsps)
        print(pysdk.balance(new_account_name))

