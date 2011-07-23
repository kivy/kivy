$(document).ready(function () {
	var height = $(document).height();
	$('#content').css('min-height', function(){ return height; });
	//$('dl.function > dd').hide();
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
