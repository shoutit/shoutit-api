/**
 * Created by Syron.
 * Date: 2/11/12
 * Time: 12:44 PM
 */

window.fbAsyncInit = function() {
  FB.init({
    appId      : '353625811317277',
    status     : false,
    cookie     : true,
    xfbml      : true,
    oauth      : true
  });

  function FBStatusChange(response) {

    if (response.authResponse) {
      //user is already logged in and connected

      var post_data = JSON.stringify(response.authResponse);

      requestAjaxily({
        url: '/fb_auth/',
        type: 'POST',
        data: {'data':post_data},
        successCallback: function (data) {
          if (redirect_after_login)
            redirect_by_response(data);
          else {
            $('body').trigger('signin_ok', [data.data.username]);
            redirect_after_login = true;
          }
        }
      });

    } else {
      //user is not connected to your app or logged out
    }
  }

  // run once with current status and whenever the status changes
  FB.Event.subscribe('auth.statusChange', FBStatusChange);

};

(function(d){
  var js, id = 'facebook-jssdk'; if (d.getElementById(id)) {return;}
  js = d.createElement('script'); js.id = id; js.async = true;
  js.src = "//connect.facebook.net/en_US/all.js";
  d.getElementsByTagName('head')[0].appendChild(js);
}(document));
