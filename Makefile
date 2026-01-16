.PHONY: install dev build preview deploy setup-app discover test-issue lint clean

# Development
install:
	npm ci

dev:
	npm run dev

build:
	npm run build

preview: build
	npm run preview

lint:
	npm run lint

# Deployment
deploy:
	git push origin main

# GitHub App setup
setup-app:
	node scripts/setup-github-app.js

# Trigger benefit discovery from Reddit
discover:
	gh workflow run discover-benefits.yml
	@echo "Workflow triggered. View at: https://github.com/agentivo/student-benefits-hub/actions"

# Test the issue-to-PR workflow
test-issue:
	@read -p "Benefit to test (e.g., 'Notion free for students'): " benefit; \
	gh issue create --title "[Benefit]: $$benefit" --body "### Describe the benefit\n\n$$benefit" --label new-benefit

# View recent workflow runs
runs:
	gh run list --limit 5

# View benefits count
stats:
	@echo "Benefits: $$(grep -c 'id:' src/data/benefits.ts)"
	@echo "Categories: $$(grep -c 'category:' src/data/benefits.ts | head -1)"

# Clean build artifacts
clean:
	rm -rf dist node_modules/.vite

# Help
help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Start dev server"
	@echo "  make build       - Build for production"
	@echo "  make preview     - Preview production build"
	@echo "  make deploy      - Push to main (triggers GitHub Pages deploy)"
	@echo "  make setup-app   - Create GitHub App for Models API"
	@echo "  make discover    - Trigger Reddit scraping workflow"
	@echo "  make test-issue  - Create a test issue to trigger add-benefit workflow"
	@echo "  make runs        - View recent workflow runs"
	@echo "  make stats       - Show benefits count"
	@echo "  make lint        - Run linter"
	@echo "  make clean       - Remove build artifacts"
