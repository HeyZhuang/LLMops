from internal.core.language_model.providers.deepseek.chat import Chat


def test_deepseek_chat_uses_fallback_encoding():
    chat = Chat(model="deepseek-chat", api_key="test-key")

    model_name, _ = chat._get_encoding_model()

    assert model_name == "gpt-3.5-turbo"


def test_deepseek_chat_can_count_tokens():
    chat = Chat(model="deepseek-chat", api_key="test-key")

    token_count = chat.get_num_tokens_from_messages([])

    assert isinstance(token_count, int)
    assert token_count >= 0
