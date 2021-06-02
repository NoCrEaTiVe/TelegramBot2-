import requests
import json
import config
import asyncio
from json import JSONDecodeError
from threading import Lock, Thread


class Stream:
    def __init__(self, bearer_token):
        self.bearer_token = bearer_token
        self._callbacks = dict()
        self._lock = Lock()
        self._stop = True
        self._thread = None

    def create_headers(self):
        headers = {
            "Authorization": "Bearer {}".format(self.bearer_token),
            "Content-type": "application/json",
        }
        return headers

    def add_rule(self, query, tag):
        headers = self.create_headers()
        data = json.dumps({"add": [{"value": query, "tag": tag}]})

        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=headers,
            data=data,
        )
        return json.loads(response.content.decode())

    def get_rules(self):
        headers = self.create_headers()
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers
        )
        return json.loads(response.content.decode())

    def delete_all_rules(self, rules):
        headers = self.create_headers()
        if rules is None or "data" not in rules:
            return None

        ids = list(map(lambda rule: rule["id"], rules["data"]))
        payload = {"delete": {"ids": ids}}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=headers,
            json=payload,
        )
        if response.status_code != 200:
            raise Exception(
                "Cannot delete rules (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )

    def add_rule(self, acc):
        headers = self.create_headers()
        payload = {"add": [{"value": "from: " + acc}]}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=headers,
            json=payload,
        )
        if response.status_code != 201:
            raise Exception(
                "Cannot add rules (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )

    def delete_rules(self, ids):
        headers = self.create_headers()
        data = json.dumps({"delete": {"ids": ids}})
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=headers,
            data=data,
        )
        return json.loads(response.content.decode())

    def set_rules(self):
        headers = self.create_headers()
        from sqliter import SQLighter

        db = SQLighter()
        accs = db.all_twitter_accs()
        sample_rules = []
        for acc in accs:
            sample_rules.append({"value": "from: " + acc})

        payload = {"add": sample_rules}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=headers,
            json=payload,
        )
        if response.status_code != 201:
            raise Exception(
                "Cannot add rules (HTTP {}): {}".format(
                    response.status_code, response.text
                )
            )

    def check_user_exists(self, username):
        headers = self.create_headers()
        resp = requests.get(
            "https://api.twitter.com/2/users/by/username/" + username,
            headers=headers,
        )
        if "errors" in resp.json():
            return False
        return True

    def add_callback(self, name, callback):
        self._callbacks[name] = callback

    def get_callbacks(self):
        return list(self._callbacks.items())

    def delete_callback(self, name):
        del self._callbacks[name]

    def _get_stream(self):
        from bot import send_to_telegram_bot

        headers = self.create_headers()
        while True:
            try:
                with requests.get(
                    "https://api.twitter.com/2/tweets/search/stream?tweet.fields=created_at,text&expansions=author_id&user.fields=created_at,username",
                    headers=headers,
                    stream=True,
                ) as stream:
                    for line in stream.iter_lines():
                        try:
                            json_response = json.loads(line.decode("utf-8"))
                            print(json_response)
                            data = json_response["data"]
                            print(json_response)
                            username = json_response["includes"]["users"][0]["username"]
                            link_to_acc = "https://twitter.com/" + username
                            user_name_text = "<a href='{}'>{}</a>".format(
                                link_to_acc, username
                            )
                            link_to_tweet = (
                                "https://twitter.com/i/web/status/" + data["id"]
                            )
                            asyncio.run(
                                send_to_telegram_bot(
                                    username,
                                    user_name_text,
                                    data["text"],
                                    data["created_at"],
                                    link_to_tweet,
                                )
                            )
                        except JSONDecodeError:
                            data = None
                        if data:
                            for callback_key in self._callbacks:
                                self._callbacks[callback_key](data)
                        if self._stop:
                            break

                continue
            except:
                continue

    def start_getting_stream(self):
        with self._lock:
            if self._thread is None:
                self._stop = False
                self._thread = Thread(target=self._get_stream)
                self._thread.start()

    def is_getting_stream(self):
        with self._lock:
            return self._thread is not None

    def stop_getting_stream(self):
        with self._lock:
            if self._thread is not None:
                self._stop = True
        if self._thread:
            self._thread.join()
            self._thread = None


def main():
    stream = Stream(config.BEARER_TOKEN)
    rules = stream.get_rules()
    stream.delete_all_rules(rules)
    stream.set_rules()
    stream.start_getting_stream()