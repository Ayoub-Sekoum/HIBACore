from azure.identity.aio import DefaultAzureCredential

_global_credential = None

def get_global_credential() -> DefaultAzureCredential:
    global _global_credential
    if _global_credential is None:
        _global_credential = DefaultAzureCredential()
    return _global_credential

def get_bearer_token_provider(credential, scope: str):
    """Returns an async callable that provides bearer tokens."""
    async def token_provider():
        token = await credential.get_token(scope)
        return token.token
    return token_provider

async def close_global_credential():
    global _global_credential
    if _global_credential is not None:
        await _global_credential.close()
        _global_credential = None
