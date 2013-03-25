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


class Game(ndb.Model):
  name = ndb.StringProperty()
  id = ndb.IntegerProperty()
  player_max = ndb.IntegerProperty()
  players_current = ndb.IntegerProperty()

  def create_game(self, new_game):
    self.name = new_game['name']
    self.id = id_gen(16)
    self.player_max = 2
    self.players_current = 0
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


class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            if Player.query(Player.email == user.email()).fetch() == []:
                Player().create_player({'name': user.nickname(), 
                                        'email': user.email()}).put()
            template_values = {'user': user.nickname()}
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
    def post(self):
        player_name = cgi.escape(self.request.get('player'))
        return


class StatusHandler(webapp2.RequestHandler):
    def get(self):
        return


class TableHandler(webapp2.RequestHandler):
    def get(self):
        return


class ActionHandler(webapp2.RequestHandler):
    def post(self):
        return


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/games', GamesHandler),
    ('/game/[id]/playerConnect', ConnectHandler),
    ('/game/[id]/status', StatusHandler),
    ('/game/id/visible_table', TableHandler),
    ('/game/id/action', ActionHandler)
], debug=True)
