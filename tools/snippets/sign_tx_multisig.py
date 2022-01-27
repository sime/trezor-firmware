"""
Similar to sign_tx.py, just for multisig.

SAME_SUFFIX boolean decides two logics for paths used to create multisig.
"""

import argparse
from decimal import Decimal
from typing import Dict, List

import requests

from trezorlib import btc, messages
from trezorlib.client import get_default_client
from trezorlib.debuglink import TrezorClientDebugLink
from trezorlib.tools import parse_path
from trezorlib.transport import enumerate_devices

parser = argparse.ArgumentParser()
parser.add_argument(
    "--autoconfirm",
    action="store_true",
    help="Whether to automatically confirm everything on the device.",
)
parser.add_argument(
    "--testnet",
    action="store_true",
    help="Use BTC testnet instead of mainnet.",
)
args = parser.parse_args()

# Can choose autoconfirm everything on the device (in the device-tests-style)
# (Suitable for long/repetitive transactions)
if args.autoconfirm:
    print("Autoconfirming everything on the device.")
    for device in enumerate_devices():
        try:
            CLIENT = TrezorClientDebugLink(device, auto_interact=True)
            break
        except Exception:
            pass
    else:
        raise RuntimeError("Could not find device")
else:
    CLIENT = get_default_client()
# Choosing between Mainnet and Testnet
if args.testnet:
    COIN = "Testnet"
    URL = "https://tbtc1.trezor.io/api/tx-specific"
else:
    COIN = "Bitcoin"
    URL = "https://btc1.trezor.io/api/tx-specific"
print(f"Operating on {COIN} at {URL}")


SAME_SUFFIX = True
if SAME_SUFFIX:
    # address (all all seed): 2NA7EkM5aJxRPf4XURQPAYBnKFdH4B6ZsE6
    # Used in tests/device_tests/bitcoin/test_multisig.py:test_2_of_3
    AMOUNT = 3
    THRESHOLD = 2
    PATHS = [f"48h/1h/{x}h/0h" for x in range(1, AMOUNT + 1)]
    SUFFIX = [0, 0]
    NODES = [
        btc.get_public_node(CLIENT, parse_path(path), coin_name="Testnet").node
        for path in PATHS
    ]
    # None means this path will be skipped
    PATHS_TO_SIGN = [
        "48h/1h/1h/0h/0/0",
        None,
        "48h/1h/3h/0h/0/0",
    ]

    INPUTS = [
        messages.TxInputType(
            amount=1_496_278,
            prev_hash=bytes.fromhex(
                "6b07c1321b52d9c85743f9695e13eb431b41708cdf4e1585258d51208e5b93fc"
            ),
            prev_index=0,
            script_type=messages.InputScriptType.SPENDMULTISIG,
        ),
    ]
    OUTPUTS = [
        messages.TxOutputType(
            address="mnY26FLTzfC94mDoUcyDJh1GVE3LuAUMbs",  # "44h/1h/0h/0/6"
            amount=1_496_278 - 10_000,
            script_type=messages.OutputScriptType.PAYTOADDRESS,
        ),
    ]
else:
    # address (all all seed): 2NFRJcruwi6hAQBs4zn7sZv4BLXCzWjS4Yd
    # Used in tests/device_tests/bitcoin/test_multisig.py:test_15_of_15
    AMOUNT = 15
    THRESHOLD = 15
    MAIN_PATH = "48h/1h/1h/0h"
    NODE = btc.get_public_node(CLIENT, parse_path(MAIN_PATH), coin_name="Testnet").node
    SUFFIXES = [[0, x] for x in range(AMOUNT)]
    PATHS_TO_SIGN = [
        f"{MAIN_PATH}/{'/'.join(str(s) for s in suffix)}" for suffix in SUFFIXES
    ]
    PUBS = [messages.HDNodePathType(node=NODE, address_n=suffix) for suffix in SUFFIXES]

    INPUTS = [
        messages.TxInputType(
            amount=1_476_278,
            prev_hash=bytes.fromhex(
                "0d5b5648d47b5650edea1af3d47bbe5624213abb577cf1b1c96f98321f75cdbc"
            ),
            prev_index=0,
            script_type=messages.InputScriptType.SPENDMULTISIG,
        ),
    ]
    OUTPUTS = [
        messages.TxOutputType(
            address="mnY26FLTzfC94mDoUcyDJh1GVE3LuAUMbs",  # "44h/1h/0h/0/6"
            amount=1_476_278 - 10_000,
            script_type=messages.OutputScriptType.PAYTOADDRESS,
        ),
    ]


def get_tx_info(tx_id: str) -> messages.TransactionType:
    """Fetch basic transaction info for the signing"""
    tx_url = f"{URL}/{tx_id}"
    tx_src = requests.get(tx_url, headers={"user-agent": "tx_cache"}).json(
        parse_float=Decimal
    )
    if "error" in tx_src:
        raise RuntimeError(tx_src["error"])
    return btc.from_json(tx_src)


def get_prev_txes(
    inputs: List[messages.TxInputType],
) -> Dict[bytes, messages.TransactionType]:
    """Get info for all the previous transactions inputs are depending on"""
    prev_txes = {}
    for input in inputs:
        tx_id = input.prev_hash
        if tx_id not in prev_txes:
            prev_txes[tx_id] = get_tx_info(tx_id.hex())

    return prev_txes


if __name__ == "__main__":
    assert len(INPUTS) > 0, "there are no inputs"
    assert len(OUTPUTS) > 0, "there are no outputs"
    if not all(isinstance(inp, messages.TxInputType) for inp in INPUTS):
        raise RuntimeError("all inputs must be TxInputType")
    if not all(isinstance(out, messages.TxOutputType) for out in OUTPUTS):
        raise RuntimeError("all outputs must be TxOutputType")
    if SAME_SUFFIX:
        assert len(NODES) == len(PATHS_TO_SIGN)
    else:
        assert len(PUBS) == len(PATHS_TO_SIGN)
    assert THRESHOLD <= len(PATHS_TO_SIGN)

    signatures = [b""] * len(PATHS_TO_SIGN)
    for index, path in enumerate(PATHS_TO_SIGN):
        if path is None:
            continue

        if SAME_SUFFIX:
            multisig = messages.MultisigRedeemScriptType(
                nodes=NODES, address_n=SUFFIX, signatures=signatures, m=THRESHOLD
            )
        else:
            multisig = messages.MultisigRedeemScriptType(
                pubkeys=PUBS, signatures=signatures, m=THRESHOLD
            )

        # Changing all the inputs to be signable by this specific path
        inputs = [
            messages.TxInputType(
                address_n=parse_path(path),
                multisig=multisig,
                amount=inp.amount,
                prev_hash=inp.prev_hash,
                prev_index=inp.prev_index,
                script_type=inp.script_type,
            )
            for inp in INPUTS
        ]

        signature, serialized_tx = btc.sign_tx(
            CLIENT, COIN, inputs, OUTPUTS, prev_txes=get_prev_txes(inputs)
        )
        print("signature", signature[0].hex())

        # Saving the current signature to be used in next step
        signatures[index] = signature[0]

    print(80 * "-")
    print(serialized_tx.hex())
