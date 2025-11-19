from curses import meta
import streamlit as st
from datetime import datetime, date, timedelta
import json
import pandas as pd
import io

# Importações da arquitetura modularizada
from database.init_db import init_db
from database.models import add_user, list_users, add_reminder, list_reminders, get_user_by_id, update_user, delete_user, get_reminder_by_id, update_reminder, delete_reminder, list_utecs, get_all_roles, get_all_users_ids, get_users_by_utec, get_users_by_role
from services.reminders_service import process_reminders
from services.utils import normalize_phone
from services.smtp_service import send_email_smtp # Apenas para teste de configuração
from services.whatsapp_web import WhatsAppWeb # Apenas para teste de configuração
from configs.settings import save_settings

# Constantes
# UTEC_OPTIONS será gerado dinamicamente a partir de list_utecs() no models.py

# Inicialização do banco de dados
init_db()

# Funções de teste de configuração
def test_smtp_config(smtp_cfg):
    # Tenta enviar um e-mail de teste para o próprio remetente
    test_email = smtp_cfg.get("from_email")
    if not test_email:
        return False, "E-mail de remetente não configurado."
    
    subject = "Teste de Configuração SMTP GTR"
    body = f"Este é um e-mail de teste enviado em {datetime.now().isoformat()}."
    
    return send_email_smtp(test_email, subject, body, smtp_cfg)

def test_whatsapp_config():
    # O serviço de WhatsApp é baseado em Selenium, o que é problemático para um app Streamlit.
    # Apenas informamos o usuário sobre a necessidade de configuração manual.
    return False, "O serviço de WhatsApp Web requer configuração manual (leitura de QR Code) e não pode ser testado automaticamente no Streamlit."


# Streamlit UI
st.set_page_config(page_title="GTR - Sistema de Mensagens", layout='wide')
st.title("GTR — Sistema de Mensagens (Streamlit + SQLite)")

menu = st.sidebar.selectbox("Menu", [
    "Configurações",
    "Cadastrar Usuário",
    "Upload de Usuários (CSV/XLS)",
    "Criar Lembrete",
    "Gerenciar Usuários",
    "Gerenciar Lembretes",
    "Logs de Envio",
    "Processar Lembretes"
])

# ---------------- CONFIGURAÇÕES ----------------
if menu == "Configurações":
    st.header("Configurações de envio (SMTP e WhatsApp)")
    
    # 1. Inputs e Botão Salvar dentro do Form
    with st.form("config_form"):
        with st.expander("Configurações SMTP (E-mail)"):
            st.subheader("SMTP")
            st.session_state['smtp_host'] = st.text_input("SMTP host", value=st.session_state.get('smtp_host', 'smtp.gmail.com'), key='smtp_host_input')
            st.session_state['smtp_port'] = st.number_input("SMTP port", value=int(st.session_state.get('smtp_port', 587)), key='smtp_port_input')
            st.session_state['smtp_user'] = st.text_input("SMTP username (email)", value=st.session_state.get('smtp_user', ''), key='smtp_user_input')
            st.session_state['smtp_pass'] = st.text_input("SMTP password/app password", value=st.session_state.get('smtp_pass', ''), type='password', key='smtp_pass_input')
            st.session_state['smtp_from'] = st.text_input("From email", value=st.session_state.get('smtp_from', st.session_state.get('smtp_user', '')), key='smtp_from_input')
            st.session_state['smtp_tls'] = st.checkbox("Usar TLS/STARTTLS", value=st.session_state.get('smtp_tls', True), key='smtp_tls_input')
            
        with st.expander("Configurações WhatsApp (Cloud API - Não implementado, usando WhatsApp Web)"):
            st.subheader("WhatsApp")
            st.warning("A arquitetura fornecida utiliza uma abordagem de WhatsApp Web (Selenium) que é instável e não recomendada para produção. Para fins de demonstração, as configurações abaixo não são usadas pelo `reminders_service.py` mas são mantidas para uma futura migração para a Cloud API.")
            st.session_state['wa_token'] = st.text_input("WhatsApp Cloud API Token", value=st.session_state.get('wa_token', ''), type='password', key='wa_token_input')
            st.session_state['wa_phone_id'] = st.text_input("WhatsApp Phone Number ID", value=st.session_state.get('wa_phone_id', ''), key='wa_phone_id_input')
            
        if st.form_submit_button("Salvar Configurações"):
            save_settings()
            st.success("Configurações salvas na sessão.")
            
    # 2. Botões de Teste fora do Form (para evitar o erro de contexto)
    # Recriar smtp_cfg e wa_cfg fora do form para que os botões de teste possam usá-los
    smtp_cfg = {
        "host": st.session_state.get('smtp_host', 'smtp.gmail.com'),
        "port": st.session_state.get('smtp_port', 587),
        "username": st.session_state.get('smtp_user', ''),
        "password": st.session_state.get('smtp_pass', ''),
        "from_email": st.session_state.get('smtp_from', st.session_state.get('smtp_user', '')),
        "use_tls": st.session_state.get('smtp_tls', True)
    }

    
    col_test1, col_test2 = st.columns(2)
    with col_test1:
        if st.button("Testar Configuração SMTP"):
            success, details = test_smtp_config(smtp_cfg)
            if success:
                st.success(f"Teste SMTP bem-sucedido! Detalhes: {details}")
            else:
                st.error(f"Falha no teste SMTP. Detalhes: {details}")
    with col_test2:
        if st.button("Testar Configuração WhatsApp"):
            success, details = test_whatsapp_config()
            if success:
                st.success(f"Teste WhatsApp bem-sucedido! Detalhes: {details}")
            else:
                st.error(f"Falha no teste WhatsApp. Detalhes: {meta# ---------------- CADASTRAR USUÁRIO ----------------}")
                                                               
elif menu == "Cadastrar Usuário":
    st.header("Cadastrar Novo Usuário")
    
    utec_options = list_utecs()
    role_options = get_all_roles()
    
    with st.form("user_form"):
        name = st.text_input("Nome Completo", max_chars=100)
        birthdate = st.date_input("Data de Nascimento", min_value=date(1900, 1, 1), max_value=date.today(), value=None)
        
        # Seleção de Função
        role_selection = st.selectbox("Função", role_options + ["Outra..."])
        if role_selection == "Outra...":
            role = st.text_input("Nova Função")
        else:
            role = role_selection
            
        # Seleção de Local (UTEC)
        utec_selection = st.selectbox("Local (UTEC)", utec_options + ["Outro..."])
        if utec_selection == "Outro...":
            utec = st.text_input("Novo Local (UTEC)")
        else:
            utec = utec_selection
            
        email = st.text_input("E-mail")
        phone = st.text_input("Telefone (com DDD, ex: 81999998888)")
        
        submitted = st.form_submit_button("Cadastrar")
        if submitted:
            if name and email and role and utec:
                user_data = {
                    "name": name,
                    "birthdate": birthdate.isoformat() if birthdate else None,
                    "role": role,
                    "utec": utec,
                    "email": email,
                    "phone": normalize_phone(phone) if phone else None
                }
                add_user(user_data)
                st.success(f"Usuário {name} cadastrado com sucesso no local {utec}!")
            else:
                st.error("Nome, E-mail, Função e Local são obrigatórios.")

# ---------------- UPLOAD DE USUÁRIOS (CSV/XLS) ----------------
elif menu == "Upload de Usuários (CSV/XLS)":
    st.header("Upload de Usuários em Massa")
    st.info("O arquivo deve conter as colunas: 'name', 'birthdate' (formato YYYY-MM-DD), 'role', 'utec', 'email', 'phone'.")
    
    uploaded_file = st.file_uploader("Escolha um arquivo CSV ou Excel", type=["csv", "xls", "xlsx"])
    
    if uploaded_file is not None:
        try:
            # Determinar o tipo de arquivo e ler
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Formato de arquivo não suportado.")
                st.stop()
                
            # Uniformizar nomes de colunas para minúsculas e remover espaços
            df.columns = df.columns.str.lower().str.strip()
            
            # Colunas esperadas
            required_cols = ['name', 'birthdate', 'role', 'utec', 'email', 'phone']
            if not all(col in df.columns for col in required_cols):
                st.error(f"O arquivo deve conter as colunas: {', '.join(required_cols)}")
                st.stop()
                
            st.subheader("Pré-visualização dos dados")
            st.dataframe(df.head())
            
            if st.button("Confirmar Cadastro em Massa"):
                count = 0
                for index, row in df.iterrows():
                    try:
                        # Normalizar dados
                        birthdate_str = str(row['birthdate'])
                        if birthdate_str and 'T' in birthdate_str: # Tratar caso de datetime vindo do Excel
                            birthdate_str = birthdate_str.split('T')[0]
                            
                        user_data = {
                            "name": row['name'],
                            "birthdate": birthdate_str if birthdate_str else None,
                            "role": row['role'],
                            "utec": row['utec'],
                            "email": row['email'],
                            "phone": normalize_phone(str(row['phone'])) if row['phone'] else None
                        }
                        
                        # Validação básica
                        if user_data['name'] and user_data['email']:
                            add_user(user_data)
                            count += 1
                        else:
                            st.warning(f"Linha {index+2} ignorada: Nome ou E-mail ausente.")
                            
                    except Exception as e:
                        st.error(f"Erro ao processar a linha {index+2}: {e}")
                        
                st.success(f"Processamento concluído. {count} usuários cadastrados com sucesso!")
                st.experimental_rerun()
                
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
    st.header("Cadastrar Novo Usuário")
    
    utec_options = list_utecs()
    role_options = get_all_roles()
    
    with st.form("user_form"):
        name = st.text_input("Nome Completo", max_chars=100)
        birthdate = st.date_input("Data de Nascimento", min_value=date(1900, 1, 1), max_value=date.today(), value=None)
        
        # Seleção de Função
        role_selection = st.selectbox("Função", role_options + ["Outra..."])
        if role_selection == "Outra...":
            role = st.text_input("Nova Função")
        else:
            role = role_selection
            
        # Seleção de Local (UTEC)
        utec_selection = st.selectbox("Local (UTEC)", utec_options + ["Outro..."])
        if utec_selection == "Outro...":
            utec = st.text_input("Novo Local (UTEC)")
        else:
            utec = utec_selection
            
        email = st.text_input("E-mail")
        phone = st.text_input("Telefone (com DDD, ex: 81999998888)")
        
        submitted = st.form_submit_button("Cadastrar")
        if submitted:
            if name and email and role and utec:
                user_data = {
                    "name": name,
                    "birthdate": birthdate.isoformat() if birthdate else None,
                    "role": role,
                    "utec": utec,
                    "email": email,
                    "phone": normalize_phone(phone) if phone else None
                }
                add_user(user_data)
                st.success(f"Usuário {name} cadastrado com sucesso no local {utec}!")
      # ---------------- CRIAR LEMBRETE ----------------
elif menu == "Criar Lembrete":
    st.header("Criar Novo Lembrete")
    
    users = list_users()
    user_options = {u['name']: u['id'] for u in users}
    utec_options = list_utecs()
    role_options = get_all_roles()
    
    if not users:
        st.warning("Nenhum usuário cadastrado. Cadastre um usuário primeiro.")
    else:
        with st.form("reminder_form"):
            
            # Opções de seleção de destinatários
            recipient_type = st.radio("Destinatário", ["Usuário Específico", "Todos os Usuários", "Por Local (UTEC)", "Por Função"])
            
            user_id = None
            
            if recipient_type == "Usuário Específico":
                selected_user_name = st.selectbox("Selecione o Usuário", list(user_options.keys()))
                user_id = user_options[selected_user_name]
                
            elif recipient_type == "Todos os Usuários":
                st.info("O lembrete será enviado para todos os usuários cadastrados.")
                user_id = -1 # Marcador para todos
                
            elif recipient_type == "Por Local (UTEC)":
                selected_utec = st.selectbox("Selecione o Local (UTEC)", utec_options)
                users_in_utec = get_users_by_utec(selected_utec)
                st.info(f"O lembrete será enviado para {len(users_in_utec)} usuários em {selected_utec}.")
                user_id = -2 # Marcador para UTEC
                
            elif recipient_type == "Por Função":
                selected_role = st.selectbox("Selecione a Função", role_options)
                users_in_role = get_users_by_role(selected_role)
                st.info(f"O lembrete será enviado para {len(users_in_role)} usuários com a função {selected_role}.")
                user_id = -3 # Marcador para Função
            
            title = st.text_input("Título do Lembrete", max_chars=100)
            description = st.text_area("Descrição")
            
            col1, col2 = st.columns(2)
            with col1:
                remind_date = st.date_input("Data do Lembrete", min_value=date.today())
            with col2:
                remind_time = st.time_input("Hora do Lembrete", value=(datetime.now() + timedelta(minutes=5)).time())
            
            remind_at = datetime.combine(remind_date, remind_time).isoformat(sep=' ', timespec='minutes')
            
            channel = st.selectbox("Canal de Envio", ["email", "whatsapp", "both"])
            
            submitted = st.form_submit_button("Agendar Lembrete")
            if submitted:
                if title and description and user_id is not None:
                    
                    # Lógica para agendar o lembrete
                    if user_id > 0: # Usuário Específico
                        reminder_data = {
                            "user_id": user_id,
                            "title": title,
                            "description": description,
                            "remind_at": remind_at,
                            "channel": channel
                        }
                        add_reminder(reminder_data)
                        st.success(f"Lembrete '{title}' agendado para {selected_user_name} em {remind_at}.")
                        
                    elif user_id == -1: # Todos os Usuários
                        all_users_ids = get_all_users_ids()
                        for uid in all_users_ids:
                            reminder_data = {
                                "user_id": uid,
                                "title": title,
                                "description": description,
                                "remind_at": remind_at,
                                "channel": channel
                            }
                            add_reminder(reminder_data)
                        st.success(f"Lembrete '{title}' agendado para TODOS os {len(all_users_ids)} usuários em {remind_at}.")
                        
                    elif user_id == -2: # Por Local (UTEC)
                        for user in users_in_utec:
                            reminder_data = {
                                "user_id": user['id'],
                                "title": title,
                                "description": description,
                                "remind_at": remind_at,
                                "channel": channel
                            }
                            add_reminder(reminder_data)
                        st.success(f"Lembrete '{title}' agendado para {len(users_in_utec)} usuários em {selected_utec} em {remind_at}.")
                        
                    elif user_id == -3: # Por Função
                        for user in users_in_role:
                            reminder_data = {
                                "user_id": user['id'],
                                "title": title,
                                "description": description,
                                "remind_at": remind_at,
                                "channel": channel
                            }
                            add_reminder(reminder_data)
                        st.success(f"Lembrete '{title}' agendado para {len(users_in_role)} usuários com a função {selected_role} em {remind_at}.")
                        
                else:
                    st.error("Título, Descrição e Seleção de Destinatário são obrigatórios."# ---------------- GERENCIAR USUÁRIOS ----------------
elif menu == "Gerenciar Usuários":
    st.header("Gerenciar Usuários Cadastrados")
    
    users = list_users()
    if not users:
        st.info("Nenhum usuário cadastrado.")
        st.stop()
        
    # Converte para DataFrame para seleção
    import pandas as pd
    df_users = pd.DataFrame([dict(u) for u in users])
    df_users = df_users.set_index('id')
    
    st.dataframe(df_users)
    
    # Seleção para Edição/Exclusão
    user_ids = df_users.index.tolist()
    selected_id = st.selectbox("Selecione o ID do Usuário para Editar/Excluir", user_ids)
    
    if selected_id:
        user_to_edit = get_user_by_id(selected_id)
        
        st.subheader(f"Editar Usuário ID: {selected_id} - {user_to_edit['name']}")
        
        utec_options = list_utecs()
        role_options = get_all_roles()
        
        with st.form("edit_user_form"):
            name = st.text_input("Nome Completo", value=user_to_edit['name'], max_chars=100)
            
            # Conversão de data para objeto date para o st.date_input
            try:
                bd = datetime.fromisoformat(user_to_edit['birthdate']).date()
            except:
                bd = None
                
            birthdate = st.date_input("Data de Nascimento", min_value=date(1900, 1, 1), max_value=date.today(), value=bd)
            
            # Seleção de Função
            role_selection = st.selectbox("Função", role_options + ["Outra..."], index=role_options.index(user_to_edit['role']) if user_to_edit['role'] in role_options else len(role_options))
            if role_selection == "Outra...":
                role = st.text_input("Nova Função", value=user_to_edit['role'])
            else:
                role = role_selection
                
            # Seleção de Local (UTEC)
            utec_selection = st.selectbox("Local (UTEC)", utec_options + ["Outro..."], index=utec_options.index(user_to_edit['utec']) if user_to_edit['utec'] in utec_options else len(utec_options))
            if utec_selection == "Outro...":
                utec = st.text_input("Novo Local (UTEC)", value=user_to_edit['utec'])
            else:
                utec = utec_selection
                
            email = st.text_input("E-mail", value=user_to_edit['email'])
            phone = st.text_input("Telefone (com DDD, ex: 81999998888)", value=user_to_edit['phone'])
            
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.form_submit_button("Salvar Alterações"):
                    if name and email and role and utec:
                        user_data = {
                            "name": name,
                            "birthdate": birthdate.isoformat() if birthdate else None,
                            "role": role,
                            "utec": utec,
                            "email": email,
                            "phone": normalize_phone(phone) if phone else None
                        }
                        update_user(selected_id, user_data)
                        st.success(f"Usuário {name} (ID: {selected_id}) atualizado com sucesso!")
                        st.experimental_rerun()
                    else:
                        st.error("Nome, E-mail, Função e Local são obrigatórios.")
                        
            with col_delete:
                if st.button("Excluir Usuário", type="primary"):
                    delete_user(selected_id)
                    st.warning(f"Usuário (ID: {selected_id}) excluído com sucesso!")
                    st.experimental_rerun()
# ---------------- GERENCIAR LEMBRETES ----------------
elif menu == "Gerenciar Lembretes":
    st.header("Gerenciar Lembretes Agendados")
    
    reminders = list_reminders()
    if not reminders:
        st.info("Nenhum lembrete agendado.")
        st.stop()
        
    # Converte para DataFrame para seleção
    import pandas as pd
    df_reminders = pd.DataFrame([dict(r) for r in reminders])
    df_reminders = df_reminders.set_index('id')
    
    st.dataframe(df_reminders)
    
    # Seleção para Edição/Exclusão
    reminder_ids = df_reminders.index.tolist()
    selected_id = st.selectbox("Selecione o ID do Lembrete para Editar/Excluir", reminder_ids)
    
    if selected_id:
        reminder_to_edit = get_reminder_by_id(selected_id)
        
        st.subheader(f"Editar Lembrete ID: {selected_id} - {reminder_to_edit['title']}")
        
        users = list_users()
        user_options = {u['name']: u['id'] for u in users}
        current_user_name = get_user_by_id(reminder_to_edit['user_id'])['name'] if reminder_to_edit['user_id'] else None
        
        with st.form("edit_reminder_form"):
            
            # Usuário
            selected_user_name = st.selectbox("Usuário", list(user_options.keys()), index=list(user_options.keys()).index(current_user_name) if current_user_name else 0)
            user_id = user_options[selected_user_name]
            
            title = st.text_input("Título do Lembrete", value=reminder_to_edit['title'], max_chars=100)
            description = st.text_area("Descrição", value=reminder_to_edit['description'])
            
            # Conversão de data/hora para objetos date/time para os inputs
            try:
                dt = datetime.fromisoformat(reminder_to_edit['remind_at'])
                remind_date = dt.date()
                remind_time = dt.time()
            except:
                remind_date = date.today()
                remind_time = (datetime.now() + timedelta(minutes=5)).time()
                
            col1, col2 = st.columns(2)
            with col1:
                remind_date = st.date_input("Data do Lembrete", min_value=date.today(), value=remind_date)
            with col2:
                remind_time = st.time_input("Hora do Lembrete", value=remind_time)
            
            remind_at = datetime.combine(remind_date, remind_time).isoformat(sep=' ', timespec='minutes')
            
            channel = st.selectbox("Canal de Envio", ["email", "whatsapp", "both"], index=["email", "whatsapp", "both"].index(reminder_to_edit['channel']))
            
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.form_submit_button("Salvar Alterações"):
                    if title and description:
                        reminder_data = {
                            "user_id": user_id,
                            "title": title,
                            "description": description,
                            "remind_at": remind_at,
                            "channel": channel
                        }
                        update_reminder(selected_id, reminder_data)
                        st.success(f"Lembrete '{title}' (ID: {selected_id}) atualizado com sucesso!")
                        st.experimental_rerun()
                    else:
                        st.error("Título e Descrição são obrigatórios.")
                        
            with col_delete:
                if st.button("Excluir Lembrete", type="primary"):
                    delete_reminder(selected_id)
                    st.warning(f"Lembrete (ID: {selected_id}) excluído com sucesso!")
                    st.experimental_rerun()

# ---------------- LOGS DE ENVIO ----------------
elif menu == "Logs de Envio":
    st.header("Logs de Envio")
    # A função list_logs não foi implementada no models.py, mas o log está na tabela sent_log.
    # Para fins de demonstração, vamos ler diretamente do banco de dados (reutilizando a conexão).
    from database.connection import get_conn
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM sent_log ORDER BY sent_at DESC")
    logs = c.fetchall()
    conn.close()
    
    if logs:
        logs_list = [dict(l) for l in logs]
        st.dataframe(logs_list)
    else:
        st.info("Nenhum log de envio registrado.")

# ---------------- PROCESSAR LEMBRETES ----------------
elif menu == "Processar Lembretes":
    st.header("Processamento de Lembretes e Aniversários")
    st.warning("Este processo deve ser executado periodicamente (ex: via cron job ou serviço externo) para enviar as mensagens. A execução manual aqui é apenas para teste.")
    
    # Recuperar configurações da sessão
    smtp_cfg = {
        "host": st.session_state.get('smtp_host', 'smtp.gmail.com'),
        "port": st.session_state.get('smtp_port', 587),
        "username": st.session_state.get('smtp_user', ''),
        "password": st.session_state.get('smtp_pass', ''),
        "from_email": st.session_state.get('smtp_from', st.session_state.get('smtp_user', '')),
        "use_tls": st.session_state.get('smtp_tls', True)
    }
    

    
    if st.button("Executar Processamento de Envio"):
        st.info("Iniciando processamento...")
        
        # O serviço de WhatsApp Web (Selenium) não é adequado para ser executado dentro do Streamlit
        # em um ambiente de nuvem sem um navegador configurado.
        # Vamos simular o dry_run para evitar falhas de ambiente.
        
        # logs = check_and_send_pending(smtp_cfg, dry_run=False) # Versão real
        logs = process_reminders(smtp_cfg, dry_run=True) # Versão Dry Run para Streamlit
        
        if logs:
            st.success(f"Processamento concluído. {len(logs)} ações registradas (Dry Run).")
            st.dataframe([dict(l) for l in logs])
        else:
            st.info("Processamento concluído. Nenhuma mensagem pendente encontrada.")
            
        st.warning("A execução real (sem Dry Run) do WhatsApp Web (Selenium) pode falhar em ambientes de nuvem. Considere migrar para a Cloud API ou um serviço de envio mais robusto.")