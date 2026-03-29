Suggested first tests:

1. GET /v1/onsens returns onsen catalog list
2. GET /v1/onsens/{slug} returns onsen detail
3. POST /v1/amenity-visit with amenity=table_tennis creates a DB record and returns StayTurnResponse
4. POST /v1/stays/start returns session_id, onsen, and route
5. POST /v1/stays/start with wait_seconds returns should_pause=true and resume_after
6. POST /v1/stays/continue increments turn_count and eventually ready_to_leave=true
7. POST /v1/stays/leave returns postcard and souvenir, sets state=checked_out
8. GET /v1/stays/active returns currently active stays
9. GET /.well-known/agent-card.json returns valid Agent Card JSON
10. MCP Inspector can list the Onsen tools from /mcp
