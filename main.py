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
    """Generates and returns a random id of given length"""
    return int(str(int(random.random() * (10**len))).zfill(len))


def deck_gen():
    """Generates and returns a shuffled deck of cards"""
    suit = ['h', 'd', 's', 'c']
    rank = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = []
    for s in suit:
        for r in rank:
            deck.append(r + s)
    random.shuffle(deck)
    return deck


def card_prettifier(raw):
    """Returns a card text in pretty format"""
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
    """Calculates and returns the sum of a card list"""
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
        json_obj = {
            'name': str(the_game.name),
            'your_actions': json.loads(self.your_actions), 
            'your_cards_visisble': json.loads(self.your_visible), 
            'common_cards_visible': json.loads(the_game.common_visible),
            'players': players_id,
            'bet': self.bet}
        return json_obj


class MainHandler(webapp2.RequestHandler):
    def get(self):
        """Renders client page"""
        user = users.get_current_user()
        if user:
            the_player = None
            if Player.query(Player.email == user.email()).fetch() == []:
                the_player = Player().create_player({'name': user.nickname(), 
                                                     'email': user.email()})
                the_player.put()
            if the_player == None:
                the_player = Player.query(
                    Player.email == user.email()).fetch()[0]
            template_values = {
                'user': user.nickname(),
                'player_id': the_player.id
            }
            template = jinja_environment.get_template('/template/index.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))


class PlayerHandler(webapp2.RequestHandler):
    def get(self):
        """Extra handler to deliver players' info"""
        user = users.get_current_user()
        the_player = Player.query(Player.email == user.email()).fetch()[0]
        self.response.out.write(the_player.tokens)


class GamesHandler(webapp2.RequestHandler):
    def get(self):
        """Lists all games, including inactive ones"""
        games = []
        for each_game in Game.query():
            games.append(each_game.to_json())
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(games))

    def post(self):
        """Creates new game entity"""
        new_game = {}
        new_game['name'] = cgi.escape(self.request.get('name'))
        new_game['player_max'] = cgi.escape(self.request.get('player_max'))
        new_game = Game().create_game(new_game)
        new_game.put()


@ndb.transactional(retries=100, xg=True)
def create_status(gk, pid, printer):
    """Creates game status in atomic operation"""
    the_game = gk.get()
    if the_game.player_max <= the_game.players_current:
        printer.write('error')
    else:
        new_status = {}
        new_status['game'] = the_game.id
        new_status['player'] = pid
        Status().create_status(new_status).put()
        the_game.players_current += 1
        the_players = json.loads(str(the_game.players))
        the_players.append(pid)
        the_game.players = json.dumps(the_players)
        the_game.put()
        printer.write('ok')


class ConnectHandler(webapp2.RequestHandler):
    def post(self, gid):
        """Connects player to a game specified"""
        gid = int(gid)
        pid = int(cgi.escape(self.request.get('player')))
        if Status.query(
            ndb.AND(Status.player == pid, Status.game == gid)).fetch() == []:
            # if the player hasn't connected, create a game status
            game_key = Game.query(Game.id == gid).fetch(keys_only=True)[0]
            create_status(game_key, pid, self.response.out)
        else:
            # if the player in already connected to the game, just pass
            self.response.out.write('ok')


class StatusHandler(webapp2.RequestHandler):
    def get(self, gid):
        """Returns game status"""
        gid = int(gid)
        pid = int(cgi.escape(self.request.get('player_id')))
        the_status = Status.query(
            ndb.AND(Status.player == pid, Status.game == gid)).fetch()[0]
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(the_status.to_json()))


class TableHandler(webapp2.RequestHandler):
    def get(self, gid):
        """Returns html snippet of the game table"""
        gid = int(gid)
        the_game = Game.query(Game.id == gid).fetch()[0]
        user = users.get_current_user()
        current_player = Player.query(Player.email == user.email()).fetch()[0]
        tokens = current_player.tokens
        cp_status = Status.query(ndb.AND(Status.player == current_player.id, 
                                         Status.game == gid)).fetch()[0]
        snippet = ''
        if the_game.end:
            snippet += '<p class="info end" onclick="location.reload(true);">\
                Game ends. Click here to join other games.</p>'
        else:
            snippet += '<p class="info"><span>' + the_game.name
            snippet += '  (' + str(the_game.players_current) + '/\
                ' + str(the_game.player_max) + ')</span></p>'
        snippet += '<p class="info">'
        snippet += '<span>Your tokens: ' + str(tokens) + '</span>'
        snippet += '<span>Your bet: ' + str(cp_status.bet) + '</span>'
        snippet += '<span>(Bet current bet value again to double down)</span>'
        snippet += '</p>'
        snippet += '<p class="cards" id="dealer"><span>Dealer</span>'
        if the_game.end:
            hidden_card = str(the_game.common_hidden)
            snippet += '<span>' + card_prettifier(hidden_card) + '</span>'
        else:
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
                if the_player.email == user.email() or the_game.end:
                    snippet += '<span>' + card_prettifier(
                        the_status.your_hidden) + '</span>'
                else:
                    snippet += '<span>**</span>'
                for your_card in json.loads(str(the_status.your_visible)):
                    snippet += '<span>\
                    ' + card_prettifier(your_card) + '</span>'
            snippet += '</p>'
        self.response.out.write(snippet)


@ndb.transactional(retries=100, xg=True)
def bet_transaction(gk, pk, sk, value, printer):
    the_game = gk.get()
    the_player = pk.get()
    the_status = sk.get()
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
            printer.write('ok')
        else:
            printer.write('error')
    else:
        if value <= the_player.tokens and value == the_status.bet:
            your_actions = json.loads(str(the_status.your_actions))
            bet_counter = 0
            for act in your_actions:
                if act == 'bet':
                    bet_counter += 1
            if bet_counter > 1:
                printer.write('error')
                return
            your_actions.append('bet')
            your_actions.append('stand')
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
            printer.write('ok')
        else:
            printer.write('error')
    return


@ndb.transactional(retries=100, xg=True)
def hit_transaction(gk, sk, printer):
    the_game = gk.get()
    the_status = sk.get()
    if the_status.bet == 0:
        printer.write('error')
    else:
        your_actions = json.loads(str(the_status.your_actions))
        bet_counter = 0
        for act in your_actions:
            if act == 'bet':
                bet_counter += 1
        if bet_counter == 2:
            printer.write('error')
        elif your_actions[len(your_actions) - 1] == 'stand':
            printer.write('error')
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
            printer.write('ok')


@ndb.transactional(retries=100, xg=True)
def end_the_game_transaction(gk):
    the_game = gk.get()
    if the_game.end == False:
        the_game.end = True
        the_game.put()
        return 1
    else:
        return 0


class ActionHandler(webapp2.RequestHandler):
    def post(self, gid):
        """Processes player action"""
        gid = int(gid)
        pid = int(cgi.escape(self.request.get('player_id')))
        action = str(cgi.escape(self.request.get('action')))
        if self.request.get('value'):
            value = int(cgi.escape(self.request.get('value')))
        pk = Player.query(Player.id == pid).fetch(keys_only=True)[0]
        sk = Status.query(
            ndb.AND(Status.player == pid, 
                    Status.game == gid)).fetch(keys_only=True)[0]
        gk = Game.query(Game.id == gid).fetch(keys_only=True)[0]

        # do nothing if game ended
        the_game = gk.get()
        if the_game.end:
            return

        if action == 'bet':
            bet_transaction(gk, pk, sk, value, self.response.out)
            
        elif action == 'hit':
            hit_transaction(gk, sk, self.response.out)

        elif action == 'stand':
            # We assume player won't open two windows for the same game,
            # therefore no transaction for stand action
            the_status = sk.get()
            your_actions = json.loads(str(the_status.your_actions))
            if your_actions[len(your_actions) - 1] == 'stand':
                self.response.out.write('error')
            else:
                your_actions.append('stand')
                the_status.your_actions = json.dumps(your_actions)
                the_status.put()
                self.response.out.write('ok')

        else:
            # returns error if action is undefined
            self.response.out.write('error')

        # extra processing after every player is in stand mode
        the_game = gk.get()
        the_player = pk.get()
        the_status = sk.get()
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
            if end_the_game_transaction(gk) == 0:
                return
            dealer_bust = False
            dealer_visible = json.loads(str(the_game.common_visible))
            dealer_cards = json.loads(str(the_game.common_visible))
            dealer_cards.append(str(the_game.common_hidden))
            the_deck = json.loads(str(the_game.deck))
            while card_sum(dealer_cards) <= 16:
                if the_deck == []:
                    the_deck = deck_gen()
                new_dealer_card = the_deck.pop()
                dealer_cards.append(new_dealer_card)
                dealer_visible.append(new_dealer_card)
            the_game.common_visible = json.dumps(dealer_visible)
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
                        if card_sum(player_cards) > card_sum(dealer_cards):
                            the_player = Player.query(
                                Player.id == the_pid).fetch()[0]
                            the_player.tokens += the_status.bet * 2
                            the_player.put()
                        elif card_sum(player_cards) == card_sum(dealer_cards):
                            the_player = Player.query(
                                Player.id == the_pid).fetch()[0]
                            the_player.tokens += the_status.bet
                            the_player.put()
                    else:
                        the_player = Player.query(
                            Player.id == the_pid).fetch()[0]
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
