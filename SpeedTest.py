# meta developer: @svo_rkn
__version__ = (2,5,0)

from .. import loader, utils
import asyncio
import subprocess

@loader.tds
class SpeedTestMod(loader.Module):
    """
    Тест скорости интернета
    """
    strings = {"name": "SpeedTest", "version": "1.5.0"}

    async def client_ready(self, client, db):
        """Инициализация модуля и проверка статуса Premium."""
        self.premium = getattr(await client.get_me(), 'premium', False)

    async def speedcmd(self, message):
        """
        Запустить тест скорости интернета
        """
        EMOJI = {
            'header': "⚡️",
            'server': "📡",  
            'ping': "⏱️",   
            'download_upload_line_prefix': "📊",
            'share': "🔗",
            'dev': "✨"
        }

        if self.premium:
            EMOJI['header'] = "<emoji document_id=5881806211195605908>📸</emoji>"
            EMOJI['server'] = "<emoji document_id=5879785854284599288>ℹ️</emoji>"
            EMOJI['ping'] = "<emoji document_id=5890925363067886150>✨</emoji>"
            EMOJI['download_upload_line_prefix'] = "<emoji document_id=5874986954180791957>📶</emoji>"
            EMOJI['share'] = "<emoji document_id=6039451237743595514>📎</emoji>"
            EMOJI['dev'] = "<emoji document_id=5805532930662996322>✅</emoji>"

        status_message = await utils.answer(message, f"{EMOJI['header']} <b>Запускаю тест скорости...</b>\n<i>Это может занять некоторое время (до 1-2 минут).</i>")

        try:
            process = await asyncio.create_subprocess_exec(
                "speedtest-cli", "--secure", "--share",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout_bytes, stderr_bytes = await process.communicate()
            
            stdout = stdout_bytes.decode().strip()
            stderr = stderr_bytes.decode().strip()
            returncode = process.returncode

            if returncode != 0:
                error_output = stderr if stderr else stdout
                await status_message.edit(f"⚠️ <b>Ошибка при выполнении speedtest (код {returncode}):</b>\n<code>{error_output}</code>")
                return

            if not stdout:
                await status_message.edit(f"⚠️ <b>Ошибка:</b> Не удалось получить вывод от speedtest-cli. Проверьте установку или права доступа.")
                return

            parsed_data = {}
            for line in stdout.split('\n'):
                if "Hosted by" in line:
                    parts = line.split("Hosted by ", 1)[1]
                    server_name_loc = parts.split('[')[0].strip()
                    ping_match = parts.split(']: ')[-1].replace(' ms', '').strip()
                    
                    server_location_match = server_name_loc.split('(')[-1].replace(')', '').strip() if '(' in server_name_loc else "Неизвестно"
                    parsed_data['server_display'] = server_location_match
                    parsed_data['server_ping'] = ping_match
                elif "Download:" in line:
                    parsed_data['download'] = line.replace("Download: ", "").strip()
                elif "Upload:" in line:
                    parsed_data['upload'] = line.replace("Upload: ", "").strip()
                elif "Share results:" in line:
                    parsed_data['share_link'] = line.replace("Share results: ", "").strip()

            result_lines = [
                f"<b>{EMOJI['header']} Результаты SpeedTest</b>",
                f"{EMOJI['server']} <b>Сервер:</b> {parsed_data.get('server_display', 'Неизвестно')}",
                f"{EMOJI['ping']} <b>Пинг:</b> {parsed_data.get('server_ping', 'N/A')} мс",
                f"{EMOJI['download_upload_line_prefix']} <b>Загрузка:</b> {parsed_data.get('download', 'N/A')} | <b>Отдача:</b> {parsed_data.get('upload', 'N/A')}",
            ]
            if parsed_data.get('share_link'):
                result_lines.append(f"{EMOJI['share']} <b>Поделиться:</b> <a href='{parsed_data['share_link']}'>Результат</a>")

            final_message = "\n".join(result_lines)
            await status_message.edit(final_message, parse_mode='html', link_preview=False)

        except FileNotFoundError:
            await status_message.edit("⚠️ <b>Ошибка:</b> Команда speedtest-cli не найдена.\nПожалуйста, установите ее на ваш сервер. Например: sudo apt install speedtest-cli или pip install speedtest-cli")
        except Exception as e:
            await status_message.edit(f"⚠️ <b>Произошла непредвиденная ошибка:</b> {e}")