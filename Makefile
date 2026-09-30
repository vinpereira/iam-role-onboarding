.DEFAULT_GOAL := help

# Override on the command line, e.g.:
#   make configure COMPANY_NAME="Acme Cloud" SHORT_NAME=Acme ACCOUNT_ID=123456789012 BUCKET=acme-iam-roles
COMPANY_NAME ?=
SHORT_NAME   ?=
ACCOUNT_ID   ?=
BUCKET       ?=
REGION       ?= eu-central-1
PORT         ?= 8000

CFN_LINT := $(shell command -v cfn-lint >/dev/null 2>&1 && echo cfn-lint || echo "uvx cfn-lint")

.PHONY: help configure serve lint checkov validate deploy

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

configure: ## Fill in the __PLACEHOLDER__ tokens (requires COMPANY_NAME, SHORT_NAME, ACCOUNT_ID, BUCKET)
	@test -n "$(COMPANY_NAME)" || { echo "COMPANY_NAME is required, e.g.:"; echo '  make configure COMPANY_NAME="Acme Cloud" SHORT_NAME=Acme ACCOUNT_ID=123456789012 BUCKET=acme-iam-roles'; exit 1; }
	@test -n "$(SHORT_NAME)"   || { echo "SHORT_NAME is required"   >&2; exit 1; }
	@test -n "$(ACCOUNT_ID)"   || { echo "ACCOUNT_ID is required"   >&2; exit 1; }
	@test -n "$(BUCKET)"       || { echo "BUCKET is required"       >&2; exit 1; }
	python3 scripts/configure.py \
		--company-name "$(COMPANY_NAME)" \
		--short-name "$(SHORT_NAME)" \
		--account-id "$(ACCOUNT_ID)" \
		--bucket "$(BUCKET)" \
		--region "$(REGION)"

serve: ## Serve the page locally at http://localhost:8000 (override with PORT=...)
	python3 -m http.server $(PORT)

lint: ## Lint the CloudFormation templates with cfn-lint
	$(CFN_LINT) templates/*.yaml

checkov: ## Scan the CloudFormation templates with checkov
	checkov -d templates --framework cloudformation --quiet --compact

validate: lint checkov ## Run cfn-lint and checkov (skipped automatically until configure has run)

deploy: ## Upload index.html and templates/ to the bucket (requires BUCKET; assumes the bucket already exists — see README)
	@test -n "$(BUCKET)" || { echo "BUCKET is required, e.g. make deploy BUCKET=acme-iam-roles"; exit 1; }
	@! grep -qrE '__[A-Z_]+__' index.html templates/ || { echo "index.html or templates/ still has __PLACEHOLDER__ tokens — run 'make configure' first" >&2; exit 1; }
	aws s3 cp index.html s3://$(BUCKET)/index.html --region $(REGION) --content-type "text/html; charset=utf-8"
	aws s3 sync templates/ s3://$(BUCKET)/templates/ --region $(REGION) --content-type "text/yaml; charset=utf-8"
