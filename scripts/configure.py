#!/usr/bin/env python3
"""Fill in the company placeholders in index.html and templates/*.yaml, in place.

Run this once, with your own company's values, before deploying. It edits the
real files directly (find & replace) — there is no separate template engine.
The project version is read from the VERSION file, not a flag.

Usage:
    scripts/configure.py --company-name "Acme Cloud" --short-name Acme \\
        --account-id 123456789012 --bucket acme-iam-roles [--region eu-central-1]

Re-running it after the files are already configured is a no-op (the
placeholders are gone), so to reconfigure for a different company, restore
the placeholders first (e.g. `git checkout -- index.html templates/`) and run
this again.
"""
import argparse
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = [
    REPO_ROOT / "index.html",
    REPO_ROOT / "templates" / "admin-role.yaml",
    REPO_ROOT / "templates" / "readonly-role.yaml",
    REPO_ROOT / "templates" / "cost-optimization-enablement-role.yaml",
]

# IAM role names are limited to 64 characters; the longest suffix is "CostOptimizationEnablementRole" (30)
MAX_SHORT_NAME_LENGTH = 34


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--company-name", required=True, help='Full company name shown on the page, e.g. "Acme Cloud"'
    )
    parser.add_argument(
        "--short-name",
        required=True,
        help='Short, alphanumeric-only name used in IAM role names, e.g. "Acme"',
    )
    parser.add_argument(
        "--account-id", required=True, help="Your own 12-digit AWS account ID — the one the roles will trust"
    )
    parser.add_argument("--bucket", required=True, help="S3 bucket that will host the page and templates")
    parser.add_argument("--region", default="eu-central-1", help="AWS region of the bucket (default: eu-central-1)")
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9]+", args.short_name):
        sys.exit("--short-name must contain only letters and digits (used in IAM role names)")
    if len(args.short_name) > MAX_SHORT_NAME_LENGTH:
        sys.exit(
            f"--short-name must be at most {MAX_SHORT_NAME_LENGTH} characters "
            "(IAM role names are limited to 64 characters)"
        )
    if not re.fullmatch(r"\d{12}", args.account_id):
        sys.exit("--account-id must be a 12-digit AWS account ID")

    version = (REPO_ROOT / "VERSION").read_text().strip()

    replacements = {
        "__COMPANY_NAME__": args.company_name,
        "__COMPANY_SHORT_NAME__": args.short_name,
        "__TRUSTED_ACCOUNT_ID__": args.account_id,
        "__BUCKET_NAME__": args.bucket,
        "__REGION__": args.region,
        "__VERSION__": version,
    }

    for path in FILES:
        text = path.read_text()
        before = text
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        path.write_text(text)
        status = "configured" if text != before else "unchanged (no placeholders found)"
        print(f"{status}: {path.relative_to(REPO_ROOT)}")

    print("\nDone. Review the changes (git diff) before committing and deploying.")


if __name__ == "__main__":
    main()
