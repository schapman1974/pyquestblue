"""No-model-import quickstart for the pyquestblue 1.1 simple facade."""

from questblue import SimpleQuestBlue


def main() -> None:
    with SimpleQuestBlue() as qb:
        balance = qb.account.balance()
        numbers = qb.numbers.search(zip_code="27513", limit=5)
        calls = qb.reports.calls(period="today")
        print(balance, numbers, calls)


if __name__ == "__main__":
    main()
