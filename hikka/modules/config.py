import ast
import functools
import logging
from math import ceil
from typing import Optional, Union, Any
from telethon.tl.types import Message
from .. import loader, utils, translations
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class HikkaConfigMod(loader.Module):
    """Interactive configurator for Hikka Userbot"""

    strings = {
        "name": "Config",
        "choose_core": "🎚 <b>Choose a category of modules to configure</b>",
        "configure": "🎚 <b>Choose a module to configure</b>",
        "configuring_mod": "🎚 <b>Choose config option for mod</b> <code>{}</code>\n\n<b>Current options:</b>\n\n{}",
        "configuring_option": "🎚 <b>Configuring option </b><code>{}</code><b> of mod </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Default: {}</b>\n\n<b>Current: {}</b>\n\n{}",
        "option_saved": "🎚 <b>Option </b><code>{}</code><b> of mod </b><code>{}</code><b> saved!</b>\n<b>Current: {}</b>",
        "option_reset": "♻️ <b>Option </b><code>{}</code><b> of mod </b><code>{}</code><b> has been reset to default</b>\n<b>Current: {}</b>",
        "args": "🚫 <b>You specified incorrect args</b>",
        "no_mod": "🚫 <b>Module doesn't exist</b>",
        "no_option": "🚫 <b>Configuration option doesn't exist</b>",
        "validation_error": "🚫 <b>You entered incorrect config value. \nError: {}</b>",
        "try_again": "🔁 Try again",
        "typehint": "🕵️ <b>Must be a{eng_art} {}</b>",
        "set": "set",
        "set_default_btn": "♻️ Reset default",
        "enter_value_btn": "✍️ Enter value",
        "enter_value_desc": "✍️ Enter new configuration value for this option",
        "add_item_desc": "✍️ Enter item to add",
        "remove_item_desc": "✍️ Enter item to remove",
        "back_btn": "👈 Back",
        "close_btn": "🔻 Close",
        "add_item_btn": "➕ Add item",
        "remove_item_btn": "➖ Remove item",
        "show_hidden": "🚸 Show value",
        "hide_value": "🔒 Hide value",
        "builtin": "🕋 Built-in",
        "external": "🛸 External",
    }

    strings_ru = {
        "choose_core": "🎚 <b>Выбери категорию модуля</b>",
        "configure": "🎚 <b>Выбери модуль для изменения конфигурации</b>",
        "configuring_mod": "🎚 <b>Выбери параметр для модуля</b> <code>{}</code>\n\n<b>Текущие настройки:</b>\n\n{}",
        "configuring_option": "🎚 <b>Управление параметром </b><code>{}</code><b> модуля </b><code>{}</code>\n<i>ℹ️ {}</i>\n\n<b>Стандартное: {}</b>\n\n<b>Текущее: {}</b>\n\n{}",
        "option_saved": "🎚 <b>Параметр </b><code>{}</code><b> модуля </b><code>{}</code><b> сохранен!</b>\n<b>Текущее: {}</b>",
        "option_reset": "♻️ <b>Параметр </b><code>{}</code><b> модуля </b><code>{}</code><b> сброшен до значения по умолчанию</b>\n<b>Текущее: {}</b>",
        "_cmd_doc_config": "Настройки модулей",
        "_cmd_doc_fconfig": "<имя модуля> <имя конфига> <значение> - Расшифровывается как ForceConfig - Принудительно устанавливает значение в конфиге, если это не удалось сделать через inline бота",
        "_cls_doc": "Интерактивный конфигуратор Hikka",
        "args": "🚫 <b>Ты указал неверные аргументы</b>",
        "no_mod": "🚫 <b>Модуль не существует</b>",
        "no_option": "🚫 <b>У модуля нет такого значения конфига</b>",
        "validation_error": "🚫 <b>Введено некорректное значение конфига. \nОшибка: {}</b>",
        "try_again": "🔁 Попробовать еще раз",
        "typehint": "🕵️ <b>Должно быть {}</b>",
        "set": "поставить",
        "set_default_btn": "♻️ Значение по умолчанию",
        "enter_value_btn": "✍️ Ввести значение",
        "enter_value_desc": "✍️ Введи новое значение этого параметра",
        "add_item_desc": "✍️ Введи элемент, который нужно добавить",
        "remove_item_desc": "✍️ Введи элемент, который нужно удалить",
        "back_btn": "👈 Назад",
        "close_btn": "🔻 Закрыть",
        "add_item_btn": "➕ Добавить элемент",
        "remove_item_btn": "➖ Удалить элемент",
        "show_hidden": "🚸 Показать значение",
        "hide_value": "🔒 Скрыть значение",
        "builtin": "🕋 Встроенные",
        "external": "🛸 Внешние",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._row_size = 3
        self._num_rows = 5

    @staticmethod
    def prep_value(value: Any) -> Any:
        if isinstance(value, str):
            return f"</b><code>{utils.escape_html(value.strip())}</code><b>"

        if isinstance(value, list) and value:
            return (
                "</b><code>[</code>\n    "
                + "\n    ".join(
                    [f"<code>{utils.escape_html(str(item))}</code>" for item in value]
                )
                + "\n<code>]</code><b>"
            )

        return f"</b><code>{utils.escape_html(value)}</code><b>"

    def hide_value(self, value: Any) -> str:
        if isinstance(value, list) and value:
            return self.prep_value(["*" * len(str(i)) for i in value])

        return self.prep_value("*" * len(str(value)))

    async def inline__set_config(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        is_core: bool = False,
    ):
        try:
            self.lookup(mod).config[option] = query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"is_core": is_core},
                },
            )
            return

        await call.edit(
            self.strings("option_saved").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"is_core": is_core},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__reset_default(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        is_core: bool = False,
    ):
        mod_instance = self.lookup(mod)
        mod_instance.config[option] = mod_instance.config.getdef(option)

        await call.edit(
            self.strings("option_reset").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"is_core": is_core},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
        )

    async def inline__set_bool(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
        is_core: bool = False,
    ):
        try:
            self.lookup(mod).config[option] = value
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"is_core": is_core},
                },
            )
            return

        validator = self.lookup(mod).config._config[option].validator
        doc = utils.escape_html(
            validator.doc.get(
                self._db.get(translations.__name__, "lang", "en"), validator.doc["en"]
            )
        )

        await call.edit(
            self.strings("configuring_option").format(
                utils.escape_html(option),
                utils.escape_html(mod),
                utils.escape_html(self.lookup(mod).config.getdoc(option)),
                self.prep_value(self.lookup(mod).config.getdef(option)),
                self.prep_value(self.lookup(mod).config[option])
                if not validator or validator.internal_id != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
                self.strings("typehint").format(
                    doc,
                    eng_art="n" if doc.lower().startswith(tuple("euioay")) else "",
                )
                if doc
                else "",
            ),
            reply_markup=self._generate_bool_markup(mod, option, is_core),
        )

        await call.answer("✅")

    def _generate_bool_markup(
        self,
        mod: str,
        option: str,
        is_core: bool = False,
    ) -> list:
        return [
            [
                *(
                    [
                        {
                            "text": f"✅ {self.strings('set')} `True`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, True),
                            "kwargs": {"is_core": is_core},
                        }
                    ]
                    if not self.lookup(mod).config[option]
                    else [
                        {
                            "text": f"❌ {self.strings('set')} `False`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, False),
                            "kwargs": {"is_core": is_core},
                        }
                    ]
                ),
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"is_core": is_core},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"is_core": is_core},
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ],
        ]

    async def inline__add_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        is_core: bool = False,
    ):
        try:
            try:
                query = ast.literal_eval(query)
            except Exception:
                pass

            if isinstance(query, (set, tuple)):
                query = list(query)

            if not isinstance(query, list):
                query = [query]

            self.lookup(mod).config[option] = self.lookup(mod).config[option] + query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"is_core": is_core},
                },
            )
            return

        await call.edit(
            self.strings("option_saved").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"is_core": is_core},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__remove_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
        is_core: bool = False,
    ):
        try:
            try:
                query = ast.literal_eval(query)
            except Exception:
                pass

            if isinstance(query, (set, tuple)):
                query = list(query)

            if not isinstance(query, list):
                query = [query]

            query = list(map(str, query))

            old_config_len = len(self.lookup(mod).config[option])

            self.lookup(mod).config[option] = [
                i for i in self.lookup(mod).config[option] if str(i) not in query
            ]

            if old_config_len == len(self.lookup(mod).config[option]):
                raise loader.validators.ValidationError(
                    f"Nothing from passed value ({self.prep_value(query)}) is not in target list"
                )
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                    "kwargs": {"is_core": is_core},
                },
            )
            return

        await call.edit(
            self.strings("option_saved").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option])
                if not self.lookup(mod).config._config[option].validator
                or self.lookup(mod).config._config[option].validator.internal_id
                != "Hidden"
                else self.hide_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"is_core": is_core},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    def _generate_series_markup(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        is_core: bool = False,
    ) -> list:
        return [
            [
                {
                    "text": self.strings("enter_value_btn"),
                    "input": self.strings("enter_value_desc"),
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                    "kwargs": {"is_core": is_core},
                }
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("remove_item_btn"),
                            "input": self.strings("remove_item_desc"),
                            "handler": self.inline__remove_item,
                            "args": (mod, option, call.inline_message_id),
                            "kwargs": {"is_core": is_core},
                        },
                        {
                            "text": self.strings("add_item_btn"),
                            "input": self.strings("add_item_desc"),
                            "handler": self.inline__add_item,
                            "args": (mod, option, call.inline_message_id),
                            "kwargs": {"is_core": is_core},
                        },
                    ]
                    if self.lookup(mod).config[option]
                    else []
                ),
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                            "kwargs": {"is_core": is_core},
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                    "kwargs": {"is_core": is_core},
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ],
        ]

    async def inline__configure_option(
        self,
        call: InlineCall,
        mod: str,
        config_opt: str,
        force_hidden: Optional[bool] = False,
        is_core: bool = False,
    ):
        module = self.lookup(mod)
        args = [
            utils.escape_html(config_opt),
            utils.escape_html(mod),
            utils.escape_html(module.config.getdoc(config_opt)),
            self.prep_value(module.config.getdef(config_opt)),
            self.prep_value(module.config[config_opt])
            if not module.config._config[config_opt].validator
            or module.config._config[config_opt].validator.internal_id != "Hidden"
            or force_hidden
            else self.hide_value(module.config[config_opt]),
        ]

        if (
            module.config._config[config_opt].validator
            and module.config._config[config_opt].validator.internal_id == "Hidden"
        ):
            additonal_button_row = (
                [
                    [
                        {
                            "text": self.strings("hide_value"),
                            "callback": self.inline__configure_option,
                            "args": (mod, config_opt, False),
                            "kwargs": {"is_core": is_core},
                        }
                    ]
                ]
                if force_hidden
                else [
                    [
                        {
                            "text": self.strings("show_hidden"),
                            "callback": self.inline__configure_option,
                            "args": (mod, config_opt, True),
                            "kwargs": {"is_core": is_core},
                        }
                    ]
                ]
            )
        else:
            additonal_button_row = []

        try:
            validator = module.config._config[config_opt].validator
            doc = utils.escape_html(
                validator.doc.get(
                    self._db.get(translations.__name__, "lang", "en"),
                    validator.doc["en"],
                )
            )
        except Exception:
            doc = None
            validator = None
            args += [""]
        else:
            args += [
                self.strings("typehint").format(
                    doc,
                    eng_art="n" if doc.lower().startswith(tuple("euioay")) else "",
                )
            ]
            if validator.internal_id == "Boolean":
                await call.edit(
                    self.strings("configuring_option").format(*args),
                    reply_markup=additonal_button_row
                    + self._generate_bool_markup(mod, config_opt, is_core),
                )
                return

            if validator.internal_id == "Series":
                await call.edit(
                    self.strings("configuring_option").format(*args),
                    reply_markup=additonal_button_row
                    + self._generate_series_markup(call, mod, config_opt, is_core),
                )
                return

        await call.edit(
            self.strings("configuring_option").format(*args),
            reply_markup=additonal_button_row
            + [
                [
                    {
                        "text": self.strings("enter_value_btn"),
                        "input": self.strings("enter_value_desc"),
                        "handler": self.inline__set_config,
                        "args": (mod, config_opt, call.inline_message_id),
                        "kwargs": {"is_core": is_core},
                    }
                ],
                [
                    {
                        "text": self.strings("set_default_btn"),
                        "callback": self.inline__reset_default,
                        "args": (mod, config_opt),
                        "kwargs": {"is_core": is_core},
                    }
                ],
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                        "kwargs": {"is_core": is_core},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ],
            ],
        )

    async def inline__configure(
        self,
        call: InlineCall,
        mod: str,
        is_core: bool = False,
    ):
        btns = [
            {
                "text": param,
                "callback": self.inline__configure_option,
                "args": (mod, param),
                "kwargs": {"is_core": is_core},
            }
            for param in self.lookup(mod).config
        ]

        await call.edit(
            self.strings("configuring_mod").format(
                utils.escape_html(mod),
                "\n".join(
                    [
                        f"▫️ <code>{utils.escape_html(key)}</code>: <b>{self.prep_value(value) if not self.lookup(mod).config._config[key].validator or self.lookup(mod).config._config[key].validator.internal_id != 'Hidden' else self.hide_value(value)}</b>"
                        for key, value in self.lookup(mod).config.items()
                    ]
                ),
            ),
            reply_markup=list(utils.chunks(btns, 2))
            + [
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__global_config,
                        "kwargs": {"is_core": is_core},
                    },
                    {"text": self.strings("close_btn"), "action": "close"},
                ]
            ],
        )

    async def inline__choose_category(self, call: Union[Message, InlineCall]):
        await utils.answer(
            call,
            self.strings("choose_core"),
            reply_markup=[
                [
                    {
                        "text": self.strings("builtin"),
                        "callback": self.inline__global_config,
                        "kwargs": {"is_core": True},
                    },
                    {
                        "text": self.strings("external"),
                        "callback": self.inline__global_config,
                    },
                ],
                [{"text": self.strings("close_btn"), "action": "close"}],
            ],
        )

    async def inline__global_config(
        self,
        call: InlineCall,
        page: int = 0,
        is_core: bool = False,
    ):
        to_config = [
            mod.strings("name")
            for mod in self.allmodules.modules
            if hasattr(mod, "config")
            and callable(mod.strings)
            and (getattr(mod, "__origin__", None) == "<core>" or not is_core)
            and (getattr(mod, "__origin__", None) != "<core>" or is_core)
        ]

        to_config.sort()

        kb = []
        for mod_row in utils.chunks(
            to_config[
                page
                * self._num_rows
                * self._row_size : (page + 1)
                * self._num_rows
                * self._row_size
            ],
            3,
        ):
            row = [
                {
                    "text": btn,
                    "callback": self.inline__configure,
                    "args": (btn,),
                    "kwargs": {"is_core": is_core},
                }
                for btn in mod_row
            ]
            kb += [row]

        if len(to_config) > self._num_rows * self._row_size:
            kb += self.inline.build_pagination(
                callback=functools.partial(self.inline__global_config, is_core=is_core),
                total_pages=ceil(len(to_config) / (self._num_rows * self._row_size)),
                current_page=page + 1,
            )

        kb += [
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__choose_category,
                },
                {"text": self.strings("close_btn"), "action": "close"},
            ]
        ]

        await call.edit(self.strings("configure"), reply_markup=kb)

    async def configcmd(self, message: Message):
        """Configure modules"""
        args = utils.get_args_raw(message)
        if self.lookup(args):
            form = await self.inline.form(
                "🌘 <b>Loading configuration</b>",
                message,
                {"text": "🌘", "data": "empty"},
                ttl=24 * 60 * 60,
            )
            await self.inline__configure(form, args)
            return

        await self.inline__choose_category(message)

    async def fconfigcmd(self, message: Message):
        """<module_name> <propery_name> <config_value> - Stands for ForceConfig - Set the config value if it is not possible using default method"""
        args = utils.get_args_raw(message).split(maxsplit=2)

        if len(args) < 3:
            await utils.answer(message, self.strings("args"))
            return

        mod, option, value = args

        instance = self.lookup(mod)
        if not instance:
            await utils.answer(message, self.strings("no_mod"))
            return

        if option not in instance.config:
            await utils.answer(message, self.strings("no_option"))
            return

        instance.config[option] = value
        await utils.answer(
            message,
            self.strings("option_saved").format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(instance.config[option])
                if not instance.config._config[option].validator
                or instance.config._config[option].validator.internal_id != "Hidden"
                else self.hide_value(instance.config[option]),
            ),
        )
