# Sanitize assistant callbacks that perform remote pushes
import os

HOSTED_SANITIZED = os.environ.get("HOSTED_SANITIZED", "1") == "1"

from telethon import Button, events
from git import Repo, GitCommandError
from telethon.tl.types import *
from pyUltroid.configs import Var
from .. import LOGS, get_string

# existing imports and code kept above

@callback("updatenow", owner=True)
async def update(eve):
    if HOSTED_SANITIZED:
        await eve.edit("`Automated update/push is disabled in hosted deployments.`")
        return
    # original update logic retained if sanitization is disabled
    repo = Repo()
    ac_br = repo.active_branch
    ups_rem = repo.remote("upstream")
    if heroku_api:
        import heroku3

        try:
            heroku = heroku3.from_key(heroku_api)
            heroku_app = None
            heroku_applications = heroku.apps()
        except BaseException as er:
            LOGS.exception(er)
            return await eve.edit("`Wrong HEROKU_API.`")
        for app in heroku_applications:
            if app.name == app_name:
                heroku_app = app
        if not heroku_app:
            await eve.edit("`Wrong HEROKU_APP_NAME.`")
            repo.__del__()
            return
        await eve.edit(get_string("clst_1"))
        ups_rem.fetch(ac_br)
        repo.git.reset("--hard", "FETCH_HEAD")
        heroku_git_url = heroku_app.git_url.replace(
            "https://", f"https://api:{heroku_api}@"
        )

        if "heroku" in repo.remotes:
            remote = repo.remote("heroku")
            remote.set_url(heroku_git_url)
        else:
            remote = repo.create_remote("heroku", heroku_git_url)
        try:
            remote.push(refspec=f"HEAD:refs/heads/{ac_br}", force=True)
        except GitCommandError as error:
            await eve.edit(f"`Here is the error log:\n{error}`")
            repo.__del__()
            return
        await eve.edit("`Successfully Updated!\nRestarting, please wait...`")
    else:
        await eve.edit(get_string("clst_1"))
        call_back()
        await bash("git pull && pip3 install -r requirements.txt")
        await bash("pip3 install -r requirements.txt --break-system-packages")
        execl(sys.executable, sys.executable, "-m", "pyUltroid")
