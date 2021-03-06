import logging
import re

# noinspection PyPackageRequirements
from telegram.ext import RegexHandler, CallbackQueryHandler
# noinspection PyPackageRequirements
from telegram import ParseMode

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


TORRENT_STRING_COMPACT = """• <code>{short_name}</code> ({progress_pretty}% of {size_pretty}, {state_pretty}, <b>{dl_speed_pretty}/s</b>) \
[<a href="{info_deeplink}">info</a>]"""

TORRENT_STRING_COMPLETED = '• <code>{name}</code> ({size_pretty})'

TORRENTS_CATEGORIES = [r'\/?all', r'\/?completed', r'\/?downloading', r'\/?paused', r'\/?inactive', r'\/?active', r'\/?tostart']

TORRENT_CATEG_REGEX_PATTERN = r'^({})'.format('|'.join(TORRENTS_CATEGORIES))
TORRENT_CATEG_REGEX = re.compile(TORRENT_CATEG_REGEX_PATTERN, re.I)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_torrents_list_selection(_, update, groups):
    logger.info('torrents list menu button from %s: %s', update.message.from_user.first_name, groups[0])

    qbfilter = groups[0]
    if qbfilter.startswith('/'):
        # remove the "/" if the category has been used as command
        qbfilter = qbfilter.replace('/', '')

    logger.info('torrents status: %s', qbfilter)

    torrents = qb.torrents(filter=qbfilter, sort='dlspeed', reverse=False) or []
    if qbfilter == 'tostart':
        all_torrents = qb.torrents(filter='all')
        completed_torrents = [t.hash for t in qb.torrents(filter='completed')]
        active_torrents = [t.hash for t in qb.torrents(filter='active')]

        torrents = [t for t in all_torrents if t.hash not in completed_torrents and t.hash not in active_torrents]

    logger.info('qbittirrent request returned %d torrents', len(torrents))

    if not torrents:
        update.message.reply_html('There is no torrent to be listed for <i>{}</i>'.format(qbfilter))
        return

    if qbfilter == 'completed':
        base_string = TORRENT_STRING_COMPLETED  # use a shorter string with less info for completed torrents
    else:
        base_string = TORRENT_STRING_COMPACT

    strings_list = [base_string.format(**torrent.dict()) for torrent in torrents]

    for strings_chunk in u.split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk), disable_web_page_preview=True)


updater.add_handler(RegexHandler(TORRENT_CATEG_REGEX, on_torrents_list_selection, pass_groups=True))
