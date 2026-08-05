from __future__ import annotations

from typing import Any, Dict, List

import httpx
import pytest
from pydantic import ValidationError

from examples.dlc import register_brand, register_campaign
from questblue import (
    AsyncQuestBlue,
    BrandCreateRequest,
    BrandCreateResponse,
    BrandLegalType,
    BrandListRequest,
    BrandListResponse,
    BrandUpdateRequest,
    BrandUpdateResponse,
    CampaignCreateRequest,
    CampaignCreateResponse,
    CampaignListRequest,
    CampaignListResponse,
    CampaignType,
    CampaignUpdateRequest,
    DLCYesNo,
    HelpReply,
    LEINumberType,
    QuestBlue,
    QuestBlueAPIError,
    QuestBlueResponseError,
    QuestBlueServerError,
    SpecialCampaignType,
    StandardCampaignType,
    WarningResponse,
)

BRAND = {
    "id": "101",
    "address": "100 Main Street",
    "company_name": "Example Communications",
    "contact": "Compliance Team",
    "legal_type": "Private Company",
    "lei_number": "123456789",
    "lei_number_type": "GIIN",
    "status": "Approved",
    "tax_number": "12-3456789",
    "url": "https://example.test",
    "vertical_type": "Communications",
}

CAMPAIGN = {
    "id": "202",
    "age_gated_contact": "no",
    "brand_id": "101",
    "campaign_description": "Account alerts requested by customers",
    "campaign_did": "15551234567,15557654321",
    "campaign_type": "standard",
    "campaign_type_standard": "Account Notification",
    "consumer_opt_ins": "Customer checks an unchecked consent box",
    "consumer_opt_outs": "STOP immediately suppresses future messages",
    "embedded_link": "no",
    "embedded_phone": "no",
    "loan_arrange": "no",
    "marketing_used": "no",
    "reply_help": "yes",
    "sample_message": "Example Communications: your account was updated. Reply STOP to opt out.",
    "status": "Submitted",
    "vertical_type": "Communications",
}


def response(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/dlc/brand":
        if request.method in ("GET", "POST"):
            return httpx.Response(
                200,
                json={"data": [BRAND], "current_page": 1, "total": 1, "total_pages": 1},
            )
        if request.method == "PUT":
            return httpx.Response(200, json={"data": {}})
        return httpx.Response(200)
    if request.method == "GET":
        return httpx.Response(
            200,
            json={"data": [CAMPAIGN], "current_page": 1, "total": 1, "total_pages": 1},
        )
    if request.method == "POST":
        return httpx.Response(200, json={"data": {"id": "202"}})
    return httpx.Response(200)


def client(handler: Any = response, max_retries: int = 2) -> QuestBlue:
    return QuestBlue(
        "u",
        "p",
        "k",
        max_retries=max_retries,
        http_client=httpx.Client(base_url="https://test", transport=httpx.MockTransport(handler)),
    )


def brand_create_request() -> BrandCreateRequest:
    return BrandCreateRequest(
        company_name="Example Communications",
        legal_type=BrandLegalType.PRIVATE,
        vertical_type=2,
        tax_number="12-3456789",
        lei_number_type=LEINumberType.GIIN,
        lei_number="123456789",
        contact="Compliance Team",
        address="100 Main Street",
        url="https://example.test",
    )


def campaign_create_request(**changes: Any) -> CampaignCreateRequest:
    values: Dict[str, Any] = {
        "brand_id": 101,
        "campaign_type": CampaignType.STANDARD,
        "campaign_type_standard": StandardCampaignType.ACCOUNT_NOTIFICATION,
        "company_name": "Example Communications",
        "vertical_type": 2,
        "campaign_description": "Account alerts requested by customers",
        "sample_message": "Your account was updated. Reply STOP to opt out.",
        "consumer_opt_ins": "Customer checks an unchecked consent box",
        "consumer_opt_outs": "STOP immediately suppresses future messages",
        "reply_help": HelpReply.YES,
        "campaign_did": [15551234567, 15557654321],
        "loan_arrange": DLCYesNo.NO,
        "embedded_link": DLCYesNo.NO,
        "embedded_phone": DLCYesNo.NO,
        "marketing_used": DLCYesNo.NO,
        "age_gated_contact": DLCYesNo.NO,
    }
    values.update(changes)
    return CampaignCreateRequest(**values)


def campaign_update_request() -> CampaignUpdateRequest:
    return CampaignUpdateRequest(id=202, **campaign_create_request().model_dump())


def test_all_sync_dlc_operations_and_fields() -> None:
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response(request)

    qb = client(handler)
    assert isinstance(qb.dlc.list_brands(BrandListRequest(id=[101, 102])), BrandListResponse)
    assert isinstance(qb.dlc.create_brand(brand_create_request()), BrandCreateResponse)
    assert isinstance(
        qb.dlc.update_brand(
            BrandUpdateRequest(
                id=101,
                company_name="Example Communications LLC",
                legal_type=BrandLegalType.PRIVATE,
                vertical_type=2,
                tax_number="12-3456789",
                lei_number_type=LEINumberType.GIIN,
                lei_number="123456789",
                contact="Compliance Team",
                address="100 Main Street",
                url="https://example.test",
            )
        ),
        BrandUpdateResponse,
    )
    assert qb.dlc.delete_brand(101) is None
    assert isinstance(
        qb.dlc.list_campaigns(CampaignListRequest(id=[101, 102])), CampaignListResponse
    )
    assert isinstance(qb.dlc.create_campaign(campaign_create_request()), CampaignCreateResponse)
    assert qb.dlc.update_campaign(campaign_update_request()) is None
    assert qb.dlc.delete_campaign(202) is None

    queries = [(item.method, item.url.path, dict(item.url.params)) for item in seen]
    assert queries[0][2]["id"] == "101,102"
    assert queries[1][2]["legal_type"] == "2"
    assert queries[2][2]["lei_number_type"] == "giin"
    assert queries[4][2]["id"] == "101,102"
    assert queries[5][2]["campaign_type_standard"] == "2"
    assert queries[5][2]["campaign_did"] == "15551234567,15557654321"
    assert queries[6][2]["id"] == "202"


async def test_all_async_dlc_operations_have_parity() -> None:
    http = httpx.AsyncClient(base_url="https://test", transport=httpx.MockTransport(response))
    qb = AsyncQuestBlue("u", "p", "k", http_client=http)
    assert isinstance(await qb.dlc.list_brands(), BrandListResponse)
    assert isinstance(await qb.dlc.create_brand(brand_create_request()), BrandCreateResponse)
    assert isinstance(
        await qb.dlc.update_brand(BrandUpdateRequest(id=101, company_name="New Name")),
        BrandUpdateResponse,
    )
    assert await qb.dlc.delete_brand(101) is None
    assert isinstance(await qb.dlc.list_campaigns(), CampaignListResponse)
    special = campaign_create_request(
        campaign_type=CampaignType.SPECIAL,
        campaign_type_standard=None,
        campaign_type_special=SpecialCampaignType.CHARITY,
    )
    assert isinstance(await qb.dlc.create_campaign(special), CampaignCreateResponse)
    special_update = CampaignUpdateRequest(id=202, **special.model_dump())
    assert await qb.dlc.update_campaign(special_update) is None
    assert await qb.dlc.delete_campaign(202) is None
    await http.aclose()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: BrandListRequest(id=[]),
        lambda: BrandListRequest(id=0),
        lambda: BrandCreateRequest(
            company_name="Example",
            legal_type=BrandLegalType.PRIVATE,
            vertical_type=1,
            tax_number="123",
            lei_number="missing-type",
            contact="Team",
            address="Main Street",
            url="https://example.test",
        ),
        lambda: BrandCreateRequest(
            company_name="Example",
            legal_type=BrandLegalType.PRIVATE,
            vertical_type=1,
            tax_number="123",
            lei_number_type=LEINumberType.LEI,
            contact="Team",
            address="Main Street",
            url="https://example.test",
        ),
        lambda: BrandCreateRequest(
            company_name="Example",
            legal_type=BrandLegalType.PRIVATE,
            vertical_type=0,
            tax_number="123",
            contact="Team",
            address="Main Street",
            url="not-a-url",
        ),
        lambda: BrandUpdateRequest(id=101),
        lambda: BrandUpdateRequest(id=101, lei_number="missing-type"),
        lambda: campaign_create_request(campaign_type_standard=None),
        lambda: campaign_create_request(campaign_type_special=SpecialCampaignType.CHARITY),
        lambda: campaign_create_request(
            campaign_type=CampaignType.SPECIAL,
            campaign_type_standard=None,
            campaign_type_special=None,
        ),
        lambda: campaign_create_request(campaign_did="not-a-number"),
        lambda: campaign_create_request(campaign_did=[]),
        lambda: campaign_create_request(campaign_did=5551234),
    ],
)
def test_dlc_validation(factory: Any) -> None:
    with pytest.raises((ValidationError, ValueError)):
        factory()


def test_sensitive_registration_fields_are_hidden_from_diagnostics() -> None:
    brand = brand_create_request()
    assert "12-3456789" not in repr(brand)
    assert "100 Main Street" not in repr(brand)
    campaign = campaign_create_request()
    assert "Reply STOP" not in repr(campaign)
    assert "15551234567" not in repr(campaign)
    with pytest.raises(ValidationError) as invalid:
        campaign_create_request(campaign_did="private-invalid-value")
    assert "private-invalid-value" not in str(invalid.value)


@pytest.mark.parametrize("status", ["Approved", "Pending", "Rejected", "Provider Review"])
def test_brand_lifecycle_is_forward_compatible(status: str) -> None:
    payload = {**BRAND, "status": status, "provider_detail": {"score": 91}}
    result = BrandListResponse(data=[payload])
    assert result.data[0].status is not None and result.data[0].status.value == status
    assert result.data[0].extra_fields == {"provider_detail": {"score": 91}}


@pytest.mark.parametrize(
    "status", ["Submitted", "Approved", "Pending", "Rejected", "Carrier Review"]
)
def test_campaign_lifecycle_is_forward_compatible(status: str) -> None:
    result = CampaignListResponse(data=[{**CAMPAIGN, "status": status}])
    assert result.data[0].status is not None and result.data[0].status.value == status


def test_pagination_and_guarded_workflow_examples() -> None:
    assert BrandListResponse(current_page=1, total_pages=2).next_page() == 2
    assert BrandListResponse(current_page=2, total_pages=2).next_page() is None
    assert CampaignListResponse(current_page=1, total_pages=2).next_page() == 2
    assert CampaignListResponse(current_page=2, total_pages=2).next_page() is None
    string_dids = campaign_create_request(campaign_did="15551234567 15557654321")
    assert string_dids.campaign_did == "15551234567 15557654321"
    qb = client()
    with pytest.raises(ValueError, match="confirm_registration_is_accurate"):
        register_brand(qb, brand_create_request())
    assert isinstance(
        register_brand(qb, brand_create_request(), confirm_registration_is_accurate=True),
        BrandCreateResponse,
    )
    with pytest.raises(ValueError, match="confirm_compliance_review"):
        register_campaign(qb, campaign_create_request())
    assert isinstance(
        register_campaign(qb, campaign_create_request(), confirm_compliance_review=True),
        CampaignCreateResponse,
    )


def test_warning_rejection_details_malformed_responses_and_retry_safety() -> None:
    warning_payload = {
        "warning": ["registration accepted with caveat"],
        "registration": {"field": "campaign_did", "code": "pending_review"},
    }
    warning = client(lambda _: httpx.Response(202, json=warning_payload))
    result = warning.dlc.delete_campaign(202)
    assert isinstance(result, WarningResponse)
    assert result.extra_fields == {"registration": warning_payload["registration"]}
    typed_warning = warning.dlc.list_brands()
    assert isinstance(typed_warning, WarningResponse)
    assert typed_warning.extra_fields == {"registration": warning_payload["registration"]}

    rejection_payload = {
        "error": "campaign rejected",
        "validation": [{"field": "consumer_opt_ins", "reason": "insufficient detail"}],
        "registration_id": "reg-123",
    }
    rejected = client(lambda _: httpx.Response(206, json=rejection_payload))
    with pytest.raises(QuestBlueAPIError, match="campaign rejected") as caught:
        rejected.dlc.create_campaign(campaign_create_request())
    assert caught.value.details == rejection_payload

    malformed = client(lambda _: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(QuestBlueResponseError, match="body for an empty 10DLC response"):
        malformed.dlc.delete_brand(101)

    attempts = 0

    def uncertain(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    unsafe = client(uncertain, max_retries=10)
    with pytest.raises(QuestBlueServerError):
        unsafe.dlc.update_campaign(campaign_update_request())
    assert attempts == 1
