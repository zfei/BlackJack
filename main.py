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


def draw_card(deck):
    return deck.pop()


class Game(ndb.Model):
    name = ndb.StringProperty()
    id = ndb.IntegerProperty()
    player_max = ndb.IntegerProperty()
    players_current = ndb.IntegerProperty()
    players = ndb.TextProperty()
    common_visible = ndb.TextProperty()
    deck = ndb.TextProperty()

    def create_game(self, new_game):
        self.name = new_game['name']
        self.id = id_gen(16)
        self.player_max = 2
        self.players_current = 0
        self.players = '[]'
        the_deck = deck_gen()
        the_common = []
        the_common.append(draw_card(the_deck))
        the_common.append(draw_card(the_deck))
        self.common_visible = json.dumps(the_common)
        self.deck = json.dumps(the_deck)
        return self

    def to_json(self):
        json_obj = {'name': self.name, 'id': self.id, 
                    'player_max': self.player_max, 
                    'players_current': self.players_current}
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
    common_visible = ndb.TextProperty()

    def create_status(self, new_status):
        self.game = new_status['game']
        self.player = new_status['player']
        self.your_actions = '[]'
        self.your_visible = '[]'
        return self

    def to_json(self):
        the_game = Game.query(Game.id == self.game).fetch()[0]
        json_obj = {
            'your_actions': json.loads(self.your_actions), 
            'your_cards_visisble': json.loads(self.your_visible), 
            'common_cards_visible': json.loads(the_game.common_visible),
            'players': json.loads(the_game.players)}
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
        return


class ActionHandler(webapp2.RequestHandler):
    def post(self, gid):
        return


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/games', GamesHandler),
    ('/game/(\d+)/playerConnect', ConnectHandler),
    ('/game/(\d+)/status', StatusHandler),
    ('/game/(\d+)/visible_table', TableHandler),
    ('/game/(\d+)/action', ActionHandler)
], debug=True)
