from algopy import (
    ARC4Contract,
    BoxMap,
    Global,
    String,
    Txn,
    UInt64,
    arc4,
    itxn,
)


class AsaBox(ARC4Contract):
    def __init__(self) -> None:
        self.asa_metadata = BoxMap(UInt64, String, key_prefix="")

    @arc4.abimethod()
    def update_metadata(self, asa_id: UInt64, data: String) -> None:
        """Update metadata.
        Args:
            asa_id (UInt64): An Asa_id
            data (String): json representation of data

        Returns:
            None: Void.
        """
        assert Txn.sender == Global.creator_address
        self.asa_metadata[asa_id] = data

    @arc4.abimethod()
    def delete_metadata(self, asa_id: UInt64) -> None:
        """Delete metadata.
        Args:
            asa_id (UInt64): An Asa_id
        """
        assert Txn.sender == Global.creator_address
        a = (
            8
            + self.asa_metadata.key_prefix.length
            + self.asa_metadata[asa_id].bytes.length
        )
        del self.asa_metadata[asa_id]
        mbr = 2_500 + (400 * (a))
        itxn.Payment(
            receiver=Global.creator_address,
            amount=mbr,
        ).submit()

    @arc4.abimethod(readonly=True)
    def get_metadata(self, asa_id: UInt64) -> String:
        """Get metadata.
        Args:
            asa_id (UInt64): An Asa_id
        Returns:
            data (String): json representation of data
        """
        assert Txn.sender == Global.creator_address
        return self.asa_metadata[asa_id]

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete_application(self) -> None:
        # Only allow the creator to delete the application
        assert Txn.sender == Global.creator_address
        # Send the remaining balance to the creator
        itxn.Payment(
            receiver=Global.creator_address,
            amount=0,
            # Close the account to get back ALL the ALGO in the account
            close_remainder_to=Global.creator_address,
        ).submit()
