__version__ = (2, 2, 0)


# ▄▀█ █▄ █ █▀█ █▄ █ █▀█ ▀▀█ █▀█ █ █ █▀
# █▀█ █ ▀█ █▄█ █ ▀█ ▀▀█   █ ▀▀█ ▀▀█ ▄█
#
#           © Copyright 2022
#
#        developed by @anon97945
#
#     https://t.me/apodiktum_modules
#      https://github.com/anon97945
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/gpl-3.0.html

# meta developer: @apodiktum_modules
# meta banner: https://t.me/file_dumbster/11
# meta pic: https://t.me/file_dumbster/13

# scope: hikka_min 1.3.3
# requires: emoji alphabet_detector

import ast
import asyncio
import collections
import contextlib
import copy
import hashlib
import html
import io
import logging
import math
import os
import re
from datetime import datetime, timedelta
from typing import IO, Any, Optional, Tuple, Union
from urllib.parse import urlparse

import aiohttp
import emoji
import grapheme
import requests
from aiogram.types import ChatPermissions
from aiogram.utils.exceptions import (
    BotKicked,
    ChatNotFound,
    MessageCantBeDeleted,
    MessageToDeleteNotFound,
)
from telethon.errors import UserNotParticipantError
from telethon.hints import EntityLike
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditAdminRequest,
    EditBannedRequest,
    GetFullChannelRequest,
    InviteToChannelRequest,
)
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.types import (
    Channel,
    Chat,
    ChatAdminRights,
    ChatBannedRights,
    Message,
    MessageEntityUrl,
    User,
)

from .. import loader, main, utils

logger = logging.getLogger(__name__)


class ApodiktumLib(loader.Library):
    """
    The Apodiktum Library is a collection of useful functions and classes for all Hikka developers.
    """

    developer = "@apodiktum_modules"
    version = __version__

    strings = {
        "_cfg_cst_auto_migrate": "Wheather to auto migrate defined changes on startup.",
        "_cfg_doc_log_channel": "Wheather to log debug as info in logger channel.",
        "_cfg_doc_log_debug": (
            "Wheather to log declared debug messages as info in logger channel."
        ),
    }

    strings_de = {
        "_cfg_cst_auto_migrate": (
            "Ob definierte Änderungen beim Start automatisch migriert werden sollen."
        ),
        "_cfg_doc_log_channel": (
            "Ob Debug als Info im Logger-Kanal protokolliert werden soll."
        ),
        "_cfg_doc_log_debug": (
            "Ob deklarierte Debug-Meldungen als Info im Logger-Kanal"
            " protokolliert werden sollen."
        ),
    }

    strings_ru = {}

    all_strings = {
        "strings": strings,
        "strings_en": strings,
        "strings_de": strings_de,
        "strings_ru": strings_ru,
    }

    def __init__(self):
        """
        Initializes the library config.
        """
        self.config = loader.LibraryConfig(
            loader.ConfigValue(
                "auto_migrate",
                True,
                doc=lambda: self.strings("_cfg_cst_auto_migrate"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "log_channel",
                True,
                doc=lambda: self.strings("_cfg_doc_log_channel"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "log_debug",
                False,
                doc=lambda: self.strings("_cfg_doc_log_debug"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def init(self):
        """
        Initializes the library.
        """
        if self.config["log_channel"]:
            logging.getLogger(self.__class__.__name__).info(
                "Apodiktum Library"
                f" v{__version__[0]}.{__version__[1]}.{__version__[2]} loading..."
            )
        else:
            logging.getLogger(self.__class__.__name__).debug(
                "Apodiktum Library"
                f" v{__version__[0]}.{__version__[1]}.{__version__[2]} loading..."
            )
        logging.getLogger(self.__class__.__name__).debug(
            "Apodiktum Library"
            f" v{__version__[0]}.{__version__[1]}.{__version__[2]} started for"
            f" {self.client} | {self.client.tg_id}"
        )
        self._lib_set("version", __version__)
        self.loaded_classes = {}
        if not hasattr(self, "_watcher_q_queue"):
            self._watcher_q_queue = {}
        if not hasattr(self, "_watcher_q_task"):
            self._watcher_q_task = {}
        await self.__init_classes()
        await self.__refresh_classes()
        self._ss_task = asyncio.ensure_future(self._internal._send_stats())
        self._acl_task = asyncio.ensure_future(
            self._controllerloader.ensure_controller()
        )
        self.utils.log(
            logging.DEBUG,
            self.__class__.__name__,
            "Apodiktum Library"
            f" v{__version__[0]}.{__version__[1]}.{__version__[2]} successfully"
            " loaded.",
        )

    async def __init_classes(self):
        """
        Initializes all classes in the library.
        """
        self.utils = ApodiktumUtils(self)
        self._controllerloader = ApodiktumControllerLoader(self)
        self._internal = ApodiktumInternal(self)
        self.migrator = ApodiktumMigrator(self)
        self.watcher_q = ApodiktumWatcherQueue(self)
        self.utils_beta = (
            ApodiktumUtilsBeta(self) if await self._internal._beta_access() else None
        )
        self.loaded_classes["utils"] = self.utils
        self.loaded_classes["_controllerloader"] = self._controllerloader
        self.loaded_classes["_internal"] = self._internal
        self.loaded_classes["migrator"] = self.migrator
        self.loaded_classes["watcher_q"] = self.watcher_q
        if self.utils_beta:
            self.loaded_classes["utils_beta"] = self.utils_beta

    async def __refresh_classes(self):
        """
        Refresh all classes.
        """
        self.utils.log(
            logging.DEBUG,
            self.__class__.__name__,
            "Refreshing all classes to the current library state.",
            debug_msg=True,
        )
        for cl in self.loaded_classes:
            self.utils.log(
                logging.DEBUG,
                self.__class__.__name__,
                f"Refreshing {cl} to the current library state.",
                debug_msg=True,
            )
            self.loaded_classes[cl] = await self.loaded_classes[cl]._refresh_lib(self)
            if getattr(self, cl):
                setattr(self, cl, self.loaded_classes[cl])
        self.utils.log(
            logging.DEBUG,
            self.__class__.__name__,
            "Refreshing of all classes done.",
            debug_msg=True,
        )

    def apodiktum_module(self):
        """
        Sets Apodiktum Library init module to Apodiktum Module
        """
        self._internal._is_apodiktum_module()

    async def on_lib_update(self, new_lib: loader.Library):
        """
        Called when the library is updated, to give old vars to the new library.
        :param new_lib: The new library
        """
        await self.__refresh_classes()
        with contextlib.suppress(Exception):
            self._acl_task.cancel()
        with contextlib.suppress(Exception):
            self._ss_task.cancel()
        (
            new_lib._watcher_q_queue,
            new_lib._watcher_q_task,
        ) = self._internal._lib_update_watcher_q_handler()
        self.utils.log(
            logging.DEBUG,
            self.__class__.__name__,
            "Apodiktum Library"
            f" v{__version__[0]}.{__version__[1]}.{__version__[2]} was"
            " updated.",
        )
        self.allmodules._apodiktum_controller_init = False
        return


class ApodiktumControllerLoader(loader.Module):
    """
    This class is used to load the Apo-LibController
    """

    def __init__(
        self,
        lib: loader.Library,
    ):
        self.utils = lib.utils
        self.utils.log(
            logging.DEBUG,
            lib.__class__.__name__,
            f"class {self.__class__.__name__} is being initiated!",
            debug_msg=True,
        )
        self.lib = lib
        self._db = lib.db
        self._client = lib.client
        self.inline = lib.inline
        self._libclassname = lib.__class__.__name__

    async def _refresh_lib(
        self,
        lib: loader.Library,
    ):
        """
        !do not use this method directly!
        Refreshes the class with the current state of the library
        :param lib: The library class
        :return: None
        """
        self.lib = lib
        self.utils = lib.utils
        return self

    async def ensure_controller(self, first_loop: bool = True):
        """
        Ensures that the Apo-LibController is loaded
        """
        if not getattr(self.lib.allmodules, "_apodiktum_controller_init", False):
            self.lib.allmodules._apodiktum_controller_init = True
            while True:
                if first_loop:
                    if (
                        not await self._wait_load(
                            delay=5, retries=5, first_loop=first_loop
                        )
                        and not self._controller_refresh()
                    ):
                        await self._init_controller()
                    first_loop = False
                elif not self._controller_refresh():
                    await self._init_controller()
                await asyncio.sleep(5)
        return

    async def _init_controller(self):
        """
        Initializes the Apo-LibController downnload and load
        """
        self.utils.log(
            logging.DEBUG,
            self._libclassname,
            "Attempting to load ApoLibController from GitHub.",
            debug_msg=True,
        )
        controller_loaded = await self._load_github()
        if controller_loaded:
            return controller_loaded
        self._controller_found = False
        return None

    def _controller_refresh(self):
        """
        Checks if the Apo-LibController is loaded
        """
        self._controller_found = bool(self.lib.lookup("Apo-LibController"))
        return self._controller_found

    async def _load_github(self):
        """
        Downloads the Apo-LibController from GitHub
        """
        link = "https://raw.githubusercontent.com/anon97945/hikka-mods/master/apolib_controller.py"
        async with aiohttp.ClientSession() as session, session.head(link) as response:
            if response.status >= 300:
                return None
        link_message = await self._client.send_message(
            "me", f"{self.lib.get_prefix()}dlmod {link}"
        )
        await self.lib.allmodules.commands["dlmod"](link_message)
        lib_controller = await self._wait_load(delay=5, retries=5)
        await link_message.delete()
        return lib_controller

    async def _wait_load(self, delay, retries, first_loop=False):
        """
        Waits for the Apo-LibController to load
        :param delay: The delay between retries
        :param retries: The number of retries
        :param first_loop: Whether this is the first loop
        :return: Whether the Apo-LibController was loaded
        """
        while retries:
            if lib_controller := self.lib.lookup("Apo-LibController"):
                self.utils.log(
                    logging.DEBUG,
                    self._libclassname,
                    "ApoLibController found!",
                    debug_msg=True,
                )
                return lib_controller
            if not getattr(self.lib.lookup("Loader"), "_fully_loaded", False):
                retries = 1
            elif (
                getattr(self.lib.lookup("Loader"), "_fully_loaded", False)
                and first_loop
            ):
                retries = 0
            else:
                retries -= 1
            if retries != 0:
                self.utils.log(
                    logging.DEBUG,
                    self._libclassname,
                    "ApoLibController not found, retrying in"
                    f" {delay} seconds...\nHikka"
                    " fully loaded:"
                    f" {getattr(self.lib.lookup('Loader'), '_fully_loaded', False)}",
                    debug_msg=True,
                )
            if retries == 0:
                return False
            await asyncio.sleep(delay)


class ApodiktumWatcherQueue(loader.Module):
    """
    Apodiktum Watcher Queue queues messages for the watcher
    """

    def __init__(
        self,
        lib: loader.Library,
    ):
        self.utils = lib.utils
        self.utils.log(
            logging.DEBUG,
            lib.__class__.__name__,
            f"class {self.__class__.__name__} is being initiated!",
            debug_msg=True,
        )
        self.lib = lib
        self._db = lib.db
        self._client = lib.client
        self.inline = lib.inline
        self._libclassname = self.lib.__class__.__name__
        self._lib_db = self._db.setdefault(self._libclassname, {})
        self._chats_db = self._lib_db.setdefault("chats", {})
        self._watcher_q_queue = lib._watcher_q_queue
        self._watcher_q_task = lib._watcher_q_task
        self.__init_old_watcher_handler()

    async def _refresh_lib(
        self,
        lib: loader.Library,
    ):
        """
        !do not use this method directly!
        Refreshes the class with the current state of the library
        :param lib: The library class
        :return: None
        """
        self.lib = lib
        self.utils = lib.utils
        return self

    def __init_old_watcher_handler(self):
        """
        Initializes the old watcher handler
        """
        if not getattr(self, "first_run", True):
            return
        self.first_run = False
        for name in list(self._watcher_q_task):
            for method in list(self._watcher_q_task[name]):
                self._watcher_q_task[name].pop(method)
                self.register(name, method)
            if not self._watcher_q_queue[name]:
                self._watcher_q_task.pop(name)

    async def msg_reciever(self, message: Message):
        """
        !do not use this method directly, it will be used by `apolib_controller.py`!
        Recieves messages and queues them for the handler.
        :param message: The message to queue
        :return: None
        """
        for sub_queue in self._watcher_q_queue:
            for queue in self._watcher_q_queue[sub_queue].values():
                await queue.put(message)

    def register(self, name: str, method: str = "q_watcher"):
        """
        Adds a new method to the queue
        :param name: The name of the module
        :param method: The method to use for the queue
        :return: None
        """
        if not hasattr(self.lib.lookup(name), method):
            self.utils.log(
                logging.ERROR,
                self.__class__.__name__,
                f"Module `{name}` has no method called `{method}`!",
            )
            return
        self._watcher_q_queue.setdefault(name, {}).setdefault(method, asyncio.Queue())
        self._watcher_q_task.setdefault(name, {}).setdefault(
            method, asyncio.create_task(self.__queue_method_handler(name, method))
        )
        self.utils.log(
            logging.DEBUG,
            self.__class__.__name__,
            f"Registered Method `{method}` for `{name}` to the queue!",
            debug_msg=True,
        )

    def unregister(self, name: str, method: str = "q_watcher"):
        """
        Removes a queue handler
        :param name: The name of the module
        :param method: The method to remove
        :return: None
        """
        self._watcher_q_task[name][method].cancel()
        self._watcher_q_task[name].pop(method)
        self._watcher_q_queue[name].pop(method)
        if not self._watcher_q_task[name]:
            self._watcher_q_task.pop(name)
        if not self._watcher_q_queue[name]:
            self._watcher_q_queue.pop(name)
        self.utils.log(
            logging.DEBUG,
            self.__class__.__name__,
            f"Unregistered method `{method}` for `{name}` from the queue!\nCurrent"
            f" watcher tasks: {self._watcher_q_task}",
            debug_msg=True,
        )

    async def __queue_method_handler(self, name: str, method: str):
        """
        Handles the queue for a module
        :param name: The name of the module
        :param method: The method to use for the queue
        :return: Message Object
        """
        try:
            while True:
                try:
                    msg = await self._watcher_q_queue[name][method].get()
                    await getattr(self.lib.lookup(name), method)(msg) if hasattr(
                        self.lib.lookup(name), method
                    ) else self.unregister(name, method)
                except KeyError:
                    self.utils.log(
                        logging.DEBUG,
                        self.__class__.__name__,
                        f"Task stopped! Method `{method}` of `{name}` is not"
                        " registered!",
                        debug_msg=True,
                    )
                    break
            return
        except asyncio.CancelledError:
            return


class ApodiktumUtils(loader.Module):
    """
    This class is used to handle all the utility functions of the library.
    """

    def __init__(
        self,
        lib: loader.Library,
    ):
        self.lib = lib
        self._db = lib.db
        self._client = lib.client
        self.inline = lib.inline
        self._libclassname = lib.__class__.__name__
        self._lib_db = self._db.setdefault(self._libclassname, {})
        self._chats_db = self._lib_db.setdefault("chats", {})
        self._perms_cache = {}
        self._get_fullchannelrequest_cache = {}
        self.log(
            logging.DEBUG,
            self._libclassname,
            f"class {self.__class__.__name__} is being initiated!",
            debug_msg=True,
        )

    async def _refresh_lib(
        self,
        lib: loader.Library,
    ):
        """
        !do not use this method directly!
        Refreshes the class with the current state of the library
        :param lib: The library class
        :return: None
        """
        self.lib = lib
        self.utils = lib.utils
        return self

    def get_str(
        self, string: str, all_strings: dict, message: Optional[Message] = None
    ) -> str:
        """
        Get a string from a dictionary
        :param string: The string to get
        :param all_strings: The dictionary to get the string from
        :param message: The message to check for forced chat strings
        :return: The translated string
        """
        base_strings = "strings"
        default_lang = None
        if (
            "hikka.translations" in self._db
            and "lang" in self._db["hikka.translations"]
        ):
            default_lang = self._db["hikka.translations"]["lang"]
        languages = {base_strings: all_strings[base_strings]}
        for lang, strings in all_strings.items():
            if len(lang.split("_", 1)) == 2:
                languages[lang.split("_", 1)[1]] = {
                    **all_strings[base_strings],
                    **all_strings[lang],
                }
        if message:
            if chat_id := utils.get_chat_id(message):
                chatid_db = self._chats_db.setdefault(str(chat_id), {})
                forced_lang = chatid_db.get("forced_lang")
                for lang, strings in languages.items():
                    if lang and forced_lang == lang:
                        if string in strings:
                            return strings[string].replace("<br>", "\n")
                        break
        if (
            default_lang
            and default_lang in list(languages)
            and string in languages[default_lang]
        ):
            return languages[default_lang][string].replace("<br>", "\n")
        return all_strings[base_strings][string].replace("<br>", "\n")

    def log(
        self,
        level: int,
        name: str,
        text: str,
        debug_msg: Optional[bool] = False,
        exc_info: Optional[Exception] = False,
    ):
        """
        Logs a message to the console
        :param level: The logging level
        :param name: The name of the module
        :param text: The text to log
        :param debug_msg: Whether to log the message as a defined debug message
        :return: None
        """
        apo_logger = logging.getLogger(name)
        if (
            not debug_msg and self.lib.config["log_channel"] and level == logging.DEBUG
        ) or (debug_msg and self.lib.config["log_debug"] and level == logging.DEBUG):
            return apo_logger.info(text, exc_info=exc_info)
        if level in [logging.CRITICAL, logging.FATAL]:
            return apo_logger.critical(text, exc_info=exc_info)
        if level == logging.ERROR:
            return apo_logger.error(text, exc_info=exc_info)
        if level == logging.WARNING:
            return apo_logger.warning(text, exc_info=exc_info)
        if level == logging.INFO:
            return apo_logger.info(text, exc_info=exc_info)

        return (
            apo_logger.debug(text, exc_info=exc_info)
            if level == logging.DEBUG
            else None
        )

    async def is_member(
        self,
        entity: EntityLike,
        user: Optional[EntityLike] = None,
        exp: Optional[int] = 5,
        force: Optional[bool] = False,
    ) -> bool:
        """
        Checks if a user is a member of a chat
        :param entity: Chat ID or Chat Entity
        :param user: User ID or User Entity
        :param exp: The max time of cached results in seconds
        :param force: Whether to force a refresh of the cache
        :return: perms if user is a member of the chat, None otherwise
        """
        try:
            perms = await self._client.get_perms_cached(
                entity,
                user,
                exp=exp,
                force=force,
            )
            return None if perms.is_banned else perms
        except UserNotParticipantError:
            return None

    async def is_linkedchannel(
        self,
        chat: EntityLike,
        user: EntityLike,
        exp: Optional[int] = 300,
        force: Optional[bool] = False,
    ) -> bool:
        """
        Checks if the message is from the linked channel
        :param chat: Chat ID or Chat Entity
        :param user: User ID or User Entity
        :param exp: The max time of cached results in seconds
        :param force: Whether to force refresh the cache
        :return: True if the message is from the linked channel, False otherwise
        """
        chat = await self._client.get_entity(chat) if isinstance(chat, int) else chat
        user = (
            await self._client.get_entity(user)
            if user and isinstance(user, int)
            else user
        )
        if not isinstance(user, Channel):
            return False
        full_channel = await self._client.get_fullchannel(
            user,
            exp=exp,
            force=force,
        )
        if (
            full_channel
            and full_channel.full_chat
            and full_channel.full_chat.linked_chat_id
        ):
            return chat.id == int(full_channel.full_chat.linked_chat_id)

    @staticmethod
    async def get_buttons(
        message: Message,
    ) -> dict:
        """
        Gets the buttons as a dict
        :param message: Message
        :return: Buttons as dict
        """
        chat_id = utils.get_chat_id(message)
        button_dict = {}
        bmsg = await message.client.get_messages(chat_id, ids=message.id)
        buttons = bmsg.buttons
        for row_count, row in enumerate(buttons):
            button_dict[row_count] = {}
            for button_count, button in enumerate(row):
                button_dict[row_count][button_count] = {"text": button.text}
                if button.data:
                    button_dict[row_count][button_count]["data"] = button.data
                if button.url:
                    button_dict[row_count][button_count]["url"] = button.url
        return button_dict

    async def get_tag(
        self,
        user: EntityLike,
        WithID: bool = False,
    ) -> str:
        """
        Get the tag of a user/channel
        :param user: User/Channel
        :param WithID: Return the tag with the ID
        :return: Tag message as string
        """
        user = await self._client.get_entity(user) if isinstance(user, int) else user
        if isinstance(user, Channel):
            if WithID:
                return (
                    f"<a href='tg://resolve?domain={user.username}'>{user.title}</a>"
                    f" (<code>{str(user.id)}</code>)"
                    if user.username
                    else f"{user.title}(<code>{str(user.id)}</code>)"
                )
            return (
                f"<a href='tg://resolve?domain={user.username}'>{user.title}</a>"
                if user.username
                else f"{user.title}"
            )
        if WithID:
            return (
                f"<a href='tg://resolve?domain={user.username}'>{user.first_name}</a>"
                f" (<code>{str(user.id)}</code>)"
                if user.username
                else (
                    f"<a href='tg://user?id={str(user.id)}'>{user.first_name}</a>"
                    f" (<code>{str(user.id)}</code>)"
                )
            )
        return (
            f"<a href='tg://resolve?domain={user.username}'>{user.first_name}</a>"
            if user.username
            else f"<a href='tg://user?id={str(user.id)}'>{user.first_name}</a>"
        )

    async def get_tag_link(self, user: EntityLike) -> str:
        """
        Returns a tag link to the user's profile
        :param user: User or user ID
        :return: Tag link as string
        """
        user = await self._client.get_entity(user) if isinstance(user, int) else user
        if isinstance(user, User):
            return f"tg://user?id={user.id}"
        if isinstance(user, Channel) and getattr(user, "username", None):
            return f"tg://resolve?domain={user.username}"
        return ""

    async def get_invite_link(
        self,
        chat: Union[Chat, int],
    ) -> str:
        """
        Gets the invite link for the chat (need to be admin and invite user perms)
        :param chat: Chat or chat ID
        :return: Invite link as string
        """
        if isinstance(chat, int):
            chat = await self._client.get_entity(chat)
        if chat.username:
            link = f"https://t.me/{chat.username}"
        elif chat.admin_rights and chat.admin_rights.invite_users:
            link = await self._client(GetFullChannelRequest(channel=chat.id))
            link = link.full_chat.exported_invite.link
        else:
            link = None
        return link

    async def get_user_id(self, message: Message, strip: bool = False) -> int:
        """
        Gets the user ID from a message
        :param message: Message
        :param strip: Remove -100 from the user_id
        :return: User ID
        """
        try:
            user_id = (
                getattr(message, "sender_id", False)
                or message.action_message.action.users[0]
            )
        except Exception:  # skipcq: PYL-W0703
            try:
                user_id = message.action_message.action.from_id.user_id
            except Exception:  # skipcq: PYL-W0703
                try:
                    user_id = message.from_id.user_id
                except Exception:  # skipcq: PYL-W0703
                    try:
                        user_id = message.action_message.from_id.user_id
                    except Exception:  # skipcq: PYL-W0703
                        try:
                            user_id = message.action.from_user.id
                        except Exception:  # skipcq: PYL-W0703
                            try:
                                user_id = (await message.get_user()).id
                            except Exception:  # skipcq: PYL-W0703
                                try:
                                    user_id = message.peer_id.channel_id
                                except Exception:  # skipcq: PYL-W0703
                                    try:
                                        user_id = message.from_id
                                    except Exception:  # skipcq: PYL-W0703
                                        self.log(
                                            logging.DEBUG,
                                            self._libclassname,
                                            "Can't extract entity from event"
                                            f" {type(message)}",
                                        )
                                        return
        if str(user_id).startswith("-100") and strip:
            user_id = int(str(user_id)[4:])
        else:
            user_id = int(user_id)
        return user_id

    @staticmethod
    def validate_boolean(s: Any) -> bool:
        """
        Validates a boolean value
        :param s: String
        :return: True if the string represents a boolean, False otherwise
        """
        try:
            return loader.validators.Boolean().validate(s)
        except loader.validators.ValidationError:
            return False

    @staticmethod
    def validate_integer(
        s: Any,
        digits: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
    ) -> bool:
        """
        Checks if the string represents an integer
        :param s: String to check
        :param digits: Number of digits
        :param minimum: Minimum value
        :param maximum: Maximum value
        :return: True if the string represents an integer, False otherwise
        """
        kwargs = {}
        if digits is not None:
            kwargs["digits"] = digits
        if minimum is not None:
            kwargs["minimum"] = minimum
        if maximum is not None:
            kwargs["maximum"] = maximum
        try:
            loader.validators.Integer().validate(s, **kwargs)
            return True
        except loader.validators.ValidationError:
            return False

    @staticmethod
    def validate_string(
        s: Any,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        length: Optional[int] = None,
    ) -> bool:
        """
        Checks if the string represents a string
        :param s: String to check
        :param minimum: Minimum length
        :param maximum: Maximum length
        :param length: Exact length
        :return: True if the string represents a string, False otherwise
        """
        try:
            if not isinstance(length, int):
                if (
                    isinstance(minimum, int)
                    and len(list(grapheme.graphemes(str(s)))) < minimum
                ):
                    return False
                if (
                    isinstance(maximum, int)
                    and len(list(grapheme.graphemes(str(s)))) > maximum
                ):
                    return False
            elif (
                isinstance(length, int)
                and len(list(grapheme.graphemes(str(s)))) != length
            ):
                return False
            return True
        except TypeError:
            return False

    @staticmethod
    def validate_float(
        s: Any,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
    ) -> bool:
        """
        Checks if the string represents a float
        :param s: String to check
        :param minimum: Minimum value
        :param maximum: Maximum value
        :return: True if the string represents a float, False otherwise
        """
        kwargs = {}
        if minimum is not None:
            kwargs["minimum"] = minimum
        if maximum is not None:
            kwargs["maximum"] = maximum
        try:
            loader.validators.Float().validate(s, **kwargs)
            return True
        except loader.validators.ValidationError:
            return False

    @staticmethod
    def validate_datetime(s: Any, dt_format: Optional[str] = "%Y-%m-%d") -> bool:
        """
        Checks if the string represents a date
        :param s: String to check
        :param dt_format: Date/Time/Datetime format -> https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior
        :return: True if the string represents a date, False otherwise
        """
        try:
            datetime.strptime(s, dt_format)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_tgid(s: Any) -> bool:
        """
        Checks if the string represents a Telegram ID
        :param s: String to check
        :return: True if the string represents a Telegram ID, False otherwise
        """
        try:
            loader.validators.TelegramID().validate(s)
            return True
        except loader.validators.ValidationError:
            return False

    @staticmethod
    def validate_none(s: Any) -> bool:
        """
        Checks if the string represents a None value
        :param s: String to check
        :return: True if the string represents a None value, False otherwise
        """
        try:
            return s in {None, False, ""}
        except TypeError:
            return False

    @staticmethod
    def validate_regex(
        s: Any,
        regex: str,
    ) -> bool:
        """
        Checks if the string matches the regex
        :param s: String to check
        :param regex: Regex to match
        :return: True if the string matches the regex, False otherwise
        """
        try:
            return re.match(regex, s) is not None
        except TypeError:
            return False

    @staticmethod
    def validate_dict(s: Any) -> bool:
        """
        Checks if the string represents a dict
        :param s: String to check
        :return: True if the string represents a dict, False otherwise
        """
        try:
            return isinstance(ast.literal_eval(s), dict)
        except SyntaxError:
            return False

    @staticmethod
    def validate_list(s: Any) -> bool:
        """
        Checks if the string represents a list
        :param s: String to check
        :return: True if the string represents a list, False otherwise
        """
        try:
            return isinstance(ast.literal_eval(s), list)
        except SyntaxError:
            return False

    @staticmethod
    def validate_tuple(s: Any) -> bool:
        """
        Checks if the string represents a list
        :param s: String to check
        :return: True if the string represents a list, False otherwise
        """
        try:
            return isinstance(ast.literal_eval(s), tuple)
        except SyntaxError:
            return False

    @staticmethod
    def validate_email(s: Any) -> bool:
        """
        Checks if the string represents an email
        :param s: String to check
        :return: True if the string represents an email, False otherwise
        """
        try:
            pat = r"^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
            return bool(re.match(pat, s))
        except TypeError:
            return False

    @staticmethod
    def get_entityurls(message: Message) -> list:
        """
        Returns a list of entityurls from the message
        :param message: Message
        :return: list of entityurls
        """
        return [
            url
            for ent, url in message.get_entities_text()
            if isinstance(ent, MessageEntityUrl)
        ]

    @staticmethod
    def get_href_urls(text: str) -> list:
        """
        Returns a list of href urls from the text
        :param text: str
        :return: list of href urls
        """
        return re.findall("href=[\"'](.*?)[\"']", text)

    @staticmethod
    def get_urls(text: str) -> list:
        """
        Returns a list of urls from the text
        :param text: str
        :return: list of urls
        """
        URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
        return re.findall(URL_REGEX, text)

    def get_all_urls(self, text: str, rem_duplicates: bool = False) -> str:
        """
        Get all urls from text, search regex link types and href. This might double urls.
        :param text: str
        :param rem_duplicates: True to remove duplicates from the list
        :return: list of urls
        """
        text = self.unescape_html(text)
        urls = []
        urls = self.get_urls(text) + self.get_href_urls(text)
        if rem_duplicates:
            urls = self.rem_duplicates_list(urls)
        return urls

    @staticmethod
    async def get_file_from_url(url: str) -> IO[bytes]:
        """
        Get file from url
        :param url: url
        :return: file
        """
        text = (await utils.run_sync(requests.get, url)).text
        file = io.BytesIO(bytes(text, "utf-8"))
        file.name = url.split("/")[-1]
        return file, file.name

    @staticmethod
    def rem_duplicates_list(s: list) -> list:
        """
        Remove duplicates from list
        :param s: list
        :return: list without duplicates
        """
        return list(dict.fromkeys(s))

    @staticmethod
    def convert_time(t: Union[str, int]) -> int:
        """
        Tries to export time from text
        :param t: Xs/Xm/Xh/Xd/Xw/Xy
        :return: converted time to seconds as integer
        """
        try:
            if not str(t)[:-1].isdigit():
                return 0
            if "y" in str(t):
                return int(str(t)[:-1]) * 60 * 60 * 24 * 365
            if "w" in str(t):
                t = int(t[:-1]) * 60 * 60 * 24 * 7

            if "d" in str(t):
                t = int(t[:-1]) * 60 * 60 * 24

            if "h" in str(t):
                t = int(t[:-1]) * 60 * 60

            if "m" in str(t):
                t = int(t[:-1]) * 60

            if "s" in str(t):
                t = int(t[:-1])

            t = int(re.sub(r"[^0-9]", "", str(t)))
        except ValueError:
            return 0
        return t

    @staticmethod
    def tdstring_to_seconds(
        tdstr: Any,
        rev_order: Optional[bool] = False,
    ) -> int:
        """
        Convert timedelta string to seconds
        :param tdstr: timedelta string
        :param reversed: if True s:m:h -> h:m:s
        :return: seconds as int or None if timedelta string is invalid
        """
        try:
            if not isinstance(tdstr, Any):
                tdstr = str(tdstr)
            if isinstance(tdstr, timedelta):
                return int(tdstr.total_seconds())
            if not isinstance(tdstr, str):
                tdstr = str(tdstr)
            parts = tdstr.strip(" ").split(" ")
            d = int(parts[0]) if len(parts) > 1 else 0
            if rev_order:
                s = sum(
                    x * y for x, y in zip(map(int, parts[-1].split(":")), (1, 60, 3600))
                )
            else:
                s = sum(
                    x * y for x, y in zip(map(int, parts[-1].split(":")), (3600, 60, 1))
                )
            return 86400 * d + s
        except TypeError:
            return None

    @staticmethod
    def time_formatter(seconds: int, short: Optional[bool] = False) -> str:
        """
        Inputs time in seconds, to get beautified time,
        as string
        :param seconds: time in seconds
        :param short: if True, will return short time format
        :return: beautified time
        """
        result = ""
        v_m = 0
        remainder = seconds
        if short:
            times = {
                "y": (60 * 60 * 24 * 365),
                "w": (60 * 60 * 24 * 7),
                "d": (60 * 60 * 24),
                "h": (60 * 60),
                "m": 60,
                "s": 1,
            }
        else:
            times = {
                "millenia": (60 * 60 * 24 * 365 * 1000),
                "centuries": (60 * 60 * 24 * 365 * 100),
                "decades": (60 * 60 * 24 * 365 * 10),
                "years": (60 * 60 * 24 * 365),
                "month": (60 * 60 * 24 * 30),
                "weeks": (60 * 60 * 24 * 7),
                "days": (60 * 60 * 24),
                "hours": (60 * 60),
                "minutes": 60,
                "seconds": 1,
            }
        for string, divisor in times.items():
            v_m, remainder = divmod(remainder, divisor)
            v_m = int(v_m)
            if v_m != 0:
                result += f"{v_m}{string}, " if short else f"{v_m} {string}, "
        return result[:-2]

    @staticmethod
    def get_ids_from_tglink(link: str) -> str:
        """
        Get chat ID and message ID from telegram link
        :param link: telegram link
        :return: chat ID and message ID as string
        """
        regex = re.compile(
            r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$"
        )
        match = regex.match(link)
        if not match:
            return False
        chat_id = match[4]
        msg_id = int(match[5])
        if chat_id.isnumeric():
            chat_id = int(chat_id)
        return chat_id, msg_id

    @staticmethod
    def is_emoji(text: str) -> str:
        """
        Check if text is only emoji
        :param text: text
        :return: True if text is only emoji, False otherwise
        """
        return not emoji.replace_emoji(text, replace="") if text else False

    @staticmethod
    def rem_emoji(text: str) -> str:
        """
        Remove emoji from text
        :param text: text
        :return: text
        """
        return emoji.replace_emoji(text, replace="")

    @staticmethod
    def distinct_emoji_list(text: str) -> list:
        """
        Get distinct list of emoji from text
        :param text: text
        :return: list of distinct emoji
        """
        return emoji.distinct_emoji_list(text)

    @staticmethod
    def emoji_list(text: str) -> dict:
        """
        Get dict of emoji from text with index positions
        :param text: text
        :return: dict of emoji with index positions
        """
        return emoji.emoji_list(text)

    @staticmethod
    def rem_customemoji_html(text: str) -> str:
        """
        Removes custom emoji HTML tags from text
        :param text: text
        :return: text
        """
        return re.sub(r'(<emoji document_id="\d+">|<\/emoji>)', "", text)

    @staticmethod
    def unescape_html(text: str) -> str:
        """
        Unescape HTML entities
        :param text: text
        :return: text with HTML entities unescaped
        """
        return html.unescape(text)

    @staticmethod
    def escape_html(text: str) -> str:
        """
        Escape HTML entities
        :param text: text
        :return: text with HTML entities escaped
        """
        return html.escape(text)

    @staticmethod
    def humanbytes(num: int, decimal: Optional[int] = 2) -> str:
        """
        Formats a number to a human readable string
        :param num: Bytes int to format
        :return: The formatted number
        """
        suffix = "B"
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return f"{num:3.{decimal}f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.{decimal}f} Yi{suffix}"

    def get_uptime(self, short: Optional[bool] = True) -> str:
        """
        Get uptime of bot
        :param short: if True, will return short time format
        :return: uptime
        """
        return self.time_formatter(utils.uptime(), short)

    async def get_first_msg(self, message: Message) -> Message:
        """
        Get the first message of the message thread
        :param message: message
        :return: message
        """
        reply = await self._client.get_messages(
            utils.get_chat_id(message),
            ids=getattr(getattr(message, "reply_to", None), "reply_to_top_id", None)
            or getattr(getattr(message, "reply_to", None), "reply_to_msg_id", None),
        )
        return reply

    async def check_inlinebot(
        self,
        chat_id: int,
        invite_bot: Optional[bool] = True,
        promote_bot: Optional[bool] = True,
    ) -> bool:
        """
        Check if the inline bot is in the chat and has the correct permissions
        :param chat_id: Chat ID
        :return: True if the inline bot is in the chat and has the correct permissions, False otherwise
        """
        if chat_id == self._client.tg_id:
            return
        try:
            perms = await self._client.get_permissions(chat_id, self.inline.bot_id)
            if perms.is_banned and not invite_bot and not promote_bot:
                return False
            if promote_bot:
                return bool(await self.promote_bot(chat_id)) if promote_bot else True
            if invite_bot:
                return bool(await self.invite_bot(chat_id))
        except UserNotParticipantError:
            if invite_bot:
                invited = bool(await self.invite_bot(chat_id))
            if promote_bot:
                promoted = bool(await self.promote_bot(chat_id))
            if invited and promoted:
                return True
            if promote_bot:
                return promoted
            return invited if invite_bot else False

    async def invite_bot(self, chat_id: int) -> bool:
        """
        Invite the bot to a chat
        :param chat_id: Chat ID
        :return: True if the bot was invited, False otherwise
        """
        try:
            return await self._client(
                InviteToChannelRequest(chat_id, [self.inline.bot_username])
            )
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Unable to invite inlinebot to {chat_id}. Maybe he's already"
                f" there?\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def promote_bot(
        self,
        chat_id: int,
    ) -> bool:
        """
        sets the permissions for the inline bot
        :param chat_id: The chat to promote the bot to admin in
        :return: True if the bot was promoted, False if not
        """
        try:
            bot_perms = await self._client.get_permissions(chat_id, self.inline.bot_id)
            return (
                True
                if (
                    bot_perms.is_admin
                    and bot_perms.ban_users
                    and bot_perms.delete_messages
                )
                else await self._client(
                    EditAdminRequest(
                        channel=chat_id,
                        user_id=self.inline.bot_username,
                        admin_rights=ChatAdminRights(
                            ban_users=True, delete_messages=True
                        ),
                        rank="Bot",
                    )
                )
            )

        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Inlinebot promotion in chat {chat_id} failed!\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def mute(
        self,
        chat_id: int,
        user_id: int,
        duration: Optional[int] = 0,
        use_bot: Optional[bool] = True,
    ) -> bool:
        """
        Mutes a user in a chat
        :param chat_id: The chat id to mute the user in
        :param user_id: The user to mute
        :param duration: The time in seconds for the duration
        :param use_bot: Whether to use the inline bot or not
        :return: True if the user was muted, False if not<
        """
        duration = int(math.ceil(duration))
        user = await self._client.get_entity(user_id)
        try:
            if use_bot and await self.check_inlinebot(chat_id):
                with contextlib.suppress(Exception):
                    if isinstance(user, Channel):
                        return await self.inline.bot.restrict_chat_member(
                            chat_id
                            if str(chat_id).startswith("-100")
                            else int(f"-100{chat_id}"),
                            user_id
                            if str(user_id).startswith("-100")
                            else int(f"-100{user_id}"),
                            permissions=ChatPermissions(can_send_messages=False),
                            until_date=timedelta(minutes=duration),
                        )
                    return await self.inline.bot.restrict_chat_member(
                        chat_id
                        if str(chat_id).startswith("-100")
                        else int(f"-100{chat_id}"),
                        user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=timedelta(minutes=duration),
                    )
            return await self._client.edit_permissions(
                chat_id,
                user_id,
                timedelta(minutes=duration),
                send_messages=False,
            )
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Unable to mute user {user_id} in chat {chat_id} for duration"
                f" {duration}min\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def unmute(
        self,
        chat_id: int,
        user_id: int,
        use_bot: Optional[bool] = True,
    ) -> bool:
        """
        Unmutes a user in a chat
        :param chat_id: The chat id to unmute the user in
        :param user_id: The user to unmute
        :param use_bot: Whether to use the inline bot or not
        :return: True if the user was muted, False if not<
        """
        user = await self._client.get_entity(user_id)
        try:
            if use_bot and await self.check_inlinebot(chat_id):
                with contextlib.suppress(Exception):
                    if isinstance(user, Channel):
                        return await self.inline.bot.restrict_chat_member(
                            chat_id
                            if str(chat_id).startswith("-100")
                            else int(f"-100{chat_id}"),
                            user_id
                            if str(user_id).startswith("-100")
                            else int(f"-100{user_id}"),
                            permissions=ChatPermissions(can_send_messages=True),
                        )
                    return await self.inline.bot.restrict_chat_member(
                        chat_id
                        if str(chat_id).startswith("-100")
                        else int(f"-100{chat_id}"),
                        user_id,
                        permissions=ChatPermissions(can_send_messages=True),
                    )
            return await self._client.edit_permissions(
                chat_id,
                user_id,
                send_messages=True,
            )
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Unable to unmute user {user_id} in chat {chat_id}.\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def kick(
        self,
        chat_id: int,
        user_id: int,
        use_bot: Optional[bool] = True,
    ) -> bool:
        """
        Kicks a user in a chat
        :param chat_id: The chat id to delete the message in
        :param user_id: The user to ban
        :param use_bot: Whether to use the inline bot or not
        :return: True if the user was banned, False if not
        """
        user = await self._client.get_entity(user_id)
        try:
            if use_bot and await self.check_inlinebot(chat_id):
                with contextlib.suppress(Exception):
                    if isinstance(user, Channel):
                        return await self.inline.bot.ban_chat_sender_chat(
                            chat_id
                            if str(chat_id).startswith("-100")
                            else int(f"-100{chat_id}"),
                            user_id
                            if str(user_id).startswith("-100")
                            else int(f"-100{user_id}"),
                        )
                    return await self.inline.bot.unban_chat_member(
                        chat_id
                        if str(chat_id).startswith("-100")
                        else int(f"-100{chat_id}"),
                        user_id,
                    )
            return await self._client.kick_participant(chat_id, user_id)
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Unable to kick user {user_id} in chat {chat_id}\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def ban(
        self,
        chat_id: int,
        user_id: int,
        duration: Optional[int] = 0,
        use_bot: Optional[bool] = True,
    ) -> bool:
        """
        Bans a user in a chat, optionally for a certain time
        :param chat_id: The chat id to delete the message in
        :param user_id: The user to ban
        :param duration: The time in minutes for the duration
        :param use_bot: Whether to use the inline bot or not
        :return: True if the user was banned, False if not
        """
        user = await self._client.get_entity(user_id)
        duration = int(math.ceil(duration))
        try:
            if use_bot and await self.check_inlinebot(chat_id):
                with contextlib.suppress(Exception):
                    if isinstance(user, Channel):
                        return await self.inline.bot.ban_chat_sender_chat(
                            chat_id
                            if str(chat_id).startswith("-100")
                            else int(f"-100{chat_id}"),
                            user_id
                            if str(user_id).startswith("-100")
                            else int(f"-100{user_id}"),
                        )
                    return await self.inline.bot.kick_chat_member(
                        chat_id
                        if str(chat_id).startswith("-100")
                        else int(f"-100{chat_id}"),
                        user_id,
                        until_date=timedelta(minutes=duration),
                    )
            return await self._client(
                EditBannedRequest(
                    chat_id,
                    user_id,
                    ChatBannedRights(timedelta(minutes=duration), view_messages=True),
                )
            )
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Unable to ban user {user_id} in chat {chat_id} for duration:"
                f" {duration}min.\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def unban(
        self,
        chat_id: int,
        user_id: int,
        use_bot: Optional[bool] = True,
    ) -> bool:
        """
        Unbans a user in a chat
        :param chat_id: The chat id to delete the message in
        :param user_id: The user to unban
        :param use_bot: Whether to use the inline bot or not
        :return: True if the user was unbanned, False if not
        """
        user = await self._client.get_entity(user_id)
        try:
            if use_bot and await self.check_inlinebot(chat_id):
                with contextlib.suppress(Exception):
                    if isinstance(user, Channel):
                        return await self.inline.bot.unban_chat_member(
                            chat_id
                            if str(chat_id).startswith("-100")
                            else int(f"-100{chat_id}"),
                            user_id
                            if str(user_id).startswith("-100")
                            else int(f"-100{user_id}"),
                        )
                    return await self.inline.bot.unban_chat_member(
                        chat_id
                        if str(chat_id).startswith("-100")
                        else int(f"-100{chat_id}"),
                        user_id,
                    )
            return await self._client(
                EditBannedRequest(
                    chat_id,
                    user_id,
                    ChatBannedRights(view_messages=False),
                )
            )
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Unable to unban user {user_id} in chat {chat_id}.\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def delete_message(
        self,
        message: Message,
        deltimer: Optional[int] = 0,
        use_bot: Optional[bool] = True,
    ) -> bool:
        """
        Deletes a message in a chat
        :param message: The message to delete
        :param use_bot: Whether to use the inline bot or not
        :return: True if the message was deleted, False if not
        """
        chat_id = utils.get_chat_id(message)
        chat = await self._client.get_entity(chat_id)
        try:
            message_id = getattr(message, "id", None) or getattr(
                message, "message_id", None
            )
            if deltimer:
                await asyncio.sleep(deltimer)
            if (
                use_bot
                and await self.check_inlinebot(chat_id)
                and isinstance(chat, (Channel, Chat))
            ):
                with contextlib.suppress(
                    MessageCantBeDeleted,
                    BotKicked,
                    ChatNotFound,
                    MessageToDeleteNotFound,
                ):
                    return await self.inline.bot.delete_message(
                        chat_id
                        if str(chat_id).startswith("-100")
                        else int(f"-100{chat_id}"),
                        message_id,
                    )
            return await self._client.delete_messages(
                chat_id,
                message_id,
            )
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Unable to delete {message_id} in {chat_id}!\nError: {exc}",
                debug_msg=True,
            )
            return False

    async def asset_channel(
        self,
        title: str,
        description: str,
        *,
        channel: Optional[bool] = False,
        silent: Optional[bool] = False,
        archive: Optional[bool] = False,
        avatar: Optional[str] = "",
        _folder: Optional[str] = "",
    ) -> Tuple[Channel, bool]:
        """
        Create new channel (if needed) and return its entity
        :param client: Telegram client to create channel by
        :param title: Channel title
        :param description: Description
        :param channel: Whether to create a channel or not
        :param silent: Automatically mute channel
        :param archive: Automatically archive channel
        :param avatar: Url to an avatar to set as pfp of created peer
        :param _folder: Do not use it, or things will go wrong
        :returns: Peer and bool: is channel new or pre-existent
        """
        megagroup = not channel
        async for d in self._client.iter_dialogs():
            if d.title == title:
                return d.entity, False

        peer = (
            await self._client(
                CreateChannelRequest(
                    title,
                    description,
                    megagroup=megagroup,
                )
            )
        ).chats[0]

        if silent:
            await utils.dnd(self._client, peer, archive)
        elif archive:
            await self._client.edit_folder(peer, 1)

        if avatar:
            await utils.set_avatar(self._client, peer, avatar)

        if _folder:
            if _folder != "hikka":
                raise NotImplementedError

            folders = await self._client(GetDialogFiltersRequest())

            try:
                folder = next(folder for folder in folders if folder.title == "hikka")
            except Exception:  # skipcq: PYL-W0703
                return

            if any(
                peer.id == getattr(folder_peer, "channel_id", None)
                for folder_peer in folder.include_peers
            ):
                return

            folder.include_peers += [await self._client.get_input_entity(peer)]

            await self._client(
                UpdateDialogFilterRequest(
                    folder.id,
                    folder,
                )
            )

        return peer, True


class ApodiktumUtilsBeta(loader.Module):
    """
    Apodiktum Utils Beta, just for testing purposes
    """

    def __init__(
        self,
        lib: loader.Library,
    ):
        self.utils = lib.utils
        self.utils.log(
            logging.DEBUG,
            lib.__class__.__name__,
            f"class {self.__class__.__name__} is being initiated!",
            debug_msg=True,
        )
        self.lib = lib
        self._db = lib.db
        self._client = lib.client
        self.inline = lib.inline
        self._libclassname = self.lib.__class__.__name__
        self._lib_db = self._db.setdefault(self._libclassname, {})
        self._chats_db = self._lib_db.setdefault("chats", {})
        self.utils.log(
            logging.DEBUG,
            self._libclassname,
            "Congratulations! You have access to the ApodiktumUtilsBeta!",
        )

    async def _refresh_lib(
        self,
        lib: loader.Library,
    ):
        """
        !do not use this method directly!
        Refreshes the class with the current state of the library
        :param lib: The library class
        :return: None
        """
        self.lib = lib
        self.utils = lib.utils
        return self


class ApodiktumInternal(loader.Module):
    """
    Apodiktum Internal, just for internal purposes
    """

    def __init__(
        self,
        lib: loader.Library,
    ):
        self.utils = getattr(lib, "utils", None)
        self.utils.log(
            logging.DEBUG,
            lib.__class__.__name__,
            f"class {self.__class__.__name__} is being initiated!",
            debug_msg=True,
        )
        self.lib = lib
        self._db = lib.db or lib._db
        self._client = lib.client or lib._client
        self._libclassname = lib.__class__.__name__
        self._lib_db = self._db.setdefault(self._libclassname, {})
        self._chats_db = self._lib_db.setdefault("chats", {})

    async def _refresh_lib(
        self,
        lib: loader.Library,
    ):
        """
        !do not use this method directly!
        Refreshes the class with the current state of the library
        :param lib: The library class
        :return: None
        """
        self.lib = lib
        self.utils = lib.utils
        self.watcher_q = lib.watcher_q
        return self

    async def _beta_access(self):
        """
        !do not use this method directly!
        Checks if the user has beta access
        :return: True if the user has beta access, False otherwise
        """
        beta_ids = None
        beta_access = False
        try:
            async for messages in self._client.iter_messages("@apodiktum_modules_news"):
                if (
                    messages
                    and isinstance(messages, Message)
                    and "#UtilsBetaAccess" in messages.raw_text
                ):
                    string = messages.raw_text
                    beta_ids = list(
                        map(
                            int,
                            string[string.find("[") + 1 : string.find("]")].split(","),
                        )
                    )
                    if self._client.tg_id in beta_ids:
                        beta_access = True
                    break
            return beta_access
        except Exception as exc:  # skipcq: PYL-W0703
            self.utils.log(
                logging.DEBUG,
                self._libclassname,
                f"Error while checking beta access: {exc}",
            )
            return beta_access

    async def _send_stats(self):
        """
        !do not use this method directly!
        Send anonymous stats to Hikka
        :return: None
        """
        if self._db.get(main.__name__, "stats", True):
            await asyncio.sleep(8)
            urls = [
                "https://raw.githubusercontent.com/anon97945/hikka-mods/master/apodiktum_library.py",
                "https://raw.githubusercontent.com/anon97945/hikka-mods/master/total_users.py",
            ]
            if not getattr(self, "apodiktum_module", False):
                urls.append(
                    "https://raw.githubusercontent.com/anon97945/hikka-mods/master/ApoLib_others.py"
                )
            while True:
                for url in urls:
                    asyncio.ensure_future(self.__send_stats_handler(url))
                await asyncio.sleep(6 * 60 * 60)  # 6 hours

    def _is_apodiktum_module(self):
        """
        !do not use this method directly!
        Sets the stats to apodiktum
        :return: None
        """
        self.apodiktum_module = True

    async def __send_stats_handler(self, url: str, retry: bool = False):
        """
        !do not use this method directly!
        Send anonymous stats to Hikka
        :param url: The url to send to the stats server
        :return: None
        """
        with contextlib.suppress(Exception):
            if url is not None and utils.check_url(url):
                try:
                    if not self._db.get("LoaderMod", "token"):
                        self._db.set(
                            "LoaderMod",
                            "token",
                            (
                                await (
                                    await self._client.get_messages(
                                        "@hikka_ub", ids=[10]
                                    )
                                )[0].click(0)
                            ).message,
                        )

                    res = await utils.run_sync(
                        requests.post,
                        "https://heta.hikariatama.ru/stats",
                        data={"url": url},
                        headers={"X-Hikka-Token": self._db.get("LoaderMod", "token")},
                    )
                    if res.status_code == 403:
                        if retry:
                            return
                        self._db.set("LoaderMod", "token", None)
                        return await self.__send_stats_handler(url, retry=True)
                    if filename := (os.path.basename(urlparse(url).path)).split(".")[0]:
                        self.utils.log(
                            logging.DEBUG,
                            self._libclassname,
                            f"Succesfully sent stats for {filename}",
                            debug_msg=True,
                        )
                except Exception as exc:  # skipcq: PYL-W0703
                    self.utils.log(
                        logging.DEBUG,
                        self._libclassname,
                        f"Failed to send stats: {exc}",
                    )

    def _lib_update_watcher_q_handler(self):
        self._watcher_q_queue = getattr(
            self.watcher_q if hasattr(self, "watcher_q") else None,
            "_watcher_q_queue",
            {},
        ) or getattr(self.lib if hasattr(self, "lib") else None, "_watcher_q_queue", {})
        self._watcher_q_task = getattr(
            self.watcher_q if hasattr(self, "watcher_q") else None,
            "_watcher_q_task",
            {},
        ) or getattr(self.lib if hasattr(self, "lib") else None, "_watcher_q_task", {})
        for name in list(self._watcher_q_task):
            for method in list(self._watcher_q_task[name].values()):
                method.cancel()
        if self._watcher_q_queue:
            self._watcher_q_queue.clear()
        return self._watcher_q_queue, self._watcher_q_task


class ApodiktumMigrator(loader.Module):
    """
    Apodiktum Migrator, just for migrating purposes
    It is used by the ApodiktumLibrary to migrate settings of modules to the db.
    """

    strings = {
        "_log_doc_migrated_db": "Migrated `{}` database of `{}` -> `{}`:\n{}",
        "_log_doc_migrated_cfgv_val": (
            "[Dynamic={}] Migrated default config value:\n`{}` -> `{}`"
        ),
        "_log_doc_no_dynamic_migration": (
            "No module config found. Did not dynamic migrate:\n{{{}: {}}}"
        ),
        "_log_doc_migrated_db_not_found": (
            "`{}` database not found. Did not migrate `{}` -> `{}`"
        ),
    }

    def __init__(
        self,
        lib: loader.Library,
    ):
        self.utils = lib.utils
        self.utils.log(
            logging.DEBUG,
            lib.__class__.__name__,
            f"class {self.__class__.__name__} is being initiated!",
            debug_msg=True,
        )
        self.lib = lib
        self._db = lib.db
        self._client = lib.client
        self._libclassname = lib.__class__.__name__
        self.hashs = []

    async def _refresh_lib(
        self,
        lib: loader.Library,
    ):
        """
        !do not use this method directly!
        Refreshes the class with the current state of the library
        :param lib: The library class
        :return: None
        """
        self.lib = lib
        self.utils = lib.utils
        return self

    async def migrate(
        self,
        classname: str,  # type: ignore
        name: str,  # type: ignore
        changes: dict,  # type: ignore
    ):
        """
        Migrates a module
        :param classname: The classname of the module
        :param name: The name of the module
        :param changes: The changes to migrate
        :return: True if the migration was successful, False otherwise
        """
        self._classname = classname
        self._name = name
        self._changes = changes
        self._migrate_to = list(self._changes)[-1] if self._changes else None

        if self._migrate_to is not None:
            self.hashs = self._db.get(self._classname, "hashs", [])
            migrate = await self._check_new_migration()
            full_migrated = await self._full_migrated()
            if migrate:
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    f"Open migrations: {migrate}",
                    debug_msg=True,
                )
                if await self._migrator_func():
                    self.utils.log(
                        logging.DEBUG,
                        self._name,
                        "Migration done.",
                        debug_msg=True,
                    )
                    return True
            elif not full_migrated:
                await self._force_set_hashs()
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    f"Open migrations: {migrate} | Forcehash done: {self.hashs}",
                    debug_msg=True,
                )
                return False
            else:
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    f"Open migrations: {migrate} | Skip migration.",
                    debug_msg=True,
                )
                return False
            return False
        self.utils.log(
            logging.DEBUG,
            self._name,
            "No changes in `changes` dictionary found.",
            debug_msg=True,
        )
        return False

    async def auto_migrate_handler(
        self,
        classname: str,  # type: ignore
        name: str,  # type: ignore
        changes: dict,  # type: ignore
        auto_migrate: bool = False,
    ):
        """
        Handles the auto migration of a module
        :param classname: The classname of the module
        :param name: The name of the module
        :param changes: The changes to migrate
        :param auto_migrate: True if the migration should be auto, False otherwise
        :return: True if the migration was successful, False otherwise
        """
        self._classname = classname
        self._name = name
        self._changes = changes
        self._migrate_to = list(self._changes)[-1] if self._changes else None

        if self._migrate_to is not None:
            self.hashs = self._db.get(self._classname, "hashs", [])
            migrate = await self._check_new_migration()
            full_migrated = await self._full_migrated()
            if auto_migrate and migrate:
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    f"Open migrations: {migrate} | auto_migrate: {auto_migrate}",
                    debug_msg=True,
                )
                if await self._migrator_func():
                    self.utils.log(
                        logging.DEBUG,
                        self._name,
                        "Migration done.",
                        debug_msg=True,
                    )
                    return
            elif not auto_migrate and not full_migrated:
                await self._force_set_hashs()
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    f"Open migrations: {migrate} | auto_migrate:"
                    f" {auto_migrate} | Forcehash done: {self.hashs}",
                    debug_msg=True,
                )
                return
            else:
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    f"Open migrations: {migrate} | auto_migrate:"
                    f" {auto_migrate} | Skip migrate_handler.",
                    debug_msg=True,
                )
                return
        self.utils.log(
            logging.DEBUG,
            self._name,
            "No changes in `changes` dictionary found.",
            debug_msg=True,
        )
        return

    async def _force_set_hashs(self):
        """
        !do not use this method directly!
        Forces the set of the hashs
        """
        await self._set_missing_hashs()

    async def _check_new_migration(self):
        """
        !do not use this method directly!
        Checks if a new migration is available
        :return: True if a new migration is available, False otherwise
        """
        chash = hashlib.sha256(self._migrate_to.encode("utf-8")).hexdigest()
        return chash not in self.hashs

    async def _full_migrated(self):
        """
        !do not use this method directly!
        Checks if the module is fully migrated
        :return: True if the module is fully migrated, False otherwise
        """
        full_migrated = True
        for migration in self._changes:
            chash = hashlib.sha256(migration.encode("utf-8")).hexdigest()
            if chash not in self.hashs:
                full_migrated = False
        return full_migrated

    async def _migrator_func(self):
        """
        !do not use this method directly!
        The migrator function
        :return: True if the migration was successful
        """
        for migration in self._changes:
            chash = hashlib.sha256(migration.encode("utf-8")).hexdigest()
            if chash not in self.hashs:
                (
                    old_classname,
                    new_classname,
                    old_name,
                    new_name,
                ) = await self._get_names(migration)
                for category in self._changes[migration]:
                    await self._copy_config_init(
                        migration,
                        old_classname,
                        new_classname,
                        old_name,
                        new_name,
                        category,
                    )
                await self._set_hash(chash)
        return True

    async def _copy_config_init(
        self,
        migration,
        old_classname,
        new_classname,
        old_name,
        new_name,
        category,
    ):
        """
        !do not use this method directly!
        Initializes the copy of the config
        :param migration: The migration
        :param old_classname: The old classname
        :param new_classname: The new classname
        :param old_name: The old name
        :param new_name: The new name
        :param category: The category
        :return: None
        """
        if category == "classname":
            if self._classname != old_classname and (
                old_classname in self._db.keys()
                and self._db[old_classname]
                and old_classname is not None
            ):
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    f"{migration} | {category} | old_value: {old_classname} |"
                    f" new_value: {new_classname}",
                    debug_msg=True,
                )
                await self._copy_config(
                    category, old_classname, new_classname, new_name
                )
            else:
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    self.strings["_log_doc_migrated_db_not_found"].format(
                        category, old_classname, new_classname
                    ),
                )
        elif category == "name":
            self.utils.log(
                logging.DEBUG,
                self._name,
                f"{migration} | {category} | old_value: {old_name} | new_value:"
                f" {new_name}",
                debug_msg=True,
            )
            if self._name != old_name and (
                old_name in self._db.keys()
                and self._db[old_name]
                and old_name is not None
            ):
                await self._copy_config(category, old_name, new_name, new_classname)
            else:
                self.utils.log(
                    logging.DEBUG,
                    self._name,
                    self.strings["_log_doc_migrated_db_not_found"].format(
                        category, old_name, new_name
                    ),
                )
        elif category == "config":
            await self._migrate_cfg_values(migration, category, new_name, new_classname)
        return

    async def _get_names(self, migration):
        """
        !do not use this method directly!
        Gets the names of the module
        :param migration: The migration
        :return: The old classname, the new classname, the old name, the new name
        """
        old_name = None
        old_classname = None
        new_name = None
        new_classname = None
        for category in self._changes[migration]:
            if category == "classname":
                old_classname, new_classname = await self._get_changes(
                    self._changes[migration][category].items()
                )
            elif category == "name":
                old_name, new_name = await self._get_changes(
                    self._changes[migration][category].items()
                )
        if not new_name:
            new_name = self._name
        if not new_classname:
            new_classname = self._classname
        return old_classname, new_classname, old_name, new_name

    @staticmethod
    async def _get_changes(changes):
        """
        !do not use this method directly!
        Gets the changes of the module
        :param changes: The changes
        :return: The old value, the new value"""
        old_value = None
        new_value = None
        for state, value in changes:
            if state == "old":
                old_value = value
            elif state == "new":
                new_value = value
        return old_value, new_value

    async def _migrate_cfg_values(self, migration, category, new_name, new_classname):
        """
        !do not use this method directly!
        Migrates the config values
        :param migration: The migration
        :param category: The category
        :param new_name: The new name
        :param new_classname: The new classname
        :return: None
        """
        if new_classname in self._db.keys() and "__config__" in self._db[new_classname]:
            if configdb := self._db[new_classname]["__config__"]:
                for cnfg_key in self._changes[migration][category]:
                    old_value, new_value = await self._get_changes(
                        self._changes[migration][category][cnfg_key].items()
                    )
                    for key, value in configdb.items():
                        self.utils.log(
                            logging.DEBUG,
                            self._name,
                            f"{migration} | {category} | ({{old_value:"
                            f" {str(old_value)}}} `==` {{new_value:"
                            f" {str(value)}}}) `and` {{key: {key}}} `==`"
                            f" {{cnfg_key: {cnfg_key}}}",
                            debug_msg=True,
                        )
                        if value == old_value and key == cnfg_key:
                            dynamic = False
                            self._db[new_classname]["__config__"][cnfg_key] = new_value
                            if (
                                self.lib.lookup(new_name)
                                and self.lib.lookup(new_name).config
                                and key in self.lib.lookup(new_name).config
                            ):
                                self.lib.lookup(new_name).config[cnfg_key] = new_value
                                dynamic = True
                            self.utils.log(
                                logging.DEBUG,
                                self._name,
                                self.strings["_log_doc_migrated_cfgv_val"].format(
                                    dynamic, value, new_value
                                ),
                            )
        return

    async def _copy_config(self, category, old_name, new_name, name):
        """
        !do not use this method directly!
        Copies the config
        :param category: The category
        :param old_name: The old name
        :param new_name: The new name
        :param name: The name
        :return: None
        """
        if self._db[new_name]:
            temp_db = {new_name: copy.deepcopy(self._db[new_name])}
            self._db[new_name].clear()
            self._db[new_name] = await self._deep_dict_merge(
                temp_db[new_name], self._db[old_name]
            )
            temp_db.pop(new_name)
        else:
            self._db[new_name] = copy.deepcopy(self._db[old_name])
        self._db.pop(old_name)
        self.utils.log(
            logging.DEBUG,
            self._name,
            self.strings["_log_doc_migrated_db"].format(
                category, old_name, new_name, self._db[new_name]
            ),
        )
        if category == "classname":
            await self._make_dynamic_config(name, new_name)
        if category == "name":
            await self._make_dynamic_config(new_name, name)
        return

    async def _deep_dict_merge(self, dct1, dct2, override=True) -> dict:
        """
        !do not use this method directly!
        Deep merges two dictionaries
        :param dct1: The first dictionary
        :param dct2: The second dictionary
        :param override: Whether to override the values
        :return: The merged dictionary
        """
        merged = copy.deepcopy(dct1)
        for k, v2 in dct2.items():
            if k in merged:
                v1 = merged[k]
                if isinstance(v1, dict) and isinstance(v2, collections.abc.Mapping):
                    merged[k] = await self._deep_dict_merge(v1, v2, override)
                elif isinstance(v1, list) and isinstance(v2, list):
                    merged[k] = v1 + v2
                elif override:
                    merged[k] = copy.deepcopy(v2)
            else:
                merged[k] = copy.deepcopy(v2)
        return merged

    async def _make_dynamic_config(self, new_name, new_classname=None):
        """
        !do not use this method directly!
        Makes the config dynamic
        :param new_name: The new name
        :param new_classname: The new classname
        :return: None
        """
        if new_classname is None:
            return
        if "__config__" in self._db[new_classname].keys():
            for key, value in self._db[new_classname]["__config__"].items():
                if (
                    self.lib.lookup(new_name)
                    and self.lib.lookup(new_name).config
                    and key in self.lib.lookup(new_name).config
                ):
                    self.lib.lookup(new_name).config[key] = value
                else:
                    self.utils.log(
                        logging.DEBUG,
                        self._name,
                        self.strings["_log_doc_no_dynamic_migration"].format(
                            key, value
                        ),
                    )
        return

    async def _set_hash(self, chash):
        """
        !do not use this method directly!
        Sets the hash
        :param chash: The hash
        :return: None
        """
        self.hashs.append(chash)
        self._db.set(self._classname, "hashs", self.hashs)
        return

    async def _set_missing_hashs(self):
        """
        !do not use this method directly!
        Sets the missing hashes
        :return: None
        """
        for migration in self._changes:
            chash = hashlib.sha256(migration.encode("utf-8")).hexdigest()
            if chash not in self.hashs:
                await self._set_hash(chash)
