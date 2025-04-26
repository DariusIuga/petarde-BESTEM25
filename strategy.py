import random
from time import sleep

import requests

host = "10.81.135.1"
post_url = f"{host}/submit-word"
get_url = f"{host}/get-word"
status_url = f"{host}/status"

NUM_ROUNDS = 10


def what_beats(word):
    sleep(random.randint(1, 3))  # TODO
    return random.randint(1, 77)


def play_game(player_id):

    for round_id in range(1, NUM_ROUNDS + 1):
        round_num = -1
        while round_num != round_id:
            response = requests.get(get_url)
            print(response.json())
            sys_word = response.json()["word"]
            round_num = response.json()["round"]

            sleep(1)

        if round_id > 1:
            status = requests.get(status_url)
            print(status.json())

        choosen_word = what_beats(sys_word)
        data = {"player_id": player_id, "word_id": choosen_word, "round_id": round_id}
        response = requests.post(post_url, json=data)
        print(response.json())


def register(player_id):
    register_url = f"{host}/register"
    data = {"player_id": player_id}
    response = requests.post(register_url, json=data)

    return response.json()


register("abc123")
