$(document).ready(function(){

	$.ajax({
	  url: '/games',
	  type: 'GET',
	  dataType: 'json',
	  complete: function(xhr, textStatus) {
	    //called when complete
	  },
	  success: function(data, textStatus, xhr) {
      for (key in data) {
        $('#games').append('<a href="#' + data[key]['id'] + '">' + data[key]['name'] + '</a>');
      };
	  },
	  error: function(xhr, textStatus, errorThrown) {
	    //called when there is an error
	  }
	});

  $('#create_button').click(function(){
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