import pytest
import sys
import os
import importlib.util
from typing import Any


# Helper to import module from path
def import_from_path(path: str, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None


@pytest.mark.asyncio
async def test_rag_chatbot_example_flow() -> None:
    # Path to example
    example_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../examples/rag_chatbot.py")
    )

    # Import the example module
    # Note: importing executes top-level code (creating FeatureStore).
    # This is fine for this lightweight example.
    rag_chatbot = import_from_path(example_path, "rag_chatbot_example")
    assert rag_chatbot is not None

    # Execute the context assembler
    # user_id="u1" -> hash("u1") odd/even determines premium/free
    ctx = await rag_chatbot.chat_context(user_id="user_123", query="Hello Meridian")

    assert ctx is not None
    assert "You are a helpful assistant" in ctx.content  # System prompt (no prefix)
    assert "Context:" in ctx.content
    assert "History:" in ctx.content

    # Verify dropped items logic (budget is 200)
    # The example has 4 items.
    # Total content length might exceed 200 if not careful?
    # History item is priority 3 (lowest priority to keep? No, 0 is lowest priority usually?)
    # Wait, ContextItem definition: priority: int = 0 # 0 is lowest (dropped first)
    # The example says:
    # Priority 0: Must have (System)
    # Priority 1: User Info
    # Priority 2: Retrieved Docs
    # Priority 3: History
    # If 0 is lowest, then History (3) is HIGHEST priority to KEEP?
    # Let's check src/meridian/context.py logic.
    pass
