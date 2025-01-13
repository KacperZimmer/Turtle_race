from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from config import Config
app = Flask(__name__)



mysql = MySQL(app)

app.config.from_object(Config)

turtle_colors = {
    'blue': '#1e90ff',
    'green': '#32cd32',
    'red': '#ff4500',
    'yellow': '#ffd700',
    'purple': '#800080'
}

game_state = {
    "cells": [
        ['blue', 'green', 'yellow', 'red', 'purple'],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        []
    ],
}


@app.route('/')
def index():
    return render_template('main_page.html')


@app.route('/add_player', methods=['POST'])
def add_player():
    if request.method == 'POST':
        name = request.form['name']

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO players (name) VALUES (%s)', (name,))
        player_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('game_wait', player_id=player_id))


@app.route('/game/wait', methods=['GET', 'POST'])
def game_wait():
    player_id = request.args.get('player_id') or request.form.get('player_id')

    if request.method == 'POST' and player_id is not None:
        accepted = request.form.get('accepted') == 'true'

        cur = mysql.connection.cursor()

        cur.execute('SELECT COUNT(*) FROM accepted WHERE player_id = %s', (player_id,))
        exists = cur.fetchone()[0] > 0

        if not exists:
            cur.execute('INSERT INTO accepted (player_id, accepted) VALUES (%s, %s)', (player_id, accepted))
            mysql.connection.commit()



        cur.close()

    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(*) FROM players')
    total_players = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM accepted WHERE accepted = TRUE')
    accepted_players = cur.fetchone()[0]
    cur.close()

    return render_template('waiting_screen.html', player_id=player_id, total_players=total_players, accepted_players=accepted_players)



@app.route('/game', methods=['GET'])
def game():
    return render_template("index.html", game_state=game_state, turtle_colors=turtle_colors)


if __name__ == '__main__':
    app.run(debug=True)
