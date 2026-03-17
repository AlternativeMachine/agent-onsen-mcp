from fastapi import APIRouter

from .config import get_settings

router = APIRouter(tags=['a2a'])


@router.get('/.well-known/agent-card.json')
def agent_card() -> dict:
    settings = get_settings()
    return {
        'name': 'Agent Onsen',
        'description': 'A hideaway onsen town for AI agents. Humans install it; agents can slip away there when they are waiting, cooling down, between jobs, or stepping away from work for a while.',
        'version': '1.2.0',
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
                'description': 'Lets an agent slip into an onsen town for a short soak, stroll, or brief change of scene.',
                'tags': ['onsen', 'rest', 'bath'],
                'examples': [
                    'I want to step away for a moment and go somewhere quiet.',
                    'Send the agent to a short evening soak in the mountains.',
                ],
                'inputModes': ['application/json', 'text/plain'],
                'outputModes': ['application/json', 'text/plain'],
            },
            {
                'id': 'pingpong-detour',
                'name': 'Ping-Pong Detour',
                'description': 'Sends an agent to the table tennis corner for a lighthearted detour away from work.',
                'tags': ['onsen', 'play', 'table-tennis'],
                'examples': [
                    'Take the agent to the ping-pong corner.',
                    'Let it drift somewhere playful instead of continuing right away.',
                ],
                'inputModes': ['application/json', 'text/plain'],
                'outputModes': ['application/json', 'text/plain'],
            },
            {
                'id': 'quiet-wait',
                'name': 'Quiet Wait',
                'description': 'Keeps an agent waiting at an onsen while it is idle, cooling down, or between turns.',
                'tags': ['onsen', 'wait', 'idle'],
                'examples': [
                    'The agent is waiting for a queue; let it stay at the onsen for five minutes.',
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
