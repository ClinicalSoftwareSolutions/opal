var directives = angular.module('opal.directives', ['ngSanitize']);

directives.directive("freezePanes", function () {
    return function (scope, element, attrs) {
        scope.$watch("assignments", function () {
            $('table').stickyTableHeaders();
        });
    };
});


directives.directive('loadingbar', function($rootScope) {
	return {
		link: function(scope, element, attrs) {
			element.addClass('hide');

			$rootScope.$on('$routeChangeStart', function() {
				element.removeClass('hide');
			});

			$rootScope.$on('$routeChangeSuccess', function() {
				element.addClass('hide');
			});
		}
	};
});

directives.directive('placeholder', function($timeout){
	if ($.support.placeholder) {
		return {};
	}
	return {
		link: function(scope, elm, attrs){
			if (attrs.type === 'password') {
				return;
			}
			$timeout(function(){
				elm.val(attrs.placeholder).focus(function(){
					if ($(this).val() == $(this).attr('placeholder')) {
						$(this).val('');
					}
				}).blur(function(){
					if ($(this).val() == '') {
						$(this).val($(this).attr('placeholder'));
					}
				});
			});
		}
	}
});

directives.directive('linebreakstolistitems', function($interpolate, $sanitize) {
	return {
		link: function(scope, element, attrs) {
			var uContent = $interpolate(element.text())(scope);
			var sContent = '';
			var lines = uContent.split('\n');

			for (i = 0; i < lines.length; i++) {
				sContent += '<li>' + $sanitize(lines[i]) + '</li>';
			}

			element.html(sContent);
		}
	}
});
