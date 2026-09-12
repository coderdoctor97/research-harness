# Extending the Harness
## Adding a Built-in Tool
1. Create `src/harness/tools/builtin/my_tool.py`
2. Subclass `harness.registry.tool.Tool` with `name`, `description`, `parameters`
3. Implement `run(self, **params) -> ToolResult`
4. Register in `src/harness/registry/index.py`

## Adding a Custom Endpoint (no code)
Add to `config.yaml` under `custom_endpoints`:
```yaml
custom_endpoints:
  - name: my_api
    endpoint:
      url: https://api.example.com/{{query}}
    parameters:
      body_template: '{"q": "{{query}}"}'
```
