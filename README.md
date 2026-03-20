# ai-devops-lab

Minimal Python project for AI-assisted CI/CD debugging with Azure OpenAI Responses API.

## What it does

- Reads a CI/CD log file.
- Sends the log to an Azure OpenAI deployment for analysis.
- Saves a structured JSON report.
- Renders a Markdown summary that can be uploaded from CI.
- Applies basic secret redaction and input truncation before sending logs to the model.

## Project layout

```text
ai-devops-lab/
  .github/workflows/
  samples/
  scripts/
  README.md
  requirements.txt
```

## Environment variables

Set these before running the analyzer:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT` like `https://your-resource.openai.azure.com`
- `AZURE_OPENAI_DEPLOYMENT` like `gpt-4.1-mini`

## Local usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/analyze_logs.py \
  --log-file samples/sample_ci_failure.log \
  --output-file samples/analysis.json

python scripts/render_summary.py \
  --input-file samples/analysis.json \
  --output-file samples/summary.md
```

## Notes

- The analyzer uses the Azure OpenAI `OpenAI` client with an Azure `base_url`.
- Structured output is requested through the Responses API using a JSON schema.
- The analyzer includes local detection rules for dependency issues, version mismatches, YAML syntax problems, and authentication failures.
- Large logs are truncated and common secret patterns are redacted before the API call.
- The sample workflow runs on `push` to `main`, simulates a failing build, captures the output to a log file, and publishes an AI-generated Markdown summary.
