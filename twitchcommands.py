import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
import socket
import time
from datetime import datetime
from tkinter import PhotoImage


class TwitchChatBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Twitch Chat Manager")
        self.root.geometry("700x700")
        self.root.minsize(650, 600)
        self.root.configure(bg='#0e0e10')

        try:
            icon = PhotoImage(file="icon.png")  # путь к твоему файлу
            self.root.iconphoto(False, icon)
        except Exception as e:
            print("Не удалось загрузить иконку:", e)

        # Настройка стилей
        self.setup_styles()

        # Переменные для подключения
        self.connected = False
        self.socket = None
        self.bot_thread = None
        self.stop_bot = False

        self.auto_messages_enabled = False
        self.auto_messages_thread = None
        self.stop_auto_messages = False

        # Загрузка конфигурации
        self.config = self.load_config()
        self.commands = self.load_commands()
        self.auto_messages = self.load_auto_messages()

        self.ensure_default_commands()

        # Создание интерфейса
        self.create_interface()

        # Привязка события закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.center_window()

    def ensure_default_commands(self):
        """Обеспечивает наличие команды !commands по умолчанию"""
        if 'commands' not in self.commands:
            self.commands['commands'] = {
                'response': 'Доступные команды: !commands',
                'usage_count': 0,
                'is_default': True
            }
            self.save_commands()

    def get_commands_list(self):
        """Возвращает список всех доступных команд"""
        if not self.commands:
            return "Команды не настроены. Добавьте команды через интерфейс!"

        command_list = []
        for command in sorted(self.commands.keys()):
            command_list.append(f"!{command}")

        return f"Доступные команды: {', '.join(command_list)}"

    def setup_styles(self):
        """Настройка стилей для современного вида"""
        style = ttk.Style()
        style.theme_use('clam')

        # Настройка цветов в стиле Twitch
        style.configure('Title.TLabel',
                        background='#0e0e10',
                        foreground='#ffffff',
                        font=('Segoe UI', 16, 'bold'))

        style.configure('Subtitle.TLabel',
                        background='#18181b',
                        foreground='#adadb8',
                        font=('Segoe UI', 10))

        style.configure('Custom.TButton',
                        background='#9146ff',
                        foreground='white',
                        font=('Segoe UI', 9, 'bold'),
                        borderwidth=0,
                        focuscolor='none')

        style.map('Custom.TButton',
                  background=[('active', '#772ce8'), ('pressed', '#5c1ec7')])

        style.configure('Success.TButton',
                        background='#00f593',
                        foreground='white',
                        font=('Segoe UI', 9, 'bold'),
                        borderwidth=0,
                        focuscolor='none')

        style.map('Success.TButton',
                  background=[('active', '#00d084'), ('pressed', '#00b86b')])

        style.configure('Danger.TButton',
                        background='#f13c20',
                        foreground='white',
                        font=('Segoe UI', 9, 'bold'),
                        borderwidth=0,
                        focuscolor='none')

        style.map('Danger.TButton',
                  background=[('active', '#d32f2f'), ('pressed', '#b71c1c')])

        style.configure('TNotebook',
                        background='#0e0e10',
                        borderwidth=0)

        style.configure('TNotebook.Tab',
                        background='#18181b',
                        foreground='#adadb8',
                        padding=[15, 10],
                        font=('Segoe UI', 9, 'bold'))

        style.map('TNotebook.Tab',
                  background=[('selected', '#9146ff'), ('active', '#772ce8')],
                  foreground=[('selected', 'white'), ('active', 'white')])

    def create_interface(self):
        """Создание основного интерфейса"""
        main_frame = tk.Frame(self.root, bg='#0e0e10')
        main_frame.pack(fill='both', expand=True)

        # Заголовок с современным дизайном
        header_frame = tk.Frame(main_frame, bg='#0e0e10')
        header_frame.pack(fill='x', pady=(0, 20))

        # Создание notebook для вкладок с современным дизайном
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)

        # Вкладка подключения
        self.create_connection_tab()

        # Вкладка команд
        self.create_commands_tab()

        self.create_auto_messages_tab()

        # Вкладка логов
        self.create_logs_tab()

    def create_connection_tab(self):
        """Создание вкладки подключения"""
        connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(connection_frame, text="🔗 Подключение")

        main_container = tk.Frame(connection_frame, bg='#0e0e10')
        main_container.pack(fill='both', expand=True)

        content_frame = tk.Frame(main_container, bg='#0e0e10')
        content_frame.pack(fill='both', expand=True)

        # Левая колонка - настройки и статус
        left_column = tk.Frame(content_frame, bg='#0e0e10')
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Правая колонка - инструкции
        right_column = tk.Frame(content_frame, bg='#0e0e10')
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0))

        # Карточка настроек в левой колонке
        settings_card = tk.Frame(left_column, bg='#18181b', relief='flat', bd=0)
        settings_card.pack(fill='x', pady=(0, 15))

        card_content = tk.Frame(settings_card, bg='#18181b')
        card_content.pack(fill='x', padx=20, pady=20)

        # Заголовок настроек
        tk.Label(card_content, text="⚙️ Настройки подключения", bg='#18181b', fg='#ffffff',
                 font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 15))

        # OAuth токен
        tk.Label(card_content, text="🔑 OAuth токен:", bg='#18181b', fg='#adadb8',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        self.oauth_var = tk.StringVar(value=self.config.get('oauth_token', ''))
        oauth_entry = tk.Entry(card_content, textvariable=self.oauth_var,
                               font=('Segoe UI', 10), bg='#26262c', fg='white',
                               insertbackground='#9146ff', relief='flat', bd=0,
                               highlightthickness=2, highlightcolor='#9146ff',
                               highlightbackground='#3a3a3d')
        oauth_entry.pack(fill='x', pady=(0, 15), ipady=8)
        self.setup_paste_support(oauth_entry)

        # Канал
        tk.Label(card_content, text="📺 Канал:", bg='#18181b', fg='#adadb8',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        self.channel_var = tk.StringVar(value=self.config.get('channel', ''))
        channel_entry = tk.Entry(card_content, textvariable=self.channel_var,
                                 font=('Segoe UI', 10), bg='#26262c', fg='white',
                                 insertbackground='#9146ff', relief='flat', bd=0,
                                 highlightthickness=2, highlightcolor='#9146ff',
                                 highlightbackground='#3a3a3d')
        channel_entry.pack(fill='x', pady=(0, 20), ipady=8)
        self.setup_paste_support(channel_entry)

        # Кнопки управления
        buttons_frame = tk.Frame(card_content, bg='#18181b')
        buttons_frame.pack(fill='x')

        self.connect_btn = ttk.Button(buttons_frame, text="🚀 Подключиться",
                                      command=self.toggle_connection, style='Success.TButton')
        self.connect_btn.pack(side='left', padx=(0, 10))

        ttk.Button(buttons_frame, text="💾 Сохранить",
                   command=self.save_config, style='Custom.TButton').pack(side='left')

        # Статус подключения в левой колонке
        status_card = tk.Frame(left_column, bg='#18181b', relief='flat', bd=0)
        status_card.pack(fill='x')

        status_content = tk.Frame(status_card, bg='#18181b')
        status_content.pack(fill='x', padx=20, pady=20)

        tk.Label(status_content, text="📊 Статус подключения", bg='#18181b', fg='#ffffff',
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 8))

        self.status_label = tk.Label(status_content, text="⭕ Не подключен",
                                     bg='#18181b', fg='#f13c20', font=('Segoe UI', 10, 'bold'))
        self.status_label.pack(anchor='w')

        # Инструкция в правой колонке
        instruction_card = tk.Frame(right_column, bg='#18181b', relief='flat', bd=0)
        instruction_card.pack(fill='both', expand=True)

        instruction_content = tk.Frame(instruction_card, bg='#18181b')
        instruction_content.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(instruction_content, text="📋 Как получить токен", bg='#18181b', fg='#ffffff',
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 12))

        instructions = [
            "1. Перейдите на сайт:",
            "   twitchtokengenerator.com",
            "",
            "2. Нажмите кнопку 'Generate Token'",
            "",
            "3. Авторизуйтесь через Twitch",
            "",
            "4. Скопируйте ACCESS TOKEN",
            "   (первый зеленый токен)",
            "",
            "5. Вставьте токен в поле oAuth токен",
            "   и укажите канал"
        ]

        for instruction in instructions:
            if instruction == "":
                # Добавляем небольшой отступ между пунктами
                tk.Frame(instruction_content, bg='#18181b', height=3).pack(fill='x')
            else:
                tk.Label(instruction_content, text=instruction, bg='#18181b', fg='#adadb8',
                         font=('Segoe UI', 9), justify='left').pack(anchor='w', pady=1)

    def create_commands_tab(self):
        """Создание вкладки команд"""
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="⚡ Команды")

        main_container = tk.Frame(commands_frame, bg='#0e0e10')
        main_container.pack(fill='both', expand=True)

        # Заголовок и кнопки управления
        header_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        header_card.pack(fill='x', pady=(0, 15))

        header_content = tk.Frame(header_card, bg='#18181b')
        header_content.pack(fill='x', padx=20, pady=15)

        tk.Label(header_content, text="⚡ Управление командами", bg='#18181b', fg='#ffffff',
                 font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 12))

        buttons_frame = tk.Frame(header_content, bg='#18181b')
        buttons_frame.pack(fill='x')

        ttk.Button(buttons_frame, text="➕ Добавить",
                   command=self.add_command, style='Success.TButton').pack(side='left', padx=(0, 8))

        ttk.Button(buttons_frame, text="✏️ Изменить",
                   command=self.edit_command, style='Custom.TButton').pack(side='left', padx=(0, 8))

        ttk.Button(buttons_frame, text="🗑️ Удалить",
                   command=self.delete_command, style='Danger.TButton').pack(side='left')

        # Список команд в современном стиле
        list_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        list_card.pack(fill='both', expand=True)

        list_content = tk.Frame(list_card, bg='#18181b')
        list_content.pack(fill='both', expand=True, padx=20, pady=20)

        # Создание Treeview с современным стилем
        columns = ('Команда', 'Ответ', 'Использований')
        self.commands_tree = ttk.Treeview(list_content, columns=columns, show='headings', height=18)

        # Настройка стиля Treeview
        style = ttk.Style()
        style.configure('Treeview',
                        background='#26262c',
                        foreground='white',
                        fieldbackground='#26262c',
                        font=('Segoe UI', 9))
        style.configure('Treeview.Heading',
                        background='#9146ff',
                        foreground='white',
                        font=('Segoe UI', 10, 'bold'))

        # Настройка заголовков
        self.commands_tree.heading('Команда', text='🎯 Команда')
        self.commands_tree.heading('Ответ', text='💬 Ответ')
        self.commands_tree.heading('Использований', text='📊 Счетчик')

        self.commands_tree.column('Команда', width=150)
        self.commands_tree.column('Ответ', width=350)
        self.commands_tree.column('Использований', width=100)

        # Скроллбар с современным стилем
        scrollbar = ttk.Scrollbar(list_content, orient='vertical', command=self.commands_tree.yview)
        self.commands_tree.configure(yscrollcommand=scrollbar.set)

        # Размещение элементов
        self.commands_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Загрузка команд в список
        self.refresh_commands_list()

    def create_auto_messages_tab(self):
        """Создание вкладки автосообщений"""
        auto_messages_frame = ttk.Frame(self.notebook)
        self.notebook.add(auto_messages_frame, text="⏰ Автосообщения")

        main_container = tk.Frame(auto_messages_frame, bg='#0e0e10')
        main_container.pack(fill='both', expand=True)

        # Заголовок и управление
        header_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        header_card.pack(fill='x', pady=(0, 15))

        header_content = tk.Frame(header_card, bg='#18181b')
        header_content.pack(fill='x', padx=20, pady=15)

        tk.Label(header_content, text="⏰ Автоматические сообщения", bg='#18181b', fg='#ffffff',
                 font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(0, 12))

        # Управление автосообщениями
        control_frame = tk.Frame(header_content, bg='#18181b')
        control_frame.pack(fill='x', pady=(0, 15))

        self.auto_messages_status_label = tk.Label(control_frame, text="⭕ Остановлено",
                                                   bg='#18181b', fg='#f13c20',
                                                   font=('Segoe UI', 10, 'bold'))
        self.auto_messages_status_label.pack(side='left')

        self.toggle_auto_messages_btn = ttk.Button(control_frame, text="▶️ Запустить",
                                                   command=self.toggle_auto_messages,
                                                   style='Success.TButton')
        self.toggle_auto_messages_btn.pack(side='right', padx=(0, 10))

        # Кнопки управления сообщениями
        buttons_frame = tk.Frame(header_content, bg='#18181b')
        buttons_frame.pack(fill='x')

        ttk.Button(buttons_frame, text="➕ Добавить",
                   command=self.add_auto_message, style='Success.TButton').pack(side='left', padx=(0, 8))

        ttk.Button(buttons_frame, text="✏️ Изменить",
                   command=self.edit_auto_message, style='Custom.TButton').pack(side='left', padx=(0, 8))

        ttk.Button(buttons_frame, text="🗑️ Удалить",
                   command=self.delete_auto_message, style='Danger.TButton').pack(side='left')

        # Список автосообщений
        list_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        list_card.pack(fill='both', expand=True)

        list_content = tk.Frame(list_card, bg='#18181b')
        list_content.pack(fill='both', expand=True, padx=20, pady=20)

        # Создание Treeview для автосообщений
        columns = ('Сообщение', 'Интервал (мин)', 'Статус', 'Отправлено')
        self.auto_messages_tree = ttk.Treeview(list_content, columns=columns, show='headings', height=15)

        # Настройка заголовков
        self.auto_messages_tree.heading('Сообщение', text='💬 Сообщение')
        self.auto_messages_tree.heading('Интервал (мин)', text='⏱️ Интервал')
        self.auto_messages_tree.heading('Статус', text='📊 Статус')
        self.auto_messages_tree.heading('Отправлено', text='📈 Отправлено')

        self.auto_messages_tree.column('Сообщение', width=300)
        self.auto_messages_tree.column('Интервал (мин)', width=100)
        self.auto_messages_tree.column('Статус', width=80)
        self.auto_messages_tree.column('Отправлено', width=80)

        # Скроллбар
        auto_scrollbar = ttk.Scrollbar(list_content, orient='vertical', command=self.auto_messages_tree.yview)
        self.auto_messages_tree.configure(yscrollcommand=auto_scrollbar.set)

        # Размещение элементов
        self.auto_messages_tree.pack(side='left', fill='both', expand=True)
        auto_scrollbar.pack(side='right', fill='y')

        # Загрузка автосообщений в список
        self.refresh_auto_messages_list()

    def create_logs_tab(self):
        """Создание вкладки логов"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📝 Логи")

        main_container = tk.Frame(logs_frame, bg='#0e0e10')
        main_container.pack(fill='both', expand=True)

        # Заголовок и кнопка очистки
        header_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        header_card.pack(fill='x', pady=(0, 15))

        header_content = tk.Frame(header_card, bg='#18181b')
        header_content.pack(fill='x', padx=20, pady=15)

        header_frame = tk.Frame(header_content, bg='#18181b')
        header_frame.pack(fill='x')

        tk.Label(header_frame, text="📝 Журнал событий", bg='#18181b', fg='#ffffff',
                 font=('Segoe UI', 12, 'bold')).pack(side='left')

        ttk.Button(header_frame, text="🗑️ Очистить",
                   command=self.clear_logs, style='Danger.TButton').pack(side='right')

        # Область логов с современным дизайном
        logs_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        logs_card.pack(fill='both', expand=True)

        logs_content = tk.Frame(logs_card, bg='#18181b')
        logs_content.pack(fill='both', expand=True, padx=20, pady=20)

        self.logs_text = scrolledtext.ScrolledText(logs_content, height=22, width=80,
                                                   bg='#26262c', fg='#ffffff',
                                                   font=('Consolas', 9),
                                                   insertbackground='#9146ff',
                                                   selectbackground='#9146ff',
                                                   selectforeground='white',
                                                   relief='flat', bd=0)
        self.logs_text.pack(fill='both', expand=True)

        # Добавление начального сообщения
        self.add_log("🚀 Приложение запущено")

    def load_config(self):
        """Загрузка конфигурации"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.add_log(f"Ошибка загрузки конфигурации: {e}")
        return {}

    def save_config(self):
        """Сохранение конфигурации"""
        try:
            config = {
                'oauth_token': self.oauth_var.get(),
                'channel': self.channel_var.get()
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", "Настройки сохранены!")
            self.add_log("Настройки сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
            self.add_log(f"Ошибка сохранения настроек: {e}")

    def load_commands(self):
        """Загрузка команд"""
        try:
            if os.path.exists('commands.json'):
                with open('commands.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.add_log(f"Ошибка загрузки команд: {e}")
        return {}

    def save_commands(self):
        """Сохранение команд"""
        try:
            with open('commands.json', 'w', encoding='utf-8') as f:
                json.dump(self.commands, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.add_log(f"Ошибка сохранения команд: {e}")

    def load_auto_messages(self):
        """Загрузка автосообщений"""
        try:
            if os.path.exists('auto_messages.json'):
                with open('auto_messages.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.add_log(f"Ошибка загрузки автосообщений: {e}")
        return {}

    def save_auto_messages(self):
        """Сохранение автосообщений"""
        try:
            with open('auto_messages.json', 'w', encoding='utf-8') as f:
                json.dump(self.auto_messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.add_log(f"Ошибка сохранения автосообщений: {e}")

    def refresh_commands_list(self):
        """Обновление списка команд"""
        # Очистка списка
        for item in self.commands_tree.get_children():
            self.commands_tree.delete(item)

        # Добавление команд
        for command, data in self.commands.items():
            response = data.get('response', '')
            usage_count = data.get('usage_count', 0)
            self.commands_tree.insert('', 'end', values=(command, response, usage_count))

    def refresh_auto_messages_list(self):
        """Обновление списка автосообщений"""
        # Очистка списка
        for item in self.auto_messages_tree.get_children():
            self.auto_messages_tree.delete(item)

        # Добавление автосообщений
        for msg_id, data in self.auto_messages.items():
            message = data.get('message', '')[:50] + ('...' if len(data.get('message', '')) > 50 else '')
            interval = data.get('interval', 0)
            enabled = "✅ Вкл" if data.get('enabled', True) else "❌ Выкл"
            sent_count = data.get('sent_count', 0)
            self.auto_messages_tree.insert('', 'end', values=(message, interval, enabled, sent_count))

    def add_command(self):
        """Добавление новой команды"""
        self.command_dialog()

    def edit_command(self):
        """Редактирование команды"""
        selected = self.commands_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите команду для редактирования")
            return

        item = self.commands_tree.item(selected[0])
        command = item['values'][0]
        self.command_dialog(command)

    def delete_command(self):
        """Удаление команды"""
        selected = self.commands_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите команду для удаления")
            return

        item = self.commands_tree.item(selected[0])
        command = item['values'][0]

        if command == 'commands':
            messagebox.showwarning("Предупреждение", "Команда !commands является системной и не может быть удалена")
            return

        if messagebox.askyesno("Подтверждение", f"Удалить команду '{command}'?"):
            del self.commands[command]
            self.save_commands()
            self.refresh_commands_list()
            self.add_log(f"Команда '{command}' удалена")

    def add_auto_message(self):
        """Добавление нового автосообщения"""
        self.auto_message_dialog()

    def edit_auto_message(self):
        """Редактирование автосообщения"""
        selected = self.auto_messages_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите автосообщение для редактирования")
            return

        # Получаем индекс выбранного элемента
        item_index = self.auto_messages_tree.index(selected[0])
        msg_id = list(self.auto_messages.keys())[item_index]
        self.auto_message_dialog(msg_id)

    def delete_auto_message(self):
        """Удаление автосообщения"""
        selected = self.auto_messages_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите автосообщение для удаления")
            return

        item_index = self.auto_messages_tree.index(selected[0])
        msg_id = list(self.auto_messages.keys())[item_index]

        if messagebox.askyesno("Подтверждение", "Удалить выбранное автосообщение?"):
            del self.auto_messages[msg_id]
            self.save_auto_messages()
            self.refresh_auto_messages_list()
            self.add_log(f"Автосообщение удалено")

    def command_dialog(self, edit_command=None):
        """Диалог добавления/редактирования команды"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить команду" if not edit_command else "Редактировать команду")
        dialog.geometry("450x400")
        dialog.configure(bg='#0e0e10')
        dialog.resizable(False, False)

        # Центрирование окна
        dialog.transient(self.root)
        dialog.grab_set()

        # Основной контейнер
        main_container = tk.Frame(dialog, bg='#0e0e10')
        main_container.pack(fill='both', expand=True)

        # Карточка диалога
        dialog_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        dialog_card.pack(fill='both', expand=True)

        card_content = tk.Frame(dialog_card, bg='#18181b')
        card_content.pack(fill='both', expand=True, padx=20, pady=20)

        # Заголовок
        title_text = "➕ Добавить новую команду" if not edit_command else f"✏️ Редактировать команду '{edit_command}'"
        title_label = tk.Label(card_content, text=title_text, bg='#18181b', fg='#ffffff',
                               font=('Segoe UI', 12, 'bold'))
        title_label.pack(pady=(0, 20))

        # Поля ввода с современным дизайном
        tk.Label(card_content, text="🎯 Команда (без !):", bg='#18181b', fg='#adadb8',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        command_var = tk.StringVar(value=edit_command if edit_command else '')
        command_entry = tk.Entry(card_content, textvariable=command_var,
                                 font=('Segoe UI', 10), bg='#26262c', fg='white',
                                 insertbackground='#9146ff', relief='flat', bd=0,
                                 highlightthickness=2, highlightcolor='#9146ff',
                                 highlightbackground='#3a3a3d')
        command_entry.pack(fill='x', pady=(0, 15), ipady=8)
        self.setup_paste_support(command_entry)

        tk.Label(card_content, text="💬 Ответ бота:", bg='#18181b', fg='#adadb8',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        response_text = tk.Text(card_content, width=45, height=5,
                                font=('Segoe UI', 10), bg='#26262c', fg='white',
                                insertbackground='#9146ff', relief='flat', bd=0, wrap='word',
                                highlightthickness=2, highlightcolor='#9146ff',
                                highlightbackground='#3a3a3d')
        response_text.pack(fill='x', pady=(0, 20))
        self.setup_text_paste_support(response_text)

        # Кнопки с современным дизайном
        buttons_frame = tk.Frame(card_content, bg='#18181b', height=50)
        buttons_frame.pack(fill='x', pady=(15, 0))
        buttons_frame.pack_propagate(False)

        def save_command():
            command = command_var.get().strip()
            response = response_text.get('1.0', 'end-1c').strip()

            if not command:
                messagebox.showwarning("Предупреждение", "Введите название команды")
                command_entry.focus()
                return

            if not response:
                messagebox.showwarning("Предупреждение", "Введите ответ бота")
                response_text.focus()
                return

            # Сохранение команды
            if command not in self.commands:
                self.commands[command] = {'usage_count': 0}

            self.commands[command]['response'] = response
            self.save_commands()
            self.refresh_commands_list()

            action = "обновлена" if edit_command else "добавлена"
            self.add_log(f"✅ Команда '{command}' {action}")
            messagebox.showinfo("Успех", f"Команда '{command}' успешно {action}!")
            dialog.destroy()

        def cancel_dialog():
            dialog.destroy()

        # Современные кнопки с градиентным эффектом
        save_btn = tk.Button(buttons_frame, text="💾 Сохранить",
                             command=save_command, bg='#00f593', fg='white',
                             font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
                             padx=25, pady=10, cursor='hand2')
        save_btn.pack(side='right', padx=(10, 0))

        cancel_btn = tk.Button(buttons_frame, text="❌ Отмена",
                               command=cancel_dialog, bg='#f13c20', fg='white',
                               font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
                               padx=25, pady=10, cursor='hand2')
        cancel_btn.pack(side='right')

        # Эффекты наведения
        def on_save_enter(e):
            save_btn.config(bg='#00d084')

        def on_save_leave(e):
            save_btn.config(bg='#00f593')

        def on_cancel_enter(e):
            cancel_btn.config(bg='#d32f2f')

        def on_cancel_leave(e):
            cancel_btn.config(bg='#f13c20')

        save_btn.bind('<Enter>', on_save_enter)
        save_btn.bind('<Leave>', on_save_leave)
        cancel_btn.bind('<Enter>', on_cancel_enter)
        cancel_btn.bind('<Leave>', on_cancel_leave)

        # Фокус на поле команды
        command_entry.focus()

        # Горячие клавиши
        def on_enter_key(event):
            save_command()

        def on_escape_key(event):
            cancel_dialog()

        dialog.bind('<Return>', on_enter_key)
        dialog.bind('<Escape>', on_escape_key)

    def auto_message_dialog(self, edit_msg_id=None):
        """Диалог добавления/редактирования автосообщения"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить автосообщение" if not edit_msg_id else "Редактировать автосообщение")
        dialog.geometry("500x450")
        dialog.configure(bg='#0e0e10')
        dialog.resizable(False, False)

        # Центрирование окна
        dialog.transient(self.root)
        dialog.grab_set()

        # Основной контейнер
        main_container = tk.Frame(dialog, bg='#0e0e10')
        main_container.pack(fill='both', expand=True)

        # Карточка диалога
        dialog_card = tk.Frame(main_container, bg='#18181b', relief='flat', bd=0)
        dialog_card.pack(fill='both', expand=True)

        card_content = tk.Frame(dialog_card, bg='#18181b')
        card_content.pack(fill='both', expand=True, padx=20, pady=20)

        # Заголовок
        title_text = "➕ Добавить автосообщение" if not edit_msg_id else "✏️ Редактировать автосообщение"
        title_label = tk.Label(card_content, text=title_text, bg='#18181b', fg='#ffffff',
                               font=('Segoe UI', 12, 'bold'))
        title_label.pack(pady=(0, 20))

        # Поля ввода
        tk.Label(card_content, text="💬 Текст сообщения:", bg='#18181b', fg='#adadb8',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        message_text = tk.Text(card_content, width=50, height=4,
                               font=('Segoe UI', 10), bg='#26262c', fg='white',
                               insertbackground='#9146ff', relief='flat', bd=0, wrap='word',
                               highlightthickness=2, highlightcolor='#9146ff',
                               highlightbackground='#3a3a3d')
        message_text.pack(fill='x', pady=(0, 15))
        self.setup_text_paste_support(message_text)

        tk.Label(card_content, text="⏱️ Интервал (минуты):", bg='#18181b', fg='#adadb8',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        interval_var = tk.StringVar(value='5')
        interval_entry = tk.Entry(card_content, textvariable=interval_var,
                                  font=('Segoe UI', 10), bg='#26262c', fg='white',
                                  insertbackground='#9146ff', relief='flat', bd=0,
                                  highlightthickness=2, highlightcolor='#9146ff',
                                  highlightbackground='#3a3a3d')
        interval_entry.pack(fill='x', pady=(0, 15), ipady=8)
        self.setup_paste_support(interval_entry)

        # Чекбокс активности
        enabled_var = tk.BooleanVar(value=True)
        enabled_check = tk.Checkbutton(card_content, text="✅ Включить автосообщение",
                                       variable=enabled_var, bg='#18181b', fg='#adadb8',
                                       selectcolor='#26262c', activebackground='#18181b',
                                       activeforeground='#ffffff', font=('Segoe UI', 10))
        enabled_check.pack(anchor='w', pady=(0, 20))

        # Если редактируем, заполняем поля
        if edit_msg_id and edit_msg_id in self.auto_messages:
            data = self.auto_messages[edit_msg_id]
            message_text.insert('1.0', data.get('message', ''))
            interval_var.set(str(data.get('interval', 5)))
            enabled_var.set(data.get('enabled', True))

        # Кнопки
        buttons_frame = tk.Frame(card_content, bg='#18181b', height=50)
        buttons_frame.pack(fill='x', pady=(15, 0))
        buttons_frame.pack_propagate(False)

        def save_auto_message():
            message = message_text.get('1.0', 'end-1c').strip()
            try:
                interval = int(interval_var.get())
            except ValueError:
                messagebox.showwarning("Предупреждение", "Интервал должен быть числом")
                interval_entry.focus()
                return

            if not message:
                messagebox.showwarning("Предупреждение", "Введите текст сообщения")
                message_text.focus()
                return

            if interval < 1:
                messagebox.showwarning("Предупреждение", "Интервал должен быть больше 0")
                interval_entry.focus()
                return

            # Создаем ID для сообщения
            if edit_msg_id:
                msg_id = edit_msg_id
            else:
                msg_id = str(int(time.time()))

            # Сохранение автосообщения
            self.auto_messages[msg_id] = {
                'message': message,
                'interval': interval,
                'enabled': enabled_var.get(),
                'sent_count': self.auto_messages.get(msg_id, {}).get('sent_count', 0),
                'last_sent': 0
            }

            self.save_auto_messages()
            self.refresh_auto_messages_list()

            action = "обновлено" if edit_msg_id else "добавлено"
            self.add_log(f"✅ Автосообщение {action}")
            messagebox.showinfo("Успех", f"Автосообщение успешно {action}!")
            dialog.destroy()

        def cancel_dialog():
            dialog.destroy()

        # Кнопки сохранения и отмены
        save_btn = tk.Button(buttons_frame, text="💾 Сохранить",
                             command=save_auto_message, bg='#00f593', fg='white',
                             font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
                             padx=25, pady=10, cursor='hand2')
        save_btn.pack(side='right', padx=(10, 0))

        cancel_btn = tk.Button(buttons_frame, text="❌ Отмена",
                               command=cancel_dialog, bg='#f13c20', fg='white',
                               font=('Segoe UI', 10, 'bold'), relief='flat', bd=0,
                               padx=25, pady=10, cursor='hand2')
        cancel_btn.pack(side='right')

        # Эффекты наведения
        def on_save_enter(e):
            save_btn.config(bg='#00d084')

        def on_save_leave(e):
            save_btn.config(bg='#00f593')

        def on_cancel_enter(e):
            cancel_btn.config(bg='#d32f2f')

        def on_cancel_leave(e):
            cancel_btn.config(bg='#f13c20')

        save_btn.bind('<Enter>', on_save_enter)
        save_btn.bind('<Leave>', on_save_leave)
        cancel_btn.bind('<Enter>', on_cancel_enter)
        cancel_btn.bind('<Leave>', on_cancel_leave)

        # Фокус на поле сообщения
        message_text.focus()

        # Горячие клавиши
        def on_enter_key(event):
            save_auto_message()

        def on_escape_key(event):
            cancel_dialog()

        dialog.bind('<Return>', on_enter_key)
        dialog.bind('<Escape>', on_escape_key)

    def toggle_auto_messages(self):
        """Переключение автосообщений"""
        if not self.connected:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к Twitch!")
            return

        if not self.auto_messages:
            messagebox.showwarning("Предупреждение", "Добавьте хотя бы одно автосообщение!")
            return

        if self.auto_messages_enabled:
            self.stop_auto_messages_func()
        else:
            self.start_auto_messages_func()

    def start_auto_messages_func(self):
        """Запуск автосообщений"""
        self.auto_messages_enabled = True
        self.stop_auto_messages = False

        # Запуск потока автосообщений
        self.auto_messages_thread = threading.Thread(target=self.auto_messages_loop, daemon=True)
        self.auto_messages_thread.start()

        self.auto_messages_status_label.config(text="🟢 Запущено", fg='#00f593')
        self.toggle_auto_messages_btn.config(text="⏸️ Остановить", style='Danger.TButton')

        self.add_log("🚀 Автосообщения запущены")

    def stop_auto_messages_func(self):
        """Остановка автосообщений"""
        self.auto_messages_enabled = False
        self.stop_auto_messages = True

        self.auto_messages_status_label.config(text="⭕ Остановлено", fg='#f13c20')
        self.toggle_auto_messages_btn.config(text="▶️ Запустить", style='Success.TButton')

        self.add_log("⏸️ Автосообщения остановлены")

    def auto_messages_loop(self):
        """Основной цикл автосообщений"""
        while not self.stop_auto_messages and self.auto_messages_enabled:
            try:
                current_time = time.time()

                for msg_id, data in self.auto_messages.items():
                    if not data.get('enabled', True):
                        continue

                    interval_seconds = data.get('interval', 5) * 60  # Конвертируем минуты в секунды
                    last_sent = data.get('last_sent', 0)

                    # Проверяем, пора ли отправлять сообщение
                    if current_time - last_sent >= interval_seconds:
                        if self.connected and self.socket:
                            message = data.get('message', '')
                            self.send_message(message)

                            # Обновляем статистику
                            self.auto_messages[msg_id]['last_sent'] = current_time
                            self.auto_messages[msg_id]['sent_count'] = data.get('sent_count', 0) + 1

                            self.save_auto_messages()

                            # Обновляем UI
                            self.root.after(0, self.refresh_auto_messages_list)

                            self.add_log(f"📤 Автосообщение отправлено: {message[:50]}...")

                time.sleep(10)  # Проверяем каждые 10 секунд

            except Exception as e:
                self.add_log(f"❌ Ошибка в цикле автосообщений: {e}")
                break

    def connect_to_twitch(self):
        """Подключение к Twitch"""
        oauth_token = self.oauth_var.get().strip()
        channel = self.channel_var.get().strip()

        if not all([oauth_token, channel]):
            messagebox.showerror("Ошибка", "Заполните все поля подключения")
            return

        if not oauth_token.startswith('oauth:'):
            oauth_token = f'oauth:{oauth_token}'

        try:
            self.socket = socket.socket()
            self.socket.connect(('irc.chat.twitch.tv', 6667))
            self.socket.send(f"PASS {oauth_token}\n".encode('utf-8'))
            self.socket.send(f"NICK {channel}\n".encode('utf-8'))
            self.socket.send(f"JOIN #{channel}\n".encode('utf-8'))

            self.connected = True
            self.stop_bot = False

            # Запуск потока для чтения сообщений
            self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
            self.bot_thread.start()

            self.status_label.config(text="🟢 Подключен", fg='#00f593')
            self.connect_btn.config(text="🔌 Отключиться", style='Danger.TButton')

            self.add_log(f"🚀 Подключен к каналу #{channel}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
            self.add_log(f"❌ Ошибка подключения: {e}")

    def disconnect_from_twitch(self):
        """Отключение от Twitch"""
        self.stop_bot = True
        self.connected = False

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.status_label.config(text="⭕ Не подключен", fg='#f13c20')
        self.connect_btn.config(text="🚀 Подключиться", style='Success.TButton')

        self.add_log("🔌 Отключен от Twitch")

    def toggle_connection(self):
        """Переключение состояния подключения"""
        if self.connected:
            self.disconnect_from_twitch()
        else:
            self.connect_to_twitch()

    def bot_loop(self):
        """Основной цикл бота"""
        while not self.stop_bot and self.connected:
            try:
                response = self.socket.recv(1024).decode('utf-8')

                if response.strip():
                    self.add_log(f"[DEBUG] IRC: {response.strip()}")

                if response.startswith('PING'):
                    self.socket.send("PONG\n".encode('utf-8'))
                    self.add_log("[DEBUG] Отправлен PONG")
                    continue

                if 'PRIVMSG' in response:
                    try:
                        # Более надежный парсинг IRC сообщения
                        parts = response.strip().split(' ')
                        if len(parts) >= 4:
                            # Извлекаем имя пользователя
                            username = parts[0].split('!')[0][1:] if '!' in parts[0] else parts[0][1:]

                            # Извлекаем сообщение (все после второго двоеточия)
                            message_start = response.find(':', 1)  # Находим второе двоеточие
                            if message_start != -1:
                                message = response[message_start + 1:].strip()

                                self.add_log(f"{username}: {message}")

                                if message.startswith('!'):
                                    command = message[1:].split()[0].lower()
                                    self.add_log(f"[DEBUG] Обнаружена команда: '{command}'")

                                    if command == 'commands':
                                        response_text = self.get_commands_list()
                                        self.add_log(f"[DEBUG] Генерируем список команд: {response_text}")

                                        # Отправляем ответ
                                        self.send_message(response_text)

                                        # Увеличение счетчика использований
                                        if 'commands' in self.commands:
                                            self.commands['commands']['usage_count'] += 1
                                            self.save_commands()
                                            # Обновление списка команд в UI (в основном потоке)
                                            self.root.after(0, self.refresh_commands_list)

                                        self.add_log(f"✅ Ответил на команду !commands: {response_text}")

                                    elif command in self.commands:
                                        response_text = self.commands[command]['response']
                                        self.add_log(f"[DEBUG] Найден ответ для команды '{command}': {response_text}")

                                        # Отправляем ответ
                                        self.send_message(response_text)

                                        # Увеличение счетчика использований
                                        self.commands[command]['usage_count'] += 1
                                        self.save_commands()

                                        # Обновление списка команд в UI (в основном потоке)
                                        self.root.after(0, self.refresh_commands_list)

                                        self.add_log(f"✅ Ответил на команду !{command}: {response_text}")
                                    else:
                                        self.add_log(f"[DEBUG] Команда '{command}' не найдена в списке")
                                        available_commands = list(self.commands.keys())
                                        self.add_log(f"[DEBUG] Доступные команды: {available_commands}")
                            else:
                                self.add_log("[DEBUG] Не удалось найти сообщение в IRC строке")
                        else:
                            self.add_log(f"[DEBUG] Неожиданный формат PRIVMSG: {response.strip()}")
                    except Exception as parse_error:
                        self.add_log(f"[ERROR] Ошибка парсинга сообщения: {parse_error}")
                        self.add_log(f"[ERROR] Проблемная строка: {response.strip()}")

            except Exception as e:
                if self.connected:
                    self.add_log(f"❌ Ошибка в цикле бота: {e}")
                break

            time.sleep(0.1)

    def send_message(self, message):
        """Отправка сообщения в чат"""
        if self.connected and self.socket:
            try:
                channel = self.channel_var.get().strip()
                full_message = f"PRIVMSG #{channel} :{message}\n"
                self.socket.send(full_message.encode('utf-8'))
                self.add_log(f"[DEBUG] Отправлено: {full_message.strip()}")
            except Exception as e:
                self.add_log(f"❌ Ошибка отправки сообщения: {e}")

    def add_log(self, message):
        """Добавление записи в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        # Добавление в UI (безопасно для потоков)
        self.root.after(0, lambda: self._add_log_to_ui(log_message))

    def _add_log_to_ui(self, message):
        """Добавление сообщения в UI лога"""
        self.logs_text.insert('end', message)
        self.logs_text.see('end')

    def clear_logs(self):
        """Очистка логов"""
        self.logs_text.delete('1.0', 'end')
        self.add_log("Логи очищены")

    def on_closing(self):
        """Обработка закрытия приложения"""
        if self.connected:
            self.disconnect_from_twitch()
        if self.auto_messages_enabled:
            self.stop_auto_messages_func()
        self.root.destroy()

    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

    def setup_paste_support(self, widget):
        """Настройка поддержки вставки из буфера обмена для виджета"""

        def paste_from_clipboard(event):
            try:
                # Получаем содержимое буфера обмена
                clipboard_content = self.root.clipboard_get()
                # Очищаем текущее содержимое и вставляем новое
                widget.delete(0, 'end')
                widget.insert(0, clipboard_content)
                return 'break'  # Предотвращаем стандартную обработку
            except tk.TclError:
                # Буфер обмена пуст или недоступен
                pass

        def create_context_menu(event):
            """Создание контекстного меню"""
            context_menu = tk.Menu(self.root, tearoff=0, bg='#2f2f35', fg='white',
                                   activebackground='#9146ff', activeforeground='white')

            context_menu.add_command(label="📋 Вставить",
                                     command=lambda: paste_from_clipboard(None))
            context_menu.add_separator()
            context_menu.add_command(label="✂️ Вырезать",
                                     command=lambda: widget.event_generate('<<Cut>>'))
            context_menu.add_command(label="📄 Копировать",
                                     command=lambda: widget.event_generate('<<Copy>>'))
            context_menu.add_command(label="🗑️ Очистить",
                                     command=lambda: widget.delete(0, 'end'))

            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        # Привязка горячих клавиш
        widget.bind('<Control-v>', paste_from_clipboard)
        widget.bind('<Control-V>', paste_from_clipboard)

        # Привязка правой кнопки мыши для контекстного меню
        widget.bind('<Button-3>', create_context_menu)

    def setup_text_paste_support(self, text_widget):
        """Настройка поддержки вставки для Text виджета"""

        def paste_from_clipboard(event):
            try:
                clipboard_content = self.root.clipboard_get()
                text_widget.insert('insert', clipboard_content)
                return 'break'
            except tk.TclError:
                pass

        def create_text_context_menu(event):
            """Создание контекстного меню для Text виджета"""
            context_menu = tk.Menu(self.root, tearoff=0, bg='#2f2f35', fg='white',
                                   activebackground='#9146ff', activeforeground='white')

            context_menu.add_command(label="📋 Вставить",
                                     command=lambda: paste_from_clipboard(None))
            context_menu.add_separator()
            context_menu.add_command(label="✂️ Вырезать",
                                     command=lambda: text_widget.event_generate('<<Cut>>'))
            context_menu.add_command(label="📄 Копировать",
                                     command=lambda: text_widget.event_generate('<<Copy>>'))
            context_menu.add_command(label="🗑️ Очистить",
                                     command=lambda: text_widget.delete('1.0', 'end'))

            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        # Привязка горячих клавиш
        text_widget.bind('<Control-v>', paste_from_clipboard)
        text_widget.bind('<Control-V>', paste_from_clipboard)

        # Привязка правой кнопки мыши
        text_widget.bind('<Button-3>', create_text_context_menu)

    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    app = TwitchChatBot()
    app.run()
