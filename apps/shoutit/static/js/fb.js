/**
 * Created by Syron.
 * Date: 2/11/12
 * Time: 12:44 PM
 */

window.fbAsyncInit = function () {
  FB.init({
    appId: '353625811317277',
    status: false,
    cookie: true,
    xfbml: true,
    oauth: true,
    version: 'v2.1'

  });

  function FBStatusChange(response) {

    if (response.status == 'connected') {
      //user is already logged in and connected and response has authResponse
      
      requestAjaxily({
        type: 'POST',
        url: '/fb_auth/',
        data: JSON.stringify(response.authResponse),
        contentType: 'application/json',
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


(function (d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) {
    return;
  }
  js = d.createElement(s);
  js.id = id;
  js.src = "//connect.facebook.net/en_US/sdk.js";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));
