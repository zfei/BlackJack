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

function connect(gid) {
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
        });
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      //called when there is an error
    }
  });
}

function getTableInfo(gid, pid) {
  
}