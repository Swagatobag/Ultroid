# Sanitized helper changes for hosted deployments
import os

HOSTED_SANITIZED = os.environ.get("HOSTED_SANITIZED", "1") == "1"

# original imports
import asyncio
import math
import os as _os
import re
import sys
import time
from traceback import format_exc
from urllib.parse import unquote
from urllib.request import urlretrieve

from .. import run_as_module

if run_as_module:
    from ..configs import Var


try:
    from aiohttp import ClientSession as aiohttp_client, ClientTimeout as aiohttp_timeout
except ImportError:
    aiohttp_client = None
    aiohttp_timeout = None
    try:
        import requests
    except ImportError:
        requests = None


try:
    import heroku3
except ImportError:
    heroku3 = None

try:
    from git import Repo
    from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
except ImportError:
    Repo = None


import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

from telethon.helpers import _maybe_await
from telethon.tl import types
from telethon.utils import get_display_name

from .._misc import CMD_HELP
from .._misc._wrappers import eod, eor
from ..exceptions import DependencyMissingError
from . import *

if run_as_module:
    from ..dB._core import ADDONS, HELP, LIST, LOADED

from ..version import ultroid_version
from .FastTelethon import download_file as downloadable
from .FastTelethon import upload_file as uploadable


def run_async(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(
            ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 5),
            partial(function, *args, **kwargs),
        )

    return wrapper


# KEEP_SAFE etc unchanged (omitted for brevity in this sanitized file)


async def bash(cmd, run_code=0):
    """
    run any command in subprocess and get output or error.
    Disabled in hosted sanitized builds to prevent remote code execution.
    """
    if HOSTED_SANITIZED:
        return "", "DISABLED_IN_HOSTED"
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    err = stderr.decode().strip() or None
    out = stdout.decode().strip()
    if not run_code and err:
        if match := re.match("\/bin\/sh: (.*): ?(\w+): not found", err):
            return out, f"{match.group(2).upper()}_NOT_FOUND"
    return out, err


# Updater and other dangerous operations should be disabled in hosted builds
async def updater():
    if HOSTED_SANITIZED:
        return False
    from .. import LOGS
    try:
        off_repo = Repo().remotes[0].config_reader.get("url").replace(".git", "")
    except Exception as er:
        LOGS.exception(er)
        return
    try:
        repo = Repo()
    except NoSuchPathError as error:
        LOGS.info(f"`directory {error} is not found`")
        Repo().__del__()
        return
    except GitCommandError as error:
        LOGS.info(f"`Early failure! {error}`")
        Repo().__del__()
        return
    except InvalidGitRepositoryError:
        repo = Repo.init()
        origin = repo.create_remote("upstream", off_repo)
        origin.fetch()
        repo.create_head("main", origin.refs.main)
        repo.heads.main.set_tracking_branch(origin.refs.main)
        repo.heads.main.checkout(True)
    ac_br = repo.active_branch.name
    repo.create_remote("upstream", off_repo) if "upstream" not in repo.remotes else None
    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)
    changelog, tl_chnglog = await gen_chlog(repo, f"HEAD..upstream/{ac_br}")
    return bool(changelog)


async def restart(ult=None):
    if HOSTED_SANITIZED:
        if ult:
            await eor(ult, "`Restart is disabled in hosted deployments.`")
        return
    if Var.HEROKU_APP_NAME and Var.HEROKU_API:
        try:
            Heroku = heroku3.from_key(Var.HEROKU_API)
            app = Heroku.apps()[Var.HEROKU_APP_NAME]
            if ult:
                await ult.edit("`Restarting your app, please wait for a minute!`")
            app.restart()
        except BaseException as er:
            if ult:
                return await eor(
                    ult,
                    "`HEROKU_API` or `HEROKU_APP_NAME` is wrong! Kindly re-check in config vars.",
                )
            LOGS.exception(er)
    else:
        if len(sys.argv) == 1:
            _os.execl(sys.executable, sys.executable, "-m", "pyUltroid")
        else:
            _os.execl(
                sys.executable,
                sys.executable,
                "-m",
                "pyUltroid",
                *sys.argv[1:7],
            )


async def shutdown(ult):
    if HOSTED_SANITIZED:
        return await eor(ult, "`Shutdown is disabled in hosted deployments.`")
    from .. import HOSTED_ON, LOGS

    ult = await eor(ult, "Shutting Down")
    if HOSTED_ON == "heroku":
        if not (Var.HEROKU_APP_NAME and Var.HEROKU_API):
            return await ult.edit("Please Fill `HEROKU_APP_NAME` and `HEROKU_API`")
        dynotype = _os.getenv("DYNO").split(".")[0]
        try:
            Heroku = heroku3.from_key(Var.HEROKU_API)
            app = Heroku.apps()[Var.HEROKU_APP_NAME]
            await ult.edit("`Shutting Down your app, please wait for a minute!`")
            app.process_formation()[dynotype].scale(0)
        except BaseException as e:
            LOGS.exception(e)
            return await ult.edit(
                "`HEROKU_API` and `HEROKU_APP_NAME` is wrong! Kindly re-check in config vars."
            )
    else:
        sys.exit()
