$(function() {

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
	var is_api = false;
	pagename = pagename[pagename.length - 1];
	if (pagename.search('api-') == 0) {
		pagename = pagename.substr(4, pagename.length - 9);

		ensure_bodyshortcut();
		var modulename = $('<div class="left">Module: <a href="#">' + pagename + '</a></div>')
		modulename.appendTo($('div.bodyshortcut'));
		is_api = true;
	}

	// insert breaker only for the first data/class/function found.
	var apibreaker = false;
	$('div.body dl[class]').each(function (i1, elem) {
		// these are first level class: attribute and method are inside class.
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
				  '<a id="api-toggle-desc" class="showed">Hide Description &uArr;</a>' +
				  '</h2>')
				)
			.insertBefore(elem);
		apibreaker = true;
	});


	$('div.body dl[class] dt')
	.on("mouseenter", function() { $(this).addClass('hover'); })
	.on("mouseleave", function() { $(this).removeClass('hover'); });

	if ( apibreaker == true ) {
		ensure_bodyshortcut();
		var apilink = $('<div class="navlink right"><a id="api-link" href="#api">Jump to API</a> &dArr;</div>');
		apilink.insertBefore($('div.bodyshortcut'));
	}

	$('#api-toggle-desc').on("click", function() {
		if ($(this).hasClass('showed')) {
			$('div.body dl.api-level > dd p').hide();
			$('div.body dl.api-level > dd pre').hide();
			$('div.body dl.api-level > dd blockquote').hide();
			$('div.body dl.api-level > dd ul').hide();
			$(this).removeClass('showed');
			$(this).html('Show Descriptions &dArr;');
			$.cookie('kivy.toggledesc', 'true');
		} else {
			$('div.body dl.api-level > dd p').show();
			$('div.body dl.api-level > dd pre').show();
			$('div.body dl.api-level > dd blockquote').show();
			$('div.body dl.api-level > dd ul').show();
			$(this).addClass('showed');
			$(this).html('Hide Descriptions &uArr;');
			$.cookie('kivy.toggledesc', 'false');
		}
	});

	$('div.body dl.api-level dt').on("click", function() {
		$(this).next().children().toggle();
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
	// Menu navigation
	//----------------------------------------------------------------------------
	$('div.sphinxsidebarwrapper > ul > li > a').each(function(index, item) {
		$(item)
			.attr('href', '#')
			.addClass('mainlevel');
		if ( !is_api ) {
			$(item)
				.bind('mousedown', function() {
				$('div.sphinxsidebar ul li ul').filter(function (index, child) {
					if (child != $(item).parent().children('ul').get(0)) return child;
				}).slideUp();
				$(item).parent().children('ul').slideToggle();
			});
		}
	})

	$('div.sphinxsidebarwrapper li.current').parent().show();

	if ( !is_api ) {
		$('div.sphinxsidebarwrapper ul li').each(function(index, item) {
			if ($(item).children('ul').length > 0) {
				$(item).children('a').addClass('togglable');
			}
		});
	}

	// FIXME
	$('div.sphinxsidebar a[href$="api-kivy.html"]').parent().parent().addClass('api-index');
	$('div.sphinxsidebar a[href$="api-kivy.utils.html"]').parent().parent().addClass('api-index');
	$('li.current.toctree-l2').slice(0, -1).removeClass('current');

	$('ul.api-index a').each(function(index, item) {
		var url = $(item).attr('href').slice(0, -5);
		if (url == '') {
			$(item).attr('href', location.pathname);
			url = location.pathname.slice(0, -5);
		}
		url = url.substr(url.search('api-') + 4);
		$(item).empty().append(url);
	});

	// Hide API section if we are not in the API.
	// or hide all the others sections if we are in the API
	if ( is_api ) {
		$('div.sphinxsidebarwrapper > ul > li > ul').filter(
				function(index, item) {
					if (! $(item).hasClass('api-index'))
						return item;
				}).parent().hide();
		$('.nav-api').addClass('current');
		$('body').addClass('is-api');
	} else {
		$('div.sphinxsidebarwrapper > ul > li > ul').filter(
				function(index, item) {
					if ($(item).hasClass('api-index'))
						return item;
				}).parent().hide();
		$('.nav-guides').addClass('current');
	}


	if ( is_api ) {
		$('.toc').hide();


		// Resolve API version
		function read_version(item, default_version) {
			if ( item === undefined )
				return default_version;
			var version = item.find('p').text();
			if ( version == "" )
				return default_version;
			item.detach();
			version = version.replace('New in version ', '');
			if ( version.substr(-1) == '.' )
				version = version.substr(0, version.length - 1);
			return version;
		}

		//function read_version(item, version) { return version; }

		// get module version
		var module_version = read_version($('div.body > div.section > div.versionadded'), '1.0.0');
		var html_version = '<span class="versionadded">Added in <span>' + module_version + '</span></span>';
		$('div.bodyshortcut').append(html_version);

		// resolve class version, default to module if nothing has been found
		$('div.section > dl[class]').each(function (i1, el_class) {
			var rel_class = $(el_class);
			var class_version = read_version(
				rel_class.find('> dd > div.versionadded'), module_version);

			var html_version = '<span class="versionadded">Added in <span>' + class_version + '</span></span>';
			rel_class.find('> dt').append(html_version);

			// resolve method / attr version
			rel_class.find('> dd > dl[class]').each(function (i2, el_methattr) {
				var rel_methattr = $(el_methattr);
				var methattr_version = read_version(
					rel_methattr.find('> dd > div.versionadded'), class_version);
				var html_version = '<span class="versionadded">Added in <span>' + methattr_version + '</span></span>';
				rel_methattr.find('> dt').append(html_version);
			});
		});

	} else {

		if ($('.toc > ul > li> ul').length < 1)
			$('.toc').hide();

		var section_title = $('li.toctree-l1.current > a').text();
		$('div.body h1:eq(0)').prepend(section_title + ' &raquo; ');
	}
	// Hack to add an attrib to all linenos,
	// this is needed in order to avoid certain browsers (Ex: Safari) that treat the line-number as a copyable item.
    $(".linenos, .gp").each(function(){
        let $this = $(this);
        $this.attr("unselectable-data", $this.text());
		$this.contents().filter(function(){
    			return this.nodeType === 3; //https://developer.mozilla.org/en-US/docs/Web/API/Node/nodeType
		}).remove();
  });


	$("#themeToggleSwitch").click(function () {
		let currTheme = document.documentElement.className,
			newTheme = currTheme === "light" ? "dark" : "light"
		document.documentElement.className = newTheme
		localStorage.setItem('theme', newTheme);
	});
});