import asyncio
import asyncpg
from asyncpg import Pool, Connection

from pydantic import BaseModel, EmailStr


class PSQL:
    __pool: Pool = None

    async def create_connection_pool(self):
        if self.__pool is not None:
            return 
        config = {
            'user': 'yohann',
            'password': 'yohann@327',
            # 'host': '127.0.0.1',
            'database': 'aigc'
        }
        self.__pool = await asyncpg.create_pool(
            # max_size=10,
            # max_inactive_connection_lifetime=10,
            # command_timeout=60,
            **config
        )

    async def __aexit__(self):
        if self.__pool is not None:
            print("closing pool")
            await self.__pool.close()


def pool(fun):
    async def get_pool(*args, **kwargs):
        await args[0].create_connection_pool()
        conn = await args[0].__pool.acquire()
        res = await fun(*args, **kwargs, conn = conn)
        await conn.release()
        return res

    return get_pool

class User(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserDB(PSQL):
    """
    Columns: rowid, name, password, email, is_active, is_superuser
    """
    @pool
    async def create_user(self, user_data: User, conn: Connection):
        # conn: Connection = kw['conn']
        conn.execute("")
        
    @pool
    async def get_user_by_email(self, email: EmailStr, conn: Connection):
        res = await conn.fetch("SELECT name from user WHERE email = '$1'", email)
        print(res)

    @pool
    async def is_exists(self, ):
        pass


async def main():
    user_db = UserDB()
    email = 'inteligenct@gmail.com'
    await user_db.get_user_by_email(email)
    return 0


async def main2():
    config = {
        'user': 'yohann',
        'password': 'yohann@327',
        # 'host': '127.0.0.1',
        'database': 'aigc'
    }
    pool: Pool = await asyncpg.create_pool(
        "postgresql://yohann:yohann327@localhost/aigc"
        # max_size=10,
        # max_inactive_connection_lifetime=10,
        # command_timeout=60,
        # **config
    )
    print(pool)
    await pool.close()


if __name__ == '__main__':
    asyncio.run(main2())