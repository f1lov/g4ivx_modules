# meta developer: @g4ivx
__version__ = (2,5,0)
import time
import datetime
import psutil
import platform
import subprocess
import asyncio
from .. import loader, utils

@loader.tds
class ServInfoMod(loader.Module):
    """
    Мониторинг сервера и бота
    """
    strings = {
        "name": "ServInfo",
        "servinfo_doc": "Получить расширенную статистику сервера и бота"
    }

    async def client_ready(self, client, db):
        self.premium = getattr(await client.get_me(), 'premium', False)
        self.bot_start_time = time.time()
        self.cached_system_info = await self._get_cached_system_info()

    async def _get_cached_system_info(self):
        system_info = {}

        try:
            system_info['os_info'] = subprocess.getoutput("lsb_release -d").split(":")[1].strip() if platform.system() == "Linux" else platform.system()
            system_info['arch'] = platform.machine()
            system_info['kernel_version'] = platform.release()
            system_info['proc_name'] = platform.processor()

            if not system_info['proc_name'] or "x86_64" in system_info['proc_name'].lower() or "amd64" in system_info['proc_name'].lower():
                if platform.system() == "Linux":
                    try:
                        lscpu_output = subprocess.getoutput("lscpu")
                        for line in lscpu_output.split('\n'):
                            if "Model name:" in line:
                                system_info['proc_name'] = line.split(":")[1].strip()
                                break
                    except Exception:
                        pass

            if not system_info['proc_name']:
                system_info['proc_name'] = "Неизвестный"

            system_info['cpu_cores'] = psutil.cpu_count(logical=True)
            system_info['gpu_info'] = "Неизвестно"
            if platform.system() == "Linux":
                try:
                    lspci_output = subprocess.getoutput("lspci | grep -i 'VGA\\|3D\\|Display'")
                    if lspci_output:
                        system_info['gpu_info'] = lspci_output.split('\n')[0].split(':', 1)[-1].strip()
                except Exception:
                    system_info['gpu_info'] = "Ошибка"

        except Exception as e:
            self.logger.error(f"Ошибка при получении системной информации: {e}")

        return system_info

    def _format_bytes(self, bytes_value):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"

    def _format_network_bytes(self, bytes_value):
        mb_value = bytes_value / (1024 * 1024)
        if mb_value >= 1024:
            gb_value = mb_value / 1024
            return f"{gb_value:.1f}GB"
        else:
            return f"{mb_value:.1f}MB"

    async def _get_system_info(self):
        net = psutil.net_io_counters()
        uptime_system_seconds = int(time.time() - psutil.boot_time())
        uptime_system_str = str(datetime.timedelta(seconds=uptime_system_seconds))

        mem = psutil.virtual_memory()
        used_mem_mb = mem.used / (1024 * 1024)
        total_mem_mb = mem.total / (1024 * 1024)
        disk_usage = psutil.disk_usage('/')
        used_disk_gb = disk_usage.used / (1024 * 1024 * 1024)
        total_disk_gb = disk_usage.total / (1024 * 1024 * 1024)

        return {
            'net': net,
            'uptime_system_str': uptime_system_str,
            'used_mem_mb': used_mem_mb,
            'total_mem_mb': total_mem_mb,
            'used_disk_gb': used_disk_gb,
            'total_disk_gb': total_disk_gb,
        }

    async def _get_bot_info(self):
        proc = psutil.Process()
        bot_memory_mb = proc.memory_info().rss / (1024 * 1024)
        bot_uptime_seconds = int(time.time() - self.bot_start_time)
        bot_uptime_str = str(datetime.timedelta(seconds=bot_uptime_seconds))

        return {
            'bot_memory_mb': bot_memory_mb,
            'bot_uptime_str': bot_uptime_str,
        }

    async def servinfocmd(self, message):
        """
        Получить расширенную статистику сервера и бота
        """
        start = time.time()
        EMOJI = {
            'sys_header': "🖥️",
            'bot_header': "🤖"
        }

        if self.premium:
            EMOJI['sys_header'] = "<emoji document_id=5879785854284599288>ℹ️</emoji>"
            EMOJI['bot_header'] = "<emoji document_id=5843553939672274145>⚡️</emoji>"

        loading_message = await utils.answer(message, f"{EMOJI['sys_header']} <b>Анализ системы...</b>")

        try:
            system_info = self.cached_system_info
            dynamic_system_info = await self._get_system_info()
            bot_info = await self._get_bot_info()

            system_info_block = (
                f"OS: {system_info['os_info']} {system_info['arch']}\n"
                f"Ядро: {system_info['kernel_version']}\n"
                f"Uptime: {dynamic_system_info['uptime_system_str']}\n"
                f"CPU: {system_info['proc_name']} | {system_info['cpu_cores']} ядер\n"
                f"RAM: {dynamic_system_info['used_mem_mb']:.1f}MB/{dynamic_system_info['total_mem_mb']:.1f}MB\n"
                f"Disk: {dynamic_system_info['used_disk_gb']:.1f}GB/{dynamic_system_info['total_disk_gb']:.1f}GB\n"
                f"Сеть: ▲ {self._format_network_bytes(dynamic_system_info['net'].bytes_sent)} ▼ {self._format_network_bytes(dynamic_system_info['net'].bytes_recv)}\n"
                f"Процессы: {len(psutil.pids())}\n"
                f"GPU: {system_info['gpu_info']}"
            )

            bot_info_block = (
                f"Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Пинг: {(time.time() - start) * 1000:.2f}мс\n"
                f"Память: {bot_info['bot_memory_mb']:.1f}MB\n"
                f"Аптайм: {bot_info['bot_uptime_str']}"
            )

            result = (
                f"<b>{EMOJI['sys_header']} Системная информация</b>\n"
                f"<blockquote>{system_info_block}</blockquote>\n\n"
                f"<b>{EMOJI['bot_header']} Информация о боте</b>\n"
                f"<blockquote>{bot_info_block}</blockquote>"
            )

            await message.client.edit_message(loading_message, result)

        except Exception as e:
            await message.client.edit_message(loading_message, f"⚠️ <b>Ошибка:</b> {str(e)}")