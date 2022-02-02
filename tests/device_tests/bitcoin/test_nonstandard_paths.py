# This file is part of the Trezor project.
#
# Copyright (C) 2012-2021 SatoshiLabs and contributors
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the License along with this library.
# If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>.

import pytest

from trezorlib import btc, messages
from trezorlib.tools import parse_path

from ...tx_cache import TxCache

TX_CACHE_MAINNET = TxCache("Bitcoin")
TX_CACHE_TESTNET = TxCache("Testnet")

TXHASH_6189e3 = bytes.fromhex(
    "6189e3febb5a21cee8b725aa1ef04ffce7e609448446d3a8d6f483c634ef5315"
)
TXHASH_564f5b = bytes.fromhex(
    "564f5b97aecb5608d6bdd021856ad55aeecaebd2d61b598b7161004f9619d662"
)


# Index corresponds to UTXO index in a transaction
VECTORS = (  # path, script_types_and_indexes
    # GreenAddress A m/[1,4]/address_index
    (
        "m/4/255",
        (
            # mtTCmwhifioeTxufJ3WY1wvqjfia2NQT8F
            (messages.InputScriptType.SPENDADDRESS, 7),
            # tb1q3hjq7v0jlxz0g2v4nntp67ufg65059z45kg8j6
            (messages.InputScriptType.SPENDWITNESS, 3),
            # 2N26epREypYGMKf8X325nzBozi5gvjYPwab
            (messages.InputScriptType.SPENDP2SHWITNESS, 10),
        ),
    ),
    # GreenAddress B m/3'/[1-100]'/[1,4]/address_index
    (
        "m/3'/100'/4/255",
        (
            # mtCrtJvkMRYmXpy9vxPxiGskLAmnku4xFb
            (messages.InputScriptType.SPENDADDRESS, 6),
            # tb1q3vk6rcwav6f4tadutzgjvvfut4v4fr5uj03v8q
            (messages.InputScriptType.SPENDWITNESS, 2),
            # 2NDQqoJ9n7xN7WxmKY36GDd1N7HhcvCmK8y
            (messages.InputScriptType.SPENDP2SHWITNESS, 11),
        ),
    ),
    # GreenAdress Sign A m/1195487518
    (
        "m/1195487518",
        (
            # mnN9Pyq16W2MFif5C26pctxHV7aY9Ke5at
            (messages.InputScriptType.SPENDADDRESS, 4),
            # tb1qfv0x0zcd59lzlgdrq04n77pq3pqdc04m3zl7vk
            (messages.InputScriptType.SPENDWITNESS, 0),
            # 2MuaBfmxqnoVzubA1kFqedhZg9HBtJFrTJ6
            (messages.InputScriptType.SPENDP2SHWITNESS, 9),
        ),
    ),
    # GreenAdress Sign B m/1195487518/6/address_index
    (
        "m/1195487518/6/255",
        (
            # mnc2ekbsFQbJvpgszDu3kXj9duzLLiKddm
            (messages.InputScriptType.SPENDADDRESS, 5),
            # tb1qfklf3clkeve84h50np0nkhrhac9zlyp3m55kj8
            (messages.InputScriptType.SPENDWITNESS, 1),
            # 2MuFjiqJ7mtn3Vr9Mq4NfuTeZsKYd1PUByV
            (messages.InputScriptType.SPENDP2SHWITNESS, 8),
        ),
    ),
    # Casa m/49/coin_type/account/change/address_index
    (
        "m/49/0/63/0/255",
        (
            # 2NG4J8UkePVX9LbGBX3u6ffYPuLhKD9oCDc
            (messages.InputScriptType.SPENDP2SHWITNESS, 12),
        ),
    ),
)

# 2-of-3 multisig, first path is ours
VECTORS_MULTISIG = (
    # GreenAddress A m/[1,4]/address_index
    (("m/1", "m/1", "m/4"), [255]),
    # GreenAddress B m/3'/[1-100]'/[1,4]/address_index
    (("m/3'/100'/1", "m/3'/99'/1", "m/3'/98'/1"), [255]),
    # GreenAdress Sign A m/1195487518
    (("m/1195487518", "m/1195487518", "m/1195487518"), []),
    # GreenAdress Sign B m/1195487518/6/address_index
    (("m/1195487518/6", "m/1195487518/6", "m/1195487518/6"), [255]),
    # Unchained hardened m/45'/coin_type'/account'/[0-1000000]/change/address_index
    (
        ("m/45'/0'/63'/1000000", "m/45'/0'/62'/1000000", "m/45'/0'/61'/1000000"),
        [0, 255],
    ),
    # Unchained unhardened m/45'/coin_type/account/[0-1000000]/change/address_index
    (("m/45'/0/63/1000000", "m/45'/0/62/1000000", "m/45'/0/61/1000000"), [0, 255]),
    # Unchained deprecated m/45'/coin_type'/account'/[0-1000000]/address_index
    (("m/45'/0'/63'/1000000", "m/45'/0'/62'/1000000", "m/45'/0/61/1000000"), [255]),
)


# Has AlwaysMatchingSchema but let's make sure the nonstandard paths are
# accepted in case we make this more restrictive in the future.
@pytest.mark.parametrize("path, script_types_and_indexes", VECTORS)
def test_getpublicnode(client, path, script_types_and_indexes):
    for script_type, _ in script_types_and_indexes:
        res = btc.get_public_node(
            client, parse_path(path), coin_name="Bitcoin", script_type=script_type
        )

        assert res.xpub


@pytest.mark.parametrize("path, script_types_and_indexes", VECTORS)
def test_getaddress(client, path, script_types_and_indexes):
    for script_type, _ in script_types_and_indexes:
        res = btc.get_address(
            client,
            "Bitcoin",
            parse_path(path),
            show_display=True,
            script_type=script_type,
        )

        assert res


@pytest.mark.parametrize("path, script_types_and_indexes", VECTORS)
def test_signmessage(client, path, script_types_and_indexes):
    for script_type, _ in script_types_and_indexes:
        sig = btc.sign_message(
            client,
            coin_name="Bitcoin",
            n=parse_path(path),
            script_type=script_type,
            message="This is an example of a signed message.",
        )

        assert sig.signature


@pytest.mark.parametrize("path, script_types_and_indexes", VECTORS)
def test_signtx(client, path, script_types_and_indexes):
    # tx: d5f65ee80147b4bcc70b75e4bbf2d7382021b871bd8867ef8fa525ef50864882
    # input 0: 0.0039 BTC

    for script_type, utxo_index in script_types_and_indexes:
        inp1 = messages.TxInputType(
            address_n=parse_path(path),
            amount=10_000,
            prev_hash=TXHASH_564f5b,
            prev_index=utxo_index,
            script_type=script_type,
        )

        out1 = messages.TxOutputType(
            address="1MJ2tj2ThBE62zXbBYA5ZaN3fdve5CPAz1",
            amount=10_000 - 1_000,
            script_type=messages.OutputScriptType.PAYTOADDRESS,
        )

        _, serialized_tx = btc.sign_tx(
            client, "Bitcoin", [inp1], [out1], prev_txes=TX_CACHE_TESTNET
        )

        assert serialized_tx.hex()


@pytest.mark.multisig
@pytest.mark.parametrize("paths, address_index", VECTORS_MULTISIG)
def test_getaddress_multisig(client, paths, address_index):
    pubs = [
        messages.HDNodePathType(
            node=btc.get_public_node(
                client, parse_path(path), coin_name="Bitcoin"
            ).node,
            address_n=address_index,
        )
        for path in paths
    ]
    multisig = messages.MultisigRedeemScriptType(pubkeys=pubs, m=2)

    address = btc.get_address(
        client,
        "Bitcoin",
        parse_path(paths[0]) + address_index,
        show_display=True,
        multisig=multisig,
        script_type=messages.InputScriptType.SPENDMULTISIG,
    )

    assert address


# NOTE: we're signing input using the wrong key (and possibly script type) so
#       the test is going to fail if we make firmware stricter about this
@pytest.mark.multisig
@pytest.mark.parametrize("paths, address_index", VECTORS_MULTISIG)
def test_signtx_multisig(client, paths, address_index):
    pubs = [
        messages.HDNodePathType(
            node=btc.get_public_node(
                client, parse_path(path), coin_name="Bitcoin"
            ).node,
            address_n=address_index,
        )
        for path in paths
    ]
    signatures = [b""] * 3
    multisig = messages.MultisigRedeemScriptType(
        pubkeys=pubs, signatures=signatures, m=2
    )

    out1 = messages.TxOutputType(
        address="17kTB7qSk3MupQxWdiv5ZU3zcrZc2Azes1",
        amount=10000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    inp1 = messages.TxInputType(
        address_n=parse_path(paths[0]) + address_index,
        amount=20000,
        prev_hash=TXHASH_6189e3,
        prev_index=1,
        script_type=messages.InputScriptType.SPENDMULTISIG,
        multisig=multisig,
    )

    sig, _ = btc.sign_tx(client, "Bitcoin", [inp1], [out1], prev_txes=TX_CACHE_MAINNET)

    assert sig[0]
