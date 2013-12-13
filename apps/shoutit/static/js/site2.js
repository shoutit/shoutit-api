function setup_colorbox() {
    $('[rel^=shout_]').each(function () {
        $(this).colorbox({
            rel: $(this).attr('rel'),
            innerWidth: '800px',
            innerHeight: '600px',
			photo:true
        });
    });
}

//function setup_shouts_hover() {
//    $('.shout-content').hover(function () {
//        $(this).parent().find('.arrow-left').css('border-right-color', $(this).css('background-color'));
//        $(this).parent().find('.arrow-right').css('border-left-color', $(this).css('background-color'));
//    }, function () {
//        $(this).parent().find('.arrow-left').css('border-right-color', 'white');
//        $(this).parent().find('.arrow-right').css('border-left-color', 'white');
//    });
//}

function setup_buttons_href() {
    $('button[href]').click(function () {
        window.location = $(this).attr('href');
    });
}

var modals = new Array();
var modal_data = new Array();
var modal_data_only = new Array();
var redirect_after_login = true;
function setup_modal(id, url, hash, setup_function, returned_type, data_only) {
    modals[hash] = id;
    modal_data[hash] = undefined;
    if (data_only === undefined)
        data_only = false;
    modal_data_only[hash] = data_only;
    $(id).on('show', function () {
        $('.modal-backdrop').filter(':visible').each(function () {$(this).css('z-index', parseInt($(this).css('z-index')) - 10);});
        $('.modal').filter(':visible').each(function () {$(this).css('z-index', parseInt($(this).css('z-index')) - 10);});

        var previous_hash = window.location.hash;
        window.location.hash = hash;
        if (!$(id).attr('data-loaded') && url !== undefined) {
            $(id).find('.modal-body').css('height', $(id).height() - 166 + 'px');
            $(id).find('.modal-body').find('img').css('margin-top', ($(id).find('.modal-body').height() / 2) - 8 + 'px');
            requestAjaxily({
                url: url,
                data: modal_data[hash],
                returned_type: returned_type,
                id: id,
                successCallback: function (data) {
                    $(this.id + ' .modal-body').html(data);
                    $('input[placeholder], textarea[placeholder]').placeholder();
                    fix_styles();
                    $(this.id + ' .modal-body').find('input, textarea, select').filter(':visible').filter(':not(:disabled)').filter(':first').focus();
                    $(this.id).attr('data-loaded', true);
                    if (setup_function != null && setup_function !== undefined)
                        setup_function.call($(this.id));
                }
            })
        } else if (!$(id).attr('data-loaded') && setup_function != null && setup_function !== undefined) {
            $(this.id).attr('data-loaded', true);
            setup_function.call($(this.id));
        }
        $(id).attr('data-previous-hash', previous_hash);
    });
    $(id).on('shown', function () {
        $(id + ' .modal-body').find('input, textarea, select').filter(':visible').filter(':first').focus();
    });
    $(id).on('hidden', function () {
        $('.modal-backdrop').filter(':visible').each(function () {$(this).css('z-index', parseInt($(this).css('z-index')) + 10);});
        $('.modal').filter(':visible').each(function () {$(this).css('z-index', parseInt($(this).css('z-index')) + 10);});
        window.location.hash = $(id).attr('data-previous-hash');
    });
}

function show_modal(hash, data) {
    if (modals[hash] !== undefined) {
        if (data !== undefined) {
            $(modals[hash]).attr('data-loaded', '');
            modal_data[hash] = data === undefined && data != null ? undefined : (data && {}.toString.call(data) == '[object Function]' ? data() : data);
        }
        if (!modal_data_only[hash] || modal_data[hash] !== undefined)
            $(modals[hash]).modal('show');
    }
}

function show_modal_by_hash() {
    var hash = window.location.hash;
    window.location.hash = '';
    show_modal(hash);
}

var namingIndex = 0;

function showMessage(message, type, tag, link) {
    var container = $("#notification_container");
    namingIndex++;

    var notification = container.notify("create", type + "-template", {
        text: message,
		rel: link
    }, { custom: true });

    if (tag !== undefined)
        notification.element.addClass(tag);

    if (link !== undefined) {
		notification.element.addClass('link');
		notification.element.click(function(){
			document.location.href = link;
		});
	}

    notification.element.attr('id', 'msg-' + namingIndex);
}

function fix_styles() {
    $('div.shout div.user-image img.user-profile-image:not([data-margin]), div.message div.user-image img:not([data-margin]), div.conversation-form img:not([data-margin])').each(function () {
        if ($(this).prop('complete') && this.clientHeight > 1 && this.clientWidth > 1) {
            $(this).css('margin-top', (($(this).parents('div.user-image').filter(':first').height() - $(this).height()) / 2) + 'px');
            $(this).attr('data-margin', 'true');
        }
    });
    $('[placeholder]').each(function () {
        var my = 'right center';
        var at = 'left center';
        if ($(this).attr('data-qtip-my') !== undefined)
            my = $(this).attr('data-qtip-my');
        if ($(this).attr('data-qtip-at') !== undefined)
            at = $(this).attr('data-qtip-at');
        $(this).qtip({
            overwrite: false,
            content: { text: $(this).attr('placeholder') },
            show: { event: 'focus' },
            position: {
                my: my,
                at: at,
                viewport: $(window),
                adjust: { method: 'flip' }
            },
            hide: { event: 'blur' },
            style: { classes: 'ui-tooltip-shadow ui-tooltip-green ui-tooltip-input' }
        });
    });
//    setup_shouts_hover();
    $(".pd").prettyDate({ interval: false });
}

$(document).ready(function () {
    fix_styles();
    setInterval('fix_styles();', 1000);
});

function requestAjaxily(config) {
    if (config === undefined)
        return;

    if (config.type === undefined)
        config.type = 'GET';

    var key = config.type + '-' + config.url + '-' + config.returned_type;

    if (is_loading[key] !== undefined && is_loading[key])
        return;
    else
        is_loading[key] = true;

    clearMessages();
    show_loading();

    $.ajax({
        url: config.url,
        data: config.data,
        type: config.type,
        config: config,
        cache: false,
        key: key,
        success: function (data, textStatus, jqXHR) {
            hide_loading();
            is_loading[this.key] = false;

            var returned_type = jqXHR.getResponseHeader('Content-Type');
            if (this.config.returned_type !== undefined)
                returned_type = this.config.returned_type;
            else {
                if (returned_type.match(/([^; ]+)/)[0] == 'text/html')
                    returned_type = 'HTML';
                else if (returned_type.match(/([^; ]+)/)[0] == 'application/json')
                    returned_type = 'JSON';
            }

            if (returned_type == 'HTML' && this.config.successCallback !== undefined)
                this.config.successCallback(data);
            else if (returned_type == 'JSON' && data.code == 0) {
                if (data.message != '')
                    showMessage(data.message, data.message_type, this.config.tag);
                if (this.config.successCallback !== undefined)
                    this.config.successCallback(data);
            } else if (returned_type == 'JSON' && data.code == 1) {
                if (data.message != '')
                    showMessage(data.message, 'error', this.config.tag);
                if (this.config.errorCallback !== undefined)
                    this.config.errorCallback(data);
            } else if (returned_type == 'JSON' && (data.code == 2 || data.code == 4)) {
                if (data.message != '')
                    showMessage(data.message, 'error', this.config.tag);
                else if (data.code == 4)
                    showMessage('Forbidden, you are not allowed to do this action.', 'error', this.config.tag);
                if (this.config.errorCallback !== undefined)
                    this.config.errorCallback(data);
            } else if (returned_type == 'JSON' && data.code == 3) {
                var modal_key = null;
                if (data.data['modal_key'] !== undefined)
                    modal_key = data.data['modal_key'];
                if (modal_key != null) {
                    if (data.message != '')
                        showMessage(data.message, 'warning', this.config.tag);
                    redirect_after_login = false;
                    show_modal('#' + modal_key);
                    var xhr_request = this;
                    $('body').bind(modal_key + '_ok', function () {
                        $(modals['#' + modal_key]).modal('hide');
                        $('.navbar').load('/modal/navbar/');
                        if (xhr_request.config.form !== undefined) {
                            xhr_request.config.form.find('[type="submit"]').click();
                        } else {
                            requestAjaxily(xhr_request.config);
                        }
                    });
                } else {
                    redirectToPage(data.data['link'], 1)
                }
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            is_loading[this.key] = false;
            hide_loading();
            if (errorThrown != null && errorThrown != '')
                showMessage(errorThrown, 'error', this.config.tag);
        }
    });
}

$.fn.submitAjaxily = function(successCallback, errorCallback) {
    $(this).find('[type="submit"]').filter(':first').prop('disabled', false);
    $(this).find('[type="submit"]').filter(':first').click(function () {
        var form = $(this).parents('form').filter(':first');
        form.find('.input-error').each(function () { $(this).qtip('destroy'); $('#ui-tooltip-' + $(this).attr('id') + '-error').remove() });
        form.find('.input-error').removeClass('input-error');
        form.find('div.field_error').remove();
        form.find('div.form_error').remove();
        form.parents('.modal').filter(':first').find('.modal-footer').removeClass('modal-error');
        form.parents('.modal').filter(':first').find('.modal-footer').find('div.form_error').remove();
        clearMessages(form.attr('id'));

        if (form.attr('action') === undefined || form.attr('action') == '.')
            form.attr('action', window.location.pathname + window.location.search + window.location.hash);

        if (!/https?:\/\//i.test(form.attr('action')) && !/^\/xhr/i.test(form.attr('action')))
            form.attr('action', '/xhr' + form.attr('action'));
        form.find('[type="submit"]').prop('disabled', true);
        requestAjaxily({
            url: form.attr('action'),
            data: form.serializeObject(),
            type: 'POST',
            form: form,
            successCallback: function (data) {
                form.find('[type="submit"]').prop('disabled', false);
                if (successCallback !== undefined)
                    successCallback.call(form, data);
            },
            errorCallback: function (data) {
                form.find('[type="submit"]').prop('disabled', false);
                $.each(data.errors, function (k, v) {
                    form.find('label[for="#id_' + k + '"]').addClass('input-error');
                    $('#ui-tooltip-id_' + k + '-error').remove();
                    var field = null;
                    if (form.data('fields_map') !== undefined && form.data('fields_map')['id_' + k] !== undefined)
                        field = form.find(form.data('fields_map')['id_' + k]);
                    else
                        field = form.find('#id_' + k);
                    field.each(function () {
                        var field_my = 'left center';
                        var field_at = 'right center';
                        if ($(this).attr('data-qtip-error-my') !== undefined)
                            field_my = $(this).attr('data-qtip-error-my');
                        if ($(this).attr('data-qtip-error-at') !== undefined)
                            field_at = $(this).attr('data-qtip-error-at');
                        $(this).addClass('input-error');
                        $(this).removeData('qtip').qtip({
                            id: 'id_' + k + '-error',
                            overwrite: true,
                            content: { text: v[0] },
                            show: { event: 'focus' },
                            position: {
                                my: field_my,
                                at: field_at,
                                viewport: $(window),
                                adjust: { method: 'flip' }
                            },
                            hide: { event: 'blur' },
                            style: { classes: 'ui-tooltip-shadow ui-tooltip-red ui-tooltip-input' }
                        });
                    });
                });

                if (data.message !== undefined && data.message !== '') {
                    var modal = form.parents('.modal').filter(':first');
                    if (modal.length != 0)
                        modal.find('.modal-footer').addClass('modal-error').append('<div class="form_error">' + data.message + '</div>');
                    else
                        form.append('<div class="form_error">' + data.message + '</div>');
                }

                if (errorCallback !== undefined)
                    errorCallback(data);
            },
            tag: form.attr('id')
        });

        return false;
    });
};

function redirect_by_response(data) {
    if (data.data.next === undefined)
        setTimeout("window.location = '/';", 2000);
    else
        setTimeout("window.location = '" + data.data.next + "';", 2000);
}

$.fn.submitAjaxilyAndRedirect = function(successCallback, errorCallback) {
    $(this).submitAjaxily(function (data) {
        redirect_by_response(data);
    });
};

$.fn.scrollable = function (height, resumePageScroll) {
    $(this).attr('data-delta', 0);
    $(this).slimScroll({
        height: height,
        size: '5px',
        resumePageScroll: resumePageScroll,
        onScroll: function (scrollTop, scrollHeight, height, delta) {
            this.attr('data-delta', delta);
        }
    });
};

var stream_data = [];

$.fn.scrollableStream = function (height, resumePageScroll, url, container, current_page, onScrollFunction) {
    $(this).attr('data-delta', 0);
    $(this).attr('data-url', url);
    $(this).attr('data-is-last-page',  'false');
    $(this).attr('data-is-loading',  'false');
    $(this).attr('data-container', container);
    $(this).attr('data-current-page', current_page !== undefined ? current_page : '1');
    stream_data[this] = {};
    $(this).slimScroll({
        height: height,
        size: '5px',
        resumePageScroll: resumePageScroll,
        onScroll: function (scrollTop, scrollHeight, height, delta) {
            this.attr('data-delta', delta);
            var slimScrollBar = this.parents('.slimScrollDiv').filter(':first').find('.slimScrollBar');
            if (height - slimScrollBar.css('top').match(/(\d+)/)[0] - slimScrollBar.height() <= slimScrollBar.height()) {
                if (this.attr('data-is-last-page') == 'false' && this.attr('data-is-loading') == 'false') {
                    $(this).refreshScrollableStream();
                }
            }
            if (onScrollFunction != undefined){
                onScrollFunction();
            }
        }
    });
};

$.fn.refreshScrollableStream = function (onSuccessFunction) {
    var currentPage = parseInt(this.attr('data-current-page'));
    var slimScrollBar = this.parents('.slimScrollDiv').filter(':first').find('.slimScrollBar');
    this.attr('data-current-page', ++currentPage);
    this.attr('data-is-loading', 'true');
    requestAjaxily({
        url: this.attr('data-url') + currentPage + '/',
        scrollableObject: this,
        scrollBar: slimScrollBar,
        data: stream_data[this],
        successCallback: function (data) {
            $(this.scrollableObject.attr('data-container')).append(data.data.html);
            if (data.data.is_last_page)
                this.scrollableObject.attr('data-is-last-page', 'true');
            if (data.data.count == 0) {
                this.scrollableObject.attr('data-is-last-page', 'true');
                this.scrollableObject.attr('data-current-page', parseInt(this.scrollableObject.attr('data-current-page')) - 1);
            }
            if (this.scrollableObject.attr('data-is-last-page') == 'true')
                $(this.scrollableObject.attr('data-container')).append('<div class="end_of_stream">' + gettext('End of stream!') + '</div>');
            fix_stream();
            this.scrollableObject.attr('data-is-loading', 'false');
            this.scrollBar.css('height', (this.scrollableObject.outerHeight() / this.scrollableObject[0].scrollHeight) * this.scrollableObject.outerHeight() + 'px');
            this.scrollBar.css('top', (parseInt(this.scrollableObject.attr('data-delta')) / (this.scrollableObject[0].scrollHeight / this.scrollableObject.outerHeight())) + 'px');
			if (data.data.browse_in)
				$('.browse_in').html(data.data.browse_in);
            if (onSuccessFunction != undefined)
                onSuccessFunction();
        }
    });
};

$.fn.resetScrollableStream = function () {
    $(this).attr('data-delta', 0);
    $(this).attr('data-is-last-page', 'false');
    $(this).attr('data-is-loading', 'false');
    $(this).attr('data-current-page', 0);
    $($(this).attr('data-container')).html('');
    stream_data[this] = {};
    var slimScrollBar = this.parents('.slimScrollDiv').filter(':first').find('.slimScrollBar');
    slimScrollBar.css('top', '0px');
    slimScrollBar.css('height', '192px');
};

$.fn.setScrollableStreamData = function (data) {
    stream_data[this] = data;
};

$.fn.extendScrollableStreamData = function (data) {
	stream_data[this]= $.extend(stream_data[this], data)
};

$.fn.appendScrollableStreamData = function (key, value) {
    if (stream_data[this] == undefined)
        stream_data[this] = {};
    stream_data[this][key] = value;
};

function getTopTags(encoded_city){
	if (typeof encoded_city === 'undefined')
		encoded_city = '';
	$('#tags ul').html('');
	requestAjaxily({
		url: '/xhr/top_tags/?url_encoded_city='+encoded_city,
		successCallback: function (data) {
			for(var i in data.data.top_tags){
				var tag = data.data.top_tags[i];
				var tag_bool = tag.is_interested;
				if(tag_bool==true){
					var tag_html = '<li><div class="tag"><a href="/tag/' + tag.Name + '/" class="tag_name" data-interested="' + tag_bool + '">'+tag.Name+'</a><span data-tag="'+tag.Name+'" title="'+gettext('Stop listening')+'"  class="tag_listening"></span></div></li>';
				}else{
					var tag_html = '<li><div class="tag"><a href="/tag/' + tag.Name + '/" class="tag_name" data-interested="' + tag_bool + '">'+tag.Name+'</a><span data-tag="'+tag.Name+'" title="'+gettext('Listen')+'" class="tag_listening tag_non_listening"></span></div></li>';
				}
				$('#tags ul').append(tag_html);
			}
			ShowTopTags()
		}
	})
}

// when click on the search icon
$('.search_icon').click(function() {$('#home-search-box').focus();});

//follow tags
function follow(name,selector){
	requestAjaxily({
		url: '/xhr/tag/'+name+'/interest/',
		successCallback: function (data) {
			$(selector).removeClass('tag_non_listening');
			$(selector).attr('title',gettext('Stop listening'));			
		},
		tag: 'follow_tag'
	});
}
//unfollow the tag
function unfollow(name,selector){
	requestAjaxily({
					   url: '/xhr/tag/'+name+'/uninterest/',
					   successCallback: function (data) {
						   $(selector).addClass('tag_non_listening');
						   $(selector).attr('title',gettext('Listen'));						   
					   },
					   tag: 'unfollow_tag'
				   });
}
//follow user
function follow_user(name,selector) {
	requestAjaxily({
					   url: '/xhr/user/'+name+'/follow/',
					   successCallback: function (data) {
						   $(selector).addClass('shouters_listen');
						   $(selector).removeClass('shouters_non_listen');
						   $(selector).attr('title',gettext('Stop listening'));
						   //no_of_listeners++;
						   var no_of_listeners = parseInt($(selector).parent().find('.no_of_listeners').text());
						   $(selector).parent().find('.no_of_listeners').text(no_of_listeners+1);						   
					   },
					   tag: 'follow_user'
				   });
}
//unfollow user
function unfollow_user(name,selector) {
	requestAjaxily({
					   url: '/xhr/user/'+name+'/unfollow/',
					   successCallback: function (data) {
						   $(selector).addClass('shouters_non_listen');
						   $(selector).removeClass('shouters_listen');
						   $(selector).attr('title',gettext('Listen'));
						   //no_of_listeners--;
						   var no_of_listeners = parseInt($(selector).parent().find('.no_of_listeners').text());
						   $(selector).parent().find('.no_of_listeners').text(no_of_listeners-1);						   
					   },
					   tag: 'unfollow_user'
				   });
}

//how the tags will appear
function ShowTopTags() {

	var tag_width=0;
	$('.tag').each(function(i) {
		if($('.tag:eq('+i+') .tag_name').text().length>20){
		var x= $('.tag:eq('+i+') .tag_name').text().substring(0,19);
		$('.tag:eq('+i+') .tag_name').text(x+"..");
		}

//		tag_width = 4+tag_width+$('.tag:eq('+i+')').outerWidth();
//		var ul_width=$('.tag').parent().parent().outerWidth()-20;
//		if(tag_width >ul_width){
//			$('.tag:eq('+i+')').parent().addClass("clear");
//			tag_width=$('.tag:eq('+i+')').outerWidth()+4;
//		}
	});
//	var lang = $('html').attr('lang');
//	$('.tag').hover(function() {
//		if(lang =="en"){
//		$(this).stop().animate({ paddingRight: ($('.tag_listening', this).outerWidth() - 13) }, 'easeInOutExpo');
//		}else if(lang =="ar"){
//		$(this).stop().animate({ paddingLeft: ($('.tag_listening', this).outerWidth() - 13) }, 'easeInOutExpo');
//		}
//	}, function() {
//		if(lang =="en"){
//		$(this).stop().animate({ paddingRight: 5 }, 'easeInOutExpo');
//		}else if(lang =="ar"){
//		$(this).stop().animate({ paddingLeft: 5 }, 'easeInOutExpo');
//		}
//
//	});
	$('.tag_listening').click(function(){
		var listen_class = $(this).attr('class');
		var tag_name = $(this).attr('data-tag');
		if(listen_class=="tag_listening tag_non_listening"){
			follow(tag_name,this);
		}else{
			unfollow(tag_name,this);
		}

	});

}
//$(".select_lang").mouseover(function(){
//	$('.langs_list').show();
//});
//$(".select_lang").mouseout(function(){
//	$('.langs_list').hide();
//});