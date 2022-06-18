# ▀█▀ █▀▀ █▀▄▀█ █░█ █▀█
# ░█░ ██▄ █░▀░█ █▄█ █▀▄
# ═══════════════════════
# █▀▀ █▀█ █▄▀ █ █▄░█ █▀█ █░█
# ██▄ █▀▄ █░█ █ █░▀█ █▄█ ▀▄▀
# ═════════════════════════════
# meta developer: @netuzb
# meta channel: @umodules

import logging

import git
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, main, utils
from ..inline.types import InlineQuery

logger = logging.getLogger(__name__)


@loader.tds
class InfomodMod(loader.Module):
    """Userbot ma'lumotlarini ko'rsatish"""

    strings = {
        "name": "Info",
        "owner": "Boshqaruvchi",
        "version": "Soso-versiyasi",
        "soso_update": "◍ soso-yangilash",
        "soso_chat": "◍ soso-guruh",
        "soso_platforma": "Soso-platforma",
        "soso_userbot": "<b>◍ Soso-Userbot (◕ᴗ◕✿) soso</b>",
        "soso_einstein": "<b>◍ <u>Eynshteyn</u> teoriyasi (ʘᴗʘ✿):</b> temurni soso'si top",
        "_cfg_cst_msg": "Ma'lumot uchun maxsus xabar. O'z ichiga olishi mumkin {me}, {version}, {build}, {prefix}, {platform}",
        "_cfg_cst_btn": "Ma'lumot uchun maxsus tugma. O'chirish uchun tugmani bo'sh qoldiring",
        "_cfg_banner": "Rasm bannerini oʻchirish uchun “True” ni oʻrnating",
    }
    
    strings_ru = {
        "owner": "Управляющий",
        "version": "Soso-версия",
        "soso_update": "◍ soso-обновить",
        "soso_chat": "◍ soso-группа",
        "soso_platforma": "Soso-платформа",
        "soso_userbot": "<b>◍ Soso-Юзербот (◕ᴗ◕✿) soso</b>",
        "soso_einstein": "<b>◍ Теория <u>Эйнштейна</u> (ʘᴗʘ✿):</b> soso темура топ из топов",
        "_cfg_cst_msg": "Специальное информационное сообщение. Может включать {me}, {version}, {build}, {prefix}, {platform}",
        "_cfg_cst_btn": "Специальная кнопка для информации. Оставьте кнопку пустой, чтобы отключить ее.",
        "_cfg_banner": "Установите True, чтобы удалить баннер с изображением",
    }


    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_button12",
                ["soso", "https://t.me/+5o1a-UjPfCZhNmE5"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(fixed_len=2),
            ),         
            loader.ConfigValue(
                "custom_button13",
                ["soso", "http://t.me/share/url?url=.update --force"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(fixed_len=2),
            ),         
            loader.ConfigValue(
                "disable_banner",
                False,
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()

    def _render_info(self) -> str:
        ver = utils.get_git_hash() or "Unknown"

        try:
            repo = git.Repo()
            diff = repo.git.log(["HEAD..origin/master", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = f'<code><a href="tg://user?id={self._me.id}">{utils.escape_html(get_display_name(self._me))}</a></code>'
        version = f'<i>{".".join(list(map(str, list(main.__version__))))}</i>'
        build = f'<a href="https://github.com/Netuzb/sosi/commit/{ver}">#{ver[:8]}</a>'  # fmt: skip
        prefix = f"•<code>{utils.escape_html(self.get_prefix())}</code>•"
        platform = utils.get_named_platform()

        return (
            ""
            + self.config["custom_message"].format(
                me=me,
                version=version,
                build=build,
                prefix=prefix,
                platform=platform,
            )
            if self.config["custom_message"] and self.config["custom_message"] != "no"
            else (
                f"{self.strings('soso_userbot')}\n"
                f'<b>◍ {self.strings("owner")}</b> ◍ <a href="tg://user?id={self._me.id}">{me}</a>\n'
                f"<b>◍ {self.strings('version')}</b> ◍ <code>{version}</code> <a href='{build}'></a>\n"
                f"<b>◍ {self.strings('soso_platforma')}</b> <code>{platform}</code>"
                f"\n\n{self.strings('soso_einstein')}"
            )
        )

    def _get_mark(self):
        return (
            None
            if not self.config["custom_button12"]
            else [
            {"text": f"{self.strings('soso_chat')}",
             "url": "https://t.me/+5o1a-UjPfCZhNmE5",
            },   
            {"text": f"{self.strings('soso_update')}",
             "url": "http://t.me/share/url?url=.update --force",
            },         
          ]
        )

    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Userbot ma'lumotlarini yuboring"""
        await self.inline.form(
            message=message,
            text=self._render_info(),
            reply_markup=self._get_mark(),
            **(
                {"photo": "https://te.legra.ph/file/695db61e0d6e83fcb7953.jpg"}
                if not self.config["disable_banner"]
                else {}
            ),
        ) 
