/*
The MIT License

Copyright (c) 2011 M.F.A. ten Veldhuis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

FourSquareEndpoint.getUpdatesClient = function()
{
	var client = this;
	return {
		UPDATES_URL: "https://api.foursquare.com/v2/updates/{update_id}",
		
		NOTIFICATIONS_URL: "https://api.foursquare.com/v2/updates/notifications",
		
		MARK_NOTIFICATIONS_READ_URL: "https://api.foursquare.com/v2/updates/marknotificationsread",
		
		updates: function(updateId, requestCallback)
		{
			var requestUrl = this.UPDATES_URL.replace("{update_id}", updateId) + client.requestQuery();
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		notifications: function(parameters, requestCallback)
		{
//			var parameters = {
//					limit
//			}
			
			var requestUrl = this.NOTIFICATIONS_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback, "GET");
		},
		
		marknotificationsread: function(parameters, requestCallback)
		{
//			var parameters = {
//				highWatermark
//			}
			
			var requestUrl = this.MARK_NOTIFICATIONS_READ_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback, "POST");
		}
	};
};