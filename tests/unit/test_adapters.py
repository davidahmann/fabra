import pytest
from unittest.mock import MagicMock
from fabra.adapters.openai import wrap_openai_call
from fabra.adapters.langchain import FabraLangChainCallbackHandler

# --- OpenAI Adapter Tests ---


def test_openai_wrapper_success():
    recorder = MagicMock()
    mock_func = MagicMock(
        return_value={"choices": [{"message": {"content": "Hello world"}}]}
    )

    # Create wrapped function
    wrapped = wrap_openai_call(
        mock_func,
        recorder=recorder,
        context_function="test.openai",
        emit_logs=False,
        emit_otel=False,
    )

    # Call it
    result = wrapped(messages=[{"role": "user", "content": "Hi"}])

    assert result == mock_func.return_value
    mock_func.assert_called_once()

    # Verify recorder called (sync)
    recorder.record_sync.assert_called_once()
    call_args = recorder.record_sync.call_args
    assert call_args.kwargs["context_function"] == "test.openai"
    assert "Hi" in call_args.kwargs["content"]
    assert "Hello world" in call_args.kwargs["inputs"]["response_text"]


def test_openai_wrapper_error():
    recorder = MagicMock()
    mock_func = MagicMock(side_effect=ValueError("Test Error"))

    wrapped = wrap_openai_call(
        mock_func,
        recorder=recorder,
        context_function="test.openai_error",
        emit_logs=False,
        emit_otel=False,
    )

    with pytest.raises(ValueError):
        wrapped(prompt="Why?")

    recorder.record_sync.assert_called_once()
    call_args = recorder.record_sync.call_args
    assert "error" in call_args.kwargs["context_function"]
    assert "ValueError" in call_args.kwargs["inputs"]["error"]["type"]


# --- LangChain Adapter Tests ---


def test_langchain_callback_flow():
    recorder = MagicMock()
    handler = FabraLangChainCallbackHandler(
        recorder=recorder, emit_logs=False, emit_otel=False
    )

    run_id = "run-123"

    # 1. Start
    handler.on_llm_start(serialized={}, prompts=["Tell me a joke"], run_id=run_id)

    # Should not record yet
    recorder.record_sync.assert_not_called()
    assert run_id in handler._pending

    # 2. End
    # response should be an object with generations attribute for the extraction logic
    from types import SimpleNamespace

    response = SimpleNamespace(
        generations=[[SimpleNamespace(text="Why did the chicken cross the road?")]]
    )

    handler.on_llm_end(response, run_id=run_id)

    # Should record now
    recorder.record_sync.assert_called_once()
    assert run_id not in handler._pending

    call_args = recorder.record_sync.call_args
    assert "Tell me a joke" in call_args.kwargs["content"]
    assert "Why did the chicken" in call_args.kwargs["inputs"]["output_text"]
    assert call_args.kwargs["inputs"]["run_id"] == run_id


def test_langchain_callback_error():
    recorder = MagicMock()
    handler = FabraLangChainCallbackHandler(
        recorder=recorder, emit_logs=False, emit_otel=False
    )

    run_id = "run-err"

    handler.on_llm_start(serialized={}, prompts=["Fail me"], run_id=run_id)

    handler.on_llm_error(RuntimeError("Boom"), run_id=run_id)

    recorder.record_sync.assert_called_once()
    call_args = recorder.record_sync.call_args
    assert "Boom" in call_args.kwargs["inputs"]["error"]["message"]
    assert "RuntimeError" in call_args.kwargs["inputs"]["error"]["type"]
