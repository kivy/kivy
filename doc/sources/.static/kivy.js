function updateheadercookie(st) {
	$.cookie('kivy.header', st);
}

function hideheader(do_animation) {
	if (do_animation) {
		$('#wrapper').animate({'padding-top': '40'}, 500);
		$('div.anchor').animate({'margin-top': '-40'}, 500);
		$('#topbar').animate({'margin-top': '-120'}, 500);
	} else {
		$('#wrapper').css('padding-top', '40px');
		$('div.anchor').css('margin-top', '-40px');
		$('#topbar').css('margin-top', '-120px');
	}
	$('#toggleheader').html('Expand header');
	updateheadercookie('hide');
}

function showheader() {
	$('#wrapper').animate({'padding-top': '160'}, 500);
	$('div.anchor').animate({'margin-top': '-160'}, 500);
	$('#topbar').animate({'margin-top': '0'}, 500);
	$('#toggleheader').html('Hide header');
	updateheadercookie('show');
}

$(document).ready(function () {

	st = $.cookie('kivy.header')
	if ( st == 'hide' )
		hideheader();
	else
		showheader();
	$('#toggleheader').click(function() {
		if ( $.cookie('kivy.header') == 'hide' )
			showheader();
		else
			hideheader(true);
	});


	$(['div.section[id]', 'dt[id]']).each(function(i1, elem) {
		$(elem).each(function(i2, e) {
			var eid = $(e).attr('id');
			$(e).removeAttr('id');
			$('<div></div>').attr('id', eid).addClass('anchor').insertBefore(e);
		});
	});
});
