from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
import paramiko

BOT_TOKEN = "7049921798:AAH7b4r-ILn4TomvRl5xVYCEfUDeZwRlwAM"

ALLOWED_COMMANDS = {
    "debian 10": "passwd",
    "debian 11": "passwd",
    "debian 12": "passwd",
    "ubuntu 20.04": "passwd",
    "ubuntu 22.04": "passwd",
    "ubuntu 24.04": "passwd"
}

user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silakan masukkan IP VPS (contoh: 192.168.1.10)")
    user_sessions[update.message.from_user.id] = {"step": "ip"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    session = user_sessions.get(user_id)

    if not session:
        await update.message.reply_text("Ketik /start untuk memulai.")
        return

    step = session.get("step")

    if step == "ip":
        session["ip"] = text
        session["step"] = "username"
        await update.message.reply_text("Masukkan username VPS (contoh: root)")

    elif step == "username":
        session["username"] = text
        session["step"] = "password"
        await update.message.reply_text("Masukkan password VPS")

    elif step == "password":
        session["password"] = text
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=session["ip"],
                username=session["username"],
                password=session["password"]
            )
            ssh.close()
            session["step"] = "authenticated"

            keyboard = [
                [InlineKeyboardButton(os_name, callback_data=os_name)]
                for os_name in ALLOWED_COMMANDS.keys()
            ]
            await update.message.reply_text(
                "Login berhasil. Pilih OS untuk di rebuild:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await update.message.reply_text(f"Gagal login: {str(e)}")
            session["step"] = "ip"

    elif step == "await_new_password":
        new_pass = text
        chosen_os = session.get("chosen_os", "Unknown OS")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
            hostname=session["ip"],
            username=session["username"],
            password=session["password"]
    )

    # Script bash untuk mengganti password dan reboot
            bash_script = f"""#!/bin/bash
    
echo -e "#!/bin/bash
            curl -O https://raw.githubusercontent.com/bin456789/reinstall/main/reinstall.sh || wget -O reinstall.sh && chmod +x reinstall.sh && ./reinstall.sh {chosen_os} --password {new_pass}
"""

    # Upload file ke VPS
            sftp = ssh.open_sftp()
            remote_path = "/root/ganti.sh"
            with sftp.file(remote_path, "w") as f:
            f.write(bash_script)
            sftp.chmod(remote_path, 0o755)
            sftp.close()

             Eksekusi script
            ssh.exec_command(f"bash {remote_path}")
            stdin, stdout, stderr = ssh.exec_command(f'bash {remote_path}')
exit_status = stdout.channel.recv_exit_status()  # Tunggu sampai selesai
            ssh.close()

            await update.message.reply_text(" Vps anda sedang di rebuild,l.Silanhkan tunggu 5 menit.")
        except Exception as e:
            await update.message.reply_text(f" Gagal mengeksekusi: {str(e)}")

        session["step"] = "authenticated"
        session.pop("chosen_os", None)

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions.get(user_id)

    if not session or session.get("step") != "authenticated":
        await query.edit_message_text("Sesi tidak valid. Silakan /start ulang.")
        return

    label = query.data
    command = ALLOWED_COMMANDS.get(label)

    if command == "passwd":
        session["step"] = "await_new_password"
        session["chosen_os"] = label
        await query.edit_message_text(f"Anda memilih {label}. Silakan kirim password baru untuk VPS Anda:")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_button))

    print(" Bot aktif...")
    app.run_polling()