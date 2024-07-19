"""Azure Function wrapper around the FastAPI application.

This file needs to be placed at the root of the repository and named function_app.py specifically for it to be detected by the Azure Functions Runtime.
"""

import azure.functions as func

from cpeq_infolettre_automatique.api import app as fastapi_app


# https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Capplication-level&pivots=python-mode-decorators#web-frameworks
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
