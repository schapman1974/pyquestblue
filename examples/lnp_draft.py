"""Create a reviewed LNP draft without accidentally submitting a production port."""

from pathlib import Path

from questblue import LNPBillUpload, LNPCreateRequest, LNPSubmissionStatus, QuestBlue


def create_draft(
    client: QuestBlue,
    bill_path: Path,
    *,
    confirm_production_draft: bool = False,
) -> object:
    if not confirm_production_draft:
        raise ValueError("QuestBlue has no documented sandbox; confirm the production draft")
    bill = LNPBillUpload.from_path(bill_path)
    request = LNPCreateRequest.with_bill(
        bill,
        number2port=[15551234567],
        provider_name="Current Carrier",
        account_no="account-number",
        authorize_contact="Jane Customer",
        contact_title="Owner",
        street_no="123",
        street_name="Main Street",
        city="Cary",
        state="NC",
        zipcode="27513",
        billing_telephone_no="5551234567",
        company="Example LLC",
        status=LNPSubmissionStatus.DRAFT,
    )
    return client.lnp.create(request)
