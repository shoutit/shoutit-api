$.fn.serializeObject = function () {
  var o = {};
  var disabled = this.find(':disabled').removeAttr('disabled');
  var a = this.serializeArray();
  disabled.attr('disabled', 'disabled');
  $.each(a, function () {
    if (o[this.name] !== undefined) {
      if (!o[this.name].push) {
        o[this.name] = [o[this.name]];
      }
      o[this.name].push(this.value || '');
    } else {
      o[this.name] = this.value || '';
    }
  });
  return o;
};

var messageHeads = {};
messageHeads['info'] = 'Heads up!';
messageHeads['success'] = 'Well done!';
messageHeads['warning'] = 'Holy gaucamole!';
messageHeads['error'] = 'Oh snap!';

var is_modal_visible = false;

var namingIndex = 0;

function get_messages_container() {
  if (is_modal_visible)
    return $('div#my-modal-messages-container');
  else
    return $('div#messages_container');
}

//function showMessage(message, type, tag) {
//    var ctr = get_messages_container();
//    namingIndex++;
//    if (!ctr.is(":visible")) {
//        ctr.children('div.alert-message').hide();
//        ctr.show();
//    }
//    var msg = $('<div class="alert-message ' + type + (tag !== undefined ? ' tag_' + tag : '') + '" id="msg-' + namingIndex + '"><a href="#" class="close" onclick=\'$("#msg-' + namingIndex + '").slideUp(); return false;\'>×</a><p><strong>' + messageHeads[type] + '</strong></p>' + message + '</div>');
//    msg.hide().prependTo(ctr).slideDown();
//
//    if (!is_modal_visible)
//        setTimeout('$("#msg-' + namingIndex + '").slideUp();', 5000);
//}

function show_loading() {
  if (is_modal_visible)
    $('#my-modal-loading').show();
  else
    $('#ajax_loading').show();
}

function hide_loading() {
  if (is_modal_visible)
    $('#my-modal-loading').hide();
  else
    $('#ajax_loading').hide();
}

function clearMessages(tag) {
  if (tag !== undefined)
    get_messages_container().find('div.tag_' + tag).slideUp();
  else
    get_messages_container().find('div.alert-message').slideUp();
}

function redirectToPage(url, timeout) {
  var t = 2000;
  if (timeout !== undefined)
    t = timeout;
  setTimeout("window.location = '" + url + "';", t);
}

var is_loading = {};

//function requestAjaxily(config) {
//    if (config === undefined)
//        return;
//
//    if (config.type === undefined)
//        config.type = 'GET';
//
//    if (config.returned_type === undefined)
//        config.returned_type = 'JSON';
//
//    var key = config.type + '-' + config.url + '-' + config.returned_type;
//
//    if (is_loading[key] !== undefined && is_loading[key])
//        return;
//    else
//        is_loading[key] = true;
//
//    //if (config.tag !== undefined)
//    clearMessages();
//
//    show_loading();
//    $.ajax({
//        url: config.url,
//        data: config.data,
//        type: config.type,
//        config: config,
//        key: key,
//        success: function (data) {
//            hide_loading();
//            is_loading[this.key] = false;
//            if (this.config.returned_type == 'HTML' && this.config.successCallback !== undefined)
//                this.config.successCallback(data);
//            else if (data.code == 0) {
//                if (data.message != '')
//                    showMessage(data.message, data.message_type, this.config.tag);
//                if (this.config.successCallback !== undefined)
//                    this.config.successCallback(data);
//            } else if (data.code == 1) {
//                if (data.message != '')
//                    showMessage(data.message, 'error', this.config.tag);
//                if (this.config.errorCallback !== undefined)
//                    this.config.errorCallback(data);
//            } else if (data.code == 2) {
//                if (data.message != '')
//                    showMessage(data.message, 'error', this.config.tag);
//                if (this.config.errorCallback !== undefined)
//                    this.config.errorCallback(data);
//            } else if (data.code == 3) {
//                if (data.message != '')
//                    showMessage(data.message, 'warning', this.config.tag);
//                //redirectToPage(data.data['link']);
//                show_loading();
//                var xhr_request = this;
//                $('#my-modal .modal-header h4').html('Sign in');
//                $('#my-modal-content').load('/xhr/signin/', function () {
//                    hide_loading();
//                    $('#my-modal').modal({
//                        keyboard: true,
//                        show: true,
//                        backdrop: true
//                    });
//
//                    $('body').bind('logged_in', function () {
//                        $('#my-modal').modal();
//                        is_modal_visible = false;
//                        requestAjaxily(xhr_request.config);
//                    });
//
//                    $('#my-modal').bind('hidden', function () {
//                        is_modal_visible = false;
//                        $('div#my-modal-messages-container div.alert-message').remove();
//                    });
//
//                    $('#my-modal').bind('shown', function () {
//                        is_modal_visible = true;
//                    });
//                });
//            }
//        },
//        error: function (jqXHR, textStatus, errorThrown) {
//            is_loading[this.key] = false;
//            hide_loading();
//            if (errorThrown != null && errorThrown != '')
//                showMessage(errorThrown, 'error', this.config.tag);
//        }
//    });
//}


function backToConversations() {
  if (window.location.pathname == "/messages/") {
    $("#conversation_shout").hide();
    $("#conversation_shout").children().remove();
  }

  $("#conversations_header_buttons").html("");
  $("#conversations_header_title").html("Conversations");

//    $("#conversations_stream").children().show();
  $('.conversations').show();
  $('.conversation_messages').hide();
  $('.conversation_messages .box-content').children().remove();

  $("#messages").remove();
  $('form#send_message_form').remove();
  current_conversation_id = -1;
}

function share_experience(id, domObj) {
  requestAjaxily({
    url: '/xhr/share_experience/' + id + '/',
    type: 'POST',
    clickedObject: domObj,
    experince_id: id,
    successCallback: function (data) {
      var label = $('label[id*=' + "numberOfSharedExps" + this.experince_id + ']');
      label.html(parseInt(label.html()) + 1);
      $(this.clickedObject).remove()
    }
  });
}

function report(id, type) {
  show_modal('#report', {id: id, report_type: type});
}

function edit_experience(id) {
  show_modal('#edit_experience', {id: id});
}

function users_shared_experience(id) {
  requestAjaxily({
    url: '/xhr/users_shared_experience/' + id + '/',
    successCallback: function (data) {
      var users = data.data.users;
      var html = '';
      html += '<div class="clearfix">';
      for (var i = 0; i < users.length; i++) {
        html += '<a class="btn large user_thumb" href="/user/' + users[i].username + '"><img src="' + users[i].image + '"><span>' + users[i].name + '</span></a>';
      }
      $('#users_shared_experience_modal_conatiner').html(html);
    }
  });
}

function comments_on_experience(id, timestamp) {
  var post_data = {page: $('#' + id).val(), timestamp: timestamp  };
  requestAjaxily({
    url: '/xhr/post_comments/' + id + '/',
    data: post_data,
//                clickedObject : this,
    comment_id: id,
    successCallback: function (data) {
      var comments = data.data.comments;
      $('#' + this.comment_id).val(parseInt($('#' + this.comment_id).val()) + 1);
      for (var i = comments.length - 1; i >= 0; i--) {
        var reportHtml = (comments[i]['isOwner'] == 1) ?
            " <a onclick=\"delete_comment('" + comments[i]['id'] + "',this)\">x</a>" :
            " <a title='report comment' onclick=\"report_comment('" + comments[i]['id'] + "')\">x</a>";
        $('#' + this.comment_id).parent().prepend('<div>' + comments[i]['text'] + reportHtml + '</div>');
      }
      $('.social_comments').show();
      $('.comment_on_experience_form #id_text').focus();
    }
  });
}

function delete_comment(id, clickedObject) {
  requestAjaxily({
    url: '/xhr/delete_comment/' + id + '/',
    type: 'POST',
    clickedObject: clickedObject,
    successCallback: function (data) {
      $(this.clickedObject).parent().first().remove()
    }
  });
}

function delete_event(id, clickedObject) {
  requestAjaxily({
    url: '/xhr/delete_event/' + id + '/',
    type: 'POST',
    clickedObject: clickedObject,
    successCallback: function (data) {
      var confirm_modal = $('<div class="modal"><div class="modal-header"><a class="close" data-dismiss="modal">×</a></div><div class="modal-title">' + gettext("Delete Activity") + '</div><div class="modal-body">' + gettext("Are you sure you want to delete this activity?") + '</div><div class="modal-footer"><button data-dismiss="modal" class="btn">' + gettext("no") + '</button><button class="yes btn" data-dismiss="modal">' + gettext("yes") + '</button></div></div>');
      confirm_modal.modal();
      confirm_modal.find('.yes').click(function () {
        $(clickedObject).parent().remove()
      });
      return false;
    }
  });
}

function delete_gallery_item(id, clickedObject) {
  requestAjaxily({
    url: '/xhr/delete_gallery_item/' + id + '/',
    type: 'POST',
    clickedObject: clickedObject,
    successCallback: function (data) {
      $(this.clickedObject).parent().first().remove()
    }
  });
}

function deleteMessage(conversationId, messageId, domObj) {
  requestAjaxily({
    url: '/xhr/delete_message/' + conversationId + '/' + messageId + '/',
    type: 'DELETE',
    div: $(domObj).parents('div.message'),
    beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
    },
    successCallback: function (data) {
      this.div.remove();
    }
  });
}

function deleteConversation(conversationId, domObj) {
  requestAjaxily({
    url: '/xhr/delete_conversation/' + conversationId + '/',
    type: 'DELETE',
    div: $(domObj).parents('div.message'),
    beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
    },
    successCallback: function (data) {
      this.div.remove();
    }
  })
}
function showMessagesAjaxly(id) {
//    $('a[id*="showMessagesAjaxly"]').click(function(){
//        id = this.id.toString().substr(18);
  current_conversation_id = id;
  var post_data = {};
  requestAjaxily({
    url: '/xhr/messages/' + id + '/',
    data: post_data,
    type: 'GET',
    successCallback: function (data) {
      if (window.location.pathname == "/messages/") {
        $("#conversation_shout").html(data.data.conversation_shout_html);
        $("#conversation_shout").show();
      }

      $("#conversations_header_buttons").html("<a onclick=\"backToConversations()\" class=\"back btn\" > back</a>");
      $("#conversations_header_title").html("Conversation");

//                $("#conversations_stream").children().hide();
//                $("#conversations_stream").append(data.data.conversation_messages_html);
      $('.conversations').hide();
      $('.conversation_messages').show();
      $('.conversation_messages .box-content').append(data.data.conversation_messages_html);

      $('.pd').prettyDate();
      $('form#send_message_form').submitAjaxily(function (data) {
        $("#messages").append(data.data.html);
        $('#id_text').val("");
        $('.pd').prettyDate();

        var scrollDiv = $('.slimScrollDiv:first');
        var slimScrollBar = scrollDiv.filter(':first').find('.slimScrollBar');
        var scrollableObject = scrollDiv.find('div#messages');
        slimScrollBar.css('top', scrollDiv.height() - slimScrollBar.height() + 'px');
        scrollableObject.scrollTop(scrollableObject[0].scrollHeight - scrollableObject.height());
      });
    }
  });
//    });
//
}


function save_location(id_location, id_city, id_country) {
  var location = $('#' + id_location).val();
  if (location == 'Error') {
    alert('Location Not Valid');
    return;
  }
  var post_data = {
    country: $('#' + id_country).val(),
    city: $('#' + id_city).val(),
    latitude: location.split(',')[0],
    longitude: location.split(',')[1]
  };
  requestAjaxily({
    url: '/xhr/update_location/',
    data: post_data,
    type: 'POST',
    successCallback: function (data) {
      var user_country = data.data.user_country;
      var user_city = data.data.user_city;
      var user_lat = data.data.user_lat;
      var user_lng = data.data.user_lng;

      window.location.replace('/offers/' + data.data.user_city_encoded + '/');
//            $('#ShowMap').html("<i class=\"icon-map-marker\"></i> [" + $('#'+id_city).val()+"]");
//            $('#MapModal').modal('hide');
//            if ($('.shouts .box-content').length != 0){
//                $('.shouts .box-content').resetScrollableStream();
//                $('.shouts .box-content').refreshScrollableStream();
//            }
//
//			$('.browse_in').html($('#'+id_city).val());
//
//
//
////			current_last_shout_live_id = null;
//            timestamp = null;
//			$(e_container).empty();
//			clearInterval(currentEventsInterval);
//			currentEventsInterval = 0;
//			startLiveEventsPolling(liveEventsUrl, e_container);
//			if ($('#tags ul'))
//				getTopTags();
    }
  });
}

//$.fn.submitAjaxily = function(successCallback, errorCallback) {
//    $(this).find('[type="submit"]').filter(':first').click(function () {
//        var form = $(this).parents('form').filter(':first');
//        form.find('div.clearfix.error').removeClass('error');
//        form.find('span.field_error').remove();
//        clearMessages(form.attr('id'));
//
//        if (form.attr('action') === undefined || form.attr('action') == '.')
//            form.attr('action', window.location.pathname + window.location.search + window.location.hash);
//
//        if (!/^\/xhr/i.test(form.attr('action')))
//            form.attr('action', '/xhr' + form.attr('action'));
//
//        requestAjaxily({
//            url: form.attr('action'),
//            data: form.serializeObject(),
//            type: 'POST',
//            successCallback: successCallback,
//            errorCallback: function (data) {
//                $.each(data.errors, function (k, v) {
//                    form.find('#id_' + k).parents('div.clearfix').addClass('error');
//                    form.find('#id_' + k).parents('div').filter(':first').append($('<span class="field_error">' + v + '</span>'));
//                });
//
//                if (errorCallback !== undefined)
//                        errorCallback(data);
//            },
//            tag: form.attr('id')
//        });
//
//        return false;
//    });
//};

$.fn.clickAjaxily = function (config) {
  $(this).click(function () {
    if ($(this).attr('id') === undefined) {
      namingIndex++;
      $(this).attr('id', 'randomly_' + this.nodeName.toLowerCase() + '_' + namingIndex);
    }

    requestAjaxily({
      url: config.url,
      data: config.data,
      successCallback: config.successCallback,
      errorCallback: config.errorCallback,
      tag: $(this).attr('id')
    });

    return false;
  });
};

function fix_stream() {
  $('.pd').prettyDate();
  $('a.shout_post_delete').click(function () {
    var shout_id = $(this).attr('shout_id');
    requestAjaxily({
      url: '/xhr/shout/' + shout_id + '/delete/',
      type: 'DELETE',
      div: $(this).parents('div.shout_post').filter(':first'),
      successCallback: function (data) {
        this.div.remove();
      }
    })
  });

  $('[rel^=shout_]').each(function () {
    $(this).colorbox({rel: $(this).attr('rel')});
  });
  $('.shout_post_text p').automaticDirection();
//    $('.hovercard').hoverIntent({
//        over:function(){
//            var elm = $(this);
//            var elms = $('[hovercard-name="'+elm.attr('hovercard-name')+'"][hovercard-type="'+elm.attr('hovercard-type')+'"]');
//            $.get('/xhr/hovercard/',{name:$(this).attr('hovercard-name'),type:$(this).attr('hovercard-type')}, function(response){
//                elms.unbind();
//                var html = $( "#hovercardTemplate" ).tmpl( response.data ).html();
//                elms.attr('hovercard-data',html);
//                elms.popover({
//                    title:function(){
//                        return elm.attr('hovercard-name');
//                    }
//                    ,content:function(){
//                        return elm.attr('hovercard-data');
//                    }
//                    ,html:true
//                    ,delayIn:1000 // to popup the hovercard
//                    ,live:true
//                });
//                elm.mouseover();
//            });
//        },
//        timeout:1500
//    });
}


var streams = [];
var stream_containers = [];
var current_page = [];
var is_last_page = [];
var loading_stream = [];
//var stream_data = []

function register_stream(url, stream_container, currentPage) {
  if (currentPage === undefined)
    currentPage = 1;
  streams[streams.length] = url;
  stream_containers[streams.length - 1] = stream_container;
  current_page[streams.length - 1] = currentPage;
  is_last_page[streams.length - 1] = false;
  loading_stream[streams.length - 1] = false;
  stream_data[streams.length - 1] = {};
  $(window).scroll();
}

function unregister_stream(url) {
  var index = streams.indexOf(url);
  if (index != -1) {
    streams.splice(index, 1);
    stream_containers.splice(index, 1);
    current_page.splice(index, 1);
    is_last_page.splice(index, 1);
    loading_stream.splice(index, 1);
    stream_data.splice(index, 1);
  }
}

function set_stream_data(url, data) {
  var index = streams.indexOf(url);
  if (index != -1) {
    stream_data[index] = data;
  }
}

function reset_stream(url) {
  var index = streams.indexOf(url);
  if (index != -1) {
    current_page[index] = 0;
    is_last_page[index] = false;
    loading_stream[index] = false;
    stream_data[index] = {};
  }
}

function refresh_stream(url) {
  var i = streams.indexOf(url);
  loading_stream[i] = true;
  requestAjaxily({
    url: streams[i] + ++current_page[i] + '/',
    index: i,
    data: stream_data[i],
    successCallback: function (data) {
      $(stream_containers[this.index]).append(data.data.html);
      if (data.data.is_last_page)
        is_last_page[this.index] = true;
      if (data.data.count == 0) {
        is_last_page[this.index] = true;
        current_page[this.index]--;
      }
      if (is_last_page[this.index])
        $(stream_containers[this.index]).append('<div class="end_of_stream">' + gettext('End of stream!') + '</div>');
      fix_stream();
      loading_stream[this.index] = false;
    }
  });
}

var current_last_shout_live_id = null;
var shouts = [];
var v_container = '';
var liveUrl = '';
var count = 0;
var currentInterval = 0;
var i = 0;

function startLiveShoutsPolling(url, container) {
  v_container = container;
  liveUrl = url;
  getShoutLiveChunk();
}

function getShoutLiveChunk() {
  if (currentInterval > 0) {
    setTimeout("getShoutLiveChunk()", 1000);
    return;
  }
  shouts = [];
  requestAjaxily({
    url: liveUrl + (current_last_shout_live_id == null ? "" : current_last_shout_live_id + '/'),
    type: 'GET',
    successCallback: function (data) {
      count = data.data['count'];
      if (count > 0) {
        i = count - 1;
        shouts = data.data['shouts'];
//                var terms = shouts[0].url.split('/').filter(function(x){if (x != "") return x});
        current_last_shout_live_id = shouts[0]['id'];
        var interval = 60000 / count | 0;
        currentInterval = setInterval("append()", interval);
//                $('.pd').prettyDate();
      }
      else
        setTimeout("getShoutLiveChunk()", 20000);
    }
  });
}


function append() {
//    var parts = shouts[i].date_created.match(/(\d+)/g)
//    var date_string = parts[2] + '-' + pad(parts[1], parts[1] > 9 ? 2 : 1) + '-' + pad(parts[0], 2) + ' ' + pad(parts[3],2) + ':' + pad(parts[4],2) + ':' + pad(parts[5],2);
  appendLiveShout(v_container, shouts[i]['html']);
  i--;
  if (i < 0) {
    clearInterval(currentInterval);
    currentInterval = 0;
    startLiveShoutsPolling(liveUrl, v_container);
  }
}

function appendLiveShout(container, content) {
  var new_item = $(content);
  new_item.hide();
  new_item.prependTo(container).show('normal');
}


var timestamp = null;
var events = [];
var e_container = '';
var liveEventsUrl = '';
var eventsCount = 0;
var currentEventsInterval = 0;
var eventsIterator = 0;


function startLiveEventsPolling(url, container) {
  e_container = container;
  liveEventsUrl = url;
  getEventLiveChunk();
}

function getEventLiveChunk() {
  if (currentEventsInterval > 0) {
    setTimeout("getEventLiveChunk()", 1000);
    return;
  }
  events = [];
  requestAjaxily({

    data: {timestamp: (timestamp != null) ? timestamp : ''},
    url: liveEventsUrl,
    type: 'GET',
    successCallback: function (data) {
      timestamp = data.data['timestamp'];
      eventsCount = data.data['count'];
      if (eventsCount > 0) {
        eventsIterator = eventsCount - 1;
        events = data.data['events'];
        var interval = 60000 / eventsCount | 0;
        currentEventsInterval = setInterval("appendEvent()", interval);
//                $('.pd').prettyDate();
      }
      else
        setTimeout("getEventLiveChunk()", 20000);
    }
  });
}


function appendEvent() {
//    var parts = shouts[i].date_created.match(/(\d+)/g)
//    var date_string = parts[2] + '-' + pad(parts[1], parts[1] > 9 ? 2 : 1) + '-' + pad(parts[0], 2) + ' ' + pad(parts[3],2) + ':' + pad(parts[4],2) + ':' + pad(parts[5],2);
  appendLiveEvent(e_container, events[eventsIterator]['html']);
  eventsIterator--;
  if (eventsIterator < 0) {
    clearInterval(currentEventsInterval);
    currentEventsInterval = 0;
    startLiveEventsPolling(liveEventsUrl, e_container);
  }
}

function appendLiveEvent(container, content) {
  var new_item = $(content);
  new_item.hide();
  new_item.prependTo(container).show('normal');
}


//function pad(num, size) {
//    var s = num+"";
//    while (s.length > size && s[0] == '0') s = s.substr(1, s.length-1);
//    while (s.length < size) s = "0" + s;
//    return s;
//}

function getCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ')
      c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) == 0)
      return c.substring(nameEQ.length, c.length);
  }
  return null;
}

var rtlChars = '\u0600-\u06FF';
rtlChars += '\u0750-\u077F';
rtlChars += '\uFB50-\uFDFF';
rtlChars += '\uFE70-\uFEFF';

var controlChars = '\u0000-\u0020';
controlChars += '\u2000-\u200D';

var reRTL = new RegExp('[' + rtlChars + ']', 'g');
var reNotRTL = new RegExp('[^' + rtlChars + controlChars + ']', 'g');

$.fn.automaticDirection = function () {
  for (var i = 0; i < this.length; i++) {
    var value = $(this[i]).val();
    if (value == '')
      value = $(this[i]).text();
    if (value != '') {
      var rtls = value.match(reRTL);
      if (rtls != null)
        rtls = rtls.length;
      else
        rtls = 0;

      var notrtls = value.match(reNotRTL);
      if (notrtls != null)
        notrtls = notrtls.length;
      else
        notrtls = 0;

      if (rtls > notrtls)
        $(this[i]).css('direction', 'rtl').css('text-align', 'right');
      else
        $(this[i]).css('direction', 'ltr').css('text-align', 'left');
    }
  }
};

var current_conversation_id = -1;
$(document).ready(function () {
  // place holder support
  current_conversation_id = -1;
  if (!Modernizr.input.placeholder) {
    $('input, textarea').placeholder();
  }
  // prettify the date
  $('.pd').prettyDate();
  $('.shout_user_info').automaticDirection();
  $('input[type="text"], textarea').keyup(function () {
    $(this).automaticDirection();
  });

  $(window).scroll(function () {
    if (($(document).height() - $(window).height()) - $(window).scrollTop() <= 50) {
      for (var i = 0; i < streams.length; i++) {
        while (!is_last_page[i] && !loading_stream[i] && (($(document).height() - $(window).height()) - $(window).scrollTop() <= 50)) {
          refresh_stream(streams[i]);
        }
      }
    }
  });

  $(window).scroll();

  $(window).resize(function () {
    $(window).scroll();
  });


  $('form#send_message_form').submitAjaxily(function (data) {
    current_conversation_id = data.data.conversation_id;
    $("#messages").append(data.data.html);
    $('#id_text').val("");
    $('.pd').prettyDate();
    var scrollDiv = $(this).parents('.box-content').filter(':first').find('.slimScrollDiv');
    var slimScrollBar = scrollDiv.find('.slimScrollBar');
    var scrollableObject = scrollDiv.find('div#messages');
    slimScrollBar.css('top', scrollDiv.height() - slimScrollBar.height() + 'px');
    scrollableObject.scrollTop(scrollableObject[0].scrollHeight - scrollableObject.height());
  });

});
