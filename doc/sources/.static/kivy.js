$(document).ready(function () {
	$(['div.section[id]', 'dt[id]']).each(function(i1, elem) {
		$(elem).each(function(i2, e) {
			var eid = $(e).attr('id');
			$(e).removeAttr('id');
			$('<div></div>').attr('id', eid).addClass('anchor').insertBefore(e);
		});
	});
});
