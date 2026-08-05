"""SIP trunk provisioning and troubleshooting examples."""

from questblue import QuestBlue, SIPTrunkCreateRequest, SIPTrunkStatusResponse, WarningResponse


def registration_status(client: QuestBlue, trunk: str) -> SIPTrunkStatusResponse:
    result = client.sip_trunks.status(trunk)
    if isinstance(result, WarningResponse):
        raise RuntimeError("QuestBlue warning: " + "; ".join(result.warning))
    return result


def create_static_trunk(
    client: QuestBlue, trunk: str, address: str, *, confirm_routing_change: bool = False
) -> None:
    if not confirm_routing_change:
        raise ValueError("set confirm_routing_change=True after reviewing the PBX route")
    client.sip_trunks.create(SIPTrunkCreateRequest(trunk=trunk, ip_address=address))
