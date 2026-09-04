"""HTTP API for EverTrack.

The same core/ domain package the desktop app uses, exposed over HTTP. No
business logic lives here: routers validate input, call core, and shape output.
"""
