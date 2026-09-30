# IAM Roles Onboarding Page

A generic static page any company can host so their clients can create, in the client's own AWS
account, the IAM role that company uses to access it. Each button opens the AWS CloudFormation
console with a quick-create stack (the client must already be logged in to their own AWS account).

| Button | Creates | Permissions |
|---|---|---|
| Create Admin Role | `<short>AdminRole` | `AdministratorAccess` + `job-function/Billing` |
| Create ReadOnly Role | `<short>ReadOnlyRole` | `ReadOnlyAccess` + `AWSBillingReadOnlyAccess` + cost optimization opt-ins |
| Enable Billing Access | — | Opens the Billing console so the root user can activate IAM access to billing information |

Both roles trust the company's own AWS account.

There is no build step, template engine, or infra-as-code. `index.html` and `templates/*.yaml` are
the exact files that get uploaded to S3 — see [Configure](#configure) for how a company's name and
AWS account ID get into them.

## About the "root" references

A few occurrences of the word "root" here can look alarming at first glance, but none of them is
the AWS root user of any account:

- **`arn:aws:iam::<account>:root` in the templates' trust policy** — standard AWS IAM syntax
  meaning "this AWS account as a whole" (any IAM identity in it with `sts:AssumeRole` permission),
  not that account's root user. It's the normal way to scope a cross-account trust policy to an
  account rather than to one specific role or user.
- **`RootRole` logical ID in the CloudFormation templates** — just the resource's internal name
  inside the template. It has no special meaning or effect.
- **"root" in the Enable Billing Access instructions on the page** — this refers to the **client's
  own AWS account root user**, the only identity that can activate IAM access to billing
  information. It never touches these templates; it's a one-time manual step the client does
  directly in their own Billing console.

In short: nothing here creates, uses, or requires the root user of the account that owns this page.
The client's root user is only needed once, for a billing setting only the root user can change.

## Repository layout

| Path | Purpose |
|---|---|
| `index.html` | The page — self-contained HTML with inline CSS, `__PLACEHOLDER__` tokens |
| `templates/` | CloudFormation templates referenced by the page, same placeholders |
| `scripts/configure.py` | Fills in the placeholders in place, once, before deploying |
| `Makefile` | Shortcuts for configure/serve/lint/checkov (`make help`) |
| `VERSION` | Current project version — single source of truth, stamped into `index.html` |
| `CHANGELOG.md` | Release history |

## Configure

Before the first deploy, run `scripts/configure.py` once with your company's values. It finds and
replaces the `__PLACEHOLDER__` tokens directly in `index.html` and `templates/*.yaml` — there's no
separate template file to keep in sync.

```sh
python3 scripts/configure.py \
  --company-name "Acme Cloud" \
  --short-name Acme \
  --account-id 123456789012 \
  --bucket acme-iam-roles \
  --region eu-central-1

# or, equivalently:
make configure COMPANY_NAME="Acme Cloud" SHORT_NAME=Acme \
  ACCOUNT_ID=123456789012 BUCKET=acme-iam-roles REGION=eu-central-1
```

| Flag | Used for |
|---|---|
| `--company-name` | Shown on the page and in role `Description` fields |
| `--short-name` | Alphanumeric only — used in role names (`AcmeAdminRole`) and the stack name |
| `--account-id` | Your own 12-digit AWS account ID — the one the roles will trust |
| `--bucket` | The S3 bucket that will host this page (see Deploy below) |
| `--region` | AWS region of that bucket (default `eu-central-1`) |

The version stamped into `index.html` (`<meta name="version">` and the footer) comes from the
`VERSION` file, not a flag — bump `VERSION` and `CHANGELOG.md` together (see [Versioning](#versioning)).

Review the diff (`git diff`) before committing. Running the script again after the files are
already configured is a no-op; to reconfigure for a different company, restore the placeholders
first (`git checkout -- index.html templates/`) and run it again.

## Local development

```sh
make serve   # or: python3 -m http.server 8000 — open http://localhost:8000
```

Once configured (see above):

```sh
make validate   # or: cfn-lint templates/*.yaml && checkov -d templates --framework cloudformation --quiet --compact
```

Run `make help` to see all available targets.

The console links point to the templates hosted on S3, so template changes can only be tested in
the console after they are deployed.

## Deploy

No infra-as-code — this is 2-3 small files, plain `aws` CLI commands are enough.

**One-time bucket setup:**

```sh
aws s3api create-bucket --bucket <bucket-name> --region <region> \
  --create-bucket-configuration LocationConstraint=<region>

aws s3api put-public-access-block --bucket <bucket-name> --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false

aws s3api put-bucket-policy --bucket <bucket-name> --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadPageAndTemplates",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": [
      "arn:aws:s3:::<bucket-name>/index.html",
      "arn:aws:s3:::<bucket-name>/templates/*"
    ]
  }]
}'
```

**Every release**, after running `scripts/configure.py` (the bucket must already exist, see above):

```sh
make deploy BUCKET=<bucket-name> REGION=<region>

# or, equivalently:
aws s3 cp index.html s3://<bucket-name>/index.html --region <region> --content-type "text/html; charset=utf-8"
aws s3 sync templates/ s3://<bucket-name>/templates/ --region <region> --content-type "text/yaml; charset=utf-8"
```

`make deploy` refuses to run if `index.html`/`templates/` still have `__PLACEHOLDER__` tokens.

The bucket name and region must match what you passed to `scripts/configure.py` (they're baked
into the links in `index.html`).

## Versioning

The `VERSION` file is the single source of truth for the project's version. Bump it together with
`CHANGELOG.md`, following [Semantic Versioning](https://semver.org/):

- **MAJOR**: breaking changes for clients — role renamed, trust principal changed, role removed
- **MINOR**: new role/button, managed policy added or removed, new page section
- **PATCH**: text fixes, styling, link fixes

`scripts/configure.py` reads `VERSION` and stamps it into `index.html` (`<meta name="version">` and
the footer), so anyone can check which version is actually deployed by viewing the page source.

## Git workflow

GitFlow (`main`, `develop`, `feature/*`, `release/X.Y.Z`, `hotfix/X.Y.Z`) with
[Conventional Commits](https://www.conventionalcommits.org/). Releases are tagged `vX.Y.Z` on `main`
and documented in `CHANGELOG.md`.
