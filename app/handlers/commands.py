from aiogram import Router, F
from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, ChatMemberUpdated,BotCommandScopeAllChatAdministrators
from aiogram.enums import ChatMemberStatus
import app.keyboards as kb

router = Router()

async def set_private_commands(bot):
    private_commands = [
        BotCommand(command="/start", description="start the bot"),
        BotCommand(command="/profile", description="game profile"),
        BotCommand(command="/language", description="choose language"),
        BotCommand(command="/private", description="choose language"),
        BotCommand(command="/issue", description="write to developer (en/ru only)")
    ]
    await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())

async def set_group_commands(bot):
    group_commands = [
        BotCommand(command="/start_game", description="start the game"),
        BotCommand(command="/create_game", description="create the game"),
        BotCommand(command="/next", description="notification about next game"),
        BotCommand(command="/settings", description="notification about next game"),
        BotCommand(command="/cancel", description="cancel the game"),
        BotCommand(command="/share", description="cancel the game")]
    await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())

@router.my_chat_member()
async def on_chat_member_updated(event: ChatMemberUpdated):
    if event.new_chat_member.status == ChatMemberStatus.MEMBER:
        await event.bot.send_message(
            chat_id=event.chat.id,
            text='Привет!\nЯ бот-ведущий для игры в 🕵 Мафию.\nДля начала игры дай мне следующие права администратора:\n'
                 '✅ удалять сообщения\n✅ блокировать пользователей\n✅ закреплять сообщения',
            reply_markup=kb.group_menu
        )
        
        
# # Добавление команд для администраторов
# async def set_admin_commands(bot):
#     admin_commands = [
#         BotCommand(command="/add_admin", description="Add a new admin"),
#         BotCommand(command="/remove_admin", description="Remove an admin"),
#         BotCommand(command="/stop_bot", description="Stop the bot"),
#         BotCommand(command="/restart_game", description="Restart the game")
#     ]
#     await bot.set_my_commands(admin_commands, scope=BotCommandScopeAllChatAdministrators())
