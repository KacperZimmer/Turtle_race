from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mysqldb import MySQL
from config import Config
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app)

mysql = MySQL(app)
app.config.from_object(Config)

turtles = [
    'blue',
    'yellow',
    'red',
    'green',
    'purple',
]


cards = {
    "Yellow:+1",
    "Yellow:-1",
    "Green:+1" ,
    "Green:-1",
    "Red:+1" ,
    "Red:-1",
    "Blue:+1" ,
    "Blue:-1",
    "Purple:+1",
    "Purple:-1",
    "Joker:+1" ,
    "Joker:-1",
    "Joker:+2"
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


@app.route('/play_card', methods=['POST'])
def play_card():
    data = request.get_json()
    card = data['card']
    player_id = data['player_id']

    cur = mysql.connection.cursor()

    try:
        cur.execute("""
            DELETE FROM player_cards 
            WHERE player_id = %s AND card = %s 
            LIMIT 1
        """, (player_id, card))

        new_card = random.choice(list(cards))
        cur.execute("""
            INSERT INTO player_cards (player_id, card)
            VALUES (%s, %s)
        """, (player_id, new_card))

        mysql.connection.commit()

        socketio.emit('card_played', {
            'player_id': player_id,
            'card': card,
            'new_card': new_card,
        })

        return jsonify({
            'success': True,
            'new_card': new_card
        })

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'error': str(e)})

    finally:
        cur.close()
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

import random

@app.route('/game', methods=['GET'])
def game():
    turtle_colors = {
        'blue': '#1e90ff',
        'green': '#32cd32',
        'red': '#ff4500',
        'yellow': '#ffd700',
        'purple': '#800080'
    }

    player_id = request.args.get('player_id')
    if not player_id:
        return redirect(url_for('index'))

    try:
        player_id = int(player_id)
    except ValueError:
        return "Nieprawidłowy ID gracza.", 400

    cur = mysql.connection.cursor()

    cur.execute("SELECT name FROM players WHERE id = %s", (player_id,))
    player_data = cur.fetchone()

    if not player_data:
        return "Nie znaleziono gracza.", 404

    cur.execute("SELECT card FROM player_cards WHERE player_id = %s", (player_id,))
    player_cards = [row[0] for row in cur.fetchall()]

    if not player_cards:
        drawn_cards = random.sample(cards, 4)
        for card in drawn_cards:
            cur.execute("INSERT INTO player_cards (player_id, card) VALUES (%s, %s)", (player_id, card))
        mysql.connection.commit()
    else:
        drawn_cards = player_cards

    cur.execute("SELECT turtle_color FROM turtle_colors WHERE player_id = %s", (player_id,))
    turtle_color_data = cur.fetchone()
    cur.close()

    if not turtle_color_data:
        return "Nie przypisano koloru żółwia.", 404

    player_name = player_data[0]
    player_turtle_color = turtle_color_data[0]

    return render_template(
        "index.html",
        game_state=game_state,
        turtle_colors=turtle_colors,
        cards=cards,
        player_id=player_id,
        player_name=player_name,
        player_turtle_color=player_turtle_color,
        drawn_cards=drawn_cards
    )

@app.route('/make_move', methods=['POST'])
def make_move():
    if request.method == 'POST':
        data = request.get_json()
        turtle_color = data['turtle_color']
        new_position = data['new_position']

        for cell in game_state['cells']:
            if turtle_color in cell:
                cell.remove(turtle_color)

        game_state['cells'][new_position].append(turtle_color)

        socketio.emit('update_game_state', game_state)

        return "Move made", 200

@socketio.on('connect')
def handle_connect():
    emit('update_game_state', game_state)


@socketio.on('join_room')
def handle_join_room(data):
    player_id = data['player_id']
    join_room(f'player_{player_id}')

@socketio.on('player_accepted')
def handle_player_accepted(data):
    player_id = data['player_id']
    accepted = data['accepted']

    cur = mysql.connection.cursor()
    cur.execute('SELECT turtle_color FROM turtle_colors')
    used_turtles = [row[0] for row in cur.fetchall()]
    available_turtles = [turtle for turtle in turtles if turtle not in used_turtles]

    if not available_turtles:
        emit('error', {'message': 'Brak dostępnych kolorów żółwi'}, room=f'player_{player_id}')
        return

    random_player_turtle = random.choice(available_turtles)

    cur.execute('SELECT COUNT(*) FROM accepted WHERE player_id = %s', (player_id,))
    exists = cur.fetchone()[0] > 0

    if not exists:
        cur.execute('INSERT INTO accepted (player_id, accepted) VALUES (%s, %s)', (player_id, accepted))
        mysql.connection.commit()

    cur.execute('SELECT COUNT(*) FROM accepted WHERE accepted = TRUE')
    accepted_players = cur.fetchone()[0]

    cur.execute('INSERT INTO turtle_colors (player_id, turtle_color) VALUES (%s, %s)',
                (player_id, random_player_turtle))
    mysql.connection.commit()

    cur.close()

    emit('update_acceptance', {'accepted_players': accepted_players}, broadcast=True)

    if accepted_players >= 2:
        cur = mysql.connection.cursor()
        cur.execute('SELECT player_id FROM accepted WHERE accepted = TRUE')
        accepted_player_ids = cur.fetchall()
        cur.close()

        for pid in accepted_player_ids:
            emit('start_game', {'url': f'/game?player_id={pid[0]}', 'player_id': pid[0]}, room=f'player_{pid[0]}')

if __name__ == '__main__':
    socketio.run(app, debug=True)
