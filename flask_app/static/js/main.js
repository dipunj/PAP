$(document).scroll(function () {
	$('#mainNav').toggleClass('scrolled', $(this).scrollTop() > 0);
});

var jumboHeight = $('.jumbotron').outerHeight();

function parallax() {
	var scrolled = $(window).scrollTop();
	$('header').css('background-position-y', (-scrolled) + 'px');
}

$(window).scroll(function (e) {
	parallax();
});



$('#newPass, #confNewPass').on('keyup', function () {
	if ($('#newPass').val() == $('#confNewPass').val()) {
	  $('#passMatch').html('Matching').css('color', 'green');
	} else 
	  $('#passMatch').html('Do not Match').css('color', 'red');
  });