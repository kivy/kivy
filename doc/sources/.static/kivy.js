var sections = {};
var sections_key = [];
var prev_gsid = '';
var avoidscroll = 1;
var scrollingDiv = null;
var scrolltop = null;

function gs_enable_scroll() {
	avoidscroll = 0;
	gs_scroll(0);
}

function gs_scroll(anim) {
	if ( avoidscroll )
		return;
	var sh = $(scrollingDiv).innerHeight();
	var dh = $(document).height() - 130;
	var wtop = $(window).scrollTop();
	wtop -= scrolltop;
	if ( wtop + sh > dh )
		wtop = dh - sh;
	if ( wtop < 0 )
		wtop = 0;
	if ( anim === 0 )
		scrollingDiv.css({'marginTop': wtop + 'px'});
	else
		scrollingDiv
			.stop()
			.animate({'marginTop': wtop + 'px'}, 'slow');
}

function gs_check_hash() {
	if ( location.hash.substring(0, 5) == '#doc-' ) {
		gs_show_section(location.hash.substring(5), 1);
	} else {
		var search = $('div.panelstep' + location.hash);
		if ( search && location.hash ) {
			gs_show_section(location.hash.substring(1));
		} else {
			var id = $(location.hash).parent('.panelstep').attr('id');
			if ( typeof(id) != 'undefined' )
				gs_show_section(id, 0);
			else
				gs_show_section(sections_key[0], 1);
		}
	}
	setTimeout('gs_check_hash()', 250);
}

function gs_show_section(gsid, changehash) {
	if ( prev_gsid == gsid )
		return;
	$('html, body').animate({scrollTop:0});
	$(sections_key).each(function(i, key){
		if ( gsid == key ) {
			if ( prev_gsid == '' )
				$(sections[key][0]).show();
			else
				$(sections[key][0]).show('slide', {direction: 'right'}, 150);
			sections[key][1].attr({'font-weight': 'bold'});
			sections[key][2].animate({'stroke-width': '8', 'fill': '#f80'}, 300);
			$('#content').css('min-height', function(){
				return $(sections[key][0]).height() + 180;
			});
			$('a.current').removeClass('current');
			$('a[href="#' + gsid + '"]').addClass('current');
		}
		else if ( key == prev_gsid )
		{
			$(sections[key][0]).hide('slide', {direction: 'left'}, 150);
			sections[key][1].attr({'font-weight': 'normal'});
			sections[key][2].animate({'stroke-width': '3', 'fill': '#f7ff7a'}, 300);
		}
	});
	prev_gsid = gsid;
	if ( changehash )
		document.location.hash = 'doc-' + gsid;
}

function gs_start(firstsection) {

	var count = $('div.section h2').length;
	if ( count == 0 )
		return;

	// The page must have only one h1, and h2 will act as steps.
	$('div.footerlinks').hide();
	$('div.section h1').hide();
	$('<div id="gs-bar"></div>').insertAfter($('div.section h1').first());
	$('div.section h2').parent().addClass('panelstep').hide();
	$('div.section h2').hide();

	// Create the graphics context
	var r = Raphael('gs-bar', 820, 100);
	r.clear();
	var instrs = r.set();
	var x = 20, y = 60;
	r.path('M20,85L760,85').attr({fill: "#445fa3", stroke: "#999", "stroke-width": 4, "stroke-opacity": 0.4});
	r.path('M770,85L760,80L760,90Z').attr({fill: "#999", stroke: "#999", "stroke-width": 4, "stroke-opacity": 0.4});

	jQuery(document).bind('keydown', function (evt){
		var nid = '';
		if ( event.which == 37 ) {
			nid = $('div.panelstep[id="' + prev_gsid + '"]').prev().attr('id');
		}
		else if ( event.which == 39 ) {
			nid = $('div.panelstep[id="' + prev_gsid + '"]').next().attr('id');
		}
		if ( typeof(nid) != 'undefined' && nid != '' && nid != 'gs-bar' )
			gs_show_section(nid, 1);
		return true;
	});

	$('div.section h2').each(function(index, elem) {
		var gsid = $(elem).parent()[0].id;
		var instr_t = r.text(x - 2, y, $(elem).text().split('¶')[0]);
		instr_t.rotate(-20, x, y);
		instrs.push(instr_t);
		var instr_c = r.circle(x + 4, y + 25, 10).attr({fill: "#f7ff7a", stroke: "#000", "stroke-width": 3, "stroke-opacity": 0.4});

		instr_t.click(function() { gs_show_section(gsid, 1); });
		instr_c.click(function() { gs_show_section(gsid, 1); });
		sections[gsid] = [$(elem).parent()[0], instr_t, instr_c];
		sections_key.push(gsid);

		var prevlink = '', nextlink = '';
		var pt = $(elem).parent()[0];

		prevlink =  $(pt).prev().attr('id');
		if ( prevlink != '' && prevlink != 'gs-bar' ) {
			var text = $('#' + prevlink + ' h2').text().split('¶')[0];
			prevlink = '<a href="#doc-' + prevlink + '">&laquo; ' + text + '</a>';
		} else {
			prevlink = '';
		}

		nextlink =  $(pt).next().attr('id');
		if ( typeof(nextlink) != 'undefined' ) {
			var text = $('#' + nextlink + ' h2').text().split('¶')[0];
			nextlink = '<a href="#doc-' + nextlink + '">' + text + ' &raquo; </a>';
		} else {
			nextlink = '';
		}

		$(['<div class="footerlinks">',
		   '<table><tbody><tr><td class="leftlink">',
		   prevlink,
		   '</td><td class="rightlink">',
		   nextlink,
		   '</td></tr></tbody></table>',
		   '</div>'
		].join('')).appendTo($(elem).parent());

		x += (820/(count + 1));
	});
	instrs.attr({font: "14px Open Sans", fill: "#333", "text-anchor": "start"});

	gs_check_hash();
}

$(document).ready(function () {
	var height = $(document).height();
	$('#content').css('min-height', function(){ return height; });

	var bodyshortcut = false;
	function ensure_bodyshortcut() {
		if ( bodyshortcut == true )
			return;
		var bsc = $('<div class="bodyshortcut">&nbsp;</div>');
		bsc.insertAfter($('div.body h1:first'));
		bodyshortcut = true;
	};

	// if it's an API page, show the module name.
	var pagename = location.pathname.split('/');
	pagename = pagename[pagename.length - 1];
	if (pagename.search('api-') == 0) {
		pagename = pagename.substr(4, pagename.length - 9);

		ensure_bodyshortcut();
		var modulename = $('<div class="left">Module: <a href="#">' + pagename + '</a></div>')
		modulename.appendTo($('div.bodyshortcut'));
	}

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
		ensure_bodyshortcut();
		var apilink = $('<div class="right"><a id="api-link" href="#api">Jump to API</a> &dArr;</div>');
		apilink.appendTo($('div.bodyshortcut'));
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

	//----------------------------------------------------------------------------
	// Reduce the TOC page
	//----------------------------------------------------------------------------

	var ul = $('div.sphinxsidebarwrapper h3:eq(1) + ul > li > ul');
	$('div.sphinxsidebarwrapper h3:eq(1) + ul').detach();
	ul.insertAfter($('div.sphinxsidebarwrapper h3:eq(1)'));
	$("div.sphinxsidebarwrapper ul").each(function() {
		if ($(this).children().length < 1)
			$(this).remove()
	});

	//----------------------------------------------------------------------------
	// Make the navigation always in view
	//----------------------------------------------------------------------------

	// XXX temporary avoid scrolling
	//$(window).scroll(function() {
	//	gs_scroll();
	//});
	//scrollingDiv = $('div.sphinxsidebarwrapper');
	//scrolltop = $('div.sphinxsidebarwrapper h3:eq(1)').position().top;
	//setTimeout('gs_enable_scroll()', 50);


	//----------------------------------------------------------------------------
	// Image reflexions
	//----------------------------------------------------------------------------

	$('div.body img').reflect({'opacity': .35, 'height': 40});

	//----------------------------------------------------------------------------
	// Page to change with panel navigation
	//----------------------------------------------------------------------------

	var firstsection = $('div.section').attr('id');
	if ( firstsection == 'getting-started' || firstsection == 'pong-game-tutorial' )
		gs_start(firstsection);

});
