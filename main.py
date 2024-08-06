import asyncio # testing
from aiogram import Bot, Dispatcher
from app.config import TOKEN
from app.handlers.commands import set_private_commands, set_group_commands
from app.handlers import game,profile,start,callbacks,commands,admin


#kerngjernognpih
async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    dp.include_router(start.start_router)
    dp.include_router(profile.router)
    dp.include_router(game.router)
    dp.include_router(callbacks.router)
    dp.include_router(commands.router)
    dp.include_router(admin.router)

    # Устанавливаем команды для приватного чата
    await set_private_commands(bot)
    
    # Устанавливаем команды для группового чата
    await set_group_commands(bot)

    # await set_admin_commands(bot)
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        print('Бот включен')
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
