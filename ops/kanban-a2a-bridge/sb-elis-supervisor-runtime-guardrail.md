# sb elis-supervisor Runtime Guardrail

## Scope

This guardrail applies to sb elis-supervisor, the NemoHermes sandboxed runtime for ELIS Supervisor.

## Model/provider rule

- Primary provider: nvidia-prod
- Primary model: deepseek-ai/deepseek-v4-pro
- In-sandbox Hermes provider must remain the NemoHermes managed inference proxy:
  - provider: custom
  - base_url: https://inference.local/v1
  - _nemoclaw_upstream.provider: nvidia-prod
  - _nemoclaw_upstream.model: deepseek-ai/deepseek-v4-pro

## Fallback rule

No OpenRouter or paid fallback may be activated for sb elis-supervisor without explicit PO approval.

## A2A/Kanban rule

sb elis-supervisor must access ELIS A2A/Kanban only through:

    http://172.19.0.1:9510

It must not access raw host A2A ports 9500, 9501, 9502, or 9503 directly.

## Authority rule

sb elis-supervisor is not a domain project manager. It does not own canonical board authority and must not create, close, or validate its own tasks unless a future PO-approved delegation explicitly grants a bounded capability.
