from datetime import datetime
from database.connection import get_conn
from services.smtp_service import send_email_smtp
from services.whatsapp_web import WhatsAppWeb
from services.utils import normalize_phone

def process_reminders(smtp_cfg, dry_run=False):
    conn = get_conn()
    c = conn.cursor()
    logs = []
    now = datetime.now()
    
    # Inicializa o WhatsAppWeb (se não for dry_run)
    wa_sender = None
    if not dry_run:
        try:
            wa_sender = WhatsAppWeb()
            wa_sender.start() # Isso exigirá a leitura do QR Code pelo usuário
        except Exception as e:
            logs.append({"details": f"Falha ao iniciar WhatsAppWeb: {e}"})
            # Continua o processamento, mas sem WhatsApp

    # lembretes agendados
    c.execute("""
        SELECT r.*, u.email, u.phone, u.name
        FROM reminders r
        JOIN users u ON r.user_id = u.id
        WHERE r.sent = 0
    """)
    reminders = c.fetchall()

    # 1) lembretes agendados
    for r in reminders:
        remind_at = datetime.fromisoformat(r["remind_at"])
        if now >= remind_at:
            channels = [r["channel"]] if r["channel"] != "both" else ["email", "whatsapp"]
            for ch in channels:
                success = False
                details = "not attempted"
                
                if ch == "email" and r["email"]:
                    subject = f"Lembrete: {r['title']}"
                    body = f"Olá {r['name']},\n\nLembrete: {r['title']}\n\n{r['description']}\n\nAtenciosamente"
                    if dry_run:
                        success, details = True, "dry run"
                    else:
                        success, details = send_email_smtp(r['email'], subject, body, smtp_cfg)
                        
                if ch == "whatsapp" and r["phone"]:
                    phone = normalize_phone(r["phone"])
                    message = f"Lembrete: {r['title']}\n{r['description']}"
                    if dry_run:
                        success, details = True, "dry run"
                    elif wa_sender:
                        success, details = wa_sender.send(phone, message)
                    else:
                        details = "WhatsApp sender not initialized"
                        
                logs.append({
                    "user_id": r["user_id"],
                    "reminder_id": r["id"],
                    "sent_at": datetime.now().isoformat(),
                    "channel": ch,
                    "success": int(success),
                    "details": details
                })
                
                # Registrar no log
                c.execute("INSERT INTO sent_log (user_id, reminder_id, sent_at, channel, success, details) VALUES (?, ?, ?, ?, ?, ?)", 
                          (r["user_id"], r["id"], datetime.now().isoformat(), ch, int(success), details))
                conn.commit()
                
            # marcar como enviado - evita reenvio infinito
            c.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (r["id"],))
            conn.commit()

    # 2) aniversários do dia
    today_md = (now.month, now.day)
    c.execute("SELECT * FROM users WHERE birthdate IS NOT NULL")
    users = c.fetchall()
    
    for u in users:
        try:
            bd = datetime.fromisoformat(u["birthdate"]).date()
        except Exception:
            continue
            
        if (bd.month, bd.day) == today_md:
            # check if already sent today
            c.execute("SELECT COUNT(*) FROM sent_log WHERE user_id = ? AND DATE(sent_at) = DATE(?) AND channel = 'birthday'", (u["id"], now.isoformat()))
            already = c.fetchone()[0]
            if already:
                continue
                
            # attempt send via email + whatsapp if available
            
            # email
            if u["email"]:
                subject = "Feliz aniversário!"
                body = f"Olá {u['name']},\n\nDesejamos a você um feliz aniversário!\n\nAtenciosamente"
                if dry_run:
                    success, details = True, "dry run"
                else:
                    success, details = send_email_smtp(u['email'], subject, body, smtp_cfg)
                    
                logs.append({
                    "user_id": u["id"],
                    "reminder_id": None,
                    "sent_at": datetime.now().isoformat(),
                    "channel": "email (birthday)",
                    "success": int(success),
                    "details": details
                })
                c.execute("INSERT INTO sent_log (user_id, reminder_id, sent_at, channel, success, details) VALUES (?, ?, ?, ?, ?, ?)", 
                          (u["id"], None, datetime.now().isoformat(), 'birthday', int(success), details))
                conn.commit()
                
            # whatsapp
            if u["phone"]:
                phone = normalize_phone(u["phone"])
                message = f"Feliz aniversário, {u['name']}! 🎉\nTudo de bom hoje e sempre."
                if dry_run:
                    success, details = True, "dry run"
                elif wa_sender:
                    success, details = wa_sender.send(phone, message)
                else:
                    details = "WhatsApp sender not initialized"
                    
                logs.append({
                    "user_id": u["id"],
                    "reminder_id": None,
                    "sent_at": datetime.now().isoformat(),
                    "channel": "whatsapp (birthday)",
                    "success": int(success),
                    "details": details
                })
                c.execute("INSERT INTO sent_log (user_id, reminder_id, sent_at, channel, success, details) VALUES (?, ?, ?, ?, ?, ?)", 
                          (u["id"], None, datetime.now().isoformat(), 'birthday', int(success), details))
                conn.commit()

    # Fecha o WhatsAppWeb
    if wa_sender:
        wa_sender.close()
        
    return logs

