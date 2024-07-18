"""Azure Function wrapper around the FastAPI application."""

import azure.functions as func

from cpeq_infolettre_automatique.api import app as fastapi_app


# https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators#web-frameworks
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
