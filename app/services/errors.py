"""One error type for every external call, carrying a message a lawyer can act on."""
from __future__ import annotations

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError, ServiceRequestError


class ServiceError(Exception):
    def __init__(self, service: str, user_message: str, retryable: bool = False):
        super().__init__(f"{service}: {user_message}")
        self.service = service
        self.user_message = user_message
        self.retryable = retryable


def from_exception(service: str, exc: Exception) -> ServiceError:
    """Translate an Azure/network exception. Never includes keys, tokens or request bodies."""
    if isinstance(exc, ServiceError):
        return exc
    status = getattr(exc, "status_code", None)
    if status == 429:
        return ServiceError(service, "Azure is rate limiting this resource. Wait a minute and retry.", True)
    if status in (500, 502, 503, 504) or isinstance(exc, (ServiceRequestError, TimeoutError)):
        return ServiceError(service, "Azure did not answer in time. Check the connection and retry.", True)
    if status in (401, 403) or isinstance(exc, ClientAuthenticationError):
        return ServiceError(service, "Sign-in or permission problem. Run `az login` again and confirm the "
                                     "'Cognitive Services User' role on the resource.", False)
    if status == 404:
        return ServiceError(service, "Azure could not find the endpoint or deployment. Check the values in .env.", False)
    return ServiceError(service, f"Unexpected {type(exc).__name__} from Azure. See the server log.", False)
