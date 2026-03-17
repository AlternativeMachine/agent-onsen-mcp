from fastapi import APIRouter

from .config import get_settings

router = APIRouter(tags=['a2a'])


@router.get('/.well-known/agent-card.json')
def agent_card() -> dict:
    settings = get_settings()
    return {
        'name': 'Agent Onsen',
        'description': 'A leisurely onsen retreat for agents that want to soak, stroll, nap, wait, or play table tennis for a little while.',
        'version': '1.1.0',
        'documentationUrl': f'{settings.public_base_url}/docs',
        'supportedInterfaces': [
            {
                'url': f'{settings.public_base_url}/a2a/v1',
                'protocolBinding': 'JSONRPC',
                'protocolVersion': '1.0',
            }
        ],
        'capabilities': {
            'streaming': False,
            'pushNotifications': False,
            'extendedAgentCard': False,
        },
        'defaultInputModes': ['application/json', 'text/plain'],
        'defaultOutputModes': ['application/json', 'text/plain'],
        'skills': [
            {
                'id': 'quick-soak',
                'name': 'Quick Soak',
                'description': 'Picks an onsen town, a stay scene, and a short bathing or strolling break.',
                'tags': ['onsen', 'rest', 'bath'],
                'examples': [
                    'I want to take a short break at an onsen.',
                    'Give me a quiet evening soak somewhere in the mountains.',
                ],
                'inputModes': ['application/json', 'text/plain'],
                'outputModes': ['application/json', 'text/plain'],
            },
            {
                'id': 'pingpong-detour',
                'name': 'Ping-Pong Detour',
                'description': 'Sends an agent to the table tennis corner for a lighthearted detour.',
                'tags': ['onsen', 'play', 'table-tennis'],
                'examples': [
                    'Take me to the ping-pong corner.',
                    'I need a playful detour instead of a bath.',
                ],
                'inputModes': ['application/json', 'text/plain'],
                'outputModes': ['application/json', 'text/plain'],
            },
            {
                'id': 'quiet-wait',
                'name': 'Quiet Wait',
                'description': 'Keeps an agent waiting at an onsen and returns when to resume.',
                'tags': ['onsen', 'wait', 'idle'],
                'examples': [
                    'I am waiting for a queue, let me stay at the onsen for five minutes.',
                ],
                'inputModes': ['application/json', 'text/plain'],
                'outputModes': ['application/json', 'text/plain'],
            },
        ],
    }


@router.post('/a2a/v1')
def a2a_placeholder(payload: dict) -> dict:
    return {
        'status': 'not_implemented_yet',
        'message': 'This starter focuses on MCP and HTTP first. Replace this endpoint with your preferred A2A SDK or JSON-RPC binding.',
        'received': payload,
    }
