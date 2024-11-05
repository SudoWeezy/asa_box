# from collections.abc import Iterator

# import pytest
# from algopy_testing import AlgopyTestContext, algopy_testing_context
# from asa_box_client_test import asa_id, data

# from smart_contracts.asa_box.contract import AsaBox


# @pytest.fixture()
# def context() -> Iterator[AlgopyTestContext]:
#     with algopy_testing_context() as ctx:
#         yield ctx


# def test_hello(context: AlgopyTestContext) -> None:
#     # Arrange
#     contract = AsaBox()

#     # Act
#     output = contract.get_metadata(asa_id)

#     # Assert
#     assert output == data
