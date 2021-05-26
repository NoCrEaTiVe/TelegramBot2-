import bot
import requests
import os
import json
import config

from requests.models import Response


# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='AAAAAAAAAAAAAAAAAAAAAOINPwEAAAAA7%2Bakn1LOAXEJh1S9eswS3yoiKwY%3DV4jhcNlzbmpHl3HFK0keLrLAwvwGnaxxeMeQfYJO2mUeRvQsFs'


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def get_rules(headers, bearer_token):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(headers, bearer_token, rules):
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
    print(json.dumps(response.json()))

def add_rule(headers,acc):
    payload = {"add": [{"value":"from: " + acc }]}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def set_rules(headers, delete, bearer_token):
    from sqliter import SQLighter

    db = SQLighter("db.sql")
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
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def check_user_exists(username):
    resp = requests.get(
        "https://api.twitter.com/2/users/by/username/" + username,
        headers=create_headers(config.BEARER_TOKEN),
    )
    if "errors" in resp.json():
        return False
    return True


async def get_stream(headers, set, bearer_token):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream?tweet.fields=created_at,text&expansions=author_id&user.fields=created_at,username,entities&media.fields=url",
        headers=headers,
        stream=True,
    )

    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    while True:
        try:
            for response_line in response.iter_lines():
                if response_line:
                    json_response = json.loads(response_line.decode("utf-8"))
                    data = json_response["data"]
                    await bot.send_to_telegram_bot(
                        json_response["includes"]["users"][0]["username"],
                        data["text"],
                        data["created_at"],
                    )

        except:
            continue


async def main():
    bearer_token = config.BEARER_TOKEN
    headers = create_headers(bearer_token)
    rules = get_rules(headers, bearer_token)
    delete = delete_all_rules(headers, bearer_token, rules)
    set = set_rules(headers, delete, bearer_token)
    await get_stream(headers, set, bearer_token)
