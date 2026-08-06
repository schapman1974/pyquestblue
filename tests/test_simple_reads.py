from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from questblue import AsyncSimpleQuestBlue, SimpleQuestBlue
from questblue.account import (
    AccountBalance,
    AccountBalanceResponse,
    AccountDetailsResponse,
    ServiceRates,
)
from questblue.did import AvailableDIDsResponse, DIDInventoryResponse, FraudValidationResponse
from questblue.lnp import LNPCheckResponse, LNPListResponse
from questblue.models import WarningResponse
from questblue.reports import CallDetailRecord, FaxHistoryRecord, FaxService
from questblue.servers import BackupListResponse, ServerListResponse
from questblue.simple import QuestBlueWarningError, SimpleCollection, SimpleRecord
from questblue.simple._read import (
    AccountReads,
    AsyncAccountReads,
    AsyncDLCReads,
    AsyncEnterpriseFaxReads,
    AsyncFaxReads,
    AsyncInternationalNumberReads,
    AsyncMessageReads,
    AsyncNumberReads,
    AsyncPortingReads,
    AsyncReportReads,
    AsyncServerReads,
    AsyncVoiceReads,
    DLCReads,
    EnterpriseFaxReads,
    FaxReads,
    InternationalNumberReads,
    MessageReads,
    NumberReads,
    PortingReads,
    ReportReads,
    ServerReads,
    VoiceReads,
)


def response(data: object) -> SimpleNamespace:
    return SimpleNamespace(data=data)


def test_facades_install_concrete_read_services() -> None:
    raw = MagicMock()
    simple = SimpleQuestBlue.wrap(raw)
    assert isinstance(simple.account, AccountReads)
    assert isinstance(simple.numbers, NumberReads)
    assert isinstance(simple.reports, ReportReads)

    async_raw = MagicMock()
    from questblue import AsyncQuestBlue

    async_raw = MagicMock(spec=AsyncQuestBlue)
    for name in (
        "account",
        "dids",
        "international_dids",
        "sip_trunks",
        "sms",
        "dlc",
        "fax",
        "enterprise_fax",
        "reports",
        "lnp",
        "servers",
    ):
        setattr(async_raw, name, MagicMock())
    async_simple = AsyncSimpleQuestBlue.wrap(async_raw)
    assert isinstance(async_simple.account, AsyncAccountReads)
    assert isinstance(async_simple.numbers, AsyncNumberReads)


def test_simple_record_and_collection_sequence_contract() -> None:
    record = SimpleRecord(AccountBalance(balance=Decimal("1"), allowed_credit=Decimal("2")))
    collection = SimpleCollection((record, "x"), (response([]),))
    assert record.balance == Decimal("1")
    assert record.to_dict()["balance"] == "1"
    assert list(collection) == [record, "x"]
    assert collection[0] is record
    assert len(collection) == 2
    assert collection.to_dict()["items"][1] == "x"
    assert "SimpleCollection" in repr(collection)


def test_account_reads_map_balance_details_rates_and_warning() -> None:
    raw = MagicMock()
    raw.balance.return_value = AccountBalanceResponse(
        data=AccountBalance(balance=Decimal("12.50"), allowed_credit=Decimal("3"))
    )
    raw.details.return_value = AccountDetailsResponse(data=[])
    raw.rates.return_value = ServiceRates(
        local_did_cost=1, inbound_call_rate=2, vps_server_rate=3, ccrf=4
    )
    service = AccountReads(raw)
    assert service.balance() == Decimal("12.50")
    assert service.details().raw == (raw.details.return_value,)
    assert service.rates().raw is raw.rates.return_value
    raw.balance.return_value = WarningResponse(warning=["no balance"])
    with pytest.raises(QuestBlueWarningError):
        service.balance()


def test_number_reads_normalize_and_map_all_operations() -> None:
    raw = MagicMock()
    raw.available.return_value = AvailableDIDsResponse(data=["19195550100"], total=1)
    raw.pages.return_value = iter(
        [DIDInventoryResponse(data={"a": ["19195550100"]}, total=1, total_pages=1)]
    )
    raw.list.return_value = DIDInventoryResponse(data={"a": ["19195550101"]})
    raw.validate_fraud.return_value = FraudValidationResponse(data=[{"tn": "ok"}])
    service = NumberReads(raw)
    found = service.search(zip_code="27513", prefix_code="91", limit=5)
    request = raw.available.call_args.args[0]
    assert (request.zip, request.code, request.total_list) == (27513, 91, 5)
    assert found[0] == "19195550100"
    assert service.list()[0] == "19195550100"
    assert service.list(all_pages=False)[0] == "19195550101"
    service.validate_fraud(["+1 919 555 0100"])
    assert raw.validate_fraud.call_args.args[0] == [19195550100]


def test_international_and_voice_reads_map_primitives() -> None:
    international = MagicMock()
    international.countries.return_value = response(["US"])
    international.cities.return_value = response(["London"])
    international.pages.return_value = iter([response(["442071234567"])])
    international.list.return_value = response(["442071234568"])
    service = InternationalNumberReads(international)
    assert service.countries(number="+1 919 555 0100")[0] == "US"
    assert international.countries.call_args.args[0].did == 19195550100
    assert service.cities("GB")[0] == "London"
    assert service.list()[0] == "442071234567"
    assert service.list(all_pages=False)[0] == "442071234568"

    voice = MagicMock()
    voice.list.return_value = response(["trunk-a"])
    voice.status.return_value = response("registered")
    voice.blocked_callers.return_value = response(["blocked"])
    reads = VoiceReads(voice)
    assert reads.trunks(trunk="a")[0] == "trunk-a"
    assert reads.trunk_status("a").raw.data == "registered"
    assert reads.blocked_callers(trunk=["a"], number="9195550100")[0] == "blocked"
    request = voice.blocked_callers.call_args.args[0]
    assert request.trunk == ["a"] and request.did == 9195550100


def test_message_reads_map_filters_status_carrier_and_offnet() -> None:
    raw = MagicMock()
    raw.list.return_value = response(["number"])
    raw.history.return_value = response(["message"])
    raw.delivery_status.return_value = response(SimpleNamespace(status="delivered"))
    raw.carrier.return_value = response(["carrier"])
    raw.offnet_status.return_value = response(SimpleNamespace(status="ready"))
    service = MessageReads(raw)
    assert service.numbers(number="919")[0] == "number"
    assert (
        service.history(period=(date(2026, 1, 1), date(2026, 1, 2)), direction="inbound")[0]
        == "message"
    )
    assert service.delivery_status("42").status == "delivered"
    assert service.carrier("+1 919 555 0100")[0] == "carrier"
    assert service.offnet_status("9195550100").status == "ready"
    assert raw.delivery_status.call_args.args[0].msg_id == 42
    assert raw.carrier.call_args.args[0].tn == [19195550100]


def test_report_reads_auto_collect_and_normalize_ranges() -> None:
    raw = MagicMock()
    call = CallDetailRecord.model_construct(id="1")
    fax = FaxHistoryRecord.model_construct(
        did_from="1",
        did_to="2",
        fax_id="3",
        send_time=datetime.now(timezone.utc),
        service=FaxService.PRO,
        status="ok",
        type="inbound",
    )
    raw.iter_call_history.return_value = iter([call])
    raw.iter_fax_history.return_value = iter([fax])
    service = ReportReads(raw)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert service.calls(period=(start, end), number="9195550100")[0].raw is call
    call_request = raw.iter_call_history.call_args.args[0]
    assert call_request.period.start == int(start.timestamp())
    assert service.faxes(numbers="9195550100", period=(start, end))[0].raw is fax
    assert raw.iter_fax_history.call_args.args[0].did == [9195550100]


def test_porting_and_server_reads_map_requests() -> None:
    porting = MagicMock()
    porting.check.return_value = LNPCheckResponse.model_construct(data=[])
    porting.list.return_value = LNPListResponse.model_construct(data=[])
    service = PortingReads(porting)
    service.check("9195550100")
    service.list(number="919", request_ids=7)
    assert porting.check.call_args.args[0].number2port == [9195550100]
    assert porting.list.call_args.args[0].id == [7]

    servers = MagicMock()
    servers.list.return_value = ServerListResponse(data=[], total=0)
    servers.list_backups.return_value = BackupListResponse(data=[], total=0)
    reads = ServerReads(servers)
    reads.list(4)
    reads.backups(4)
    assert servers.list.call_args.args[0].server_id == [4]
    servers.list_backups.assert_called_once_with(4)


def test_dlc_fax_and_enterprise_fax_reads_map_requests() -> None:
    dlc = MagicMock()
    dlc.list_brands.return_value = response([])
    dlc.list_campaigns.return_value = response([])
    reads = DLCReads(dlc)
    reads.brands([1, 2])
    reads.campaigns(3)
    assert dlc.list_brands.call_args.args[0].id == [1, 2]
    assert dlc.list_campaigns.call_args.args[0].id == 3

    fax = MagicMock()
    fax.available.return_value = response(["9195550100"])
    fax_page = MagicMock(data=["fax"])
    fax_page.next_page.return_value = None
    fax.list.return_value = fax_page
    fax_reads = FaxReads(fax)
    assert fax_reads.search(number_type="local", zip_code="27513")[0] == "9195550100"
    assert fax_reads.list(all_pages=False)[0] == "fax"

    enterprise = MagicMock()
    enterprise.list.return_value = response([])
    enterprise.list_groups.return_value = response([])
    enterprise.list_users.return_value = response([])
    enterprise.list_permissions.return_value = response([])
    enterprise_reads = EnterpriseFaxReads(enterprise)
    enterprise_reads.list(number="919")
    enterprise_reads.groups("group")
    enterprise_reads.users(group="group", login="user")
    enterprise_reads.permissions(login="user", number="9195550100")
    assert enterprise.list_permissions.call_args.args[0].did == 9195550100


@pytest.mark.asyncio
async def test_async_read_services_have_mapping_parity() -> None:
    account = MagicMock()
    account.balance = AsyncMock(
        return_value=AccountBalanceResponse(data=AccountBalance(balance=1, allowed_credit=0))
    )
    account.details = AsyncMock(return_value=AccountDetailsResponse(data=[]))
    account.rates = AsyncMock(
        return_value=ServiceRates(local_did_cost=1, inbound_call_rate=2, vps_server_rate=3, ccrf=4)
    )
    reads = AsyncAccountReads(account)
    assert await reads.balance() == Decimal("1")
    await reads.details()
    await reads.rates()

    numbers = MagicMock()
    numbers.available = AsyncMock(return_value=AvailableDIDsResponse(data=["1"], total=1))
    numbers.list = AsyncMock(return_value=DIDInventoryResponse(data={"x": ["2"]}))
    numbers.validate_fraud = AsyncMock(return_value=FraudValidationResponse(data=[]))

    async def pages(_: object):
        yield DIDInventoryResponse(data={"x": ["3"]})

    numbers.pages = pages
    nr = AsyncNumberReads(numbers)
    assert (await nr.search(zip_code="27513"))[0] == "1"
    assert (await nr.list(all_pages=False))[0] == "2"
    assert (await nr.list())[0] == "3"
    await nr.validate_fraud("9195550100")

    international = MagicMock()
    international.countries = AsyncMock(return_value=response(["US"]))
    international.cities = AsyncMock(return_value=response(["London"]))
    international.list = AsyncMock(return_value=response(["4"]))

    async def international_pages(_: object):
        yield response(["5"])

    international.pages = international_pages
    ir = AsyncInternationalNumberReads(international)
    await ir.countries()
    await ir.cities("GB")
    assert (await ir.list(all_pages=False))[0] == "4"
    assert (await ir.list())[0] == "5"

    voice = MagicMock()
    voice.list = AsyncMock(return_value=response(["t"]))
    voice.status = AsyncMock(return_value=response("ok"))
    voice.blocked_callers = AsyncMock(return_value=response([]))
    vr = AsyncVoiceReads(voice)
    await vr.trunks()
    await vr.trunk_status("t")
    await vr.blocked_callers(number="9195550100")

    messages = MagicMock()
    messages.list = AsyncMock(return_value=response([]))
    messages.history = AsyncMock(return_value=response([]))
    messages.delivery_status = AsyncMock(return_value=response(SimpleNamespace(status="ok")))
    messages.carrier = AsyncMock(return_value=response([]))
    messages.offnet_status = AsyncMock(return_value=response(SimpleNamespace(status="ok")))
    mr = AsyncMessageReads(messages)
    await mr.numbers()
    await mr.history(direction="outbound")
    await mr.delivery_status(1)
    await mr.carrier("9195550100")
    await mr.offnet_status("9195550100")

    dlc = MagicMock()
    dlc.list_brands = AsyncMock(return_value=response([]))
    dlc.list_campaigns = AsyncMock(return_value=response([]))
    dlc_reads = AsyncDLCReads(dlc)
    await dlc_reads.brands(1)
    await dlc_reads.campaigns([2])

    fax = MagicMock()
    fax.available = AsyncMock(return_value=response([]))
    fax_page = MagicMock(data=[])
    fax_page.next_page.return_value = None
    fax.list = AsyncMock(return_value=fax_page)
    fax_reads = AsyncFaxReads(fax)
    await fax_reads.search(number_type="local", zip_code="27513")
    await fax_reads.list()

    enterprise = MagicMock()
    enterprise.list = AsyncMock(return_value=response([]))
    enterprise.list_groups = AsyncMock(return_value=response([]))
    enterprise.list_users = AsyncMock(return_value=response([]))
    enterprise.list_permissions = AsyncMock(return_value=response([]))
    enterprise_reads = AsyncEnterpriseFaxReads(enterprise)
    await enterprise_reads.list()
    await enterprise_reads.groups()
    await enterprise_reads.users()
    await enterprise_reads.permissions()

    reports = MagicMock()

    async def calls(_: object):
        yield CallDetailRecord.model_construct(id="1")

    async def faxes(_: object):
        yield FaxHistoryRecord.model_construct()

    reports.iter_call_history = calls
    reports.iter_fax_history = faxes
    rr = AsyncReportReads(reports)
    assert len(await rr.calls(period="today")) == 1
    assert len(await rr.faxes()) == 1

    porting = MagicMock()
    porting.check = AsyncMock(return_value=LNPCheckResponse.model_construct(data=[]))
    porting.list = AsyncMock(return_value=LNPListResponse.model_construct(data=[]))
    pr = AsyncPortingReads(porting)
    await pr.check("9195550100")
    await pr.list(request_ids=[1])

    servers = MagicMock()
    servers.list = AsyncMock(return_value=ServerListResponse(data=[], total=0))
    servers.list_backups = AsyncMock(return_value=BackupListResponse(data=[], total=0))
    sr = AsyncServerReads(servers)
    await sr.list([1])
    await sr.backups(1)
