"""Consume the host-selected installation supplier; never discover an identity."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess


TOKEN_COMMAND_ENV = "NOODLES_TOKEN_COMMAND"


class CredentialRefusal(ValueError):
    def __init__(self, field, value, required):
        super().__init__(f"credential: invalid {field}={value!r}")
        self.field, self.value, self.required = field, value, required


def resolve_host_environment(control_root, *, environ=None):
    """Resolve only the atom host's fixed registration, after authorization."""
    env = dict(os.environ if environ is None else environ)
    command = env.get(TOKEN_COMMAND_ENV)
    if isinstance(command, str) and command.strip():
        return env  # Legacy commands are opaque, including their arguments.

    def require(condition, field):
        if not condition:
            name = "provider_credential_profile." + field
            raise CredentialRefusal(name, "missing-or-invalid", name)

    require(not any(key in env for key in ("NOODLE_SESSION_ID", "NOODLE_ORDER_ID")),
            "context")
    config = env.get("XDG_CONFIG_HOME")
    if not config:
        home = env.get("HOME")
        require(isinstance(home, str) and home.startswith("/"), "path")
        config = home + "/.config"
    require(isinstance(config, str) and config.startswith("/"), "path")
    root = Path(control_root).resolve()

    def locator(value, field, *, external=False, executable=False):
        require(isinstance(value, str) and value.startswith("/") and "\0" not in value, field)
        try:
            require(not external or not Path(os.path.abspath(value)).is_relative_to(root), field)
            path = Path(value).resolve(strict=True)
            require(not external or not path.is_relative_to(root), field)
            require(path.is_file() and os.access(path, os.R_OK), field)
            require(not executable or os.access(path, os.X_OK), field)
        except (OSError, ValueError, RuntimeError):
            require(False, field)
        return path

    profile = locator(config + "/soodles/provider.json", "path", external=True)
    try:
        spec = json.loads(profile.read_bytes())
    except (OSError, ValueError):
        require(False, "path")
    require(isinstance(spec, dict), "path")
    require(type(spec.get("schema")) is int and spec["schema"] == 1, "schema")
    require(spec.get("kind") == "github_app_supplier", "kind")
    require(set(spec) == {"schema", "kind", "supplier", "app"}, "path")
    for group, fields in (("supplier", {"path", "sha256"}),
                          ("app", {"client_id", "installation_id", "private_key_path"})):
        require(isinstance(spec.get(group), dict), group)
        for field in sorted(fields):
            require(field in spec[group], group + "." + field)
        require(set(spec[group]) == fields, group)
    supplier = locator(spec["supplier"]["path"], "supplier.path", external=True, executable=True)
    digest = spec["supplier"]["sha256"]
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "supplier.sha256")
    try:
        require(hashlib.sha256(supplier.read_bytes()).hexdigest() == digest, "supplier.sha256")
    except OSError:
        require(False, "supplier.path")
    app = spec["app"]
    require(isinstance(app["client_id"], str) and app["client_id"].strip()
            and "\0" not in app["client_id"], "app.client_id")
    require(isinstance(app["installation_id"], str)
            and re.fullmatch(r"[0-9]+", app["installation_id"]), "app.installation_id")
    key = locator(app["private_key_path"], "app.private_key_path")
    # Validate the locator only; private-key bytes belong to the supplier.
    env[TOKEN_COMMAND_ENV] = shlex.quote(str(supplier))
    env["NOODLES_APP_CLIENT_ID"] = app["client_id"]
    env["NOODLES_APP_INSTALLATION_ID"] = app["installation_id"]
    env["NOODLES_APP_PRIVATE_KEY_PATH"] = str(key)
    return env


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
