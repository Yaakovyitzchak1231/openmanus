import asyncio
import io
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.llm import LLM


@pytest.mark.asyncio
async def test_llm_ask_caching():
    # Initialize LLM
    llm = LLM()
    # Reset cache for test isolation
    LLM._response_cache.clear()

    # Mock the client
    mock_client = AsyncMock()
    llm.client = mock_client

    # Mock the response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Cached Response"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5

    # For non-streaming
    mock_client.chat.completions.create.return_value = mock_response

    # Define prompt
    prompt = [{"role": "user", "content": "Hello"}]

    # First call
    response1 = await llm.ask(prompt, stream=False)
    assert response1 == "Cached Response"
    assert mock_client.chat.completions.create.call_count == 1

    # Second call (same prompt)
    response2 = await llm.ask(prompt, stream=False)
    assert response2 == "Cached Response"

    print(f"Call count: {mock_client.chat.completions.create.call_count}")
    return mock_client.chat.completions.create.call_count


@pytest.mark.asyncio
async def test_llm_ask_caching_stream():
    # Initialize LLM
    llm = LLM()
    LLM._response_cache.clear()

    mock_client = AsyncMock()
    llm.client = mock_client

    # Mock streaming response
    async def async_generator():
        chunks = ["Cached", " ", "Response", " ", "Stream"]
        for c in chunks:
            m = MagicMock()
            m.choices[0].delta.content = c
            yield m

    mock_client.chat.completions.create.return_value = async_generator()

    prompt = [{"role": "user", "content": "Hello Stream"}]

    # Capture stdout
    captured_output = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output

    try:
        # First call
        response1 = await llm.ask(prompt, stream=True)
        assert response1 == "Cached Response Stream"
        assert mock_client.chat.completions.create.call_count == 1

        # Second call
        response2 = await llm.ask(prompt, stream=True)
        assert response2 == "Cached Response Stream"
        assert mock_client.chat.completions.create.call_count == 1

    finally:
        sys.stdout = original_stdout

    output = captured_output.getvalue()
    # Check if output contains the response
    if "Cached Response Stream" in output:
        print("Stream output verified")
    else:
        print(f"Stream output missing. Got: {output}")

    return mock_client.chat.completions.create.call_count


@pytest.mark.asyncio
async def test_llm_ask_with_images_caching():
    # Initialize LLM
    llm = LLM()
    # Mock model to be multimodal - need to ensure it's set on instance or config
    llm.model = "gpt-4o"
    LLM._response_cache.clear()

    mock_client = AsyncMock()
    llm.client = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Image Response"
    mock_response.usage.prompt_tokens = 20
    mock_response.usage.completion_tokens = 5

    mock_client.chat.completions.create.return_value = mock_response

    prompt = [{"role": "user", "content": "Describe this image"}]
    images = ["http://example.com/image.jpg"]

    # First call
    response1 = await llm.ask_with_images(prompt, images, stream=False)
    assert response1 == "Image Response"
    assert mock_client.chat.completions.create.call_count == 1

    # Second call
    response2 = await llm.ask_with_images(prompt, images, stream=False)
    assert response2 == "Image Response"
    assert mock_client.chat.completions.create.call_count == 1

    print(f"Image Call count: {mock_client.chat.completions.create.call_count}")
    return mock_client.chat.completions.create.call_count


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print("Running test_llm_ask_caching...")
    count1 = loop.run_until_complete(test_llm_ask_caching())

    print("Running test_llm_ask_caching_stream...")
    count2 = loop.run_until_complete(test_llm_ask_caching_stream())

    print("Running test_llm_ask_with_images_caching...")
    count3 = loop.run_until_complete(test_llm_ask_with_images_caching())

    if count1 == 1 and count2 == 1 and count3 == 1:
        print("PASS: Caching is working for all cases")
    else:
        print(
            f"FAIL: Caching failed (count1={count1}, count2={count2}, count3={count3})"
        )
