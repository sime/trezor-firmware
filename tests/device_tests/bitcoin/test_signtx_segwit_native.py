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

from trezorlib import btc, messages
from trezorlib.debuglink import TrezorClientDebugLink as Client
from trezorlib.tools import H_, parse_path

from ...bip32 import deserialize
from ...common import assert_tx_matches
from ...tx_cache import TxCache
from ..signtx import request_finished, request_input, request_meta, request_output

B = messages.ButtonRequestType
TX_API_TESTNET = TxCache("Testnet")

TXHASH_20912f = bytes.fromhex(
    "20912f98ea3ed849042efed0fdac8cb4fc301961c5988cba56902d8ffb61c337"
)
TXHASH_091446 = bytes.fromhex(
    "09144602765ce3dd8f4329445b20e3684e948709c5cdcaf12da3bb079c99448a"
)
TXHASH_9c3192 = bytes.fromhex(
    "9c31922be756c06d02167656465c8dc83bb553bf386a3f478ae65b5c021002be"
)
TXHASH_f41cbe = bytes.fromhex(
    "f41cbedd8becee05a830f418d13aa665125464547db5c7a6cd28f21639fe1228"
)
TXHASH_c93480 = bytes.fromhex(
    "c9348040bbc2024e12dcb4a0b4806b0398646b91acf314da028c3f03dd0179fc"
)
TXHASH_31bc1c = bytes.fromhex(
    "31bc1c88ce6ae337a6b3057a16d5bad0b561ad1dfc047d0a7fbb8814668f91e5"
)
TXHASH_a345b8 = bytes.fromhex(
    "a345b85759b385c6446055e4c3baa77e8161a65009dc009489b48aa6587ce348"
)
TXHASH_ec16dc = bytes.fromhex(
    "ec16dc5a539c5d60001a7471c37dbb0b5294c289c77df8bd07870b30d73e2231"
)
TXHASH_b36780 = bytes.fromhex(
    "b36780ceb86807ca6e7535a6fd418b1b788cb9b227d2c8a26a0de295e523219e"
)
TXHASH_fcb3f5 = bytes.fromhex(
    "fcb3f5436224900afdba50e9e763d98b920dfed056e552040d99ea9bc03a9d83"
)
TXHASH_d159fd = bytes.fromhex(
    "d159fd2fcb5854a7c8b275d598765a446f1e2ff510bf077545a404a0c9db65f7"
)
TXHASH_65047a = bytes.fromhex(
    "65047a2b107d6301d72d4a1e49e7aea9cf06903fdc4ae74a4a9bba9bc1a414d2"
)


def test_send_p2sh(client: Client):
    inp1 = messages.TxInputType(
        address_n=parse_path("m/49h/1h/0h/1/0"),
        # 2N1LGaGg836mqSQqiuUBLfcyGBhyZbremDX
        amount=123_456_789,
        prev_hash=TXHASH_20912f,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDP2SHWITNESS,
    )
    out1 = messages.TxOutputType(
        address="tb1qqzv60m9ajw8drqulta4ld4gfx0rdh82un5s65s",
        amount=12_300_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )
    out2 = messages.TxOutputType(
        address="2N1LGaGg836mqSQqiuUBLfcyGBhyZbremDX",
        script_type=messages.OutputScriptType.PAYTOADDRESS,
        amount=123_456_789 - 11_000 - 12_300_000,
    )
    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                request_output(1),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_20912f),
                request_input(0, TXHASH_20912f),
                request_output(0, TXHASH_20912f),
                request_output(1, TXHASH_20912f),
                request_input(0),
                request_output(0),
                request_output(1),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1, out2], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "0100000000010137c361fb8f2d9056ba8c98c5611930fcb48cacfdd0fe2e0449d83eea982f91200000000017160014d16b8c0680c61fc6ed2e407455715055e41052f5ffffffff02e0aebb00000000001600140099a7ecbd938ed1839f5f6bf6d50933c6db9d5c3df39f060000000017a91458b53ea7f832e8f096e896b8713a8c6df0e892ca8702483045022100bd3d8b8ad35c094e01f6282277300e575f1021678fc63ec3f9945d6e35670da3022052e26ef0dd5f3741c9d5939d1dec5464c15ab5f2c85245e70a622df250d4eb7c012103e7bfe10708f715e8538c92d46ca50db6f657bbc455b7494e6a0303ccdb868b7900000000"
    )


def test_send_p2sh_change(client: Client):
    inp1 = messages.TxInputType(
        address_n=parse_path("m/49h/1h/0h/1/0"),
        # 2N1LGaGg836mqSQqiuUBLfcyGBhyZbremDX
        amount=123_456_789,
        prev_hash=TXHASH_20912f,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDP2SHWITNESS,
    )
    out1 = messages.TxOutputType(
        address="tb1qqzv60m9ajw8drqulta4ld4gfx0rdh82un5s65s",
        amount=12_300_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )
    out2 = messages.TxOutputType(
        address_n=parse_path("m/49h/1h/0h/1/0"),
        script_type=messages.OutputScriptType.PAYTOP2SHWITNESS,
        amount=123_456_789 - 11_000 - 12_300_000,
    )
    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                request_output(1),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_20912f),
                request_input(0, TXHASH_20912f),
                request_output(0, TXHASH_20912f),
                request_output(1, TXHASH_20912f),
                request_input(0),
                request_output(0),
                request_output(1),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1, out2], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "0100000000010137c361fb8f2d9056ba8c98c5611930fcb48cacfdd0fe2e0449d83eea982f91200000000017160014d16b8c0680c61fc6ed2e407455715055e41052f5ffffffff02e0aebb00000000001600140099a7ecbd938ed1839f5f6bf6d50933c6db9d5c3df39f060000000017a91458b53ea7f832e8f096e896b8713a8c6df0e892ca8702483045022100bd3d8b8ad35c094e01f6282277300e575f1021678fc63ec3f9945d6e35670da3022052e26ef0dd5f3741c9d5939d1dec5464c15ab5f2c85245e70a622df250d4eb7c012103e7bfe10708f715e8538c92d46ca50db6f657bbc455b7494e6a0303ccdb868b7900000000"
    )


def test_send_native(client: Client):
    inp1 = messages.TxInputType(
        # tb1qajr3a3y5uz27lkxrmn7ck8lp22dgytvagr5nqy
        address_n=parse_path("m/84h/1h/0h/0/87"),
        amount=100_000,
        prev_hash=TXHASH_b36780,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
    )
    out1 = messages.TxOutputType(
        address="2N4Q5FhU2497BryFfUgbqkAJE87aKHUhXMp",
        amount=40_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )
    out2 = messages.TxOutputType(
        address="tb1qe48wz5ysk9mlzhkswcxct9tdjw6ejr2l9e6j8q",
        script_type=messages.OutputScriptType.PAYTOADDRESS,
        amount=100_000 - 40_000 - 10_000,
    )
    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                request_output(1),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_b36780),
                request_input(0, TXHASH_b36780),
                request_output(0, TXHASH_b36780),
                request_output(1, TXHASH_b36780),
                request_input(0),
                request_output(0),
                request_output(1),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1, out2], prev_txes=TX_API_TESTNET
        )

    assert_tx_matches(
        serialized_tx,
        segwit_hash="bc1d39c603d6b59554c5181ec267409086484dcb7e645ed386e29442d8c067fa",
        hash_link="https://tbtc1.trezor.io/api/tx/65047a2b107d6301d72d4a1e49e7aea9cf06903fdc4ae74a4a9bba9bc1a414d2",
        tx_hex="010000000001019e2123e595e20d6aa2c8d227b2b98c781b8b41fda635756eca0768b8ce8067b30000000000ffffffff02409c00000000000017a9147a55d61848e77ca266e79a39bfc85c580a6426c98750c3000000000000160014cd4ee15090b177f15ed0760d85956d93b5990d5f0247304402200c734ed16a9226162a29133c14fad3565332c60346050ceb9246e73a2fc8485002203463d40cf78eb5cc9718d6617d9f251b987e96cb58525795a507acb9b91696c7012103f60fc56bf7b5326537c7e86e0a63b6cd008eeb87d39af324cee5bcc3424bf4d000000000",
    )


def test_send_to_taproot(client: Client):
    inp1 = messages.TxInputType(
        address_n=parse_path("m/84h/1h/0h/0/0"),
        amount=10_000,
        prev_hash=TXHASH_ec16dc,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
    )
    out1 = messages.TxOutputType(
        address="tb1pdvdljpj774356dpk32c2ks0yqv7q7c4f98px2d9e76s73vpudpxs7tl6vp",
        amount=7_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )
    out2 = messages.TxOutputType(
        address="tb1qcc4ext5rsa8pzqa2m030jk670wmn5f649pu7sr",
        script_type=messages.OutputScriptType.PAYTOADDRESS,
        amount=10_000 - 7_000 - 200,
    )
    with client:
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1, out2], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "0100000000010131223ed7300b8707bdf87dc789c294520bbb7dc371741a00605d9c535adc16ec0000000000ffffffff02581b0000000000002251206b1bf9065ef5634d34368ab0ab41e4033c0f62a929c26534b9f6a1e8b03c684df00a000000000000160014c62b932e83874e1103aadbe2f95b5e7bb73a275502473044022008ce0e893e91935ada9a31fe6b2f6228070dd2a5bdebc413429e658be761901502207086e0d3aa6abbad29c966444d3b791e43c174f88154381d07c92a84fec7c527012103adc58245cf28406af0ef5cc24b8afba7f1be6c72f279b642d85c48798685f86200000000"
    )


def test_send_native_change(client: Client):
    inp1 = messages.TxInputType(
        # tb1qajr3a3y5uz27lkxrmn7ck8lp22dgytvagr5nqy
        address_n=parse_path("m/84h/1h/0h/0/87"),
        amount=100_000,
        prev_hash=TXHASH_fcb3f5,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
    )
    out1 = messages.TxOutputType(
        address="2N4Q5FhU2497BryFfUgbqkAJE87aKHUhXMp",  # m/49h/1h/0h/0/0
        amount=40_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )
    out2 = messages.TxOutputType(
        address_n=parse_path("m/84h/1h/0h/1/87"),
        script_type=messages.OutputScriptType.PAYTOWITNESS,
        amount=100_000 - 40_000 - 10_000,
    )
    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                request_output(1),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_fcb3f5),
                request_input(0, TXHASH_fcb3f5),
                request_input(1, TXHASH_fcb3f5),
                request_output(0, TXHASH_fcb3f5),
                request_output(1, TXHASH_fcb3f5),
                request_input(0),
                request_output(0),
                request_output(1),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1, out2], prev_txes=TX_API_TESTNET
        )

    assert_tx_matches(
        serialized_tx,
        segwit_hash="a3668f39bc79f021303892a1a1a0c265ab5e192def801816246ef153b008c630",
        hash_link="https://tbtc1.trezor.io/api/tx/2161a89815814c3866f5953c1e59a977f7cd5432c731cd5633378cfc3fb87fdd",
        tx_hex="01000000000101839d3ac09bea990d0452e556d0fe0d928bd963e7e950bafd0a90246243f5b3fc0000000000ffffffff02409c00000000000017a9147a55d61848e77ca266e79a39bfc85c580a6426c98750c3000000000000160014cc3e33b1eb529cea8b34af5d2c5d6e6e332de9040247304402207413e26bf9eff16513f5ed1db710aa6f766b51f6c6f23ad5e9e8ddf5c67e8aba02204e09b0755ec173f6beeb8ddfa515d36afb25f046d0c851d48fdbc2e0ad3b9f13012103f60fc56bf7b5326537c7e86e0a63b6cd008eeb87d39af324cee5bcc3424bf4d000000000",
    )


def test_send_both(client: Client):
    inp1 = messages.TxInputType(
        address_n=parse_path("m/49h/1h/0h/0/0"),  # 2N4Q5FhU2497BryFfUgbqkAJE87aKHUhXMp
        amount=40_000,
        prev_hash=TXHASH_65047a,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDP2SHWITNESS,
    )
    inp2 = messages.TxInputType(
        address_n=parse_path("m/84h/1h/0h/0/87"),
        amount=100_000,
        prev_hash=TXHASH_d159fd,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
    )
    out1 = messages.TxOutputType(
        address="tb1q54un3q39sf7e7tlfq99d6ezys7qgc62a6rxllc",
        amount=25_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )
    out2 = messages.TxOutputType(
        address="2N6UeBoqYEEnybg4cReFYDammpsyDw8R2Mc",
        script_type=messages.OutputScriptType.PAYTOADDRESS,
        amount=35_000,
    )
    out3 = messages.TxOutputType(
        address="mvbu1Gdy8SUjTenqerxUaZyYjmveZvt33q",
        amount=100_000 + 40_000 - 25_000 - 35_000 - 10_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_input(1),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                request_output(1),
                messages.ButtonRequest(code=B.ConfirmOutput),
                request_output(2),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_65047a),
                request_input(0, TXHASH_65047a),
                request_output(0, TXHASH_65047a),
                request_output(1, TXHASH_65047a),
                request_input(1),
                request_meta(TXHASH_d159fd),
                request_input(0, TXHASH_d159fd),
                request_output(0, TXHASH_d159fd),
                request_output(1, TXHASH_d159fd),
                request_output(2, TXHASH_d159fd),
                request_input(0),
                request_input(1),
                request_output(0),
                request_output(1),
                request_output(2),
                request_input(0),
                request_input(1),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client,
            "Testnet",
            [inp1, inp2],
            [out1, out2, out3],
            prev_txes=TX_API_TESTNET,
        )

    assert_tx_matches(
        serialized_tx,
        segwit_hash="8f22e3e15f3504aa0dcafd6a7ad95606479e0392ee2e594050bf7a7d2f67230a",
        hash_link="https://tbtc1.trezor.io/api/tx/9012ec5daf9f09d79ab7ed63d1881f1e114a4ecc3754208d9254300bbdd8812e",
        tx_hex="01000000000102d214a4c19bba9b4a4ae74adc3f9006cfa9aee7491e4a2dd701637d102b7a046500000000171600140099a7ecbd938ed1839f5f6bf6d50933c6db9d5cfffffffff765dbc9a004a4457507bf10f52f1e6f445a7698d575b2c8a75458cb2ffd59d10000000000ffffffff03a861000000000000160014a579388225827d9f2fe9014add644487808c695db88800000000000017a91491233e24a9bf8dbb19c1187ad876a9380c12e7878770110100000000001976a914a579388225827d9f2fe9014add644487808c695d88ac024730440220109f615c54b409fde8292ff27529dea51497ac6c72d83e555146cfb817e64cda02203b06c0d5ca3529ab56e0ad5fae44184f56afe1fec187ba00e2cb0da387ea7f7e0121033add1f0e8e3c3136f7428dd4a4de1057380bd311f5b0856e2269170b4ffa65bf0248304502210097f6be59665df66777e9804c92ac7c770089f532ce3668be9abc687f6a6f60290220634433824ad8dca5f20a3907d6e370312fdcb652434f6398f1bebe61858cf1cb012103f60fc56bf7b5326537c7e86e0a63b6cd008eeb87d39af324cee5bcc3424bf4d000000000",
    )


@pytest.mark.multisig
def test_send_multisig_1(client: Client):
    nodes = [
        btc.get_public_node(
            client, parse_path(f"m/49h/1h/{index}'"), coin_name="Testnet"
        )
        for index in range(1, 4)
    ]
    multisig = messages.MultisigRedeemScriptType(
        nodes=[deserialize(n.xpub) for n in nodes],
        address_n=[0, 0],
        signatures=[b"", b"", b""],
        m=2,
    )

    inp1 = messages.TxInputType(
        address_n=parse_path("m/49h/1h/1h/0/0"),
        prev_hash=TXHASH_9c3192,
        prev_index=1,
        script_type=messages.InputScriptType.SPENDP2SHWITNESS,
        multisig=multisig,
        amount=1_610_436,
    )

    out1 = messages.TxOutputType(
        address="tb1qch62pf820spe9mlq49ns5uexfnl6jzcezp7d328fw58lj0rhlhasge9hzy",
        amount=1_605_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_9c3192),
                request_input(0, TXHASH_9c3192),
                request_output(0, TXHASH_9c3192),
                request_output(1, TXHASH_9c3192),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        signatures, _ = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )
        # store signature
        inp1.multisig.signatures[0] = signatures[0]
        # sign with third key
        inp1.address_n[2] = H_(3)
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_9c3192),
                request_input(0, TXHASH_9c3192),
                request_output(0, TXHASH_9c3192),
                request_output(1, TXHASH_9c3192),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "01000000000101be0210025c5be68a473f6a38bf53b53bc88d5c46567616026dc056e72b92319c01000000232200208d398cfb58a1d9cdb59ccbce81559c095e8c6f4a3e64966ca385078d9879f95effffffff01887d180000000000220020c5f4a0a4ea7c0392efe0a9670a73264cffa90b19107cd8a8e9750ff93c77fdfb0400483045022100dd6342c65197af27d7894d8b8b88b16b568ee3b5ebfdc55fdfb7caa9650e3b4c02200c7074a5bcb0068f63d9014c7cd2b0490aba75822d315d41aad444e9b86adf5201483045022100e7e6c2d21109512ba0609e93903e84bfb7731ac3962ee2c1cad54a7a30ff99a20220421497930226c39fc3834e8d6da3fc876516239518b0e82e2dc1e3c46271a17c01695221021630971f20fa349ba940a6ba3706884c41579cd760c89901374358db5dd545b92102f2ff4b353702d2bb03d4c494be19d77d0ab53d16161b53fbcaf1afeef4ad0cb52103e9b6b1c691a12ce448f1aedbbd588e064869c79fbd760eae3b8cd8a5f1a224db53ae00000000"
    )


@pytest.mark.multisig
def test_send_multisig_2(client: Client):
    nodes = [
        btc.get_public_node(
            client, parse_path(f"m/84h/1h/{index}'"), coin_name="Testnet"
        )
        for index in range(1, 4)
    ]
    multisig = messages.MultisigRedeemScriptType(
        nodes=[deserialize(n.xpub) for n in nodes],
        address_n=[0, 1],
        signatures=[b"", b"", b""],
        m=2,
    )

    inp1 = messages.TxInputType(
        address_n=parse_path("m/84h/1h/2h/0/1"),
        prev_hash=TXHASH_f41cbe,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
        multisig=multisig,
        amount=1_605_000,
    )

    out1 = messages.TxOutputType(
        address="tb1qr6xa5v60zyt3ry9nmfew2fk5g9y3gerkjeu6xxdz7qga5kknz2ssld9z2z",
        amount=1_604_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_f41cbe),
                request_input(0, TXHASH_f41cbe),
                request_output(0, TXHASH_f41cbe),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        signatures, _ = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )
        # store signature
        inp1.multisig.signatures[1] = signatures[0]
        # sign with first key
        inp1.address_n[2] = H_(1)
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_f41cbe),
                request_input(0, TXHASH_f41cbe),
                request_output(0, TXHASH_f41cbe),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "010000000001012812fe3916f228cda6c7b57d5464541265a63ad118f430a805eeec8bddbe1cf40000000000ffffffff01a0791800000000002200201e8dda334f11171190b3da72e526d441491464769679a319a2f011da5ad312a10400473044022001b7f4f21a8ddcd5e0faaaee3b95515bf8b84f2a7cbfdf66996c64123617a5cf02202fc6a776a7225420dbca759ad4ac83a61d15bf8d2883b6bf1aa31de7437f9b6e0147304402206c4125c1189a3b3e93a77cdf54c60c0538b80e5a03ec74e6ac776dfa77706ee4022035be14de76259b9d8a24863131a06a65b95df02f7d3ace90d52b37e8d94b167f0169522103bab8ecdd9ae2c51a0dc858f4c751b27533143bf6013ba1725ba8a4ecebe7de8c21027d5e55696c875308b03f2ca3d8637f51d3e35da9456a5187aa14b3de8a89534f2103b78eabaea8b3a4868be4f4bb96d6f66973f7081faa7f1cafba321444611c241e53ae00000000"
    )


@pytest.mark.multisig
def test_send_multisig_3_change(client: Client):
    nodes = [
        btc.get_public_node(
            client, parse_path(f"m/84h/1h/{index}'"), coin_name="Testnet"
        )
        for index in range(1, 4)
    ]
    multisig = messages.MultisigRedeemScriptType(
        nodes=[deserialize(n.xpub) for n in nodes],
        address_n=[1, 0],
        signatures=[b"", b"", b""],
        m=2,
    )
    multisig2 = messages.MultisigRedeemScriptType(
        nodes=[deserialize(n.xpub) for n in nodes],
        address_n=[1, 1],
        signatures=[b"", b"", b""],
        m=2,
    )

    inp1 = messages.TxInputType(
        address_n=parse_path("m/84h/1h/1h/1/0"),
        prev_hash=TXHASH_c93480,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
        multisig=multisig,
        amount=1_604_000,
    )

    out1 = messages.TxOutputType(
        address_n=parse_path("m/84h/1h/1h/1/1"),
        amount=1_603_000,
        multisig=multisig2,
        script_type=messages.OutputScriptType.PAYTOP2SHWITNESS,
    )

    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_c93480),
                request_input(0, TXHASH_c93480),
                request_output(0, TXHASH_c93480),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        signatures, _ = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )
        # store signature
        inp1.multisig.signatures[0] = signatures[0]
        # sign with third key
        inp1.address_n[2] = H_(3)
        out1.address_n[2] = H_(3)
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_c93480),
                request_input(0, TXHASH_c93480),
                request_output(0, TXHASH_c93480),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "01000000000101fc7901dd033f8c02da14f3ac916b6498036b80b4a0b4dc124e02c2bb408034c90000000000ffffffff01b87518000000000017a914536250d41937e5b641082447580ff6a8e46c122a870400473044022003c26107a5a47f1f900ef8aa758977530cd13ea37a33971abae8d75cac2f9f34022039e2b8c2c1d0c24ff4fc026652e1f27ad8e3ed6c9bf485f61d9aa691cb57830801483045022100963b0dc0ab46e963a66ab6e69e5e41bac6c4fedc127cac12c560b029d54fe87402205b3bcdcf313dccd78e5dce0540e7d3c8cc1bf83f13c1f9f01811eb791fd35c8101695221039dba3a72f5dc3cad17aa924b5a03c34561465f997d0cb15993f2ca2c0be771c42103cd39f3f08bbd508dce4d307d57d0c70c258c285878bfda579fa260acc738c25d2102cd631ba95beca1d64766f5540885092d0bb384a3c13b6c3a5334d0ebacf51b9553ae00000000"
    )


@pytest.mark.multisig
def test_send_multisig_4_change(client: Client):
    nodes = [
        btc.get_public_node(
            client, parse_path(f"m/49h/1h/{index}'"), coin_name="Testnet"
        )
        for index in range(1, 4)
    ]
    multisig = messages.MultisigRedeemScriptType(
        nodes=[deserialize(n.xpub) for n in nodes],
        address_n=[1, 1],
        signatures=[b"", b"", b""],
        m=2,
    )
    multisig2 = messages.MultisigRedeemScriptType(
        nodes=[deserialize(n.xpub) for n in nodes],
        address_n=[1, 2],
        signatures=[b"", b"", b""],
        m=2,
    )

    inp1 = messages.TxInputType(
        address_n=parse_path("m/49h/1h/1h/1/1"),
        prev_hash=TXHASH_31bc1c,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDP2SHWITNESS,
        multisig=multisig,
        amount=1_603_000,
    )

    out1 = messages.TxOutputType(
        address_n=parse_path("m/49h/1h/1h/1/2"),
        amount=1_602_000,
        multisig=multisig2,
        script_type=messages.OutputScriptType.PAYTOWITNESS,
    )

    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_31bc1c),
                request_input(0, TXHASH_31bc1c),
                request_output(0, TXHASH_31bc1c),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        signatures, _ = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )
        # store signature
        inp1.multisig.signatures[0] = signatures[0]
        # sign with third key
        inp1.address_n[2] = H_(3)
        out1.address_n[2] = H_(3)
        client.set_expected_responses(
            [
                request_input(0),
                request_output(0),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_31bc1c),
                request_input(0, TXHASH_31bc1c),
                request_output(0, TXHASH_31bc1c),
                request_input(0),
                request_output(0),
                request_input(0),
                request_finished(),
            ]
        )
        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1], [out1], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "01000000000101e5918f661488bb7f0a7d04fc1dad61b5d0bad5167a05b3a637e36ace881cbc310000000023220020fa6c73de618ec134eeec0c16f6dd04d46d4347e9a4fd0a95fd7938403a4949f9ffffffff01d071180000000000220020bcea2324dacbcde5a9db90cc26b8df9cbc72010e05cb68cf034df6f0e05239a2040047304402206bbddb45f12e31e77610fd85b50a83bad4426433b1c4860b1c5ddc0a69f803720220087b0607daab14830f4b4941f16b953b38e606ad70029bac24af7267f93c4242014730440220551a0cb6b0d5b3fa0cfd0b07bb5d751494b827b1c6a08702186696cfbc18278302204f37c382876c4117cca656654599b508f2d55fc3b083dc938e3cd8491b29719601695221036a5ec3abd10501409092246fe59c6d7a15fff1a933479483c3ba98b866c5b9742103559be875179d44e438db2c74de26e0bc9842cbdefd16018eae8a2ed989e474722103067b56aad037cd8b5f569b21f9025b76470a72dc69457813d2b76e98dc0cd01a53ae00000000"
    )


def test_multisig_mismatch_inputs_single(client: Client):
    # Ensure that if there is a non-multisig input, then a multisig output
    # will not be identified as a change output.

    # m/84'/1'/0' for "alcohol woman abuse ..." seed.
    node_int = deserialize(
        "Vpub5kFDCYhiYuAzjk7TBQPNFffbexHF7iAd8AVVgHQKUany7e6NQvthgk86d7DfH57DY2dwBK4PyVTDDaS1r2gjkdyJyUYGoV9qNujGSrW9Dpe"
    )

    # m/84'/1'/0' for "all all ... all" seed.
    node_ext = deserialize(
        "Vpub5jR76XyyhBaQXPSRf3PBeY3gF914d9sf7DWFVhMESEQMCdNv35XiVvp8gZsFXAv222VPHLNnAEXxMPG8DPiSuhAXfEydBf55LTLBGHCDzH2"
    )

    # tb1qpzmgzpcumztvmpu3q27wwdggqav26j9dgks92pvnne2lz9ferxgssmhzlq
    multisig_in = messages.MultisigRedeemScriptType(
        nodes=[node_int, node_ext], address_n=[0, 0], signatures=[b"", b""], m=1
    )

    multisig_out = messages.MultisigRedeemScriptType(
        nodes=[node_int, node_ext], address_n=[1, 0], signatures=[b"", b""], m=1
    )

    inp1 = messages.TxInputType(
        address_n=parse_path("m/84h/1h/0h/0/0"),
        amount=12_300_000,
        prev_hash=TXHASH_091446,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
    )

    inp2 = messages.TxInputType(
        address_n=parse_path("m/84h/1h/0h/0/0"),
        prev_hash=TXHASH_a345b8,
        prev_index=0,
        script_type=messages.InputScriptType.SPENDWITNESS,
        multisig=multisig_in,
        amount=100,
    )

    out1 = messages.TxOutputType(
        address="2N4Q5FhU2497BryFfUgbqkAJE87aKHUhXMp",
        amount=5_000_000,
        script_type=messages.OutputScriptType.PAYTOADDRESS,
    )

    out2 = messages.TxOutputType(
        address_n=parse_path("m/84h/1h/0h/1/0"),
        script_type=messages.OutputScriptType.PAYTOWITNESS,
        multisig=multisig_out,
        amount=12_300_000 + 100 - 5_000_000 - 10_000,
    )

    with client:
        client.set_expected_responses(
            [
                request_input(0),
                request_input(1),
                request_output(0),
                messages.ButtonRequest(code=B.ConfirmOutput),
                request_output(1),
                # Ensure that the multisig output is not identified as a change output.
                messages.ButtonRequest(code=B.ConfirmOutput),
                messages.ButtonRequest(code=B.SignTx),
                request_input(0),
                request_meta(TXHASH_091446),
                request_input(0, TXHASH_091446),
                request_output(0, TXHASH_091446),
                request_output(1, TXHASH_091446),
                request_input(1),
                request_meta(TXHASH_a345b8),
                request_input(0, TXHASH_a345b8),
                request_output(0, TXHASH_a345b8),
                request_input(0),
                request_input(1),
                request_output(0),
                request_output(1),
                request_input(0),
                request_input(1),
                request_finished(),
            ]
        )

        _, serialized_tx = btc.sign_tx(
            client, "Testnet", [inp1, inp2], [out1, out2], prev_txes=TX_API_TESTNET
        )

    assert (
        serialized_tx.hex()
        == "010000000001028a44999c07bba32df1cacdc50987944e68e3205b4429438fdde35c76024614090000000000ffffffff48e37c58a68ab4899400dc0950a661817ea7bac3e4556044c685b35957b845a30000000000ffffffff02404b4c000000000017a9147a55d61848e77ca266e79a39bfc85c580a6426c987f43c6f0000000000220020733ecfbbe7e47a74dde6c7645b60cdf627e90a585cde7733bc7fdaf9fe30b37402473044022037dc98b16be542a6e3e1ab32007a74192c43f2498170cc5e1dffb6847e3663e402206715102d0eb59e6461a97c78eb40a8679a04a8921fdafef25f0d3d16cc65de39012103adc58245cf28406af0ef5cc24b8afba7f1be6c72f279b642d85c48798685f8620300473044022070a24bcb00041cbed465f1f546bc59e1e353a6e182393932d5ba96e20bc32ef702202ddc76a97c01465692d5b0a0a61d653f64b9ea833af1810022110fd4d505ff950147512103505f0d82bbdd251511591b34f36ad5eea37d3220c2b81a1189084431ddb3aa3d2103adc58245cf28406af0ef5cc24b8afba7f1be6c72f279b642d85c48798685f86252ae00000000"
    )
