# Security

## Data classification

This repository is designed for synthetic workshop data. Do not commit real PHI, credentials, secrets, service principal values, access tokens, connection strings, private keys, exported logs with identifiers, or customer-confidential data.

## Reporting issues

For workshop development, report security concerns to the repository owner or workshop lead. Before external sharing, replace this section with the approved Kaiser Permanente and Microsoft reporting process.

## Required controls for labs

1. Use synthetic data by default.
2. Use managed identities or participant identity where possible.
3. Store secrets outside source control.
4. Log privileged tool access.
5. Keep PHI-minimizing defaults in all tool contracts.
6. Require human review before operational actions.

