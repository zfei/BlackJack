$(document).ready(function() {

  getTokens();

	$.ajax({
	  url: '/games',
	  type: 'GET',
	  dataType: 'json',
	  success: function(data, textStatus, xhr) {
      for (key in data) {
        if ( !data[key]['end'] ) {
          $('#games').append('<a onclick="connect(' + data[key]['id'] + ');">' + data[key]['name'] + '</a>');
        }
      };
	  }
	});

  $('#create_button').click(function() {
    $.ajax({
      url: '/games',
      type: 'POST',
      dataType: 'json',
      data: {'name': $('#create_name').val(),
             'player_max': $('#create_max').val()},
      success: function(data, textStatus, xhr) {
        location.reload(true);
      }
    });
  });

});

function getTokens() {
  $.ajax({
    url: '/player',
    type: 'GET',
    dataType: 'html',
    success: function(data, textStatus, xhr) {
      $('#tokens').html('Your Tokens: ' + data);
    }
  });
}

function connect(game_id) {
  gid = game_id;
  $.ajax({
    url: '/game/' + gid + '/playerConnect',
    type: 'POST',
    dataType: 'html',
    data: {'player': pid},
    success: function(data, textStatus, xhr) {
      if( data === 'error' ) {
        alert('Failed joining the game. Maybe this room is full.');
      } else {
        $('#lobby_wrapper').fadeOut('slow', function(){
          getTableInfo();
          $('#game_wrapper').fadeIn('slow');
          setInterval(function(){
            getTableInfo();
          }, 1000);
        });
      }
    }
  });
}

function getTableInfo() {
  $.ajax({
    url: '/game/' + gid + '/visible_table',
    type: 'GET',
    dataType: 'html',
    success: function(data, textStatus, xhr) {
      $('#table').html(data);
    }
  });
}

function bet() {
  var amount = prompt("Please make your bet.", 10);
  $.ajax({
    url: '/game/' + gid + '/action',
    type: 'POST',
    dataType: 'html',
    data: {'player_id': pid, 'action': 'bet', 'value': amount},
    success: function(data, textStatus, xhr) {
      if( data === 'error' ) {
        alert('Failed making bet. Please check your amount.');
      } else {
        alert('Succeeded.');
      }
      getTableInfo();
    }
  });
}

function hit() {
  $.ajax({
    url: '/game/' + gid + '/action',
    type: 'POST',
    dataType: 'html',
    data: {'player_id': pid, 'action': 'hit'},
    success: function(data, textStatus, xhr) {
      if( data === 'error' ) {
        alert('Failed drawing card. Maybe you chose to stand, doubled down, or busted.');
      } else {
        alert('Succeeded.');
      }
      getTableInfo();
    }
  });
}

function stand() {
  $.ajax({
    url: '/game/' + gid + '/action',
    type: 'POST',
    dataType: 'html',
    data: {'player_id': pid, 'action': 'stand'},
    success: function(data, textStatus, xhr) {
      if( data === 'error' ) {
        alert('Failed. Maybe you chose to stand, doubled down, or busted.');
      } else {
        alert('Succeeded.');
      }
      getTableInfo();
    }
  });
}