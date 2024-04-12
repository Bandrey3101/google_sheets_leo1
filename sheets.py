from __future__ import print_function
from create_bot import dp
import logging
from aiogram.utils import executor
from handlers import admins, clients

logging.basicConfig(level=logging.INFO)

admins.register_handlers_admin(dp)
clients.register_handlers_client(dp)

executor.start_polling(dp, skip_updates=False)
