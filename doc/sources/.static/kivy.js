$(document).ready(function () {
	var height = $(document).height();
	$('#content').css('min-height', function(){ return height; });

	// insert breaker only for the first data/class/function found.
	var apibreaker = false;
	$('div.body dl[class]').each(function (i1, elem) {
		// theses are first level class: attribute and method are inside class.
		if (!$(elem).hasClass('data') &&
			!$(elem).hasClass('class') &&
			!$(elem).hasClass('exception') &&
			!$(elem).hasClass('function'))
			return;
		// dont accept dl inside dl
		if ($(elem).parents().filter('dl').length > 0)
			return;

		$(elem).addClass('api-level');

		if ( apibreaker == true )
			return;
		$('<div id="api"></div>')
			.attr('id', 'api')
			.html(
				$('<h2>API ' +
				  '<a id="api-toggle-all" class="showed">Collapse All &uArr;</a>' +
				  '<a id="api-toggle-desc" class="showed">Hide Description &uArr;</a>' +
				  '</h2>')
				)
			.insertBefore(elem);
		apibreaker = true;
	});


	$('div.body dl[class] dt').hover(
		function() { $(this).addClass('hover'); },
		function() { $(this).removeClass('hover'); }
	);

	if ( apibreaker == true ) {
		var apilink = $('<div class="bodyshortcut">&raquo; <a id="api-link" href="#api">Jump to API</a></div>');
		apilink.insertAfter($('div.body h1:first'));
	}

	$('#api-toggle-all').click(function() {
		if ($(this).hasClass('showed')) {
			$('div.body dl.api-level > dd').slideUp();
			$(this).removeClass('showed');
			$(this).html('Expand All &dArr;');
			$.cookie('kivy.toggleall', 'true');
		} else {
			$('div.body dl.api-level > dd').slideDown();
			$(this).addClass('showed');
			$(this).html('Collapse All &uArr;');
			$.cookie('kivy.toggleall', 'false');
		}
	});

	$('#api-toggle-desc').click(function() {
		if ($(this).hasClass('showed')) {
			$('div.body dl.api-level > dd > dl > dd').slideUp();
			$(this).removeClass('showed');
			$(this).html('Show Descriptions &dArr;');
			$.cookie('kivy.toggledesc', 'true');
		} else {
			$('div.body dl.api-level > dd > dl > dd').slideDown();
			$(this).addClass('showed');
			$(this).html('Hide Descriptions &uArr;');
			$.cookie('kivy.toggledesc', 'false');
		}
		console.log($.cookie('kivy.toggledesc'));
	});

	$('div.body dl dt').click(function() {
		$(this).next().slideToggle();
	});

	if ( $.cookie('kivy.toggledesc') == 'true' ) {
		$('div.body dl.api-level > dd > dl > dd').hide();
		$('#api-toggle-desc').removeClass('showed');
		$('#api-toggle-desc').html('Show Descriptions &dArr;');
	}

	if ( $.cookie('kivy.toggleall') == 'true' ) {
		$('div.body dl.api-level > dd').hide();
		$('#api-toggle').removeClass('showed');
		$('#api-toggle').html('Expand All &dArr;');
	}

	//$('div.body dl[class]:first-child').hide();
	/**
	$('dl[class]:first-child > a[class="headerlink"]').each(function(i1, elem) {
		console.log(i1);
		console.log(elem);
		$(elem).each(function(i2, e) {
			var eid = $(e).attr('id');
			$(e).removeAttr('id');
			$('<div></div>').attr('id', eid).addClass('anchor').insertBefore(e);
		});
	});
	**/
});
