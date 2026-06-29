import os

import paramiko
from dotenv import load_dotenv


load_dotenv()


# Функция подключается к Debian по SSH и выполняет команду.
def run_ssh_command(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=os.getenv("RM_HOST"),
            port=int(os.getenv("RM_PORT")),
            username=os.getenv("RM_USER"),
            password=os.getenv("RM_PASSWORD"),
            look_for_keys=False,
            allow_agent=False,
            timeout=10
        )

        stdin, stdout, stderr = client.exec_command(command)

        result = stdout.read().decode(
            "utf-8",
            errors="replace"
        ).strip()

        error = stderr.read().decode(
            "utf-8",
            errors="replace"
        ).strip()

        if result:
            return result

        if error:
            return "Ошибка команды: " + error

        return ""

    except Exception as error:
        return "Ошибка SSH: " + str(error)

    finally:
        client.close()