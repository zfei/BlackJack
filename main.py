#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
import cgi
import json
import random
from google.appengine.ext import ndb
from google.appengine.api import users
from cors.cors_application import CorsApplication
from cors.cors_options import CorsOptions


def id_gen(len=16):
    return int(str(int(random.random() * (10**len))).zfill(len))


def deck_gen():
    suit = ['h', 'd', 's', 'c']
    rank = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = []
    for s in suit:
        for r in rank:
            deck.append(r + s)
    random.shuffle(deck)
    return deck


def card_prettifier(raw):
    card = ''
    raw_len = len(raw)
    if raw[raw_len - 1] == 'h':
        card = '&hearts;'
    elif raw[raw_len - 1] == 'd':
        card = '&diams;'
    elif raw[raw_len - 1] == 's':
        card = '&spades;'
    elif raw[raw_len - 1] == 'c':
        card = '&clubs;'
    if raw_len == 3:
        card += '10'
    else:
        card += raw[0]
    return card


def card_sum(cards):
    sum = 0
    a_counter = 0
    for card in cards:
        card_len = len(card)
        if card_len == 3:
            sum += 10
        elif card[0] == 'A':
            sum += 11
            a_counter += 1
        elif (card[0] == 'J' or card[0] == 'Q' or card[0] == 'K'):
            sum += 10
        else:
            sum += int(card[0])
    while sum > 21:
        if a_counter > 0:
            sum -= 10
            a_counter -= 1
        else:
            break
    return sum


class Game(ndb.Model):
    name = ndb.StringProperty()
    id = ndb.IntegerProperty()
    player_max = ndb.IntegerProperty()
    players_current = ndb.IntegerProperty()
    players = ndb.TextProperty()
    common_visible = ndb.TextProperty()
    common_hidden = ndb.TextProperty()
    deck = ndb.TextProperty()
    end = ndb.BooleanProperty()

    def create_game(self, new_game):
        self.name = new_game['name']
        self.id = id_gen(16)
        if new_game['player_max'] == '':
            self.player_max = 13
        else:
            self.player_max = int(new_game['player_max'])
        self.players_current = 0
        self.players = '[]'
        the_deck = deck_gen()
        the_common = []
        the_common.append(the_deck.pop())
        the_common_hidden = the_deck.pop()
        self.common_visible = json.dumps(the_common)
        self.common_hidden = the_common_hidden
        self.deck = json.dumps(the_deck)
        self.end = False
        return self

    def to_json(self):
        json_obj = {'name': self.name, 'id': self.id, 
                    'player_max': self.player_max, 
                    'players_current': self.players_current,
                    'end': self.end}
        return json_obj


class Player(ndb.Model):
    name = ndb.StringProperty()
    id = ndb.IntegerProperty()
    tokens = ndb.IntegerProperty()
    email = ndb.StringProperty()

    def create_player(self, new_player):
        self.name = new_player['name']
        self.id = id_gen(4)
        self.tokens = 1000
        self.email = new_player['email']
        return self

    def to_json(self):
        json_obj = {'name': self.name, 'id': self.id, 
                    'tokens': self.tokens, 
                    'email': self.email}
        return json_obj


class Status(ndb.Model):
    game = ndb.IntegerProperty()
    player = ndb.IntegerProperty()
    your_actions = ndb.TextProperty()
    your_visible = ndb.TextProperty()
    your_hidden = ndb.TextProperty()
    bet = ndb.IntegerProperty()

    def create_status(self, new_status):
        self.game = new_status['game']
        self.player = new_status['player']
        self.your_actions = '[]'
        self.your_visible = '[]'
        self.your_hidden = ''
        self.bet = 0
        return self

    def to_json(self):
        the_game = Game.query(Game.id == self.game).fetch()[0]
        players_id = json.loads(the_game.players)
        # players_json = []
        # for pid in players_id:
        #     players_json.append(
        #         Player.query(Player.id == pid).fetch()[0].to_json())
        json_obj = {
            'name': str(the_game.name),
            'your_actions': json.loads(self.your_actions), 
            'your_cards_visisble': json.loads(self.your_visible), 
            'common_cards_visible': json.loads(the_game.common_visible),
            # 'players': players_json}
            'players': players_id,
            'bet': self.bet}
        return json_obj


class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            if Player.query(Player.email == user.email()).fetch() == []:
                Player().create_player({'name': user.nickname(), 
                                        'email': user.email()}).put()
            template_values = {
                'user': user.nickname(),
                'player_id': Player.query(
                    Player.email == user.email()).fetch()[0].id
                }
            template = jinja_environment.get_template('/template/index.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))


class PlayerHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        the_player = Player.query(Player.email == user.email()).fetch()[0]
        self.response.out.write(the_player.tokens)


class GamesHandler(webapp2.RequestHandler):
    def get(self):
        games = []
        for each_game in Game.query():
            games.append(each_game.to_json())
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(games))

    def post(self):
        new_game = {}
        new_game['name'] = cgi.escape(self.request.get('name'))
        new_game['player_max'] = cgi.escape(self.request.get('player_max'))
        new_game = Game().create_game(new_game)
        new_game.put()


class ConnectHandler(webapp2.RequestHandler):
    def post(self, gid):
        gid = int(gid)
        pid = int(cgi.escape(self.request.get('player')))
        if Status.query(
            ndb.AND(Status.player == pid, Status.game == gid)).fetch() == []:
            the_game = Game.query(Game.id == gid).fetch()[0]
            if the_game.player_max <= the_game.players_current:
                self.response.out.write('error')
            else:
                new_status = {}
                new_status['game'] = gid
                new_status['player'] = pid
                Status().create_status(new_status).put()
                the_game.players_current += 1
                the_players = json.loads(str(the_game.players))
                the_players.append(pid)
                the_game.players = json.dumps(the_players)
                the_game.put()
                self.response.out.write('ok')
        else:
            self.response.out.write('ok')


class StatusHandler(webapp2.RequestHandler):
    def get(self, gid):
        gid = int(gid)
        pid = int(cgi.escape(self.request.get('player_id')))
        the_status = Status.query(
            ndb.AND(Status.player == pid, Status.game == gid)).fetch()[0]
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(the_status.to_json()))


class TableHandler(webapp2.RequestHandler):
    def get(self, gid):
        gid = int(gid)
        the_game = Game.query(Game.id == gid).fetch()[0]
        snippet = ''
        if the_game.end:
            snippet = '<script>\
            alert("Game Ends. Please check your tokens.");\
            location.reload(true);</script>'
        snippet += '<p id="info"><span id="game_name">\
            ' + the_game.name + '</span> '
        snippet += '<span id="player_count">(' + str(
            the_game.players_current) + '/' + str(the_game.player_max) + ')\
            </span>'
        snippet += '</p>'
        snippet += '<p class="cards" id="dealer"><span>Dealer</span>'
        snippet += '<span>**</span>'
        for common_card in json.loads(str(the_game.common_visible)):
            snippet += '<span>' + card_prettifier(common_card) + '</span>'
        snippet += '</p>'
        for pid in json.loads(str(the_game.players)):
            the_status = Status.query(
                ndb.AND(Status.player == pid, Status.game == gid)).fetch()[0]
            snippet += '<p class="cards" id="' + str(pid) + '"><span>\
                ' + Player.query(Player.id == pid).fetch()[0].name + '</span>'
            if the_status.bet != 0:
                the_player = Player.query(Player.id == pid).fetch()[0]
                user = users.get_current_user()
                if the_player.email == user.email():
                    snippet += '<span>' + card_prettifier(
                        the_status.your_hidden) + '</span>'
                else:
                    snippet += '<span>**</span>'
                for your_card in json.loads(str(the_status.your_visible)):
                    snippet += '<span>\
                    ' + card_prettifier(your_card) + '</span>'
            snippet += '</p>'
        self.response.out.write(snippet)


class ActionHandler(webapp2.RequestHandler):
    def post(self, gid):
        gid = int(gid)
        pid = int(cgi.escape(self.request.get('player_id')))
        action = str(cgi.escape(self.request.get('action')))
        if self.request.get('value'):
            value = int(cgi.escape(self.request.get('value')))
        the_player = Player.query(Player.id == pid).fetch()[0]
        the_status = Status.query(
                ndb.AND(Status.player == pid, Status.game == gid)).fetch()[0]
        the_game = Game.query(Game.id == gid).fetch()[0]
        if action == 'bet':
            if the_status.bet == 0:
                if value <= the_player.tokens and value > 0:
                    your_actions = json.loads(str(the_status.your_actions))
                    your_actions.append('bet')
                    the_status.your_actions = json.dumps(your_actions)
                    the_status.bet = value
                    the_player.tokens -= value

                    the_deck = json.loads(str(the_game.deck))
                    if the_deck == []:
                        the_deck = deck_gen()
                    your_hidden = the_deck.pop()
                    if the_deck == []:
                        the_deck = deck_gen()
                    your_visible = [the_deck.pop()]
                    the_game.deck = json.dumps(the_deck)

                    the_status.your_hidden = your_hidden
                    the_status.your_visible = json.dumps(your_visible)
                    the_game.put()
                    the_status.put()
                    the_player.put()
                    self.response.out.write('ok')
                else:
                    self.response.out.write('error')
            else:
                if value <= the_player.tokens and value == the_status.bet:
                    your_actions = json.loads(str(the_status.your_actions))
                    bet_counter = 0
                    for act in your_actions:
                        if act == 'bet':
                            bet_counter += 1
                    if bet_counter > 1:
                        self.response.out.write('error')
                        return
                    your_actions.append('bet')
                    the_status.your_actions = json.dumps(your_actions)
                    the_status.bet += value
                    the_player.tokens -= value

                    the_deck = json.loads(str(the_game.deck))
                    if the_deck == []:
                        the_deck = deck_gen()
                    your_visible = json.loads(str(the_status.your_visible))
                    your_visible.append(the_deck.pop())
                    the_game.deck = json.dumps(the_deck)
                    the_status.your_visible = json.dumps(your_visible)
                    the_game.put()

                    the_status.put()
                    the_player.put()
                    self.response.out.write('ok')
                else:
                    self.response.out.write('error')
            return
        elif action == 'hit':
            if the_status.bet == 0:
                self.response.out.write('error')
            else:
                your_actions = json.loads(str(the_status.your_actions))
                bet_counter = 0
                for act in your_actions:
                    if act == 'bet':
                        bet_counter += 1
                if bet_counter == 2:
                    self.response.out.write('error')
                elif your_actions[len(your_actions) - 1] == 'stand':
                    self.response.out.write('error')
                else:
                    your_actions.append('hit')
                    
                    the_deck = json.loads(str(the_game.deck))
                    if the_deck == []:
                        the_deck = deck_gen()
                    your_visible = json.loads(str(the_status.your_visible))
                    your_visible.append(the_deck.pop())
                    the_game.deck = json.dumps(the_deck)
                    the_status.your_visible = json.dumps(your_visible)
                    the_game.put()

                    cards = json.loads(str(the_status.your_visible))
                    cards.append(str(the_status.your_hidden))
                    if card_sum(cards) > 21:
                        your_actions.append('stand')
                    the_status.your_actions = json.dumps(your_actions)
                    the_status.put()
                    self.response.out.write('ok')
        elif action == 'stand':
            your_actions = json.loads(str(the_status.your_actions))
            if your_actions[len(your_actions) - 1] == 'stand':
                self.response.out.write('error')
            else:
                your_actions.append('stand')
                the_status.your_actions = json.dumps(your_actions)
                the_status.put()
                self.response.out.write('ok')
        else:
            self.response.out.write('error')

        stand_flag = True
        for the_pid in json.loads(str(the_game.players)):
            the_status = Status.query(
                ndb.AND(Status.player == the_pid, 
                Status.game == gid)).fetch()[0]
            your_actions = json.loads(str(the_status.your_actions))
            if your_actions[len(your_actions) - 1] != 'stand':
                stand_flag = False
                break
        if stand_flag:
            dealer_bust = False
            dealer_cards = json.loads(str(the_game.common_visible))
            dealer_cards.append(str(the_game.common_hidden))
            the_deck = json.loads(str(the_game.deck))
            while card_sum(dealer_cards) <= 16:
                if the_deck == []:
                    the_deck = deck_gen()
                dealer_cards.append(the_deck.pop())
            if card_sum(dealer_cards) > 21:
                dealer_bust = True
            for the_pid in json.loads(str(the_game.players)):
                the_status = Status.query(
                    ndb.AND(Status.player == the_pid, 
                    Status.game == gid)).fetch()[0]
                player_cards = json.loads(str(the_status.your_visible))
                player_cards.append(str(the_status.your_hidden))
                if card_sum(player_cards) <= 21:
                    if not dealer_bust:
                        user = users.get_current_user()
                        if card_sum(player_cards) > card_sum(dealer_cards):
                            the_player = Player.query(
                                Player.email == user.email()).fetch()[0]
                            the_player.tokens += the_status.bet * 2
                            the_player.put()
                    else:
                        the_player = Player.query(
                                Player.email == user.email()).fetch()[0]
                        the_player.tokens += the_status.bet * 2
                        the_player.put()
            the_game.end = True
            the_game.put()
        else:
            return


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

base_app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/player', PlayerHandler),
    ('/games', GamesHandler),
    ('/game/(\d+)/playerConnect', ConnectHandler),
    ('/game/(\d+)/status', StatusHandler),
    ('/game/(\d+)/visible_table', TableHandler),
    ('/game/(\d+)/action', ActionHandler)
], debug=True)


app = CorsApplication(base_app,
                      CorsOptions(allow_origins=True,
                                  continue_on_error=True))


# app = webapp2.WSGIApplication([
#     ('/', MainHandler),
#     ('/player', PlayerHandler),
#     ('/games', GamesHandler),
#     ('/game/(\d+)/playerConnect', ConnectHandler),
#     ('/game/(\d+)/status', StatusHandler),
#     ('/game/(\d+)/visible_table', TableHandler),
#     ('/game/(\d+)/action', ActionHandler)
# ], debug=True)
