$(document).scroll(function(){
    $('#mainNav').toggleClass('scrolled', $(this).scrollTop() > 0);
});

var jumboHeight = $('.jumbotron').outerHeight();

function parallax(){
    var scrolled = $(window).scrollTop();
    $('header').css('background-position-y', (-scrolled) + 'px');
}

$(window).scroll(function(e){
    parallax();
});


$( "#dialog-link, #icons li" ).hover(
	function() {
		$( this ).addClass( "ui-state-hover" );
	},
	function() {
		$( this ).removeClass( "ui-state-hover" );
	}
);