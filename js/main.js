$(document).ready(function() {

	$.ajax({
	  url: '/games',
	  type: 'GET',
	  dataType: 'json',
	  complete: function(xhr, textStatus) {
	    //called when complete
	  },
	  success: function(data, textStatus, xhr) {
      for (key in data) {
        $('#games').append('<a onclick="connect(' + data[key]['id'] + ');">' + data[key]['name'] + '</a>');
      };
	  },
	  error: function(xhr, textStatus, errorThrown) {
	    //called when there is an error
	  }
	});

  $('#create_button').click(function() {
    $.ajax({
      url: '/games',
      type: 'POST',
      dataType: 'json',
      data: {'name': $('#create_name').val(),
             'player_max': $('#create_max').val()},
      complete: function(xhr, textStatus) {
        //called when complete
      },
      success: function(data, textStatus, xhr) {
        location.reload(true);
      },
      error: function(xhr, textStatus, errorThrown) {
        //called when there is an error
      }
    });
  });

});

function connect(game_id) {
  gid = game_id;
  $.ajax({
    url: '/game/' + gid + '/playerConnect',
    type: 'POST',
    dataType: 'html',
    data: {'player': pid},
    complete: function(xhr, textStatus) {
      //called when complete
    },
    success: function(data, textStatus, xhr) {
      if( data == 'error' ) {
        alert('Failed joining the game. Maybe this room is full.');
      } else {
        $('#lobby_wrapper').fadeOut('slow', function(){
          $('#game_wrapper').fadeIn('slow');
          getTableInfo();
        });
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      //called when there is an error
    }
  });
}

function getTableInfo() {
  $.ajax({
    url: '/game/' + gid + '/visible_table',
    type: 'GET',
    dataType: 'html',
    complete: function(xhr, textStatus) {
      //called when complete
    },
    success: function(data, textStatus, xhr) {
      $('#table').html(data);
    },
    error: function(xhr, textStatus, errorThrown) {
      //called when there is an error
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
    complete: function(xhr, textStatus) {
      //called when complete
    },
    success: function(data, textStatus, xhr) {
      if( data == 'error' ) {
        alert('Failed making bet. Please check your amount.');
      } else {
        alert('Succeeded.');
        getTableInfo(gid);
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      //called when there is an error
    }
  });
}

function hit() {
  $.ajax({
    url: '/game/' + gid + '/action',
    type: 'POST',
    dataType: 'html',
    data: {'player_id': pid, 'action': 'hit'},
    complete: function(xhr, textStatus) {
      //called when complete
    },
    success: function(data, textStatus, xhr) {
      if( data == 'error' ) {
        alert('Failed joining the game. Maybe this room is full.');
      } else {
        getTableInfo(gid);
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      //called when there is an error
    }
  });
}

function stand() {
  $.ajax({
    url: '/game/' + gid + '/action',
    type: 'POST',
    dataType: 'html',
    data: {'player_id': pid, 'action': 'stand'},
    complete: function(xhr, textStatus) {
      //called when complete
    },
    success: function(data, textStatus, xhr) {
      if( data == 'error' ) {
        alert('Failed joining the game. Maybe this room is full.');
      } else {
        getTableInfo(gid);
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      //called when there is an error
    }
  });
}