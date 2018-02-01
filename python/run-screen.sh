screen -dmS discord-bot sh
screen -S discord-bot -X stuff "cd /media/Data2/programming/Discord-Nomic/python
"
screen -S discord-bot -X stuff "~/.local/bin/pipenv run python3 main.py
"
