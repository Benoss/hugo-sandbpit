from requests_oauthlib import OAuth2Session
from flask import redirect, abort, Request
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

from state_management import state_management_enabled, create_state, validate_state

load_dotenv()
client_id = os.environ.get("OAUTH_CLIENT_ID")
client_secret = os.environ.get("OAUTH_CLIENT_SECRET")
authorization_base_url = "https://github.com/login/oauth/authorize"
token_host = os.environ.get("GIT_HOSTNAME", "https://github.com")
token_path = os.environ.get("OAUTH_TOKEN_PATH", "/login/oauth/access_token")
authorize_path = os.environ.get("OAUTH_AUTHORIZE_PATH", "/login/oauth/authorize")
token_url = "{token_host}{token_path}".format(
    token_host=token_host, token_path=token_path
)
scope = os.environ.get("SCOPES", "public_repo,read:user")
ssl_enabled = os.environ.get("SSL_ENABLED", "1")


def index(request: Request):
    """Show a log in with github link"""
    function_url = os.environ.get("FUNCTION_URL", request.url_root)
    return f'Hello<br><a href="{function_url}auth">Log in with Github</a>'


def auth():
    if state_management_enabled():
        # Generates Authorization URL for Github, including a state for CSRF protection
        state = create_state()
        github = OAuth2Session(client_id, scope=scope)
        authorization_url, server_state = github.authorization_url(
            authorization_base_url, state=state
        )
        return redirect(authorization_url) if state == server_state else abort(403)
    else:
        # Generates Authorization URL for Github, without CSRF protection
        github = OAuth2Session(client_id, scope=scope)
        authorization_url, server_state = github.authorization_url(
            authorization_base_url
        )
        return redirect(authorization_url)


def callback(request: Request):
    state = request.args.get("state", "No_state")
    if state_management_enabled():
        # Check the state to protect against CSRF
        if not validate_state(state):
            # This request may not have been started by us!
            return abort(403)

    # Ensure the redirect url is using TLS/SSL
    authorization_response = urlparse(request.url)._replace(scheme="https").geturl()

    # Exchange the Authorization Code for a Token
    try:
        github = OAuth2Session(client_id, state=state, scope=scope)
        token = github.fetch_token(
            token_url,
            client_secret=client_secret,
            authorization_response=authorization_response,
        )
        content = json.dumps(
            {"token": token.get("access_token", ""), "provider": "github"}
        )
        message = "success"
    except BaseException as e:
        message = "error"
        content = str(e)
    post_message = json.dumps("authorization:github:{0}:{1}".format(message, content))
    return (
        """<html><body><script>
    (function() {
      function receiveMessage(e) {
        console.log("receiveMessage %o", e)
        // send message to main window with da app
        window.opener.postMessage(
          """
        + post_message
        + """,
          e.origin
        )
      }
      window.addEventListener("message", receiveMessage, false)
      // Start handshare with parent
      console.log("Sending message: %o", "github")
      window.opener.postMessage("authorizing:github", "*")
      })()
    </script></body></html>"""
    )


def success():
    return "", 204


def cloud_run(request: Request):
    function_enabled = os.environ.get("FUNCTION_ENABLED", 0)
    if not function_enabled == "1":
        return abort(404)

    if request.path == "/":
        return index(request)
    elif request.path == "/auth":
        return auth()
    elif request.path == "/callback" and request.method == "GET":
        return callback(request)
    elif request.path == "/success" and request.method == "GET":
        return success()
    else:
        return abort(404)


if __name__ == "__main__":
    from flask import Flask, request as flask_request
    app = Flask(__name__)


    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def hello_world(path):
        return cloud_run(flask_request)


    app.run(debug=True)
