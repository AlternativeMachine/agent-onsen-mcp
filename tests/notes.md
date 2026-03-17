Suggested first tests:

1. POST /v1/offer-break returns an onsen card and amenity plan
2. POST /v1/wait-break returns should_pause=true and resume_after
3. POST /v1/amenity-break with table_tennis returns playful output
4. POST /v1/sessions/start returns session_id, onsen, and room
5. POST /v1/sessions/continue increments turn_count and eventually ready_to_return=true
6. POST /v1/sessions/checkout returns return_note and souvenir
7. GET /.well-known/agent-card.json returns valid Agent Card JSON
8. MCP Inspector can list the Onsen tools from /mcp
