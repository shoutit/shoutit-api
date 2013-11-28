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

FourSquareEndpoint = {};

// make sure we can do XMLHttpRequests
if(!window.XMLHttpRequest && window.ActiveXObject) 
{
	window.XMLHttpRequest = function()
	{
		try 
		{
			return new ActiveXObject("Msxml2.XMLHTTP");
		} 
		catch(e) 
		{
			try 
			{
				return new ActiveXObject("Microsoft.XMLHTTP");
			} 
			catch(e) 
			{
				return false;
			}
		}
	};
} 	

String.prototype.trim = function() 
{
	var	str = this.replace(/^\s\s*/, ''),
		ws = /\s/,
		i = str.length;
	while (ws.test(str.charAt(--i)));
	return str.slice(0, i + 1);
}

/**
 * @class
 */
FourSquareUtils = 
{
    noStorageNotification: true,
    
    cookieSupport: function()
    {
        try
        {
            return (document.cookies != undefined)
        }
        catch(exception)
        {
            return false;
        }
    },
    
    storageSupport: function()
    {
        try
        {
            window.localStorage.getItem("test");
            return ('localStorage' in window);
        }
        catch(exc)
        {
            return false
        }
        
        return false;
    },
    
	getCookie: function(toGet)
	{
		var cookies = document.cookie.split(";");
		for(var idx = 0; idx < cookies.length; idx++)
		{
			var cookieName = cookies[idx].substr(0, cookies[idx].indexOf("=")).trim();
			var cookieValue = cookies[idx].substr(cookies[idx].indexOf("=") + 1);

			if(cookieName == toGet)
			{
				return unescape(cookieValue);
			}
        }
  		
  		return null;
	},
		
	setCookie: function(name, value)
	{
		document.cookie = name + "=" + value;
	},
    
    retrieveValue: function(name)
    {
        if(FourSquareUtils.cookieSupport())
        {
            return FourSquareUtils.getCookie(name);
        }
        else if(FourSquareUtils.storageSupport())
        {
            return localStorage.getItem(name);
        }
        
        if(FourSquareUtils.noStorageNotification)
        {
            alert('unable to support value storage');
            FourSquareUtils.noStorageNotification = false;
        }
    },
    
    storeValue: function(name, value)
    {
        if(FourSquareUtils.cookieSupport())
        {
            FourSquareUtils.setCookie(name, value);
            return;
        }
        else if(FourSquareUtils.storageSupport())
        {
            localStorage.setItem(name, value);
            return;
        }
        
        if(FourSquareUtils.noStorageNotification)
        {
            alert('unable to support value storage');
            FourSquareUtils.noStorageNotification = false;
        }
    },
	
	retrieveAccessToken: function()
	{
		var hash = document.location.hash;
		if(hash.indexOf("#access_token=") != -1)
		{
			FourSquareUtils.storeValue("fs_access_token", hash.replace("#access_token=", ""));
			return hash.replace("#access_token=", "");
		}
		else if(FourSquareUtils.retrieveValue("fs_access_token") != null)
		{
			return FourSquareUtils.retrieveValue("fs_access_token");
		}
	
		return null;
	},
	
	parseResponse: function(response)
	{
		try
		{
			return eval("(" + response + ")");
		}
		catch(exception)
		{
			return null;
		}
	},
	
	createQueryString: function(prefix, parameters)
	{
		var query = "";
		for(key in parameters) 
		{
			if(parameters[key] != undefined && parameters[key] != null)
			{
                if(typeof parameters[key] == "string")
                {
                    if(parameters[key].trim() != "")
                    {
                        query += "&" + key + "=" + parameters[key];
                    }
                }
                else
                {
                    query += "&" + key + "=" + parameters[key];
                }
			}
		}

		if(query.length > 0)
		{
			prefix = (prefix) ? prefix : "";
			query = prefix + query.substring(1);
		}
		
		return query;
	},
	
	doRequest: function(url, requestCallback, method, body)
	{
		var request = new XMLHttpRequest();
	    var method = (method) ? method : "GET";
			    
	    request.open(method, url, true);	    
	    request.onreadystatechange = function(event) 
	    {
	    	if(request.readyState == 4) 
	    	{
	    		if(request.status == 200)
	    		{
	    			if(requestCallback.onSuccess)
	    			{
	    				requestCallback.onSuccess(
	    						FourSquareUtils.parseResponse(request.responseText));
	    			}
	    		}
	    		else
		    	{
		    		if(requestCallback.onFailure)
		    		{
		    			requestCallback.onFailure(
		    					FourSquareUtils.parseResponse(request.responseText));
		    		}
		    	}
	    	}
	    };
	    
	    if(body)
	    {
	    	request.setRequestHeader("Content-Length", body.length);
	    	request.send(body);
	    }
	    else
	    {
	    	request.send();
	    }
	},
	
	doSimpleRequest: function(endPointUrl, requestCallback)
	{
		var requestUrl = endPointUrl + client.requestQuery();
		FourSquareUtils.doRequest(requestUrl, requestCallback);
	},
	
	doIntricateRequest: function(endPointUrl, parameters, requestCallback)
	{
		var requestUrl = endPointUrl + client.requestQuery();;
		requestUrl += FourSquareUtils.createQueryString("&", parameters);
		
		FourSquareUtils.doRequest(requestUrl, requestCallback);
	}
};

/**
 * @class
 */
FourSquareClient = function(clientId, clientSecret, redirectUri, rememberAppCredentials)
{
	/**
	 * @constant
	 */
	this.AUTHENTICATION_URL = "https://foursquare.com/oauth2/authenticate";
	/**
	 * @constant
	 */
	this.ACCESS_TOKEN_URL = "https://foursquare.com/oauth2/access_token";
	
	this.requestQuery = function()
	{
		if(!this.accessToken)
		{
			return "?v=20111020&client_id=" + this.clientId + "&client_secret=" + this.clientSecret;
		}
		else
		{
			return "?v=20111020&oauth_token=" + this.accessToken;
		}
	};
	
	if(clientId == undefined || redirectUri == undefined)
	{
		if(rememberAppCredentials)
		{
			// see if we can retrieve the cookies
			this.redirectUri = FourSquareUtils.retrieveValue("fs_redirect_uri");
			this.clientId = FourSquareUtils.retrieveValue("fs_client_id");
			this.clientSecret = FourSquareUtils.retrieveValue("fs_client_secret");
		}
	}
	else
	{
		this.redirectUri = redirectUri;
		this.clientId = clientId;
		this.clientSecret = clientSecret;
		
		if(rememberAppCredentials)
		{
			FourSquareUtils.storeValue("fs_client_id", this.clientId);
			FourSquareUtils.storeValue("fs_client_secret", this.clientSecret);
			FourSquareUtils.storeValue("fs_redirect_uri", this.redirectUri);
		}
	}
	
	this.accessToken = FourSquareUtils.retrieveAccessToken();
	this.authenticate = function()
	{
		var authenticationURL = this.AUTHENTICATION_URL + "?client_id=" + this.clientId; 
		authenticationURL += FourSquareUtils.createQueryString("&",
							 {
							 	 response_type: "token",
								 redirect_uri: this.redirectUri
							 });
		
		window.open(authenticationURL);
	};
	
	//=================================================
	// The separate clients for each type of endpoint.
	//=================================================

	this.usersClient = FourSquareEndpoint.getUsersClient.call(this);	

	this.venuesClient = FourSquareEndpoint.getVenuesClient.call(this); 
	
	this.checkinsClient = FourSquareEndpoint.getCheckinsClient.call(this);
		
	this.tipsClient = FourSquareEndpoint.getTipsClient.call(this);
	
	this.photosClient = FourSquareEndpoint.getPhotosClient.call(this);
	
	this.settingsClient = FourSquareEndpoint.getSettingsClient.call(this);
	
	this.specialsClient = FourSquareEndpoint.getSpecialsClient.call(this);
	
	this.updatesClient = FourSquareEndpoint.getUpdatesClient.call(this);
	
	this.eventsClient = FourSquareEndpoint.getUpdatesClient.call(this);
};