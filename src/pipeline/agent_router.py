"""
agent_router.py

Runtime architecture for routing requests to agent-specific models.

Routing strategy:
- Each agent (intent_parser, entity_parser, time_parser, validator) has a dedicated Ollama model
- Models are loaded separately to avoid cross-contamination
- Stateless execution: each agent call is independent
- Deterministic outputs: temperature=0, top_p=1 enforced at model level

Why separate adapters:
- Each agent has distinct task (classification vs extraction vs validation)
- Prevents task interference (intent logic bleeding into entity extraction)
- Enables independent optimization and retraining
- Reduces prompt-graph memory bugs by isolating agent contexts

How this avoids prompt-graph memory bugs:
- No shared prompt context between agents
- Each agent model only knows its specific task
- Pipeline flow is code-controlled, not prompt-controlled
- Agent outputs are validated before passing to next stage
"""

import requests
from typing import Dict, Any, Optional

OLLAMA_URL = "http://localhost:11434/api/generate"

# Agent model names (must match Ollama model names after creation)
AGENT_MODELS = {
    "intent_parser": "kalanaya-intent-parser",
    "entity_parser": "kalanaya-entity-parser",
    "time_parser": "kalanaya-time-parser",
    "validator": "kalanaya-validator",
}


def call_agent(agent_name: str, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Route request to specified agent model.
    
    Args:
        agent_name: One of "intent_parser", "entity_parser", "time_parser", "validator"
        user_input: Input text for the agent
        context: Optional context dict (e.g., current_date for time_parser)
    
    Returns:
        Raw response string from agent (should be JSON)
    
    Architecture notes:
    - Each agent model is loaded independently in Ollama
    - System prompt enforces strict JSON-only behavior
    - Temperature=0, top_p=1 set in Modelfile (not per-request)
    - No shared memory between agent calls
    """
    if agent_name not in AGENT_MODELS:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    model_name = AGENT_MODELS[agent_name]
    
    # Build prompt based on agent and context
    if agent_name == "time_parser" and context:
        # Inject temporal context into user input for time parser
        current_date = context.get("current_date", "")
        tomorrow = context.get("tomorrow", "")
        day_after_tomorrow = context.get("day_after_tomorrow", "")
        current_year = context.get("current_year", "")
        
        prompt = f"Context (Asia/Kolkata): Today: {current_date}, Tomorrow: {tomorrow}, Day after tomorrow: {day_after_tomorrow}, Current year: {current_year}\n\nUser input:\n{user_input}"
    else:
        prompt = user_input
    
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            # Note: temperature/top_p set in Modelfile, but can override here if needed
            # "options": {"temperature": 0.0, "top_p": 1.0}
        },
        timeout=60,
    )
    
    response.raise_for_status()
    response_data = response.json()
    
    if "error" in response_data:
        raise Exception(f"Ollama API error: {response_data['error']}")
    
    if "response" in response_data:
        return response_data["response"].strip()
    elif "content" in response_data:
        return response_data["content"].strip()
    else:
        raise KeyError(f"'response' key not found in Ollama API response")


def route_intent_parser(user_input: str) -> Dict[str, Any]:
    """Route to intent parser agent."""
    import json
    response = call_agent("intent_parser", user_input)
    # Extract JSON from response (handles markdown fences, etc.)
    # Implementation should match existing _parse_json_from_llm_response
    return json.loads(response)


def route_entity_parser(user_input: str) -> Dict[str, Any]:
    """Route to entity parser agent."""
    import json
    response = call_agent("entity_parser", user_input)
    return json.loads(response)


def route_time_parser(user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Route to time parser agent with temporal context."""
    import json
    response = call_agent("time_parser", user_input, context=context)
    return json.loads(response)


def route_validator(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """Route to validator agent with extracted fields as JSON string."""
    import json
    fields_json = json.dumps(extracted_fields)
    response = call_agent("validator", fields_json)
    return json.loads(response)


# Integration notes:
# - Replace _call_ollama in level1_intent.py with route_intent_parser
# - Replace semantic/time extraction calls in level2_extraction.py with route_entity_parser/route_time_parser
# - Replace validation logic in level3_validation.py with route_validator (if using LLM-based validation)

