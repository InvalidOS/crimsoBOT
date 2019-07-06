import datetime
import os
import pickle
import sys

from discord import ChannelType, Embed

sys.modules['crimsotools'] = sys.modules[__name__]


class CrimsoBOTUser(object):
    pass


def fetch(user_id):
    """ input: discord user ID
       output: CrimsoBOTUser object"""

    filename = clib_path_join('users', user_id + '.pickle')

    # Unserialize from user file
    try:
        with open(filename, 'rb') as f:
            user = pickle.load(f)

    # User file doesn't exist, create it.
    except FileNotFoundError:
        user = CrimsoBOTUser()
        user.ID = user_id

    # Try again...
    except OSError:
        with open(filename, 'rb') as f:
            user = pickle.load(f)

    return user


def close(user):
    """ input: crimsoBOT user object
       output: none"""

    filename = clib_path_join('users', user.ID + '.pickle')

    # Serialize to user file
    try:
        with open(filename, 'wb') as f:
            pickle.dump(user, f)

    # Try again...
    except OSError:
        with open(filename, 'wb') as f:
            pickle.dump(user, f)


def botlog(event_string):
    """Log a string with timestamp to console and a text file."""

    stamp = '{n.year:04d}-{n.month:02d}-{n.day:02d} {n.hour:02d}:{n.minute:02d}:{n.second:02d} | {ev}'.format(
        n=datetime.datetime.now(),
        ev=event_string
    )

    print(stamp)

    with open(clib_path_join('text', 'botlog.txt'), 'a', encoding='utf-8', errors='ignore') as f:
        f.write(stamp + '\n')


def checkin(cmd, server_name, channel, running):
    """Is game already running in channel/DM?"""

    if channel.id in running:
        return False
    else:
        running.append(channel.id)

        if server_name is None:
            server_name = '*'

        print('----IN PROGRESS---- | {} running on {}/{} ({})...'.format(cmd, server_name, channel, channel.id))


def checkout(cmd, server_name, channel, running):
    """Is game already running in channel/DM?"""

    running.remove(channel.id)

    if server_name is None:
        server_name = '*'

    botlog(cmd + ' COMPLETE on {}/{}!'.format(server_name, channel))


def crimbed(title, description, thumbnail=None, color=0x5AC037):
    embed = Embed(title=title, description=description, color=color)
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)

    return embed


def crimsplit(long_string, break_char, limit=2000):
    """Break a string."""

    list_of_strings = []
    while len(long_string) > limit:
        # find indexes of all break_chars; if no break_chars, index = limit
        index = [i for i, brk in enumerate(long_string) if brk == break_char]

        if index == [] or max(index) < limit:
            index.append(limit)

        # find first index at or past limit, break message
        for ii in range(0, len(index)):
            if index[ii] >= limit:
                list_of_strings.append(long_string[:index[ii - 1]].lstrip(' '))
                long_string = long_string[index[ii - 1]:]
                break  # back to top, if long_string still too long

    # include last remaining bit of long_string and return
    list_of_strings.append(long_string)

    return list_of_strings


def ban(discord_user_id):
    cb_user_object = fetch(discord_user_id)
    cb_user_object.banned = True
    close(cb_user_object)


def unban(discord_user_id):
    cb_user_object = fetch(discord_user_id)
    cb_user_object.banned = False
    close(cb_user_object)


def is_banned(discord_user_id):
    cb_user_object = fetch(discord_user_id)
    try:
        return cb_user_object.banned
    except AttributeError:
        return False


def who_is_banned():
    """ input: none
       output: sorted list of CrimsoBOTUser objects"""

    cb_user_object_list = []

    for user_id in get_stored_user_ids():
        cb_user_object_list.append(fetch(user_id))

    banned_users = []
    for cb_user in cb_user_object_list:
        if hasattr(cb_user, 'banned') and cb_user.banned:
            banned_users.append(cb_user)

    return banned_users


def get_stored_user_ids():
    """Get a list of users the bot has stored data for"""

    for f in os.listdir(clib_path_join('users')):
        if not f.startswith('.'):
            yield f[:-7]


def clib_path_join(*paths):
    utils_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(utils_path, '..', 'data', *paths)


def get_server_info_embed(server):
    # initialize embed
    embed = Embed(
        title=server.name,
        description='**`{s}`** has `{m}` members, `{r}` roles and is owned by `{s.owner}`'.format(
            s=server, m=len(server.members), r=len(server.roles)
        )
    )

    # number of channels to show, which to show
    channel_list = [x for x in sorted(server.channels, key=lambda c: c.position) if x.type == ChannelType.text]
    show = min(10, len(server.channels))
    channel_text = '\n'.join([('· {channel.name}'.format(channel=channel)) for channel in channel_list[:show]])
    embed.add_field(
        name='Channels ({}/{} shown)'.format(show, len(server.channels)),
        value=channel_text or 'No channels.',
        inline=False
    )

    # number of roles to show, which to show
    role_list = [x for x in sorted(server.roles, key=lambda r: r.position, reverse=True) if not x.is_everyone]
    # role_list = [x for x in server.roles if not x.is_everyone][0:10]
    show = min(10, len(role_list))
    role_text = '\n'.join(['· {s}{name}'.format(s='@' if r.mentionable else '', name=r.name) for r in role_list[:show]])
    embed.add_field(
        name='Roles ({}/{} shown)'.format(show, len(server.roles) - 1),  # minus 1 to not include @everyone
        value=role_text or 'No roles.',
        inline=False
    )

    # list emojis; truncate if need be
    show = len(server.emojis)
    total = show
    char_count = sum([len(emoji.name) for emoji in server.emojis])
    if char_count > 500:
        while char_count > 500:
            server.emojis = server.emojis[:-1]
            show = len(server.emojis)
            char_count = sum([len(emoji.name) for emoji in server.emojis])
    emoji_text = ' '.join(['`:{e.name}:`'.format(e=emoji) for emoji in server.emojis[:show]])
    embed.add_field(
        name='Emojis ({}/{} shown)'.format(show, total),
        value=emoji_text or 'No custom emojis.',
        inline=False
    )

    # footer, thumbnail
    embed.set_footer(text='Server ID: #{server.id}'.format(server=server))
    embed.set_thumbnail(url=server.icon_url)

    return embed