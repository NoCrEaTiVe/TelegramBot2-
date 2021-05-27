import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]


class User:
    def __init__(self, user_id):
        self.user_id = user_id

    def add_user(self):
        return "INSERT INTO users VALUES (%s);" % (self.user_id)

    def delete_user(self):
        return "DELETE from users where userid = (%s);" % (self.user_id)

    def check_user_exists(self):
        return "SELECT 1 FROM users WHERE userid=%s;" % (self.user_id)


class UserChatId:
    def __init__(self, user_id, chat_id):
        self.chat_id = chat_id
        self.user_id = user_id

    def add_chat_id(self):
        return "INSERT INTO UserChatId (chat_id, user_id) VALUES (%s,%s);" % (
            self.chat_id,
            self.user_id,
        )

    def delete_chat_id(self):
        return "DELETE from UserChatId where chat_id = (%s) and user_id = (%s);" % (
            self.chat_id,
            self.user_id,
        )

    def check_chat_id(self):
        return "SELECT 1 FROM UserChatId WHERE chat_id='%s' and user_id ='%s';" % (
            self.chat_id,
            self.user_id,
        )


class SQLighter:
    def __init__(self):
        self.connection = psycopg2.connect(DATABASE_URL, sslmode="require")
        self.cursor = self.connection.cursor()

    def add_user(self, userId):
        user = User(userId)
        self.cursor.execute(user.add_user())
        self.connection.commit()
        userChat = UserChatId(userId, userId)
        self.cursor.execute(userChat.add_chat_id())
        self.connection.commit()

    def add_chat_id_to_user(self, userId, chatId):
        userChatId = UserChatId(userId, chatId)
        self.cursor.execute(userChatId.add_chat_id())
        self.connection.commit()

    def check_chat_id_exists_in_user_list(self, userId, chatId):
        userChatId = UserChatId(userId, chatId)
        self.cursor.execute(userChatId.check_chat_id())
        return bool(self.cursor.fetchone())

    def delete_chat_id_from_user(self, userId, chatId):
        userChatId = UserChatId(userId, chatId)
        self.cursor.execute(userChatId.delete_chat_id())
        self.connection.commit()

    def check_user(self, userid):
        user = User(userid)
        self.cursor.execute(user.check_user_exists())
        return bool(self.cursor.fetchone())

    def get_twiiter_acc(self, userid):
        usernames = (
            "SELECT DISTINCT username from usertwitteracc where userid = %s " % (userid)
        )
        self.cursor.execute(usernames)
        usernames_list = [user[0] for user in self.cursor]
        return usernames_list

    def delete_user(self, userid):
        user = User(userid)
        self.cursor.execute(user.delete_user())
        self.connection.commit()

    def add_usertwitteracc(self, user_id, username):
        user_twitter_acc = UserTwitterAcc(user_id, username)
        self.cursor.execute(user_twitter_acc.add_user_twiiter_acc())
        self.connection.commit()

    def user_acc_exists(self, user_id, username):
        user_acc = UserTwitterAcc(user_id, username)
        self.cursor.execute(user_acc.check_user_twitter_acc_exists())

        return bool(self.cursor.fetchone())

    def find_users_with_this_acc(self, username):
        user_id = "SELECT DISTINCT userid from usertwitteracc where username = '%s'" % (
            username
        )
        self.cursor.execute(user_id)
        users_id = [user[0] for user in self.cursor]
        return users_id

    def find_user_chats(self, user_id):
        chat_ids = "SELECT DISTINCT chat_id from UserChatId where user_id = %s" % (
            user_id
        )
        self.cursor.execute(chat_ids)
        chat_id = [chat[0] for chat in self.cursor]
        return chat_id

    def all_twitter_accs(self):
        sql = "SELECT DISTINCT username from usertwitteracc"
        self.cursor.execute(sql)
        accs = [acc[0] for acc in self.cursor]
        return accs

    def delete_usertwitter_acc(self, user_id, acc):
        user_twitter_acc = UserTwitterAcc(user_id, acc)
        self.cursor.execute(user_twitter_acc.delete_user_twitter_acc())
        self.connection.commit()

    def close(self):
        self.connection.close()


class UserTwitterAcc:
    def __init__(self, user_id, acc_username):
        self.user_id = user_id
        self.twitter_acc = acc_username

    def add_user_twiiter_acc(self):
        return "INSERT INTO usertwitteracc (userid,username) VALUES (%s, '%s');" % (
            self.user_id,
            self.twitter_acc,
        )

    def delete_user_twitter_acc(self):
        return "Delete from usertwitteracc where userid = %s and username = '%s'" % (
            self.user_id,
            self.twitter_acc,
        )

    def check_user_twitter_acc_exists(self):
        return "SELECT 1 FROM usertwitteracc WHERE userid = %s and username='%s';" % (
            self.user_id,
            self.twitter_acc,
        )
