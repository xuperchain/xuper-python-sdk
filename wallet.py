from tkinter import *
from tkinter import ttk
import xuper
import json
sdk = xuper.XuperSDK("http://localhost:8098", "xuper")
sdk.readkeys('data/keys')

def make_menus():
    menubar = Menu(r)

    account = Menu(menubar)
    account.add_command(label="New Keys")
    account.add_command(label="Load Keys")
    account.add_command(label="New Account")
    menubar.add_cascade(label="Account", menu=account)

    contract = Menu(menubar)
    contract.add_command(label="Deploy")
    contract.add_command(label="Invoke")
    menubar.add_cascade(label="Contract", menu=contract)

    blocks = Menu(menubar)
    blocks.add_command(label="All")
    blocks.add_command(label="Query")
    menubar.add_cascade(label="Blocks", menu=blocks)

    transactions = Menu(menubar)
    transactions.add_command(label="All")
    transactions.add_command(label="Query")
    menubar.add_cascade(label="Transactions", menu=transactions)
    r.config(menu = menubar)

def make_front():
    def transfer_token():
        global toAddr, toAmount,balance, tree
        txid = sdk.transfer(toAddr.get(), toAmount.get(), desc="demo")
        balance.set(sdk.balance(sdk.address))
        txHistory.insert("", "end", text = txid, values = (toAddr.get(),toAmount.get()))

    def show_tx(event):
        item = txHistory.selection()[0]
        txid = txHistory.item(item,"text")
        theTx = sdk.query_tx(txid)
        t1 = Toplevel(r)
        txt = Text(t1, width=30, height=20)
        txt.grid(row=0, column=0)
        txt.insert(END, json.dumps(theTx))
        t1.mainloop()

    Label(r, text = "My Address", font='Helvetica 14 bold').grid(row=0, column=0,sticky=W, padx=5, pady=2)
    Label(r, textvariable=myaddr).grid(row=0, column=1,sticky=E)
    Label(r, text = "Balance", font='Helvetica 14 bold').grid(row=1, column=0, sticky=W,  padx=5, pady=2)
    Label(r, textvariable=balance).grid(row=1, column=1,sticky=E)
    txFrame = LabelFrame(r, bd=2, text="Transfer")
    txFrame.grid(row=2,column=0, columnspan=2, pady=10,padx=5)
    Label(txFrame, text="Receiver", font='Helvetica 12 bold').grid(row=0, column=1,padx=10, pady=10)
    Entry(txFrame, textvariable=toAddr, width=50).grid(row=0, column=2, padx=10, pady=10)
    Label(txFrame, text="Amount", font='Helvetica 12 bold').grid(row=1, column=1,padx=10, pady=10)
    Entry(txFrame, textvariable=toAmount, width=50).grid(row=1, column=2, padx=10, pady=10)
    Button(txFrame, text="Send", width="60", command=transfer_token).grid(row=2,column=0, padx=10, pady=10,columnspan=3)
    txHistory= ttk.Treeview(r, column=("Receiver", "Amount"))
    txHistory.heading("#0", text="Txid")
    txHistory.heading("#1", text="Receiver")
    txHistory.heading("#2", text="Amount")
    txHistory.grid(row=3,column=0,columnspan=2, pady=10,padx=5)
    txHistory.bind("<Double-1>", show_tx)

r = Tk()
myaddr = StringVar()
myaddr.set(sdk.address)
balance = IntVar()
balance.set(sdk.balance(sdk.address))
toAddr = StringVar()
toAddr.set("")
toAmount = IntVar()
toAmount.set(0)
r.title("Wallet Demo")
make_menus()
make_front()
r.mainloop()
