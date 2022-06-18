import asyncio
import datetime
import io
import json
import logging
import time
from telethon.tl.types import Message
from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

soso = "◍ "

@loader.tds
class BackupMod(loader.Module):
    """Automatic database backup"""

    strings = {
        "name": "Backup",
        "soso_hecham": soso + "bekor qilish",
        "period": soso + "<b>Men «Soso»</b> backuperman.",
        "saved": soso + "Backup period saved. You can re-configure it later with .set_backup_period",
        "never": soso + "I will not make automatic backups. You can re-configure it later with .set_backup_period",
        "invalid_args": soso + "<b>Specify correct backup period in hours, or `0` to disable</b>",
    }

    strings_ru = {
        "period": soso + "<b>Я «Soso»</b> бэкапер.",
        "soso_hecham": soso + "отменить",    
        "saved": soso + "Периодичность сохранена! Ее можно изменить с помощью .set_backup_period",
        "never": soso + "Я не буду делать автоматические резервные копии. Можно отменить используя .set_backup_period",
        "invalid_args": soso + "<b>Укажи правильную периодичность в часах, или `0` для отключения</b>",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self._tg_id,
                photo="https://te.legra.ph/file/d1e23d96b083c9a3a388d.jpg",
                caption=self.strings("period"),
                reply_markup=self.inline.generate_markup(
                    utils.chunks(
                        [
                            {"text": f"◍ {i} ◍", "data": f"backup_period/{i}"}
                            for i in {1, 2, 4, 6, 8, 12, 24, 48, 168}
                        ],
                        3,
                    )
                    + [[{"text": f"{self.strings('soso_hecham')}", "data": "backup_period/never"}]]
                ),
            )

        self._backup_channel, _ = await utils.asset_channel(
            self._client,
            "soso-backups",
            "📼 Your database backups will appear there",
            silent=True,
            archive=True,
            avatar="https://te.legra.ph/file/7fd73ee637e2878eb3045.jpg",
            _folder="hikka",
        )

        self.handler.start()

    async def backup_period_callback_handler(self, call: InlineCall):
        if not call.data.startswith("backup_period"):
            return

        if call.data == "backup_period/never":
            self.set("period", "disabled")
            await call.answer(self.strings("never"), show_alert=True)

            await self.inline.bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
            return

        period = int(call.data.split("/")[1]) * 60 * 60

        self.set("period", period)
        self.set("last_backup", round(time.time()))

        await call.answer(self.strings("saved"), show_alert=True)

        await self.inline.bot.delete_message(
            call.message.chat.id,
            call.message.message_id,
        )

    async def set_backup_periodcmd(self, message: Message):
        """<time in hours> - Change backup frequency"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit() or int(args) not in range(200):
            await utils.answer(message, self.strings("invalid_args"))
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(message, f"<b>{self.strings('never')}</b>")
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(message, f"<b>{self.strings('saved')}</b>")

    @loader.loop(interval=1)
    async def handler(self):
        try:
            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            if self.get("period") == "disabled":
                raise loader.StopLoop

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            backup = io.BytesIO(json.dumps(self._db).encode("utf-8"))
            backup.name = f"hikka-db-backup-{getattr(datetime, 'datetime', datetime).now().strftime('%d-%m-%Y-%H-%M')}.json"

            await self._client.send_file(
                self._backup_channel,
                backup,
            )
            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("HikkaBackup failed")
            await asyncio.sleep(60)
