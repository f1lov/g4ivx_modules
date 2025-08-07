#meta developer @g4ivx
# meta_name: ServInfo

import time, datetime, psutil, platform, subprocess, re
from .. import loader, utils

@loader.tds
class ServInfoMod(loader.Module):
    """
    Мониторинг сервера и бота
    """
    strings = {"name": "ServInfo", "version": "2.5.0"}

    async def client_ready(self, client, db):
        self.premium = getattr(await client.get_me(), 'premium', False)

    async def servinfocmd(self, message):
        """
        Получить расширенную статистику
        """
        start = time.time()
        
        EMOJI = {
            'sys_header': "🖥️",
            'bot_header': "🤖",
            'dev': "✨"
        }
        
        if self.premium:
            EMOJI['sys_header'] = "<emoji document_id=5879785854284599288>ℹ️</emoji>"
            EMOJI['bot_header'] = "<emoji document_id=5843553939672274145>⚡️</emoji>"
            EMOJI['dev'] = "<emoji document_id=5890925363067886150>✨</emoji>"

        # Отправляем новое сообщение, которое потом будем редактировать
        loading_message = await utils.answer(message, f"{EMOJI['sys_header']} <b>Анализ системы...</b>")

        try:
            # --- Сбор системной информации ---
            os_info = subprocess.getoutput("lsb_release -d").split(":")[1].strip() if platform.system() == "Linux" else platform.system()
            arch = platform.machine() 
            kernel_version = platform.release()
            
            net = psutil.net_io_counters()
            
            uptime_system_seconds = int(time.time() - psutil.boot_time())
            uptime_system_str = str(datetime.timedelta(seconds=uptime_system_seconds))

            proc_name = platform.processor()
            if not proc_name or "x86_64" in proc_name.lower() or "amd64" in proc_name.lower():
                if platform.system() == "Linux":
                    try:
                        lscpu_output = subprocess.getoutput("lscpu")
                        for line in lscpu_output.split('\n'):
                            if "Model name:" in line:
                                proc_name = line.split(":")[1].strip()
                                break
                    except Exception:
                        pass
            
            if not proc_name or "x86_64" in proc_name.lower() or "amd64" in proc_name.lower():
                if platform.system() == "Linux":
                    try:
                        with open('/proc/cpuinfo', 'r') as f:
                            for line in f:
                                if "model name" in line:
                                    proc_name = line.split(":")[1].strip()
                                    break
                    except Exception:
                        pass
            
            if not proc_name or "x86_64" in proc_name.lower() or "amd64" in proc_name.lower():
                proc_name = "Неизвестный"

            cpu_cores = psutil.cpu_count(logical=True)
            cpu_load = psutil.cpu_percent()

            mem = psutil.virtual_memory()
            used_mem_mb = mem.used / (1024 * 1024)
            total_mem_mb = mem.total / (1024 * 1024)
            
            disk_usage = psutil.disk_usage('/')
            used_disk_gb = disk_usage.used / (1024 * 1024 * 1024)
            total_disk_gb = disk_usage.total / (1024 * 1024 * 1024)

            gpu_info = "Неизвестно"
            if platform.system() == "Linux":
                try:
                    lspci_output = subprocess.getoutput("lspci | grep -i 'VGA\\|3D\\|Display'")
                    if lspci_output:
                        gpu_line = lspci_output.split('\n')[0].strip()
                        
                        match = re.match(r'^(?:[\da-fA-F.:\s]+)?(?:VGA|3D|Display controller|Graphics controller)?\s*:\s*(.+)', gpu_line)
                        if match:
                            gpu_info = match.group(1).strip()
                        else:
                            if ': ' in gpu_line:
                                gpu_info = gpu_line.split(': ', 1)[1].strip()
                            else:
                                gpu_info = gpu_line.strip()
                        
                        rev_index = gpu_info.rfind(' (rev ')
                        if rev_index != -1:
                            gpu_name = gpu_info[:rev_index].strip()
                            gpu_rev = gpu_info[rev_index:].strip()
                            gpu_info = f"{gpu_name} | {gpu_rev}"

                    else:
                        gpu_info = "Не обнаружено"
                except Exception:
                    gpu_info = "Ошибка получения"

            proc = psutil.Process()
            bot_memory_mb = proc.memory_info().rss / (1024 * 1024)
            bot_uptime_seconds = int(time.time() - proc.create_time())
            bot_uptime_str = str(datetime.timedelta(seconds=bot_uptime_seconds))
            
            system_info_block = (
                f"OS: {os_info} {arch}\n"
                f"Ядро: {kernel_version}\n"
                f"Uptime: {uptime_system_str}\n"
                f"CPU: {proc_name} | {cpu_cores} ядер | загрузка: {cpu_load}%\n"
                f"RAM: {used_mem_mb:.1f}MB/{total_mem_mb:.1f}MB\n"
                f"Disk: {used_disk_gb:.1f}GB/{total_disk_gb:.1f}GB\n"
                f"Сеть: ▲ {net.bytes_sent/1024/1024:.1f}MB ▼ {net.bytes_recv/1024/1024:.1f}MB\n"
                f"Процессы: {len(psutil.pids())}\n"
                f"GPU: {gpu_info}"
            )

            bot_info_block = (
                f"Время: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Пинг: {(time.time() - start) * 1000:.2f}мс\n"
                f"Память: {bot_memory_mb:.1f}MB\n"
                f"Аптайм: {bot_uptime_str}"
            )
            
            result = (
                f"<b>{EMOJI['sys_header']} Системная информация</b>\n"
                f"<blockquote>{system_info_block}</blockquote>\n\n"
                f"<b>{EMOJI['bot_header']} Информация о боте</b>\n"
                f"<blockquote>{bot_info_block}</blockquote>\n\n"
                f"{EMOJI['dev']} developer @g4ivx | beta_test | v{self.strings['version']}"
            )
            
            await message.client.edit_message(loading_message, result)

        except Exception as e:
            await message.client.edit_message(loading_message, f"⚠️ <b>Ошибка:</b> {str(e)}")
