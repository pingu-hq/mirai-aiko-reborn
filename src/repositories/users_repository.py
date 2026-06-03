from mongo_db_base import AsyncMongoDbBaseClass

class UsersRepository(AsyncMongoDbBaseClass):
    def __init__(self):
        super().__init__(collection_name="users")

    async def create_user(self, **kwargs):
        result = await self.collection.insert_one(**kwargs)
        return result.inserted_id

    async def get_user(self, user_id):
        return await self.collection.find_one({"user_id":user_id})
