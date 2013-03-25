$(document).ready(function(){

	$.ajax({
	  url: '/games',
	  type: 'GET',
	  dataType: 'json',
	  complete: function(xhr, textStatus) {
	    //called when complete
	  },
	  success: function(data, textStatus, xhr) {
	    $('#games').append('<a href="#' + data[0]['id'] + '">' + data[0]['name'] + '</a>');
	  },
	  error: function(xhr, textStatus, errorThrown) {
	    //called when there is an error
	  }
	});
	

});