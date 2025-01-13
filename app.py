from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from config import Config
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)  # Tworzymy instancję Socket.IO

mysql = MySQL(app)
app.config.from_object(Config)

turtle_colors = {
    'blue': '#1e90ff',
    'green': '#32cd32',
    'red': '#ff4500',
    'yellow': '#ffd700',
    'purple': '#800080'
}
cards = {
    "Yellow:+1" : 6,
    "Green:+1" : 6,
    "Red:+1" : 6,
    "Blue:+1" : 6,
    "Purple:+1" : 6,
    "Joker:+1" : 5,
    "Joker:+2": 5,
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

@app.route('/make_move', methods=['GET', 'POST'])
def make_move():
    if request.method == 'POST':
        pass
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



    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(*) FROM players')
    total_players = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM accepted WHERE accepted = TRUE')
    accepted_players = cur.fetchone()[0]
    cur.close()

    return render_template('waiting_screen.html', player_id=player_id, total_players=total_players, accepted_players=accepted_players)

@app.route('/game', methods=['GET'])
def game():
    return render_template("index.html", game_state=game_state, turtle_colors=turtle_colors, cards=cards)


@socketio.on('player_accepted')
def handle_player_accepted(data):
    player_id = data['player_id']
    accepted = data['accepted']


    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(*) FROM accepted WHERE player_id = %s', (player_id,))
    exists = cur.fetchone()[0] > 0

    if not exists:
        cur.execute('INSERT INTO accepted (player_id, accepted) VALUES (%s, %s)', (player_id, accepted))
        mysql.connection.commit()

    cur.execute('SELECT COUNT(*) FROM accepted WHERE accepted = TRUE')
    accepted_players = cur.fetchone()[0]
    cur.close()

    emit('update_acceptance', {'accepted_players': accepted_players}, broadcast=True)

    if accepted_players >= 2:
        emit('start_game', {'url': '/game', 'player_id': player_id}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
