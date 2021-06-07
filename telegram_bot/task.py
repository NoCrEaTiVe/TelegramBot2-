import requests
import datetime




class TwitterParser:
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token

    def check_user_exists(self, username):
        headers = self.create_headers()
        resp = requests.get(
            "https://api.twitter.com/2/users/by/username/" + username,
            headers=headers,
        )
        if "errors" in resp.json():
            return (False, -1)
        return (True, resp.json()["data"]["id"])

    def get_params(self):
        local_time = str(datetime.datetime.utcnow() - datetime.timedelta(minutes=30))
        ind = local_time.rindex(".")
        local_time = local_time[:ind].replace(" ", "T") + "Z"

        return {
            "start_time": local_time,
            "tweet.fields": "created_at",
            "user.fields": "username",
            "expansions": "author_id",
        }

    def create_headers(self):
        headers = {"Authorization": "Bearer {}".format(self.bearer_token)}
        return headers

    def get_acc_user_ids(self):
        from sqliter import SQLighter

        db = SQLighter()
        accs = db.all_twitter_accs()
        return accs

    async def connect_to_endpoint(self):
        headers = self.create_headers()
        params = self.get_params()
        accs = self.get_acc_user_ids()

        from bot import send_to_telegram_bot

        for user_id in accs:
            url = "https://api.twitter.com/2/users/{}/tweets".format(user_id)

            response = requests.get(url, headers=headers, params=params)
            json_response = response.json()
            print(json_response)
            if json_response["meta"]["result_count"] == 0:
                url = "https://api.twitter.com/2/users/{}/tweets".format(user_id)
                response = requests.get(url, headers=headers, params=params)
                json_response = response.json()
                if json_response["meta"]["result_count"] == 0:
                    continue

            data = json_response["data"]
            username = json_response["includes"]["users"][0]["username"]
            link_to_acc = "https://twitter.com/" + username
            user_name_text = "<a href='{}'>{}</a>".format(link_to_acc, username)
            for dt in data:
                link_to_tweet = "https://twitter.com/i/web/status/" + dt["id"]
                await send_to_telegram_bot(
                    username,
                    user_name_text,
                    dt["text"],
                    dt["created_at"],
                    link_to_tweet,
                )

    async def run(self):
        await self.connect_to_endpoint()
