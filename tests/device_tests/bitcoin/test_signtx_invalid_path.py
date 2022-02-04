# This file is part of the Trezor project.
#
# Copyright (C) 2012-2019 SatoshiLabs and contributors
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

from trezorlib import btc, device, messages
from trezorlib.exceptions import TrezorFailure
from trezorlib.tools import H_, parse_path

from ...tx_cache import TxCache
from ..signtx import request_finished, request_input, request_meta, request_output

B = messages.ButtonRequestType
TX_CACHE_MAINNET = TxCache("Bitcoin")
TX_CACHE_TESTNET = TxCache("Testnet")
TX_CACHE_BCASH = TxCache("Bcash")

TXHASH_ea19cb = bytes.fromhex(  # FAKE tx
    "ea19cb1b0d5fef96494b68f98e5615c92a81a2f6f322d81d58b2d5d479027031"
)
TXHASH_a5cd2a = bytes.fromhex(
    "a5cd2a706d680587e572df16a8ce5233139a094ebbd148cc66a8004dcc88819c"
)
TXHASH_895ef0 = bytes.fromhex(  # FAKE tx
    "895ef02818df40248b65298ed1a1d773de6578a5c70f60d0657ace6f9b1eaf70"
)
TXHASH_b0cf22 = bytes.fromhex(  # FAKE tx
    "b0cf22558c2a44ceac4c4c58a11fdc39524883623b386594ca010f05e5ed5ad1"
)
TXHASH_3494cc = bytes.fromhex(  # FAKE tx
    "3494cc2588ccec4ee37360e55af5f00d3fb2b95cb84c1a03b89c89b12c7a305e"
)


# Adapted from TestMsgSigntx.test_one_one_fee,
# only changed the coin from Bitcoin to Litecoin.
# Litecoin does not have strong replay protection using SIGHASH_FORKID,
# spending from Bitcoin path should fail.
@pytest.mark.altcoin
def test_invalid_path_fail(client):
    # NOTE: fake input tx

    inp1 = messages.TxInputType(
        address_n=parse_path("44h/0h/0h/0/0"),
        amount=390000,
        prev_hash=TXHASH_895ef0,
        prev_index=0,
    )

    # address is converted from 1MJ2tj2ThBE62zXbBYA5ZaN3fdve5CPAz1 by changing the version
    out1 = messages.TxOutputType(
        address="LfWz9wLHmqU9HoDkMg9NqbRosrHvEixeVZ",
        amount=390000 - 10000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    with pytest.raises(TrezorFailure) as exc:
        btc.sign_tx(client, "Litecoin", [inp1], [out1], prev_txes=TX_CACHE_MAINNET)

    assert exc.value.code == messages.FailureType.DataError
    assert exc.value.message.endswith("Forbidden key path")


# Adapted from TestMsgSigntx.test_one_one_fee,
# only changed the coin from Bitcoin to Litecoin and set safety checks to prompt.
# Litecoin does not have strong replay protection using SIGHASH_FORKID, but
# spending from Bitcoin path should pass with safety checks set to prompt.
@pytest.mark.altcoin
def test_invalid_path_prompt(client):
    # NOTE: fake input tx

    inp1 = messages.TxInputType(
        address_n=parse_path("44h/0h/0h/0/0"),
        amount=390000,
        prev_hash=TXHASH_895ef0,
        prev_index=0,
    )

    # address is converted from 1MJ2tj2ThBE62zXbBYA5ZaN3fdve5CPAz1 by changing the version
    out1 = messages.TxOutputType(
        address="LfWz9wLHmqU9HoDkMg9NqbRosrHvEixeVZ",
        amount=390000 - 10000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    device.apply_settings(
        client, safety_checks=messages.SafetyCheckLevel.PromptTemporarily
    )

    btc.sign_tx(client, "Litecoin", [inp1], [out1], prev_txes=TX_CACHE_MAINNET)


# Adapted from TestMsgSigntx.test_one_one_fee,
# only changed the coin from Bitcoin to Bcash.
# Bcash does have strong replay protection using SIGHASH_FORKID,
# spending from Bitcoin path should work.
@pytest.mark.altcoin
def test_invalid_path_pass_forkid(client):
    # NOTE: fake input tx

    inp1 = messages.TxInputType(
        address_n=parse_path("44h/0h/0h/0/0"),
        amount=390000,
        prev_hash=TXHASH_ea19cb,
        prev_index=0,
    )

    # address is converted from 1MJ2tj2ThBE62zXbBYA5ZaN3fdve5CPAz1 to cashaddr format
    out1 = messages.TxOutputType(
        address="bitcoincash:qr0fk25d5zygyn50u5w7h6jkvctas52n0qxff9ja6r",
        amount=390000 - 10000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    btc.sign_tx(client, "Bcash", [inp1], [out1], prev_txes=TX_CACHE_BCASH)


def test_attack_path_segwit(client):
    # NOTE: fake input tx
    # Scenario: The attacker falsely claims that the transaction uses Testnet paths to
    # avoid the path warning dialog, but in step6_sign_segwit_inputs() uses Bitcoin paths
    # to get a valid signature.

    device.apply_settings(
        client, safety_checks=messages.SafetyCheckLevel.PromptTemporarily
    )

    inp1 = messages.TxInputType(
        # The actual input that the attacker wants to get signed.
        address_n=parse_path("84'/0'/0'/0/0"),
        amount=9426,
        prev_hash=TXHASH_b0cf22,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
    )
    inp2 = messages.TxInputType(
        # The actual input that the attacker wants to get signed.
        # We need this one to be from a different account, so that the match checker
        # allows the transaction to pass.
        address_n=parse_path("84'/0'/1'/0/1"),
        amount=7086,
        prev_hash=TXHASH_3494cc,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
    )

    out1 = messages.TxOutputType(
        # Attacker's Mainnet address encoded as Testnet.
        address="tb1q694ccp5qcc0udmfwgp692u2s2hjpq5h407urtu",
        script_type=messages.OutputScriptType.PAYTOADDRESS,
        amount=9426 + 7086 - 500,
    )

    attack_count = 6

    def attack_processor(msg):
        nonlocal attack_count
        # Make the inputs look like they are coming from Testnet paths until we reach the
        # signing phase.
        if attack_count > 0 and msg.tx.inputs and msg.tx.inputs[0] in (inp1, inp2):
            attack_count -= 1
            msg.tx.inputs[0].address_n[1] = H_(1)

        return msg

    with client:
        client.set_filter(messages.TxAck, attack_processor)
        client.set_expected_responses(
            [
                # Step: process inputs
                request_input(0),
                # Attacker bypasses warning about non-standard path.
                request_input(1),
                # Attacker bypasses warning about non-standard path.
                # Step: approve outputs
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                # Step: verify inputs
                request_input(0),
                request_meta(TXHASH_b0cf22),
                request_input(0, TXHASH_b0cf22),
                request_output(0, TXHASH_b0cf22),
                request_output(1, TXHASH_b0cf22),
                request_input(1),
                request_meta(TXHASH_3494cc),
                request_input(0, TXHASH_3494cc),
                request_output(0, TXHASH_3494cc),
                request_output(1, TXHASH_3494cc),
                # Step: serialize inputs
                request_input(0),
                request_input(1),
                # Step: serialize outputs
                request_output(0),
                # Step: sign segwit inputs
                request_input(0),
                # Trezor must warn about non-standard path before signing.
                messages.ButtonRequest(code=B.UnknownDerivationPath),
                request_input(1),
                # Trezor must warn about non-standard path before signing.
                messages.ButtonRequest(code=B.UnknownDerivationPath),
                request_finished(),
            ]
        )

        btc.sign_tx(client, "Testnet", [inp1, inp2], [out1], prev_txes=TX_CACHE_MAINNET)


@pytest.mark.skip_t1(reason="T1 only prevents using paths known to be altcoins")
def test_invalid_path_fail_asap(client):
    inp1 = messages.TxInputType(
        address_n=parse_path("0"),
        amount=4977040,
        prev_hash=TXHASH_a5cd2a,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
        sequence=4294967293,
    )

    out1 = messages.TxOutputType(
        address_n=parse_path("84h/0h/0h/1/0"),
        amount=4977040,
        script_type=messages.OutputScriptType.PAYTOWITNESS,
    )

    with client:
        client.set_expected_responses(
            [request_input(0), messages.Failure(code=messages.FailureType.DataError)]
        )
        try:
            btc.sign_tx(client, "Testnet", [inp1], [out1], prev_txes=TX_CACHE_TESTNET)
        except TrezorFailure:
            pass
