"""
Create a multisig address controlled by the connected Trezor.

There are two possibilities how to create MultisigRedeemScriptType,
defined in branches divided by SAME_SUFFIX.
"""
from trezorlib import btc, messages
from trezorlib.client import get_default_client
from trezorlib.tools import parse_path

CLIENT = get_default_client()

COIN = "Testnet"

SAME_SUFFIX = False
if SAME_SUFFIX:
    # for i in {1,2,3}; do trezorctl btc get-public-node -n 48h/1h/${i}h/0h; done
    # trezorctl btc get-address -c Testnet -n m/48h/1h/1h/0h/0/0 -m 2 -x tpubDF4tYm8PaDydbLMZZRqcquYZ6AvxFmyTv6RhSokPh6YxccaCxP1gF2VABKV9wsinAdUbsbdLx1vcXdJH8qRcQMM9VYd926rWM685CepPUdN -x tpubDEhpbishBroZWzT7sQf9YuXiyCUSdkK6Cur95UkDdTRcyrJUhLtn69GhC8mJwrxmXRLSUitWAgsXcQ3Cb16EaqFyMob4LHPqzohSzyMMmP5 -x tpubDFLKt47Wb4BomPVBFW675DKNuhbd9hkx7s1wr2C8GMgQM5Sa5susNc78xKWsjkrkkCQsMT4o7m5RD8ZJqTgh9cjwEQg8pjCxr9Ar77C2wiv
    # address (all all seed): 2NA7EkM5aJxRPf4XURQPAYBnKFdH4B6ZsE6
    # Used in tests/device_tests/bitcoin/test_multisig.py:test_2_of_3
    AMOUNT = 3
    THRESHOLD = 2
    multisig_suffix = [0, 0]
    paths = [f"48h/1h/{x}h/0h" for x in range(1, AMOUNT + 1)]
    public_keys = [
        btc.get_public_node(CLIENT, parse_path(path), coin_name=COIN) for path in paths
    ]
    nodes = [pk.node for pk in public_keys]
    multisig = messages.MultisigRedeemScriptType(
        nodes=nodes, address_n=multisig_suffix, m=THRESHOLD
    )
    address_n = parse_path(paths[0]) + multisig_suffix

    for pk in public_keys:
        print(pk.xpub)
else:
    # address (all all seed): 2NFRJcruwi6hAQBs4zn7sZv4BLXCzWjS4Yd
    # Used in tests/device_tests/bitcoin/test_multisig.py:test_15_of_15
    AMOUNT = 15
    THRESHOLD = 15
    main_path = "48h/1h/1h/0h"
    node = btc.get_public_node(CLIENT, parse_path(main_path), coin_name=COIN).node
    multisig_suffixes = [[0, x] for x in range(AMOUNT)]
    pubs = [
        messages.HDNodePathType(node=node, address_n=suffix)
        for suffix in multisig_suffixes
    ]
    multisig = messages.MultisigRedeemScriptType(pubkeys=pubs, m=THRESHOLD)
    address_n = parse_path(main_path) + multisig_suffixes[0]


address = btc.get_address(
    CLIENT,
    COIN,
    address_n,
    show_display=False,
    script_type=messages.InputScriptType.SPENDMULTISIG,
    multisig=multisig,
)

print(80 * "*")
print("address", address)
