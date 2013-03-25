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
import json
import random
from google.appengine.ext import ndb


class Game(ndb.Model):
  name = ndb.StringProperty()
  id = ndb.IntegerProperty()
  player_max = ndb.IntegerProperty()
  players_current = ndb.IntegerProperty()

  def create_game(self, new_game):
  	self.name = new_game["name"]
  	self.id = gid_gen()
  	self.player_max = 2
  	self.players_current = 0
  	return self

  def to_json(self):
  	json_obj = {'name': self.name, 'id': self.id, 
  				'player_max': self.player_max, 
  				'players_current': self.players_current}
  	return json_obj


def gid_gen():
    return int(str(int(random.random() * 1e16)).zfill(16))


class MainHandler(webapp2.RequestHandler):
    def get(self):
    	games = []
    	template_values = {
            'games': games
        }
        template = jinja_environment.get_template('/template/index.html')
        self.response.out.write(template.render(template_values))


class GamesHandler(webapp2.RequestHandler):
    def get(self):
    	games = []
    	for each_game in Game.query():
    		games.append(each_game.to_json())
		self.response.headers['Content-Type'] = 'application/json'
    	self.response.out.write(json.dumps(games))

    def post(self):
    	new_game = json.loads(cgi.escape(self.request.get('new_game')))
    	new_game = Game().create_game(new_game)
    	new_game.put()


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/games', GamesHandler)
], debug=True)
