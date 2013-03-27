BlackJack
=========

An online BlackJack game on GAE

Demo
=========
http://zblackjackf.appspot.com/
Please use sparsingly. It's polling every single second. ToT

What to expect
=========

* A blackjack game.

* You can double down.

* Supports more than 2 players.

* Currently using polling instead of Channel API.

* Basic memcache handled by ndb.

* Supports Cross Origin Request Sharing. You can write your own client to play. (if you want)

* Concurrency is taken into consideration with properly use of transactions.
