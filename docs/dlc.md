# 10DLC Brands and Campaigns

All eight documented `/dlc` operations have validated synchronous and asynchronous methods. The
models cover every brand and campaign field in QuestBlue's pinned OpenAPI contract and retain new
provider fields through `extra_fields`.

## Register a brand

```python
from questblue import BrandCreateRequest, BrandLegalType, LEINumberType

brand = qb.dlc.create_brand(
    BrandCreateRequest(
        company_name="Example Communications",
        legal_type=BrandLegalType.PRIVATE,
        vertical_type=2,
        tax_number="12-3456789",
        lei_number_type=LEINumberType.GIIN,
        lei_number="123456789",
        contact="Compliance Team",
        address="100 Main Street",
        url="https://example.com",
    )
)
```

`BrandLegalType` maps the documented registration values: publicly traded (1), private (2),
non-profit (3), and government (4). Legal entity identifier types are `duns`, `giin`, and `lei`;
the number and type must be supplied together when creating a brand. QuestBlue's OpenAPI contract
describes `vertical_type` as an integer and gives examples, but does not publish the complete
integer table, so the SDK validates it as positive without inventing unsupported enum members.

Tax numbers, legal identifiers, contacts, addresses, campaign samples, consent descriptions, and
DIDs are hidden from ordinary model representations and Pydantic validation errors. Explicit
`model_dump()` calls contain the values for transmission and must not be logged.

## Register a campaign

```python
from questblue import (
    CampaignCreateRequest,
    CampaignType,
    DLCYesNo,
    HelpReply,
    StandardCampaignType,
)

campaign = qb.dlc.create_campaign(
    CampaignCreateRequest(
        brand_id=101,
        campaign_type=CampaignType.STANDARD,
        campaign_type_standard=StandardCampaignType.ACCOUNT_NOTIFICATION,
        company_name="Example Communications",
        vertical_type=2,
        campaign_description="Account alerts requested by customers",
        sample_message="Your account was updated. Reply STOP to opt out.",
        consumer_opt_ins="Customer checks an unchecked consent box",
        consumer_opt_outs="STOP immediately suppresses future messages",
        reply_help=HelpReply.YES,
        campaign_did=[15551234567, 15557654321],
        loan_arrange=DLCYesNo.NO,
        embedded_link=DLCYesNo.NO,
        embedded_phone=DLCYesNo.NO,
        marketing_used=DLCYesNo.NO,
        age_gated_contact=DLCYesNo.NO,
    )
)
```

Standard campaigns require exactly one `campaign_type_standard` value (1–12). Special campaigns
require exactly one `campaign_type_special` value (1–10). The named integer enums follow the
descriptions in QuestBlue's contract. Campaign DIDs accept one number, a list, or documented
comma/space-separated text and serialize as a comma-separated query value.

Brand and campaign statuses use open enums: known states are convenient constants while new carrier
states remain readable. HTTP 202 warning models retain additional upstream fields in `extra_fields`.
HTTP 206 rejections raise `QuestBlueAPIError`; its `details` property preserves the exact validation
and registration detail returned by QuestBlue.

10DLC submission can create fees and regulatory obligations. Verify legal identity, campaign/use
case, sample messages, opt-in evidence, opt-out and HELP handling, age-gated/loan/affiliate flags,
and assigned DIDs before submitting. Registration does not itself establish consent to message a
recipient. Mutations are attempted once and are not automatically retried. Use a provider-approved
test account because QuestBlue does not document a general-purpose public sandbox.

See `examples/dlc.py` for executable accuracy- and compliance-gated registration helpers.

| SDK method | Operation | Models |
| --- | --- | --- |
| `qb.dlc.list_brands()` | `GET /dlc/brand` | `BrandListRequest` → `BrandListResponse` |
| `qb.dlc.create_brand()` | `POST /dlc/brand` | `BrandCreateRequest` → `BrandCreateResponse` |
| `qb.dlc.update_brand()` | `PUT /dlc/brand` | `BrandUpdateRequest` → `BrandUpdateResponse` |
| `qb.dlc.delete_brand()` | `DELETE /dlc/brand` | `BrandDeleteRequest` → empty/warning |
| `qb.dlc.list_campaigns()` | `GET /dlc/campaign` | `CampaignListRequest` → `CampaignListResponse` |
| `qb.dlc.create_campaign()` | `POST /dlc/campaign` | `CampaignCreateRequest` → `CampaignCreateResponse` |
| `qb.dlc.update_campaign()` | `PUT /dlc/campaign` | `CampaignUpdateRequest` → empty/warning |
| `qb.dlc.delete_campaign()` | `DELETE /dlc/campaign` | `CampaignDeleteRequest` → empty/warning |
