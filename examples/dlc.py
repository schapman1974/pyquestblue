"""Accuracy- and compliance-gated 10DLC registration examples."""

from questblue import (
    BrandCreateRequest,
    BrandCreateResponse,
    CampaignCreateRequest,
    CampaignCreateResponse,
    QuestBlue,
    WarningResponse,
)


def register_brand(
    client: QuestBlue,
    request: BrandCreateRequest,
    *,
    confirm_registration_is_accurate: bool = False,
) -> BrandCreateResponse:
    if not confirm_registration_is_accurate:
        raise ValueError(
            "verify the legal registration and set confirm_registration_is_accurate=True"
        )
    result = client.dlc.create_brand(request)
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    return result


def register_campaign(
    client: QuestBlue,
    request: CampaignCreateRequest,
    *,
    confirm_compliance_review: bool = False,
) -> CampaignCreateResponse:
    if not confirm_compliance_review:
        raise ValueError(
            "complete the consent/content review and set confirm_compliance_review=True"
        )
    result = client.dlc.create_campaign(request)
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    return result
