#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Configuration for the bot."""

import os


class DefaultConfig:
    """Configuration for the bot."""

    PORT = 3978
    APP_ID = ""
    APP_PASSWORD =""
    LUIS_APP_ID = "cc60ea3d-7f7c-4b89-b1da-ccc1eb3e41ce"
    LUIS_API_KEY = "d5241c0c3da14d4cba68a3898dd58136"
    # LUIS endpoint host name, ie "westus.api.cognitive.microsoft.com"
    LUIS_API_HOST_NAME = "my-langserv.cognitiveservices.azure.com"
    APPINSIGHTS_INSTRUMENTATION_KEY = "a5ac5bb0-de74-4cbf-bb18-e007ca30d7b5"