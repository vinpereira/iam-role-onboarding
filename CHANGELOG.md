# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.1] - 2026-11-09

### Changed
- Enable Billing Access section on the page now says it is only needed for the Billing and Cost
  Management console (not to create the roles nor for API access to cost data), and that accounts
  created through AWS Organizations usually have it enabled already

### Fixed
- Enablement role: added `iam:PutRolePolicy` on `AWSServiceRoleForCostOptimizationHub`, which AWS
  documents as required to opt in to Cost Optimization Hub

## [0.3.0] - 2026-09-30

### Added
- `templates/cost-optimization-enablement-role.yaml` and a "Create Enablement Role" button: a
  separate, one-time-use role (`<short>CostOptimizationEnablementRole`) that holds the write
  actions needed to enable Compute Optimizer, Cost Optimization Hub, and cost allocation tags
- `scripts/configure.py`: rejects `--short-name` values longer than 34 characters, which would
  produce IAM role names above the 64-character limit

### Changed
- ReadOnly role card copy on the page now states it cannot change anything in the account
- Enablement section copy on the page states precisely what the role can do; darker text color on
  card descriptions for better contrast

### Security
- ReadOnly role: removed the inline policy `<short>CostOptimizationEnablement`, so the role is now
  strictly read-only (`ReadOnlyAccess` + `AWSBillingReadOnlyAccess`). Its write actions moved,
  unchanged, to the new enablement role. Stacks already created from an earlier version keep the
  old inline policy until they are updated or recreated
- Enablement role: added read access to the enrollment status of Compute Optimizer, Cost
  Optimization Hub, and cost allocation tags (`GetEnrollmentStatus`, `ListEnrollmentStatuses`,
  `GetPreferences`, `ListCostAllocationTags`), so the setup can be confirmed with this role alone

## [0.2.0] - 2026-09-30

### Added
- `VERSION` file as the single source of truth for the project version; `scripts/configure.py`
  reads it automatically and stamps it into `index.html` (`<meta name="version">` and footer)
- `scripts/configure.py`: fills in `__COMPANY_NAME__`, `__COMPANY_SHORT_NAME__`,
  `__TRUSTED_ACCOUNT_ID__`, `__BUCKET_NAME__`, `__REGION__`, and `__VERSION__` placeholders
  directly in `index.html` and `templates/*.yaml`, so the page and templates can be reused by any
  company
- `Makefile` with `configure`, `serve`, `lint`, `checkov`, `validate`, and `deploy` targets
- `README.md` with configure, local development, and manual deploy instructions

### Changed
- `index.html` and `templates/*.yaml` are now generic (no Corley-specific text or account ID) —
  run `scripts/configure.py` once before deploying
- Role `Description` fields and page copy switched from Italian/Corley-specific text to generic
  English

### Security
- ReadOnly role: replaced `job-function/Billing` with `AWSBillingReadOnlyAccess`, so it can no
  longer modify budgets, billing settings, or payment methods
- ReadOnly role: added inline policy `<short>CostOptimizationEnablement` allowing only the opt-in
  to Compute Optimizer and Cost Optimization Hub (with their service-linked roles) and the
  activation of cost allocation tags

## [0.1.0]

### Added
- Static page with Create Admin Role, Create ReadOnly Role, and Enable Billing Access buttons
- CloudFormation templates for the admin and read-only roles
