from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🕵 Добавить игру в свой чат", callback_data='add_game')],
    [InlineKeyboardButton(text='🎲 Войти в чат', callback_data='enter_chat')],
    [InlineKeyboardButton(text='🇷🇺 Язык / Language', callback_data='language')],
    [InlineKeyboardButton(text='👤 Профиль', callback_data='profile'), InlineKeyboardButton(text='🃏 Роли', callback_data='roles')]
])

# Меню группы
group_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🇷🇺 Язык / Language', callback_data='language')],
    [InlineKeyboardButton(text='Помощь', callback_data='help')],
])

# Меню присоединения к игре
join_game_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🤵🏻 Присоединиться', callback_data='join_game')],
])

# Меню ролей
def create_roles_keyboard():
    roles_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Мирный житель 👨🏼', callback_data='role_civilian'),
         InlineKeyboardButton(text='Дон 🤵🏻', callback_data='role_don')],
        [InlineKeyboardButton(text='Мафия 🤵🏼', callback_data='role_mafia'),
         InlineKeyboardButton(text='Комиссар Каттани 🕵️‍♂️', callback_data='role_commissar')],
        [InlineKeyboardButton(text='Сержант 👮', callback_data='role_sergeant'),
         InlineKeyboardButton(text='Доктор 👨‍⚕️', callback_data='role_doctor')],
        [InlineKeyboardButton(text='Маньяк 🔪', callback_data='role_maniac'),
         InlineKeyboardButton(text='Любовница 💃', callback_data='role_lover')],
        [InlineKeyboardButton(text='Адвокат 👨🏼‍💼', callback_data='role_lawyer'),
         InlineKeyboardButton(text='Самоубийца 😵', callback_data='role_suicide')],
        [InlineKeyboardButton(text='Бомж 🧙🏻‍♂️', callback_data='role_hobo'),
         InlineKeyboardButton(text='Счастливчик ✌️', callback_data='role_lucky')],
        [InlineKeyboardButton(text='Камикадзе 💣', callback_data='role_kamikaze')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')]
    ])
    return roles_keyboard

roles_menu = create_roles_keyboard()

# Клавиатура для отправки номера
get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер', request_contact=True)]], resize_keyboard=True)

# Клавиатура для выбора жертвы
def create_victim_keyboard(players, action_prefix):
    buttons = [InlineKeyboardButton(text=player['name'], callback_data=f'{action_prefix}_{player["id"]}') for player in players]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

# Клавиатура для голосования
def create_vote_keyboard(players):
    buttons = [InlineKeyboardButton(text=player['name'], callback_data=f'vote_{player["id"]}') for player in players]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

# Клавиатура для перехода к боту
def create_starte_game_keyboard(username):
    buttons = [InlineKeyboardButton(
        text="Перейти к боту",
        url=f"https://t.me/{username}"
    )]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

# Клавиатура для профиля
profile_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛒 Магазин', callback_data='shop')],
    [InlineKeyboardButton(text='💰 Купить деньги', callback_data='buy_money'), InlineKeyboardButton(text='💎 Купить кристаллы', callback_data='buy_crystals')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')]
])

# Клавиатура действий Комиссара
def create_commissar_action_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔍 Проверить", callback_data='commissar_action_check')],
        [InlineKeyboardButton(text="🔫 Убить", callback_data='commissar_action_kill')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура для социальных сетей
def create_social_share_keyboard(group_invite_link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='WhatsApp', url=f'https://api.whatsapp.com/send?text={group_invite_link}'),
         InlineKeyboardButton(text='VK', url=f'https://vk.com/share.php?url={group_invite_link}')],
        [InlineKeyboardButton(text='Facebook', url=f'https://www.facebook.com/sharer/sharer.php?u={group_invite_link}'),
         InlineKeyboardButton(text='Twitter', url=f'https://twitter.com/intent/tweet?url={group_invite_link}')],
        [InlineKeyboardButton(text='Одноклассники', url=f'https://connect.ok.ru/offer?url={group_invite_link}')],
    ])
