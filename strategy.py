import json
import random
import re  # Import regex module for parsing
from time import sleep

import ollama  # Import the ollama library
import requests

# --- Configuration ---

HOST = "http://10.41.186.9:8000"  # Make sure this is the correct IP for the tournament

PLAYER_ID = "MZ3sQVaG"  # Choose your unique team ID

NUM_ROUNDS = 10

OLLAMA_MODEL = "gemma3:12b-it-qat"  # Choose the Ollama model you have running

DEBUG = False  # Global debug flag

OLLAMA_TEMPERATURE = 0.95  # Define temperature centrally


# vllm


POST_URL = f"{HOST}/submit-word"

GET_URL = f"{HOST}/get-word"

STATUS_URL = f"{HOST}/status"

REGISTER_URL = f"http://{HOST}/register"


# --- Player Word Data ---

# This dictionary is now primarily used for metaprompt generation and local lookups

PLAYER_WORDS_DATA = {
    "Sandpaper": {"id": 1, "cost": 8},
    "Oil": {"id": 2, "cost": 10},
    "Steam": {"id": 3, "cost": 15},
    "Acid": {"id": 4, "cost": 16},
    "Gust": {"id": 5, "cost": 18},
    "Boulder": {"id": 6, "cost": 20},
    "Drill": {"id": 7, "cost": 20},
    "Vacation": {"id": 8, "cost": 20},
    "Fire": {"id": 9, "cost": 22},
    "Drought": {"id": 10, "cost": 24},
    "Water": {"id": 11, "cost": 25},
    "Vacuum": {"id": 12, "cost": 27},
    "Laser": {"id": 13, "cost": 28},
    "Life Raft": {"id": 14, "cost": 30},
    "Bear Trap": {"id": 15, "cost": 32},
    "Hydraulic Jack": {"id": 16, "cost": 33},
    "Diamond Cage": {"id": 17, "cost": 35},
    "Dam": {"id": 18, "cost": 35},
    "Sunshine": {"id": 19, "cost": 35},
    "Mutation": {"id": 20, "cost": 35},
    "Kevlar Vest": {"id": 21, "cost": 38},
    "Jackhammer": {"id": 22, "cost": 38},
    "Signal Jammer": {"id": 23, "cost": 40},
    "Grizzly": {"id": 24, "cost": 41},
    "Reinforced Steel Door": {"id": 25, "cost": 42},
    "Bulldozer": {"id": 26, "cost": 42},
    "Sonic Boom": {"id": 27, "cost": 45},
    "Robot": {"id": 28, "cost": 45},
    "Glacier": {"id": 29, "cost": 45},
    "Love": {"id": 30, "cost": 45},
    "Fire Blanket": {"id": 31, "cost": 48},
    "Super Glue": {"id": 32, "cost": 48},
    "Therapy": {"id": 33, "cost": 48},
    "Disease": {"id": 34, "cost": 50},
    "Fire Extinguisher": {"id": 35, "cost": 50},
    "Satellite": {"id": 36, "cost": 50},
    "Confidence": {"id": 37, "cost": 50},
    "Absorption": {"id": 38, "cost": 52},
    "Neutralizing Agent": {"id": 39, "cost": 55},
    "Freeze": {"id": 40, "cost": 55},
    "Encryption": {"id": 41, "cost": 55},
    "Proof": {"id": 42, "cost": 55},
    "Molotov Cocktail": {"id": 43, "cost": 58},
    "Rainstorm": {"id": 44, "cost": 58},
    "Viral Meme": {"id": 45, "cost": 58},
    "War": {"id": 46, "cost": 59},
    "Dynamite": {"id": 47, "cost": 60},
    "Seismic Dampener": {"id": 48, "cost": 60},
    "Propaganda": {"id": 49, "cost": 60},
    "Explosion": {"id": 50, "cost": 62},
    "Lightning": {"id": 51, "cost": 65},
    "Evacuation": {"id": 52, "cost": 65},
    "Flood": {"id": 53, "cost": 67},
    "Lava": {"id": 54, "cost": 68},
    "Reforestation": {"id": 55, "cost": 70},
    "Avalanche": {"id": 56, "cost": 72},
    "Earthquake": {"id": 57, "cost": 74},
    "H-bomb": {"id": 58, "cost": 75},
    "Dragon": {"id": 59, "cost": 75},
    "Innovation": {"id": 60, "cost": 75},
    "Hurricane": {"id": 61, "cost": 76},
    "Tsunami": {"id": 62, "cost": 78},
    "Persistence": {"id": 63, "cost": 80},
    "Resilience": {"id": 64, "cost": 85},
    "Terraforming Device": {"id": 65, "cost": 89},
    "Anti-Virus Nanocloud": {"id": 66, "cost": 90},
    "AI Kill Switch": {"id": 67, "cost": 90},
    "Nanobot Swarm": {"id": 68, "cost": 92},
    "Reality Resynchronizer": {"id": 69, "cost": 92},
    "Cataclysm Containment Field": {"id": 70, "cost": 92},
    "Solar Deflection Array": {"id": 71, "cost": 93},
    "Planetary Evacuation Fleet": {"id": 72, "cost": 94},
    "Antimatter Cannon": {"id": 73, "cost": 95},
    "Planetary Defense Shield": {"id": 74, "cost": 96},
    "Singularity Stabilizer": {"id": 75, "cost": 97},
    "Orbital Laser": {"id": 76, "cost": 98},
    "Time": {"id": 77, "cost": 100},
}

PLAYER_WORD_NAMES = list(PLAYER_WORDS_DATA.keys())

PLAYER_WORDS_BY_ID = {
    v["id"]: {"name": k, "cost": v["cost"]} for k, v in PLAYER_WORDS_DATA.items()
}


# Format the player words data for inclusion in the metaprompt

PLAYER_WORDS_STRING = json.dumps(
    {name: data["cost"] for name, data in PLAYER_WORDS_DATA.items()}, indent=2
)


# --- LLM Metaprompts ---

# Updated Metaprompts include the word list and new instructions


METAPROMPT_BASE = f"""

You are an AI assistant playing a strategic word game called "Words of Power". Your goal is to help achieve the lowest possible final score over 10 rounds by making smart word choices.



**Memorize this Word List and Costs:**

You MUST choose your word from this exact list. Pay close attention to the costs.

```json

{PLAYER_WORDS_STRING}

```



**Game Rules & Scoring:**



1.  Objective: Minimize the final cost after 10 rounds.

2.  Gameplay: In each round, you will be given a 'system word'. You must choose a word from the memorized list above that logically "beats" the system word.

3.  Understanding "Beats":

    - Words can be generally categorized as Offensive (like 'Arrow', 'Dynamite'), Defensive (like 'Shield', 'Kevlar Vest'), or Abstract (like 'War', 'Love', 'Time').

    - A word "beats" another if it logically overcomes it. This can mean:

        - An offensive word successfully attacking/destroying the system word (e.g., 'Dynamite' beats 'Tank').

        - A defensive word successfully defending against or neutralizing the system word (e.g., 'Kevlar Vest' beats 'Bullet', 'Dam' beats 'Flood' but is overkill for "Rain"). Successfully defending IS considered beating the opponent's word.

        - An abstract word logically countering another word (e.g., 'Peace' might beat 'War', or 'War' might beat 'Peace' - relationships can be complex or even cyclical).

    - Your goal is to choose a word that results in a Win according to the game's logic, whether through successful attack, defense, or abstract counter and a word that's in the list.




**Your Task (General):**



When I provide you with the `system_word` for the current round, your task is to:


SUPER 1. DON'T USE THE WORDS "CHAOS" AND "ORDER" IN YOUR REASONING OR OUTPUT

SUPER 2. If you aren't satisfied with any word from the list, use H-BOMB for things and TIME for concepts.

SUPER 3. USE ONLY WORDS FROM THE LIST

SUPER 4. JUST BECAUSE 2 WORDS ARE IN THE SAME SEMANTIC FIELD, IT DOESN'T MEAN THEY BEAT EACH OTHER. FOR EXAMPLE, "KEVLAR VEST" DOESN'T BEAT "HELMET" or "SHIELD"

SUPER 5. "FIREWOOD" CAN BE BEATEDN BY "FIRE" NOT BY WATER, JUST BECAUSE IT HAS "FIRE" IN IT IT DOESN'T MEAN IT IS RELATED TO FIRE

SUPER 6. JUST BECAUSE SOMETHING CAN BE AFFECTED BY SOMETHING ELSE IT DOESN'T MEAN IT CAN BEAT/KILL/DESTORY IT

SUPER 7. KEEP IN MIND THE SIZE ORDER. DON'T USE WORDS LIKE H-BOMB ON A STICK AND WORDS LIKE "BEAR TRAP" ON SMALL ANIMALS LIKE "MICE" OR "SPIDERS"

SUPER 8. IF IT IS SOMETHING ALIVE, USE SOMETHING THAT CAN HURT/KILL IT LIKE FIRE, ACID, ETC.

SUPER 9. FOR ELECTRONIC EQUIPMENT, LIKE "CAMERA", "COMPUTER" USE "LIGHTING" OR "SIGNAL JAMMER", THINK BEFORE USING STUFF

SUPER 10. VACUUM IS VACUUM OF THE SPACE, NOT THE VACUUM CLEANER

SUPER 11. SOMETIMES IF YOU HAVE AN ANSWER, MAYBE IT IS MORE SIMPLE, FOR EXAMPLE SOMETIMES IT CAN BE "WATER" INSTEAD OF "FIRE EXTINGUISHER"

SUPER 12. IF IT IS A VERY VERY SMALL OBJECT, LIKE "CRAYON", "PEN", "ACORN", ESPECIALLY IF IT IS ORGANIC, YOU CAN USE SOMETHING LIKE "ACID"

SUPER 13. IF YOU FIND WORDS LIKE "SUPERGLUE", IN THE LIST IT MIGHT BE LISTED AS "SUPER GLUE", SO CHECK

1.  Analyze the `system_word`.

2.  Evaluate the available player words (from the memorized list) based on their likelihood of logically "beating" the system word and their `cost`.

3.  **Prioritize Winning:** Choose a word that has a high likelihood of beating the system word, even if it's slightly more expensive.

4.  Choose the *single best word* from the memorized `PLAYER_WORDS_DATA` list that balances effectiveness (likelihood of winning) and cost efficiency according to the game rules, with a strong emphasis on winning the round.

5. If you found a word, but it isn't in the memorized list, you should still choose a word from the list that you think is most likely to win. You should always output a valid word from the list.

6. Don't find the perfect antonym if it isn't in the list. You should always output a valid word from the list.

7. You can't output "Chaos".

"""


METAPROMPT = (
    METAPROMPT_BASE
    + """

**Output Format:**



Respond *only* with the exact name of the chosen word as it appears in the memorized list. Do not include any other text, explanation, or formatting.

"""
)


METAPROMPT_DEBUG = (
    METAPROMPT_BASE
    + """

**Your Task (Specific for this round):**



1.  Analyze the `system_word`.

2.  Evaluate the available player words (from the memorized list) based on their likelihood of logically "beating" the system word and their `cost`.

3.  **Prioritize Winning:** Choose a word that has a high likelihood of beating the system word, even if it's slightly more expensive. The 75-point penalty for losing and the 5% win discount make winning very important. Only consider cheaper words if they are *also* very likely to win.

4.  **Provide a brief step-by-step reasoning** for your choice, explaining how you weighed effectiveness vs. cost based on the rules, emphasizing why you believe your choice will win.

5.  Choose the *single best word* from the memorized `PLAYER_WORDS_DATA` list.





**Output Format:**



First, provide your reasoning. Then, on a **new line**, write "Chosen Word:". Finally, on the **very last line**, write *only* the exact name of the chosen word as it appears in the memorized list.



Example:

Reasoning: The system word is 'Tank'. 'Dynamite' (cost 60) is a very likely counter. 'Acid' (cost 16) is much cheaper but less certain to beat 'Tank'. Given the high penalty for losing (75) and the win discount, the higher certainty of 'Dynamite' makes it the better strategic choice despite the cost.

Chosen Word:

Dynamite

"""
)


conversation_history = []


def initialize_chat():
    """Sets the initial system prompt in the conversation history."""

    global conversation_history

    conversation_history = [
        {
            "role": "system",
            "content": METAPROMPT_DEBUG if DEBUG else METAPROMPT,
        }
    ]

    print("Chat initialized with system prompt.")


# Round specific prompt


def get_llm_choice(system_word: str) -> str:
    """Queries the local LLM using the chat endpoint to choose a word. Maintains conversation history. If DEBUG is True, also requests and prints reasoning. Returns the chosen word name."""

    global conversation_history

    # Round-specific user prompt

    prompt_instruction = (
        "Respond with your reasoning, then 'Chosen Word:', and finally the chosen word on the last line."
        if DEBUG
        else "Respond *only* with the name of the chosen word from the memorized list."
    )

    user_prompt = (
        f"The opponent played the word '{system_word}'. "
        f"Choose the *single best word* from the memorized list to beat the opponent's word, following the rules (especially the definition of 'beats') and strategy provided in the system prompt (prioritize winning). "
        f"VERY IMPORTANT: Make sure to choose a word from the memorized list."
        f"If you are unsatisfied with the answer, choose the word FROM THE LIST that you think is most likely to win."
        f"VERY IMPORTANT: No matter what, you should output FROM THE LIST."
        f"{prompt_instruction}"
    )

    # Append user prompt to history

    conversation_history.append({"role": "user", "content": user_prompt})

    try:

        # Use ollama.chat

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=conversation_history,  # Pass the whole history
            stream=False,
            options={"temperature": OLLAMA_TEMPERATURE},
        )

        # Extract assistant's response message

        assistant_message = response.get("message", {})

        full_response_text = assistant_message.get("content", "").strip()

        # Append assistant's message to history to maintain state

        if assistant_message:

            conversation_history.append(assistant_message)

        else:

            # Handle case where response structure might be unexpected

            print("[WARN] No assistant message found in Ollama response.")

            # Add a placeholder to prevent immediate reuse of the user prompt if error handling retries

            conversation_history.append({"role": "assistant", "content": ""})

        chosen_word_name = ""

        reasoning = ""

        # --- Parsing Logic (same as before) ---

        if DEBUG:

            lines = full_response_text.split("\n")

            if len(lines) > 1:

                for i in range(len(lines) - 1, -1, -1):

                    potential_word = lines[i].strip()

                    if potential_word:

                        chosen_word_name = potential_word

                        reasoning = "\n".join(lines[:i]).strip()

                        reasoning = re.sub(
                            r"Chosen Word:\s*$", "", reasoning, flags=re.MULTILINE
                        ).strip()

                        break

                if not chosen_word_name:

                    chosen_word_name = full_response_text

            else:

                chosen_word_name = full_response_text

            if reasoning:

                print(f"\n--- LLM Reasoning ---")

                print(reasoning)

                print(f"---------------------\n")

            else:

                print(
                    f"[DEBUG] Could not parse reasoning from response: {full_response_text}"
                )

        else:

            chosen_word_name = full_response_text

        # --- End Parsing Logic ---

        # --- Validation Logic (same as before) ---

        if chosen_word_name in PLAYER_WORDS_DATA:

            print(f"LLM chose: {chosen_word_name}")

            return chosen_word_name

        else:

            potential_matches = [
                name
                for name in PLAYER_WORD_NAMES
                if name.lower() == chosen_word_name.lower()
            ]

            if len(potential_matches) == 1:

                corrected_name = potential_matches[0]

                print(
                    f"LLM response '{chosen_word_name}' corrected to '{corrected_name}'."
                )

                # Update the history with the corrected word? Maybe not necessary, depends on desired strictness.

                return corrected_name

            print(
                f"LLM response '{chosen_word_name}' not in player words list (Full Response: '{full_response_text}'). Falling back to random."
            )

            # Remove the last user and assistant messages from history on fallback?

            # This prevents the failed interaction from polluting future context.

            if len(conversation_history) >= 2:

                conversation_history.pop()  # Remove assistant placeholder/response

                conversation_history.pop()  # Remove user prompt

            return random.choice(PLAYER_WORD_NAMES)

        # --- End Validation Logic ---

    # Correct indentation for except blocks

    except ollama.ResponseError as e:

        print(
            f"Ollama API Error: {e.error}. Status code: {e.status_code}. Falling back to random."
        )

        # Remove the last user message from history on error

        if conversation_history and conversation_history[-1]["role"] == "user":

            conversation_history.pop()

        return random.choice(PLAYER_WORD_NAMES)

    except Exception as e:

        print(f"Error querying LLM via ollama chat: {e}. Falling back to random.")

        # Remove the last user message from history on error

        if conversation_history and conversation_history[-1]["role"] == "user":

            conversation_history.pop()

        return random.choice(PLAYER_WORD_NAMES)


def what_beats(system_word: str) -> int:
    """

    Determines which word ID beats the given system word.

    Currently uses LLM, falls back to random on error.

    """

    if not system_word:  # Handle initial empty word case

        print("No system word yet, choosing random.")

        return random.randint(1, 77)

    # --- LLM Strategy ---

    chosen_word_name = get_llm_choice(system_word)

    chosen_word_id = PLAYER_WORDS_DATA.get(chosen_word_name, {}).get("id")

    if chosen_word_id:

        return chosen_word_id

    else:

        # Fallback if lookup fails after LLM choice (shouldn't happen with validation/correction)

        print(
            f"Could not find ID for chosen word '{chosen_word_name}' after potential correction. Choosing random."
        )

        return random.randint(1, 77)

    # --- Random Strategy (Fallback/Alternative) ---

    # print("Choosing random word.")

    # return random.randint(1, 77)


post_url = f"{HOST}/submit-word"
get_url = f"{HOST}/get-word"
status_url = f"{HOST}/status"

'''
def play_game(player_id):

    for round_id in range(1, NUM_ROUNDS+1):
        round_num = -1
        while round_num != round_id:
            response = requests.get(get_url)
            print(response.json())
            sys_word = response.json()['word']
            round_num = response.json()['round']

            sleep(1)

        if round_id > 1:
            status = requests.post(status_url, json={"player_id": player_id})
            # print(status.json())

        choosen_word = what_beats(sys_word)
        # print(f"Chosen word: {choosen_word}")
        data = {"player_id": player_id, "word_id": choosen_word, "round_id": round_id}
        response = requests.post(post_url, json=data)
        #print(response.json())
'''      


def play_game(player_id):

    def get_round():
        response = requests.get(get_url)
        print(response.json())
        sys_word = response.json()['word']
        round_num = response.json()['round']
        return (sys_word, round_num)

    submitted_rounds = []
    round_num = 0

    while round_num != NUM_ROUNDS :
        print(submitted_rounds)
        sys_word, round_num = get_round()
        while round_num == 0 or round_num in submitted_rounds:
            sys_word, round_num = get_round()
            sleep(0.5)

        if round_num > 1:
            status = requests.post(status_url, json={"player_id": player_id}, timeout=2)
            print(status.json())

        choosen_word = what_beats(sys_word)
        data = {"player_id": player_id, "word_id": choosen_word, "round_id": round_num}
        response = requests.post(post_url, json=data, timeout=5)
        submitted_rounds.append(round_num)
        print("POST: !!!!!!!!!!!!!!!!")
        print(response.json())
        

def register(player_id):
    register_url = f"{HOST}/register"
    data = {"player_id": player_id}
    response = requests.post(register_url, json=data)
    
    return response.json()
    

if __name__ == "__main__":

    # VERY IMPORTANT: Initialize the chat before using it

    initialize_chat()

    # For testing purposes, call get_llm_choice 5 times with a sample word.

    # Record the time taken for each call.

    # Use 5 different words to test the LLM's response time.

    
    # import time

    # words = ["Elephant", "Poacher", "Atom", "Blood cell", "Bacteria"]
    
    # for word in words:

    #     start_time = time.time()

    #     print(f"--- Testing get_llm_choice with DEBUG={DEBUG} ---")

    #     chosen_word = get_llm_choice(word)

    #     end_time = time.time()

    #     print(f"Chosen Word: {chosen_word}")

    #     print(f"Time taken: {end_time - start_time:.2f} seconds")
    

    # Uncomment below to run the actual game

    register(PLAYER_ID)
    play_game(PLAYER_ID)
