from __future__ import annotations

import discord, aiohttp, os, traceback, sys, hashlib, asyncio, json, math, mimetypes
from datetime import datetime
from discord import app_commands
from discord.ext import commands, tasks

from types import SimpleNamespace
from urllib.parse import urlparse

import mcv

botver = "2.1.1"

# --- mcv and json handing functions ---
def load_mcv_file(filepath: str):
    try:
        with open(filepath, "r") as marge:
            mcv_data = marge.read()
        return mcv.load(mcv_data)
    except FileNotFoundError:
        return {}

def save_mcv_file(filepath: str, data: dict, comment: str = None):
    with open(filepath, "w") as john:
        john.write(mcv.save(data, comment))

def load_data():
    global cfg
    with open("data.json") as steven:
        cfg = json.load(steven)

def save_data():
    with open("data.json", "w") as howard:
        json.dump(cfg, howard, indent=2)

# --- bot initialization ---
token = None
with open("token.txt") as whatever_vrombler:
    token = whatever_vrombler.read().strip()

cfgfile = load_mcv_file("config.mcv") # load config from mcv
developer = int(cfgfile["developer"])
prefix = cfgfile["prefix"]
filesdir = cfgfile["filesdir"]
global_limit = int(cfgfile["global_limit"])
user_limit = int(cfgfile["user_limit"])
file_limit = int(cfgfile["file_limit"])
discord_limit = int(cfgfile["discord_limit"])
splash = cfgfile["splash"]
page_size = int(cfgfile["page_size"])
trusted_user_limit = int(cfgfile["trusted_user_limit"])
trusted_file_limit = int(cfgfile["trusted_file_limit"])
website = cfgfile.get("website", "No Website Configured!")

cfg = None
load_data() # load json data to cfg

ready = False
startup_time = None

os.makedirs(filesdir, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="this is a placebo command prefix since im doing all the stuff in on_message lmao!", intents=intents)
tree = bot.tree

bot.session = None

emojis = load_mcv_file("emojis.mcv") # load emojis from mcv

err = {"badweb": f"{emojis['w']} The installer has encountered an unexpected error installing this package. This may indicate a problem with this package. The error code is 2503.",
       "notready": f"{emojis['e']} device or resource busy",
       "invalidurl": f"# :(\nYour BR ran into a problem and needs to restart. We're just collecting some error info, and then we'll restart for you.\n\n69% complete\n\n{emojis['q']} For more information and possible fixes, visit\n{website}\n\nif you call a support person, give them this info:\nError code: _resp.status_",
       "toobig": f"{emojis['w']} The file _attachment.filename_is too large for the destination file system.",
       "generic": f"{emojis['e']} The application was unable to start correctly (0x00000000). Click OK to close the application.",
       "filenotfound": f"{emojis['w']} File not found.\nCheck the file name and try again.",
       "php": f"{emojis['i']} You'll need a new app to download this\nPHP: Hypertext Preprocessor file",
       "diskfull": f"{emojis['e']} Disk Full\n\nThe Operation could not be completed because not enough space is available on the disk.",
       "quota": "An unexpected error is keeping you from downloading the file. If you continue to recieve this error, you can use the error code to search for help with this problem.\n\nError 0x00000000: Not enough quota is available to process this command.",
       "noperm": f"{emojis['w']} You don't currently have permission to access this folder.",
       "alreadyexists": f"{emojis['w']} Cannot create a file when that file already exists.",
       "successfully": f"{emojis['i']} The operation completed sucessfully",
       "filealreadyexists": f"{emojis['e']} There is already a file with the same name in this location."}

@bot.event
async def on_ready():
    global ready
    global token
    global startup_time
    del token
    bot.session = aiohttp.ClientSession()
    await tree.sync()
    ready = True
    print("i ate sand")
    update_description.start()
    startup_time = datetime.now().timestamp()

@bot.event
async def on_message(message: discord.Message):
    global ready

    if message.author.id == bot.user.id:
        return
    if message.author.id in cfg["banned_users"]:
        return
    if message.author.bot and not message.author.id in cfg["allowed_bots"]:
        return

    if message.content.startswith(prefix):
        if not ready:
            return await message.reply(err["notready"])
        cmd = message.content[len(prefix):].split()
        if not cmd:
            return await message.add_reaction(emojis['?'])
        if cmd[0] in cmds:
            if cmd[0] in trusted_only_cmds and not is_trusted(message.author.id):
                return await message.reply(err["noperm"])
            if cmd[0] in dev_only_cmds and not message.author.id == developer:
                return await message.reply(err["noperm"])

            try:
                await cmds[cmd[0]](message, cmd)
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                await message.reply(f"{err['generic']}\n-# {e}")
        else:
            await message.reply(f"```\n\n'{cmd[0]}' is not recognized as an internal or external command,\noperable program or batch file.```")
    else:
        if message.channel.id in cfg["registered_channels"]:
            if not ready:
                return await message.reply(err["notready"])
            try:
                await command_ul(message, [])
            except Exception as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                await message.reply(f"{err['generic']}\n-# {e}")

# --- command functions ---

async def command_ul(message, cmd):
    attachments = None
    url_data = None
    if message.attachments:
        attachments = message.attachments
    else:
        larp = linkrip(message.content)
        if larp:
            for bad in cfg["bad_sites"]:
                if bad in larp:
                    return await message.reply(err["badweb"])
            attachments = ["Magic"]

    if not attachments:
        return True
    await message.add_reaction(emojis["l"])
    dlerror = []
    for attachment in attachments:
        if attachment == "Magic":
            data, attachment = await downloadurl(larp, is_trusted(message.author.id))
            if data is None:
                await message.reply(attachment)
                dlerror.append("unknown-filename")
                break
        else:
            data = await attachment.read()

        fn = attachment.filename

        if data is None:
            await message.reply(err["filenotfound"])
            dlerror.append(fn)
            continue

        for php in ('.php', '.phar', '.phtml', '.pht', '.phps', '.phpt', '.cgi'):
            if fn.lower().endswith(php):
                await message.reply(err["php"])
                dlerror.append(fn)
                continue

        filim = file_limit
        if is_trusted(message.author.id):
            filim = trusted_file_limit

        filesize = size_disk(len(data))

        if filesize > file_limit: # file max check
            await message.reply(err["toobig"].replace("_attachment.filename_", f"'{fn}' "))
            dlerror.append(fn)
            continue

        os.makedirs(f"{filesdir}/{message.author.id}", exist_ok=True)

        uslim = user_limit
        if is_trusted(message.author.id):
            uslim = trusted_user_limit

        if get_folder_size(f"{filesdir}/{message.author.id}") + filesize > uslim: # user max check
            await message.reply(err["quota"])
            dlerror.append(fn)
            continue

        if get_folder_size(filesdir) + filesize > global_limit: # global max check
            await message.reply(err["diskfull"])
            dlerror.append(fn)
            continue

        fn_clean = ""
        for char in fn:
            if char in "1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZZXCVBNM.,?!@#$^&:;`-_=+()[]{}":
                fn_clean+=char
            else:
                fn_clean+="_"
        fn = fn_clean
        if fn in (".", ".."):
            fn = "billion_reservoir_file"

        dlpath = f"{filesdir}/{message.author.id}/{fn}"
        incrementor = 1
        name, ext = os.path.splitext(dlpath)
        if os.path.exists(dlpath): # ensure files dont get overwritten
            with open(dlpath, "rb") as quincy:
                dupdata = quincy.read()
            sha256 = hashlib.sha256(data).hexdigest()
            src256 = hashlib.sha256(dupdata).hexdigest()
            continuechecks = True
            if sha256 == src256: # filter duplicates
                await message.reply(err["alreadyexists"])
                dlerror.append(fn)
                continue

            while os.path.exists(dlpath) and continuechecks:
                with open(dlpath, "rb") as quincy:
                    dupdata = quincy.read()
                    src256 = hashlib.sha256(dupdata).hexdigest()
                    if sha256 == src256: # filter duplicates
                        continuechecks = False
                        await message.reply(err["alreadyexists"])
                        dlerror.append(fn)
                dlpath = name+"_"+str(incrementor)+ext
                incrementor+=1
            if not continuechecks:
                continue

        with open(dlpath, "wb") as greg:
            greg.write(data)

        mcvdata = load_mcv_file(f"{filesdir}/info.mcv")
        if not str(message.author.id) in mcvdata or not mcvdata[str(message.author.id)] == message.author.name:
            mcvdata[str(message.author.id)] = message.author.name
            save_mcv_file(f"{filesdir}/info.mcv", mcvdata, "This MCV file was generated by Billion Reservoir SSD. It contains mappings from user ids to usernames.")

    await message.remove_reaction(emojis["l"], bot.user)
    if dlerror:
        emsg = f"{emojis['w']} Failed to Download The Following files:\n```"
        for filename in dlerror:
            emsg+="* "+filename+'\n'
        emsg+="```"
        await message.reply(emsg)
        return await message.add_reaction(emojis["w"])
    else:
        await message.add_reaction("✅")
        return None # I AM SO SMART

async def command_hp(message, cmd):
    trusted=True if is_trusted(message.author.id) else False
    dev=True if message.author.id == developer else False

    res = f"""
{emojis['br']} Welcome to "Billion Reservoir" SSD v2
-# Version {botver}, developed by mari2_ok
The bot's prefix is `{prefix}`
```
* dl/down/download - Download a file from the SSD. For other user's files, do <username>/<filename>
* fr/free <optional: author, default: you> - Shows global and personal disk usage, as well as free space
* ls/list <optional: author, default: you> <optional: page> - List uploaded files
* sc/search <keyword> <optional: author, default: global> <optional: page> - Search for files
* ig/ignore - In a registered channel, ignore links/attachments on your message
* st/status <string> - Sets the bot's status/presence
* hi - Responds with "hi?"
* dt/del/delete <filename> - Deletes a file you uploaded
* rn/mv/ren/rename <old_filename> <new_filename> - Renames a file you uploaded to something else
* fi/file <filename> - Gets information about a specified file
* in/info - Gets information about this bot
* hp/help - Shows this message
```"""
    if trusted:
        res+="""```* up/ul/upload - [Trusted] Uploads a file to the SSD outside of set channels
* ad/add/add_channel - [Trusted] Registers a channel with the bot, allowing untrusted members to upload files in the channel
* rm/remove/remove_channel - [Trusted] Unregisters a channel from the bot\
```"""
    if dev:
        res+="""```* ev/eval - [Developer] Executes arbitrary code
* rs/restart - [Developer] Restarts the bot
* tr/trust <userid or mention> - [Developer] Adds specified user to trusted list
* ut/untrust <userid or mention> - [Developer] Removes specified user from trusted list
* ab/allow_bot <userid or mention> - [Developer] Adds specified bot user to allowed bots list
* bb/block_bot <userid or mention> - [Developer] Removes specified bot user from allowed bots list
* bn/ban <userid or mention> - [Developer] Bans specified user from uploading files
* ub/unban <userid or mention> - [Developer] Unbans specified user from uploading files
```"""

    await message.reply(res)

async def command_hi(message, cmd):
    await message.reply("hi?")

async def command_in(message, cmd):
    await message.reply(f"""{emojis['br']} "Billion Reservoir" SSD v{botver}
"Billion Reservoir" SSD is a bot that downloads files sent on Discord and makes them available on a simple web frontend
developed by mari2_ok
Owner: <@{developer}>
Web Frontend: {website}
Population: {len(bot.guilds)} servers
Uptime: `{relativetime(datetime.now().timestamp() - startup_time).strip()}`
""", allowed_mentions=discord.AllowedMentions.none())

async def command_rn(message, cmd):
    if len(cmd) < 3:
        return await message.reply(f"Usage: {prefix}{cmd[0]} <src_filename> <dest_filename>")
    nwp = f"{filesdir}/{message.author.id}/{cmd[2]}"
    if os.path.exists(nwp):
        return await message.reply(cmd[2]+'\n'+err["filealreadyexists"])
    try:
        os.rename(f"{filesdir}/{message.author.id}/{cmd[1]}", nwp)
        return await message.reply(f"{emojis['c']} The operation completed successfully")
    except  FileNotFoundError:
        await message.reply(cmd[1]+'\n'+err["filenotfound"])

async def command_dt(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"Usage: {prefix}{cmd[0]} <filename>")
    try:
        os.remove(f"{filesdir}/{message.author.id}/{cmd[1]}")
        return await message.reply(f"{emojis['c']} The operation completed successfully")
    except  FileNotFoundError:
        await message.reply(cmd[1]+'\n'+err["filenotfound"])

async def command_dl(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"Usage: {prefix}{cmd[0]} <filename>")
    splitcoin = cmd[1].split("/")
    if len(splitcoin) == 1:
        auth = str(message.author.id)
        fil = splitcoin[0]
    else:
        auth = splitcoin[0]
        fil = splitcoin[1]
        if not os.path.isdir(f"{filesdir}/{auth}/"):
            found = False
            possibleauthors = load_mcv_file(f"{filesdir}/info.mcv")
            for uid in possibleauthors:
                if auth == possibleauthors[uid]:
                    auth = uid
                    found = True
                    break
            if not found:
                await message.reply(f'{auth}/{fil}\n'+err["filenotfound"])

    fpath = f"{filesdir}/{auth}/{fil}"
    if os.path.isfile(fpath):
        fiel = discord.File(fpath)
        fsize = os.path.getsize(fpath)
        if fsize > discord_limit:
            await message.reply(fil+'\n'+err["toobig"].replace("_attachment.filename_", f"'{fil}' "))
        else:
            await message.add_reaction(emojis["l"])
            await message.reply(file=fiel)
            await message.remove_reaction(emojis["l"], bot.user)
    else:
        await message.reply(fil+'\n'+err["filenotfound"])

async def command_fi(message, cmd):
    possibleauthors = load_mcv_file(f"{filesdir}/info.mcv")
    if len(cmd) < 2:
        return await message.reply(f"Usage: {prefix}{cmd[0]} <filename>")
    splitcoin = cmd[1].split("/")
    if len(splitcoin) == 1:
        auth = str(message.author.id)
        fil = splitcoin[0]
    else:
        auth = splitcoin[0]
        fil = splitcoin[1]
        if not os.path.isdir(f"{filesdir}/{auth}/"):
            found = False
            for uid in possibleauthors:
                if auth == possibleauthors[uid]:
                    auth = uid
                    found = True
                    break
            if not found:
                await message.reply(f'{auth}/{fil}\n'+err["filenotfound"])

    fpath = f"{filesdir}/{auth}/{fil}"
    if os.path.isfile(fpath):
        fsize = os.path.getsize(fpath)
        fs_disk = size_disk(fsize)
        mime = mimetypes.guess_type(fpath)[0]
        ext = fil.split(".")[-1].lower()

        ftype = "File"
        if "."+ext in cfg["img"]:
            ftype = "Image"
        elif "."+ext in cfg["aud"]:
            ftype = "Audio"
        elif "."+ext in cfg["vid"]:
            ftype = "Video"
        elif "."+ext in cfg["doc"]:
            ftype = "Document"
        elif "."+ext in cfg["arc"]:
            ftype = "Archive"

        if mime is None:
            mime = "application/octet-stream"

        stat = os.stat(fpath)
        created = datetime.fromtimestamp(stat.st_ctime)
        modified = datetime.fromtimestamp(stat.st_mtime)
        accessed = datetime.fromtimestamp(stat.st_atime)

        await message.reply(f"""```
Filename:     {fil}
Type of file: {ext.upper()} {ftype} ({mime})
----------------------------------
Location:     {possibleauthors[auth]}/{fil}
Size:         {getfilesize(fsize)} ({fsize:,} bytes)
Size on disk: {getfilesize(fs_disk)} ({fs_disk:,} bytes)
----------------------------------
Created:      {created.strftime(r"%A, %B %d, %Y, %I:%M:%S %p")}
Modified:     {modified.strftime(r"%A, %B %d, %Y, %I:%M:%S %p")}
Accessed:     {accessed.strftime(r"%A, %B %d, %Y, %I:%M:%S %p")}
```""")
    else:
        await message.reply(fil+'\n'+err["filenotfound"])

async def command_rs(message, cmd):
    print("restarting...")
    await message.reply(f"{emojis['l']} Restarting")
    os.execv(sys.executable, ['python'] + sys.argv)

async def command_fr(message, cmd):
    if len(cmd) < 2:
        user = message.author.id
    else:
        user = int(cmd[1].replace("<@", "").replace(">", "")) # strip @mention syntax

    total = global_limit
    used = get_folder_size(filesdir)
    step = 40

    percent = round(((used)/total)*100, 2)

    progressbar = get_progress_bar(step, total, used)
    progressbar += "\n"

    brfr =f"{emojis['br']} Local Disk (B:)\n"
    brfr+=progressbar
    brfr+=f"{getfilesize(used)} of {getfilesize(total)} ({percent}%)\n\n"

    if os.path.isdir(f"{filesdir}/{user}/"):
        user_used = get_folder_size(f"{filesdir}/{user}/")
        user_total = user_limit
        if is_trusted(user):
            user_total = trusted_user_limit
        user_percent = round(((user_used)/user_total)*100, 2)

        cap = f"{user_total:,}"
        usd = f"{user_used:,}"
        rmn = f"{user_total-user_used:,}"

        cap, usd, rmn = formatsforthree(cap, usd, rmn)

        brfr+=f"{emojis['b']} Your used space: `{usd} bytes`      {getfilesize(user_used)} ({user_percent}%)\n"
        brfr+=f"{emojis['m']} Your free space:    `{rmn} bytes`      {getfilesize(user_total-user_used)}\n"
        brfr+="------------------------------------------------------------------\n"
        brfr+=f"Capacity:                         `{cap} bytes`      {getfilesize(user_total)}\n\n"
        userprogressbar = get_progress_bar(step, user_total, user_used, True)
        brfr+=userprogressbar

    await message.reply(brfr)

async def command_st(message, cmd):
    if len(cmd) < 2:
        cmd.append("")
    await bot.change_presence(activity=discord.CustomActivity(name=" ".join(cmd[1:])))
    if cmd[1]:
        await message.reply(f"{emojis['i']} Status updated to: `{" ".join(cmd[1:])}`.")
    else:
        await message.reply(f"{emojis['i']} Status cleared.")

async def command_ad(message, cmd):
    if message.channel.id in cfg["registered_channels"]:
        return await message.reply(f"{emojis['w']} I already download files sent here!")
    else:
        cfg["registered_channels"].append(message.channel.id)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I will now download files sent here!")

async def command_rm(message, cmd):
    if not message.channel.id in cfg["registered_channels"]:
        return await message.reply(f"{emojis['w']} I already don't download files sent here!")
    else:
        cfg["registered_channels"].remove(message.channel.id)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I will no longer download files sent here!")

async def command_tr(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"{emojis['e']} Error: user not specified.")

    user = int(cmd[1].replace("<@", "").replace(">", "")) # strip @mention syntax

    if user in cfg["trusted_users"]:
        return await message.reply(f"{emojis['w']} I already trust them!")
    else:
        cfg["trusted_users"].append(user)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I now trust <@{user}>!", allowed_mentions=discord.AllowedMentions.none())

async def command_ut(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"{emojis['e']} Error: user not specified.")

    user = int(cmd[1].replace("<@", "").replace(">", "")) # strip @mention syntax

    if not user in cfg["trusted_users"]:
        return await message.reply(f"{emojis['w']} I already don't trust them!")
    else:
        cfg["trusted_users"].remove(user)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I no longer trust <@{user}>!", allowed_mentions=discord.AllowedMentions.none())

async def command_ab(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"{emojis['e']} Error: user not specified.")

    user = int(cmd[1].replace("<@", "").replace(">", "")) # strip @mention syntax

    if user in cfg["allowed_bots"]:
        return await message.reply(f"{emojis['w']} I already allow them!")
    else:
        cfg["allowed_bots"].append(user)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I now allow <@{user}>!", allowed_mentions=discord.AllowedMentions.none())

async def command_bb(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"{emojis['e']} Error: user not specified.")

    user = int(cmd[1].replace("<@", "").replace(">", "")) # strip @mention syntax

    if not user in cfg["allowed_bots"]:
        return await message.reply(f"{emojis['w']} I already don't allow them!")
    else:
        cfg["allowed_bots"].remove(user)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I no longer allow <@{user}>!", allowed_mentions=discord.AllowedMentions.none())

async def command_bn(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"{emojis['e']} Error: user not specified.")

    user = int(cmd[1].replace("<@", "").replace(">", "")) # strip @mention syntax

    if user in cfg["banned_users"]:
        return await message.reply(f"{emojis['w']} They're already banned!")
    else:
        cfg["banned_users"].append(user)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I banned <@{user}>!", allowed_mentions=discord.AllowedMentions.none())

async def command_ub(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"{emojis['e']} Error: user not specified.")

    user = int(cmd[1].replace("<@", "").replace(">", "")) # strip @mention syntax

    if not user in cfg["banned_users"]:
        return await message.reply(f"{emojis['w']} They're not banned!")
    else:
        cfg["banned_users"].remove(user)
        save_data()
        return await message.reply(f"{emojis['i']} Ok, I unbanned <@{user}>!", allowed_mentions=discord.AllowedMentions.none())

async def command_ls(message, cmd):
    auth = str(message.author.id) if len(cmd) == 1 else cmd[1]
    page = 1 if len(cmd) < 3 else int(cmd[2])

    auth = auth.replace("<@", "").replace(">", "") # strip @mention syntax

    if auth.lower() in ("global", "*", "all", "yes", "yeah", "y", str(bot.user.id)):
        isglobal = True
        files=[]
        for auth in os.listdir(filesdir):
            if os.path.isdir(f"{filesdir}/{auth}/"):
                files.extend([os.path.join(filesdir, auth, f) for f in os.listdir(f"{filesdir}/{auth}/")])
        files.sort()

    elif not os.path.isdir(f"{filesdir}/{auth}/"):
        found = False
        possibleauthors = load_mcv_file(f"{filesdir}/info.mcv")
        for uid in possibleauthors:
            if auth == possibleauthors[uid]:
                auth = uid
                found = True
                break
        if not found:
            return await message.reply(err["filenotfound"])
        else:
            isglobal = False
            files = sorted([os.path.join(filesdir, auth, f) for f in os.listdir(f"{filesdir}/{auth}/")])
    else:
        isglobal = False
        files = sorted([os.path.join(filesdir, auth, f) for f in os.listdir(f"{filesdir}/{auth}/")])

    tage = (int(page))*page_size if str(page).isdigit() else page_size

    embed = generatetaglist(isglobal, tage, files)
    view = MenuView(isglobal, tage, files)
    view.message = await message.reply(embed=embed, view=view)

async def command_sc(message, cmd):
    if len(cmd) < 2:
        return await message.reply(f"Usage: {prefix}{cmd[0]} <filename> <optional: user> <optional: page>")

    keyword = cmd[1]
    auth = "*" if len(cmd) == 2 else cmd[2]
    page = 1 if len(cmd) < 4 else int(cmd[3])

    auth = auth.replace("<@", "").replace(">", "") # strip @mention syntax

    if auth.lower() in ("global", "*", "all", "yes", "yeah", "y", str(bot.user.id)):
        isglobal = True
        files=[]
        for auth in os.listdir(filesdir):
            if os.path.isdir(f"{filesdir}/{auth}/"):
                for f in os.listdir(f"{filesdir}/{auth}/"):
                    if keyword.lower() in f.lower():
                        files.append(os.path.join(filesdir, auth, f))
        files.sort()

    elif not os.path.isdir(f"{filesdir}/{auth}/"):
        found = False
        possibleauthors = load_mcv_file(f"{filesdir}/info.mcv")
        for uid in possibleauthors:
            if auth == possibleauthors[uid]:
                auth = uid
                found = True
                break
        if found:
            isglobal = False
            files = []
            for f in os.listdir(f"{filesdir}/{auth}/"):
                if keyword.lower() in f.lower():
                    files.append(os.path.join(filesdir, auth, f))
        else:
            return await message.reply(err["filenotfound"])
    else:
        isglobal = False
        files = []
        for f in os.listdir(f"{filesdir}/{auth}/"):
            if keyword.lower() in f.lower():
                files.append(os.path.join(filesdir, auth, f))

    tage = (int(page))*page_size if str(page).isdigit() else page_size

    embed = generatetaglist(isglobal, tage, files)
    view = MenuView(isglobal, tage, files)
    view.message = await message.reply(embed=embed, view=view)

#i am going to going to
mari_kepler = None # this is important  i think
async def command_ev(message, cmd):
    to_execute = message.content.splitlines()[1:] # discard first line
    to_exec = []
    for h in to_execute:
        if h.startswith("`"):
            continue
        else:
            to_exec.append(f"    {h}\n")

    toexec = "global mari_kepler\nasync def mari_kepler(message):\n"+"".join(to_exec)
    print(toexec)
    exec(toexec)
    try:
        await mari_kepler(message)
    except Exception as e:
        fuck = ''.join(traceback.format_exception(None, e, e.__traceback__))
        await message.reply(f"```\n{fuck[:1980]}\n```")

async def command_ig(message, cmd):
    pass

cmds = {"hi": command_hi,
        "up": command_ul,
        "ul": command_ul,
        "upload": command_ul,
        "dt": command_dt,
        "del": command_dt,
        "delete": command_dt,
        "rs": command_rs,
        "restart": command_rs,
        "ev": command_ev,
        "eval": command_ev,
        "fr": command_fr,
        "free": command_fr,
        "dl": command_dl,
        "down": command_dl,
        "download": command_dl,
        "st": command_st,
        "status": command_st,
        "ig": command_ig,
        "ignore": command_ig,
        "ad": command_ad,
        "add": command_ad,
        "add_channel": command_ad,
        "rm": command_rm,
        "remove": command_rm,
        "remove_channel": command_rm,
        "ls": command_ls,
        "list": command_ls,
        "sc": command_sc,
        "search": command_sc,
        "hp": command_hp,
        "help": command_hp,
        "tr": command_tr,
        "trust": command_tr,
        "ut": command_ut,
        "untust": command_ut,
        "rn": command_rn,
        "mv": command_rn,
        "ren": command_rn,
        "rename": command_rn,
        "ab": command_ab,
        "allow_bot": command_ab,
        "bb": command_bb,
        "block_bot": command_bb,
        "bn": command_bn,
        "ban": command_bn,
        "ub": command_ub,
        "unban": command_ub,
        "in": command_in,
        "info": command_in,
        "fi": command_fi,
        "file": command_fi,
        } # command registration

# slash command registration
@tree.command(name="hi", description="Responds with \"hi?\"")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hi_tree(ctx: commands.Context):
    await ctx.response.defer()
    await command_hi(imw(ctx), None)

@tree.command(name="upload", description="[Trusted] Uploads a file to the bot")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def up_tree(ctx: commands.Context, attachment: discord.Attachment):
    await ctx.response.defer()
    if not is_trusted(ctx.user.id):
        return await ctx.followup.send(err["noperm"])

    h = await command_ul(imw(ctx, attachment), None)
    if not h:
        await ctx.followup.send(err["successfully"]+f"\nuploaded file `{attachment.filename}`!")

@tree.command(name="delete", description="Deletes a file you uploaded")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def dt_tree(ctx: commands.Context, filename: str):
    await ctx.response.defer()
    await command_dt(imw(ctx), ["/delete", filename])

@tree.command(name="rename", description="Renames a file you uploaded")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def rn_tree(ctx: commands.Context, old_filename: str, new_filename: str):
    await ctx.response.defer()
    await command_rn(imw(ctx), ["/rename", old_filename, new_filename])

@tree.command(name="free", description="Shows global and personal disk usage, as well as free space")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def fr_tree(ctx: commands.Context, user: discord.Member = None):
    if user is None:
        user = ctx.user
    await ctx.response.defer()
    await command_fr(imw(ctx), ["/free", str(user.id)])

@tree.command(name="help", description="Shows available text commands")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hp_tree(ctx: commands.Context):
    await ctx.response.defer()
    await command_hp(imw(ctx), None)

@tree.command(name="status", description="Sets the bot's status/presence")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def st_tree(ctx: commands.Context, status: str):
    await ctx.response.defer()
    await command_st(imw(ctx), ["status", status])

@tree.command(name="add_channel", description="[Trusted] Registers a channel with the bot")
async def hi_tree(ctx: commands.Context):
    await ctx.response.defer()
    if not is_trusted(ctx.user.id):
        return await ctx.followup.send(err["noperm"])
    await command_ad(imw(ctx), None)

@tree.command(name="remove_channel", description="[Trusted] Unregisters a channel from the bot")
async def hi_tree(ctx: commands.Context):
    await ctx.response.defer()
    if not is_trusted(ctx.user.id):
        return await ctx.followup.send(err["noperm"])
    await command_rm(imw(ctx), None)

@tree.command(name="restart", description="[Developer] Restarts the bot")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hi_tree(ctx: commands.Context):
    await ctx.response.defer()
    if not ctx.user.id == developer:
        return await ctx.followup.send(err["noperm"])
    await command_rs(imw(ctx), None)

@tree.command(name="download", description="Download a file from the SSD. For other user's files, do <username>/<filename>")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hi_tree(ctx: commands.Context, filename: str):
    await ctx.response.defer()
    await command_dl(imw(ctx), ["/download", filename])

@tree.command(name="file", description="Gets information about a specified file")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def fi_tree(ctx: commands.Context, filename: str):
    await ctx.response.defer()
    await command_fi(imw(ctx), ["/file", filename])

@tree.command(name="info", description="Gets information about this bot")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def in_tree(ctx: commands.Context):
    await ctx.response.defer()
    await command_in(imw(ctx), None)

@tree.command(name="list", description="Lists your files or another user's files, or all files")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hi_tree(ctx: commands.Context, user: discord.Member = None, page: int = 1):
    if user is None:
        user = ctx.user
    await ctx.response.defer()
    await command_ls(imw(ctx), ["list", str(user.id), str(page)])

@tree.command(name="search", description="Search for files")
@app_commands.user_install()
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hi_tree(ctx: commands.Context, keyword: str, user: discord.Member = None, page: int = 1):
    if user is None:
        user = bot.user
    await ctx.response.defer()
    await command_sc(imw(ctx), ["list", keyword, str(user.id), str(page)])

trusted_only_cmds = ["up", "upload", "ad", "add", "rm", "remove", "ul", "add_channel", "remove_channel"]
dev_only_cmds = ["rs", "restart", "ev", "eval", "tr", "trust", "ut", "untrust"]

# --- misc functions ---

def pass_function(*args):
    return None

async def pass_async(*args):
    return None

def imw(ctx, attachment = None):
    message = SimpleNamespace(reply=ctx.followup.send, attachments=[attachment], add_reaction=pass_async, remove_reaction=pass_async, author=ctx.user, channel=ctx.channel)
    return message

def get_progress_bar(step, total, used, user=False):
    frac = numprogresssteps(step, total, used)

    w = ''
    if frac > (step*85)//100: # set red color theme based on *about* 85% of step
        w = 'w'

    progressbar = []
    for i in range(step):
        if i%2:
            if not (frac)%2:
                i+=1
            if frac > i:
                if user:
                    progressbar.append(emojis['b']) # add user full
                else:
                    progressbar.append(emojis[f'{w}bf']) # add full

            elif frac < i:
                if user:
                    progressbar.append(emojis['m']) # add user empty
                else:
                    progressbar.append(emojis[f'{w}be']) # add empty

            elif (i)%2:
                if user:
                    progressbar.append(emojis['bm']) # add user half
                else:
                    progressbar.append(emojis[f'{w}bh']) # add half edge
            else:
                if user:
                    progressbar.append(emojis['b']) # add user full
                else:
                    progressbar.append(emojis[f'{w}bfe']) # add full edge

    return "".join(progressbar)

def formatsforthree(cap, usd, rmn):
    maxlen = len(cap)
    while len(usd) < maxlen:
        usd = " "+usd
    while len(rmn) < maxlen:
        rmn = " "+rmn
    return cap, usd, rmn

def numprogresssteps(steps: int, total: int, current: int):
    precent = current/total
    if precent >= 1:
        return steps
    elif precent <= 0:
        return 0
    else:
        return round(precent*steps)

def linkrip(inp: str):
    stuff = inp.split()
    for word in stuff:
        if word.startswith("http"):
            if word[:7] in ("http://", "https:/"):
                return word
    return None

def is_trusted(user: int):
    if user in cfg["trusted_users"]:
        return True
    else:
        return False

def relativetime(time: float):
    time = round(time)
    days = time//86400
    hours = (time%86400)//3600
    minutes = (time%3600)//60
    seconds = (time%60)
    ts = ''
    if days:
        ts+=f"{days}d, "
    if hours:
        ts+=f"{hours}h "
    if minutes:
        ts+=f"{minutes}m "
    if seconds:
        ts+=f"{seconds}s"
    return ts

async def downloadurl(larp: str, increasefilelimit: bool = False):
    filim = file_limit
    if increasefilelimit:
        filim = trusted_file_limit
    async with bot.session.get(larp) as resp:
        content_length = resp.headers.get('Content-Length')
        if resp.status == 200:
            if content_length and int(content_length) > filim:
                return None, err["toobig"].replace("_attachment.filename_", "")

            cd = resp.headers.get("Content-Disposition")
            if cd and "filename=" in cd:
                filename = cd.split("filename=")[1].strip('"')
            else:
                filename = os.path.basename(urlparse(str(resp.url)).path)
            attachment = SimpleNamespace(filename=filename or "download", content_type=resp.headers.get("Content-Type"))
            data = await resp.read()
            return data, attachment
        else:
            return None, err["invalidurl"].replace("_resp.status_", str(resp.status))
    return None, err["generic"]

def get_folder_size(folder):
    total = 0
    for item in os.listdir(folder):
        path = os.path.join(folder, item)
        if os.path.isfile(path):
            total += os.stat(path).st_blocks*512
        elif os.path.isdir(path):
            for inner_item in os.listdir(path):
                inner_path = os.path.join(path, inner_item)
                if os.path.isfile(inner_path):
                    total += os.stat(inner_path).st_blocks*512
    return total

def getfilesize(size: int, decimalplaces = 2):
    ext = "B"
    if size > 2048:
        size = size / 1024
        ext = "KB" # binary Kilobytes
    if size > 2048:
        size = size / 1024
        ext = "MB" # binary megabytes
    if size > 2048:
        size = size / 1024
        ext = "GB" # binary gigabytes
    if size > 2048:
        size = size / 1024
        ext = "TB" # binary terabytes
    if size > 2048:
        size = size / 1024
        ext = "PB" # what
    return f"{round(size, decimalplaces)} {ext}"

def generatetaglist(authorId, tage: int, fileslist: list):
    tagslist = ""
    for tag in fileslist[tage-page_size:tage]:
        icon = emojis['fg']
        if "."+tag.split(".")[-1].lower() in cfg["img"]:
            icon = emojis['fi']
        elif "."+tag.split(".")[-1].lower() in cfg["aud"]:
            icon = emojis['fa']
        elif "."+tag.split(".")[-1].lower() in cfg["vid"]:
            icon = emojis['fv']
        elif "."+tag.split(".")[-1].lower() in cfg["doc"]:
            icon = emojis['fd']
        elif "."+tag.split(".")[-1].lower() in cfg["arc"]:
            icon = emojis['fz']

        filesize = getfilesize(os.path.getsize(tag))
        if authorId:
            h = tag.split("/")[-2]
            mcvdata = load_mcv_file(f"{filesdir}/info.mcv")
            if h in mcvdata:
                h = mcvdata[h]
            h+='/'
        else:
            h = ""
        tagslist += f"{icon} {h}**{tag.split("/")[-1].replace('_', '\\_')}** ({filesize})\n"
    if not tagslist:
        tagslist = "-# dust"
    embed = discord.Embed(
        title=f"Page ({math.floor(tage/page_size)}/{math.ceil(len(fileslist)/page_size)})",
        description=tagslist,
        color=discord.Color.from_rgb(0x92, 0xbf, 0x2b))
    return embed

def size_disk(size: int):
    return (math.ceil(size/4096))*4096

# --- PAGIATION ---
class MenuView(discord.ui.View):
    message: discord.Message | None = None

    def __init__(self, authorId: str, page: int, fileslist: list) -> None:
        super().__init__(timeout=None)
        self.authorId = authorId
        self.page = page
        self.fileslist = fileslist

    # adding a component using it's decorator
    @discord.ui.button(label="<<", style=discord.ButtonStyle.gray)
    async def firs(self, inter: discord.Interaction, button: discord.ui.Button[MenuView]) -> None:
        self.page = page_size
        embed = generatetaglist(self.authorId, self.page, self.fileslist)
        await inter.response.edit_message(embed=embed, view=self)
    @discord.ui.button(label="<", style=discord.ButtonStyle.gray)
    async def prev(self, inter: discord.Interaction, button: discord.ui.Button[MenuView]) -> None:
        self.page -= page_size
        if self.page < page_size:
            self.page = page_size
        embed = generatetaglist(self.authorId, self.page, self.fileslist)
        await inter.response.edit_message(embed=embed, view=self)
    @discord.ui.button(label=">", style=discord.ButtonStyle.gray)
    async def next(self, inter: discord.Interaction, button: discord.ui.Button[MenuView]) -> None:
        self.page += page_size
        if self.page > (math.ceil(len(self.fileslist)/page_size))*page_size:
            self.page = (math.ceil(len(self.fileslist)/page_size))*page_size
        embed = generatetaglist(self.authorId, self.page, self.fileslist)
        await inter.response.edit_message(embed=embed, view=self)
    @discord.ui.button(label=">>", style=discord.ButtonStyle.gray)
    async def last(self, inter: discord.Interaction, button: discord.ui.Button[MenuView]) -> None:
        self.page = (math.ceil(len(self.fileslist)/page_size))*page_size
        embed = generatetaglist(self.authorId, self.page, self.fileslist)
        await inter.response.edit_message(embed=embed, view=self)

    # error handler for the view
    async def on_error(
        self, interaction: discord.Interaction[discord.Client], error: Exception, item: discord.ui.Item[typing.Any]
    ) -> None:
        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        message = f"An error occurred while processing the interaction for {str(item)}:\n```py\n{tb}\n```"
        await interaction.response.send_message(message)

# --- taskloop ---
@tasks.loop(minutes = 10)
async def update_description():
    channel = bot.get_channel(cfg["registered_channels"][0])
    totalusedspace = get_folder_size(filesdir)
    res = f"{getfilesize(totalusedspace, 1)}/{getfilesize(global_limit, 1)} | {emojis['br']} "+get_progress_bar(20, global_limit, totalusedspace)+"\n\n"+splash
    await channel.edit(topic=res)

bot.run(token)
