# Security policy

## Supported versions

Until pyquestblue 1.0, security fixes are released on the latest published minor line. After 1.0,
the latest minor release receives security and compatibility fixes. The immediately preceding minor
may receive critical security fixes for up to six months after it is superseded. Unsupported
versions should be upgraded before reporting ordinary defects.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or include credentials, message content,
telephone numbers, fax documents, customer records, or other sensitive data in an issue or log.
Use GitHub's **Report a vulnerability** private-reporting flow in the repository Security tab. If
that flow is unavailable, contact the repository owner privately through the contact information on
their GitHub profile and request a secure reporting channel before sending details.

Reports should include the affected version, impact, minimal reproduction, and suggested mitigation
when known. Expect acknowledgement within three business days, an initial assessment within seven
business days, and status updates at least every fourteen days while remediation is active. Release
timing depends on severity and coordination needs. Credit and disclosure timing will be agreed with
the reporter; confidentiality is requested until a fix is available.

Compromised QuestBlue or package-index credentials are operational incidents. Revoke or rotate them
with the relevant provider immediately; do not wait for an SDK release.
