import logging
import os
import re
import shlex
from io import BytesIO

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)

from ssh_utils import run_ssh_command


load_dotenv()
TOKEN = os.getenv("TOKEN")

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

EMAIL, PHONE, PASSWORD, APT = range(4)


# Команды, которые бот выполняет на Debian через SSH.
LINUX_COMMANDS = {
    "get_release": (
        "cat /etc/os-release",
        "release.txt"
    ),
    "get_uname": (
        "uname -a",
        "uname.txt"
    ),
    "get_uptime": (
        "uptime",
        "uptime.txt"
    ),
    "get_df": (
        "df -h",
        "df.txt"
    ),
    "get_free": (
        "free -h",
        "free.txt"
    ),
    "get_mpstat": (
        "mpstat 1 1",
        "mpstat.txt"
    ),
    "get_w": (
        "w",
        "w.txt"
    ),
    "get_auths": (
        "last -n 10",
        "auths.txt"
    ),
    "get_critical": (
        "journalctl -p crit -n 5 --no-pager",
        "critical.txt"
    ),
    "get_ps": (
        "ps aux --sort=-%cpu",
        "processes.txt"
    ),
    "get_ss": (
        "ss -tuln",
        "ports.txt"
    ),
    "get_services": (
        "systemctl list-units --type=service "
        "--state=running --no-pager --plain",
        "services.txt"
    )
}


def send_result(update, result, file_name):
    if not result:
        update.message.reply_text("Информация не найдена.")
    elif len(result) < 4000:
        update.message.reply_text(result)
    else:
        file = BytesIO(result.encode("utf-8"))
        file.name = file_name
        file.seek(0)
        update.message.reply_document(document=file)


def start(update: Update, context):
    update.message.reply_text(
        "Команды поиска:\n"
        "/find_email\n"
        "/find_phone_number\n"
        "/verify_password\n\n"
        "Команды Linux:\n"
        "/get_release\n"
        "/get_uname\n"
        "/get_uptime\n"
        "/get_df\n"
        "/get_free\n"
        "/get_mpstat\n"
        "/get_w\n"
        "/get_auths\n"
        "/get_critical\n"
        "/get_ps\n"
        "/get_ss\n"
        "/get_apt_list\n"
        "/get_services"
    )
    logging.info("Вызвана команда /start")


def find_email_command(update: Update, context):
    update.message.reply_text(
        "Введите текст для поиска email-адресов:"
    )
    return EMAIL


def find_email(update: Update, context):
    pattern = (
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    emails = re.findall(pattern, update.message.text)

    if emails:
        result = "Найденные email-адреса:\n"

        for number, email in enumerate(emails, start=1):
            result += f"{number}. {email}\n"
    else:
        result = "Email-адреса не найдены."

    update.message.reply_text(result)

    logging.info(
        "Команда /find_email: найдено %s",
        len(emails)
    )

    return ConversationHandler.END


def find_phone_command(update: Update, context):
    update.message.reply_text(
        "Введите текст для поиска телефонных номеров:"
    )
    return PHONE


def find_phone(update: Update, context):
    pattern = (
        r"(?<!\d)(?:\+7|8)"
        r"(?:\s?\(\d{3}\)|[\s-]?\d{3})"
        r"[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"
    )

    phones = re.findall(pattern, update.message.text)

    if phones:
        result = "Найденные телефонные номера:\n"

        for number, phone in enumerate(phones, start=1):
            result += f"{number}. {phone}\n"
    else:
        result = "Телефонные номера не найдены."

    update.message.reply_text(result)

    logging.info(
        "Команда /find_phone_number: найдено %s",
        len(phones)
    )

    return ConversationHandler.END


def verify_password_command(update: Update, context):
    update.message.reply_text(
        "Введите пароль для проверки:"
    )
    return PASSWORD


def verify_password(update: Update, context):
    pattern = (
        r"^(?=.*[A-Z])"
        r"(?=.*[a-z])"
        r"(?=.*\d)"
        r"(?=.*[!@#$%^&*().])"
        r".{8,}$"
    )

    if re.fullmatch(pattern, update.message.text):
        update.message.reply_text("Пароль сложный")
    else:
        update.message.reply_text("Пароль простой")

    logging.info(
        "Выполнена команда /verify_password"
    )

    return ConversationHandler.END


def linux_command(update: Update, context):
    command_name = (
        update.message.text
        .split()[0]
        .lstrip("/")
        .split("@")[0]
    )

    linux_command_text, file_name = (
        LINUX_COMMANDS[command_name]
    )

    result = run_ssh_command(linux_command_text)

    send_result(
        update,
        result,
        file_name
    )

    logging.info(
        "Выполнена команда /%s",
        command_name
    )


def get_apt_list_command(update: Update, context):
    update.message.reply_text(
        "Введите all для вывода всех пакетов "
        "или название пакета для поиска:"
    )

    return APT


def get_apt_list(update: Update, context):
    query = update.message.text.strip()

    if query.lower() in ["all", "все"]:
        result = run_ssh_command(
            "apt list --installed 2>/dev/null"
        )

        send_result(
            update,
            result,
            "apt_list.txt"
        )

        logging.info(
            "Выведен список всех пакетов"
        )
    else:
        safe_query = shlex.quote(query)

        result = run_ssh_command(
            "apt list --installed 2>/dev/null "
            f"| grep -i -- {safe_query}"
        )

        if result:
            send_result(
                update,
                result,
                "apt_search.txt"
            )
        else:
            update.message.reply_text(
                "Пакет не найден."
            )

        logging.info(
            "Выполнен поиск пакета %s",
            query
        )

    return ConversationHandler.END


def main():
    if not TOKEN:
        print("В файле .env не найден TOKEN.")
        return

    updater = Updater(
        TOKEN,
        use_context=True
    )

    dispatcher = updater.dispatcher

    email_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "find_email",
                find_email_command
            )
        ],
        states={
            EMAIL: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    find_email
                )
            ]
        },
        fallbacks=[]
    )

    phone_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "find_phone_number",
                find_phone_command
            )
        ],
        states={
            PHONE: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    find_phone
                )
            ]
        },
        fallbacks=[]
    )

    password_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "verify_password",
                verify_password_command
            )
        ],
        states={
            PASSWORD: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    verify_password
                )
            ]
        },
        fallbacks=[]
    )

    apt_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "get_apt_list",
                get_apt_list_command
            )
        ],
        states={
            APT: [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_apt_list
                )
            ]
        },
        fallbacks=[]
    )

    dispatcher.add_handler(
        CommandHandler("start", start)
    )

    dispatcher.add_handler(email_handler)
    dispatcher.add_handler(phone_handler)
    dispatcher.add_handler(password_handler)
    dispatcher.add_handler(apt_handler)

    for command_name in LINUX_COMMANDS:
        dispatcher.add_handler(
            CommandHandler(
                command_name,
                linux_command
            )
        )

    print(
        "Бот запущен. "
        "Для остановки нажмите Ctrl+C."
    )

    logging.info("Бот запущен")

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()