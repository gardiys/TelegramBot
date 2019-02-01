import redis
import settings
import pickle


class Store:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)

    def set_items(self, key, items, number):
        pickled_object = pickle.dumps(items)
        self.redis.set(f"{key}:{number}", pickled_object)

    def get_item(self, key):
        unpacked = pickle.loads(self.redis.get(key))
        return unpacked

    def already_exist(self, key):
        return self.redis.exists(key)

    def reset_data(self):
        self.redis.flushall()
