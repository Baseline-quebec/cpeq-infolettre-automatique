"""Azure Function wrapper around the FastAPI application."""

import azure.functions as func

from cpeq_infolettre_automatique.api import app as fastapi_app


app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
