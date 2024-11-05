import base64
import re

import algokit_utils
import pytest
from algokit_utils import (
    Account,
    TransferParameters,
    get_localnet_default_account,
    transfer,
)
from algokit_utils.config import config
from algosdk import abi, transaction
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from smart_contracts.artifacts.asa_box.asa_box_client import AsaBoxClient

data = "{test_json}"


@pytest.fixture(scope="session")
def creator(algod_client: AlgodClient) -> Account:
    account = get_localnet_default_account(algod_client)
    return account


@pytest.fixture(scope="session")
def asa_box_client(
    algod_client: AlgodClient, indexer_client: IndexerClient, creator: Account
) -> AsaBoxClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )
    client = AsaBoxClient(
        algod_client,
        creator=creator,
        indexer_client=indexer_client,
    )

    client.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
        delete_args=None,
    )
    return client


@pytest.fixture(scope="session")
def asa_id(creator: Account, asa_box_client: AsaBoxClient) -> int:
    # Create an asset with a total supply of 10 units
    account_info = asa_box_client.algod_client.account_info(creator.address)
    if len(account_info["created-assets"]) == 0:

        # algorand://?app=<app-id>&box=<asa-id>
        atxn = transaction.AssetCreateTxn(
            sender=creator.address,
            manager=creator.address,
            url=f"algorand://?app={asa_box_client.app_id}&box=<asa-id>",
            total=10,
            decimals=0,
            default_frozen=False,
            sp=asa_box_client.algod_client.suggested_params(),
            metadata_hash=b"ARC-XX".ljust(32, b"\x00"),
        ).sign(creator.private_key)
        tx_id = asa_box_client.algod_client.send_transaction(atxn)
        results = transaction.wait_for_confirmation(
            asa_box_client.algod_client,
            tx_id,
            4,
        )
        # Return the asset ID after the transaction is confirmed
        asa_id = results["asset-index"]
    else:
        asa_id = account_info["created-assets"][0]["index"]
    return asa_id


def test_update_metadata(
    asa_box_client: AsaBoxClient, creator: Account, asa_id: int
) -> None:

    if (
        asa_box_client.algod_client.account_info(
            asa_box_client.app_address,
        )["amount"]
        == 0
    ):
        mbr = 2_500 + (400 * (8 + len(data))) + 100_000
        transfer(
            asa_box_client.algod_client,
            TransferParameters(
                from_account=creator,
                to_address=asa_box_client.app_address,
                micro_algos=mbr,
            ),
        )

    if (
        len(
            asa_box_client.algod_client.application_boxes(
                asa_box_client.app_id,
            )["boxes"]
        )
        == 0
    ):
        asa_box_client.update_metadata(
            asa_id=asa_id,
            data=data,
            transaction_parameters=algokit_utils.TransactionParameters(
                boxes=[(asa_box_client.app_id, asa_id)],
            ),
        )

    box_value = asa_box_client.algod_client.application_box_by_name(
        asa_box_client.app_id, abi.ABIType.from_string("uint64").encode(asa_id)
    )["value"]

    assert base64.b64decode(box_value).decode("utf-8") == data


def test_get_metadata(
    asa_box_client: AsaBoxClient, creator: Account, asa_id: int
) -> None:
    metadata = asa_box_client.algod_client.asset_info(
        asa_id,
    )[
        "params"
    ]["metadata-hash"]
    assert base64.b64decode(metadata).rstrip(b"\x00") == b"ARC-XX"
    url = asa_box_client.algod_client.asset_info(asa_id)["params"]["url"]
    app_id = int(re.search(r"app=(\d+)", url).group(1))
    print(app_id)
    box_value = asa_box_client.algod_client.application_box_by_name(
        app_id, abi.ABIType.from_string("uint64").encode(asa_id)
    )["value"]
    assert base64.b64decode(box_value).decode("utf-8") == data
    output = asa_box_client.get_metadata(
        asa_id=asa_id,
        transaction_parameters=algokit_utils.TransactionParameters(
            boxes=[(app_id, asa_id)],
        ),
    )
    assert output.return_value == data


def test_delete_metadata(
    asa_box_client: AsaBoxClient, creator: Account, asa_id: int
) -> None:

    params = asa_box_client.algod_client.suggested_params()
    params.min_fee = 2000
    asa_box_client.delete_metadata(
        asa_id=asa_id,
        transaction_parameters=algokit_utils.TransactionParameters(
            boxes=[(asa_box_client.app_id, asa_id)], suggested_params=params
        ),
    )
    boxes = asa_box_client.algod_client.application_boxes(
        asa_box_client.app_id,
    )["boxes"]
    assert len(boxes) == 0


def test_delete_application(asa_box_client: AsaBoxClient, creator: Account):
    params = asa_box_client.algod_client.suggested_params()
    params.min_fee = 2000

    asa_box_client.delete_delete_application(
        transaction_parameters=algokit_utils.TransactionParameters(
            suggested_params=params
        ),
    )

    account_info = asa_box_client.algod_client.account_info(creator.address)
    print(account_info)
    assert len(account_info["created-apps"]) == 0


def test_delete_asa(asa_box_client: AsaBoxClient, creator: Account, asa_id: int):
    atxn = transaction.AssetDestroyTxn(
        sender=creator.address,
        sp=asa_box_client.algod_client.suggested_params(),
        index=asa_id,
    ).sign(creator.private_key)
    asa_box_client.algod_client.send_transaction(atxn)

    account_info = asa_box_client.algod_client.account_info(creator.address)
    assert len(account_info["created-assets"]) == 0
