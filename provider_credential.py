"""Consume the host-selected installation supplier; never discover an identity."""
import json
import os
import subprocess


TOKEN_COMMAND_ENV = "NOODLES_TOKEN_COMMAND"


class CredentialRefusal(ValueError):
    def __init__(self, field, value, required):
        super().__init__(f"credential: invalid {field}={value!r}")
        self.field, self.value, self.required = field, value, required


def clean_child_env(environ=None):
    environ = os.environ if environ is None else environ
    excluded = {"GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN",
                "GITHUB_ENTERPRISE_TOKEN", TOKEN_COMMAND_ENV,
                "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH_COMMAND"}
    return {key: value for key, value in environ.items()
            if key not in excluded and not key.startswith(
                ("NOODLES_APP_", "NOODLES_GITHUB_", "GITHUB_APP_"))}


def supply_token(repository, permissions, *, environ=None):
    environ = os.environ if environ is None else environ
    command = environ.get(TOKEN_COMMAND_ENV)
    if not isinstance(command, str) or not command.strip():
        raise CredentialRefusal("provider_credential_supplier", "absent", TOKEN_COMMAND_ENV)
    # The supervisor selected the App installation. The validated caller fixes
    # repository and permissions, overriding any wider inherited request.
    env = dict(environ)
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"):
        env.pop(key, None)
    env["NOODLES_APP_REPOSITORIES_JSON"] = json.dumps([repository.split("/", 1)[1]])
    env["NOODLES_APP_PERMISSIONS_JSON"] = json.dumps(permissions, sort_keys=True)
    try:
        result = subprocess.run(["bash", "-c", command], env=env,
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        raise CredentialRefusal("provider_credential_supplier", type(error).__name__,
                                "working_provider_credential_supplier") from None
    if result.returncode:
        raise CredentialRefusal("provider_credential_supplier_exit", result.returncode,
                                "working_provider_credential_supplier")
    token = result.stdout.strip()
    if not token or any(not 33 <= ord(character) <= 126 for character in token):
        raise CredentialRefusal("provider_credential", "not-single-token",
                                "repository_scoped_installation_token")
    return token
