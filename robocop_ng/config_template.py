import datetime
import hashlib

# Basic bot config, insert your token here, update description if you want
prefixes = [".", "!"]
client_id = 0
token = "token-goes-here"
bot_description = "Robocop-NG, the moderation bot of ReSwitched."

# If you forked robocop-ng, put your repo here
source_url = "https://github.com/reswitched/robocop-ng"
rules_url = "https://reswitched.github.io/discord/#rules"

# The bot description to be used in .robocop embed
embed_desc = (
    "Robocop-NG is developed by [Ave](https://github.com/aveao)"
    " and [tomGER](https://github.com/tumGER), and is a rewrite "
    "of Robocop.\nRobocop is based on Kurisu by 916253 and ihaveamac."
)


# The cogs the bot will load on startup.
initial_cogs = [
    "cogs.common",
    "cogs.admin",
    "cogs.verification",
    "cogs.mod",
    "cogs.mod_note",
    "cogs.mod_reacts",
    "cogs.mod_userlog",
    "cogs.mod_timed",
    "cogs.mod_watch",
    "cogs.basic",
    "cogs.logs",
    "cogs.err",
    "cogs.lockdown",
    "cogs.legacy",
    "cogs.links",
    "cogs.remind",
    "cogs.robocronp",
    "cogs.vanity_url",
    "cogs.meme",
    "cogs.invites",
    "cogs.yubicootp",
]

# The following cogs are also available but aren't loaded by default:
# cogs.imagemanip - Adds a meme command called .cox.
# Requires Pillow to be installed with pip.
# cogs.lists - Allows managing list channels (rules, FAQ) easily through the bot
# PR'd in at: https://github.com/reswitched/robocop-ng/pull/65
# cogs.pin - Lets users pin important messages
# and sends pins above limit to a github gist


# The string that users need to say to get past verification
verification_string = "go read the rules, not the code"


# Minimum account age required to join the guild
# If user's account creation is shorter than the time delta given here
# then user will be kicked and informed
min_age = datetime.timedelta(minutes=15)

# The bot will only work in these guilds
guild_whitelist = [269333940928512010]  # ReSwitched discord

# Custom invite URL codes
vanity_codes = {269333940928512010: "reswitched"}

# Named roles to be used with .approve and .revoke
# Example: .approve User hacker
named_roles = {
    "community": 420010997877833731,
    "hacker": 364508795038072833,
    "participant": 434353085926866946,
    "pirate": 0,
}

# The bot manager and staff roles
# Bot manager can run eval, exit and other destructive commands
# Staff can run administrative commands
bot_manager_role_id = 466447265863696394  # Bot management role in ReSwitched
staff_role_ids = [
    364647829248933888,  # Team role in ReSwitched
    360138431524765707,  # Mod role in ReSwitched
    466447265863696394,  # Bot management role in ReSwitched
    360138163156549632,  # Admin role in ReSwitched
    287289529986187266,  # Wizard role in ReSwitched
]

# Various log channels used to log bot and guild's activity
# You can use same channel for multiple log types
# Spylog channel logs suspicious messages or messages by members under watch
# Invites created with .invite will direct to the welcome channel.
log_channel = 290958160414375946  # server-logs in ReSwitched
botlog_channel = 529070282409771048  # bot-logs channel in ReSwitched
modlog_channel = 542114169244221452  # mod-logs channel in ReSwitched
spylog_channel = 548304839294189579  # spy channel in ReSwitched
welcome_channel = 326416669058662401  # newcomers channel in ReSwitched

# These channel entries are used to determine which roles will be given
# access when we unmute on them
general_channels = [
    420029476634886144,
    414949821003202562,
    383368936466546698,
    343244421044633602,
    491316901692178432,
    539212260350885908,
]  # Channels everyone can access
community_channels = [
    269333940928512010,
    438839875970662400,
    404722395845361668,
    435687501068501002,
    286612533757083648,
]  # Channels requiring community role

# Controls which roles are blocked during lockdown
lockdown_configs = {
    # Used as a default value for channels without a config
    "default": {"channels": general_channels, "roles": [named_roles["participant"]]},
    "community": {
        "channels": community_channels,
        "roles": [named_roles["community"], named_roles["hacker"]],
    },
}

# Mute role is applied to users when they're muted
# As we no longer have mute role on ReSwitched, I set it to 0 here
mute_role = 0  # Mute role in ReSwitched

# Channels that will be cleaned every minute/hour.
# This feature isn't very good rn.
# See https://github.com/reswitched/robocop-ng/issues/23
minutely_clean_channels = []
hourly_clean_channels = []

# Edited and deletes messages in these channels will be logged
spy_channels = general_channels

# All lower case, no spaces, nothing non-alphanumeric
suspect_words = [
    "deepsea",  # piracy-enabling cfw
    "sx",  # piracy-enabling cfw
    "tx",  # piracy-enabling cfw
    "reinx",  # piracy-enabling cfw
    "gomanx",  # piracy-enabling cfw
    "neutos",  # piracy-enabling cfw
    "underpack",  # piracy-enabling cfw
    "underos",  # piracy-enabling cfw
    "tinfoil",  # title manager
    "dz",  # title manager
    "goldleaf",  # potential title manager
    "lithium",  # title manager
    "cracked",  # older term for pirated games
    "xci",  # "backup" format
    "xcz",  # "backup" format
    "nsz",  # "backup" format
    "hbg",  # piracy source
    "jits",  # piracy source
]

# List of words that will be ignored if they match one of the
# suspect_words (This is used to remove false positives)
suspect_ignored_words = [
    "excit",
    "s/x",
    "3dsx",
    "psx",
    "txt",
    "s(x",
    "txd",
    "t=x",
    "osx",
    "rtx",
    "shift-x",
    "users/x",
    "tx1",
    "tx2",
    "tcptx",
    "udptx",
    "ctx",
    "jit's",
]

# == For cogs.links ==
links_guide_text = """**Generic starter guides:**
Nintendo Homebrew's Guide: <https://nh-server.github.io/switch-guide/>

**Specific guides:**
Manually Updating/Downgrading (with HOS): <https://switch.homebrew.guide/usingcfw/manualupgrade>
Manually Repairing/Downgrading (without HOS): <https://switch.homebrew.guide/usingcfw/manualchoiupgrade>
How to set up a Homebrew development environment: <https://devkitpro.org/wiki/Getting_Started>
Getting full RAM in homebrew without NSPs: As of Atmosphere 0.8.6, hold R while opening any game.
Check if a switch is vulnerable to RCM through serial: <https://akdm.github.io/ssnc/checker/>
"""

# == For cogs.verification ==
# ReSwitched verification system is rather unique.
# You might want to reimplement it.
# If you do, use a different name for easier upstream merge.

# https://docs.python.org/3.7/library/hashlib.html#shake-variable-length-digests
_welcome_blacklisted_hashes = {"shake_128", "shake_256"}

# List of hashes that are to be used during verification
welcome_hashes = tuple(hashlib.algorithms_guaranteed - _welcome_blacklisted_hashes)

# Header before rules in #newcomers - https://elixi.re/i/opviq90y.png
welcome_header = """
<:ReSwitched:326421448543567872> __**Welcome to ReSwitched!**__

__**Be sure you read the following rules and information before participating. If you came here to ask about "backups", this is NOT the place.**__

__**Got questions about Nintendo Switch hacking? Before asking in the server, please see our FAQ at <https://reswitched.github.io/faq/> to see if your question has already been answered.**__

__**This is a server for technical discussion and development support. If you are looking for end-user support, the Nintendo Homebrew discord server may be a better fit: <https://discord.gg/C29hYvh>.**__

​:bookmark_tabs:__Rules:__
"""

# Rules in #newcomers - https://elixi.re/i/dp3enq5i.png
welcome_rules = (
    # 1
    """
    Read all the rules before participating in chat. Not reading the rules is *not* an excuse for breaking them.
     • It's suggested that you read channel topics and pins before asking questions as well, as some questions may have already been answered in those.
    """,
    # 2
    """
    Be nice to each other. It's fine to disagree, it's not fine to insult or attack other people.
     • You may disagree with anyone or anything you like, but you should try to keep it to opinions, and not people. Avoid vitriol.
     • Constant antagonistic behavior is considered uncivil and appropriate action will be taken.
     • The use of derogatory slurs -- sexist, racist, homophobic, transphobic, or otherwise -- is unacceptable and may be grounds for an immediate ban.
    """,
    # 3
    'If you have concerns about another user, please take up your concerns with a staff member (someone with the "mod" role in the sidebar) in private. Don\'t publicly call other users out.',
    # 4
    """
    From time to time, we may mention everyone in the server. We do this when we feel something important is going on that requires attention. Complaining about these pings may result in a ban.
     • To disable notifications for these pings, suppress them in "ReSwitched → Notification Settings".
    """,
    # 5
    """
    Don't spam.
     • For excessively long text, use a service like <https://0bin.net/>.
    """,
    # 6
    "Don't brigade, raid, or otherwise attack other people or communities. Don't discuss participation in these attacks. This may warrant an immediate permanent ban.",
    # 7
    "Off-topic content goes to #off-topic. Keep low-quality content like memes out.",
    # 8
    "Trying to evade, look for loopholes, or stay borderline within the rules will be treated as breaking them.",
    # 9
    """
    Absolutely no piracy or related discussion. This includes:
     • "Backups", even if you legally own a copy of the game.
     • "Installable" NSPs, XCIs, and NCAs; this **includes** installable homebrew (i.e. on the Home Menu instead of within nx-hbmenu).
     • Signature and ES patches, also known as "sigpatches"
     • Usage of piracy-focused groups' (Team Xecuter, etc.) hardware and software, such as SX OS.
    This is a zero-tolerance, non-negotiable policy that is enforced strictly and swiftly, up to and including instant bans without warning.
    """,
    # 10
    "The first character of your server nickname should be alphanumeric if you wish to talk in chat.",
    # 11
    """
    Do not boost the server.
     • ReSwitched neither wants nor needs your server boosts, and your money is better off elsewhere. Consider the EFF (or a charity of your choice).
     • Boosting the server is liable to get you kicked (to remove the nitro boost role), and/or warned. Roles you possessed prior to the kick may not be restored in a timely fashion.
    """,
)


# Footer after rules in #newcomers - https://elixi.re/i/uhfiecib.png
welcome_footer = (
    """
    :hash: __Channel Breakdown:__
    #news - Used exclusively for updates on ReSwitched progress and community information. Most major announcements are passed through this channel and whenever something is posted there it's usually something you'll want to look at.

    #switch-hacking-meta - For "meta-discussion" related to hacking the switch. This is where we talk *about* the switch hacking that's going on, and where you can get clarification about the hacks that exist and the work that's being done.

    #user-support - End-user focused support, mainly between users. Ask your questions about using switch homebrew here.

    #tool-support - Developer focused support. Ask your questions about using PegaSwitch, libtransistor, Mephisto, and other tools here.

    #hack-n-all - General hacking, hardware and software development channel for hacking on things *other* than the switch. This is a great place to ask about hacking other systems-- and for the community to have technical discussions.
    """,
    """
    #switch-hacking-general - Channel for everyone working on hacking the switch-- both in an exploit and a low-level hardware sense. This is where a lot of our in-the-open development goes on. Note that this isn't the place for developing homebrew-- we have #homebrew-development for that!

    #homebrew-development - Discussion about the development of homebrew goes there. Feel free to show off your latest creation here.

    #off-topic - Channel for discussion of anything that doesn't belong in #general. Anything goes, so long as you make sure to follow the rules and be on your best behavior.

    #toolchain-development - Discussion about the development of libtransistor itself goes there.

    #cfw-development - Development discussion regarding custom firmware (CFW) projects, such as Atmosphère. This channel is meant for the discussion accompanying active development.

    #bot-cmds - Channel for excessive/random use of Robocop's various commands.

    **If you are still not sure how to get access to the other channels, please read the rules again.**
    **If you have questions about the rules, feel free to ask here!**

    **Note: This channel is completely automated (aside from responding to questions about the rules). If your message didn't give you access to the other channels, you failed the test. Feel free to try again.**
    """,
)

# Line to be hidden in rules
hidden_term_line = ' • When you have finished reading all of the rules, send a message in this channel that includes the {0} hex digest of your discord "name#discriminator", and bot will automatically grant you access to the other channels. You can find your "name#discriminator" (your username followed by a ‘#’ and four numbers) under the discord channel list.'

# == Only if you want to use cogs.pin ==
# Used for the pinboard. Leave empty if you don't wish for a gist pinboard.
github_oauth_token = ""

# Channels and roles where users can pin messages
allowed_pin_channels = []
allowed_pin_roles = []

# Channel to upload text files while editing list items. (They are cleaned up.)
list_files_channel = 0

# == Only if you want to use cogs.lists ==
# Channels that are lists that are controlled by the lists cog.
list_channels = []

# == Only if you want to use cogs.sar ==
self_assignable_roles = {
    "streamnotifs": 715158689060880384,
}

# == Only if you want to use cogs.mod_reswitched ==
pingmods_allow = [named_roles["community"]] + staff_role_ids
pingmods_role = 360138431524765707
modtoggle_role = 360138431524765707

# == Only if you want to use cogs.yubicootp ==
# Optiona: Get your own from https://upgrade.yubico.com/getapikey/
yubico_otp_client_id = 1
# Note: You can keep client ID on 1, it will function.
yubico_otp_secret = ""
# Optional: If you provide a secret, requests will be signed
# and responses will be verified.
