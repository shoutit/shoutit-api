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

FourSquareEndpoint.getVenuesClient = function()
{
	var client = this;
	return {
		/**
		 * @constant
		 */	
		VENUES_URL: "https://api.foursquare.com/v2/venues/{venue_id}",
		/**
		 * @constant
		 */
		ADD_URL: "https://api.foursquare.com/v2/venues/add",
		/**
		 * @constant
		 */
		CATEGORIES_URL: "https://api.foursquare.com/v2/venues/categories",
		/**
		 * @constant
		 */
		EXPLORE_URL: "https://api.foursquare.com/v2/venues/explore",
		/**
		 * @constant
		 */
		MANAGED_URL: "https://api.foursquare.com/v2/venues/managed",
		/**
		 * @constant
		 */
		SEARCH_URL: "https://api.foursquare.com/v2/venues/search",
		/**
		 * @constant
		 */
		SUGGESTIONCOMPLETION_URL: "https://api.foursquare.com/v2/venues/suggestcompletion",
		/**
		 * @constant
		 */
		TIMESERIES_URL: "https://api.foursquare.com/v2/venues/timeseries",
		/**
		 * @constant
		 */
		TRENDING_URL: "https://api.foursquare.com/v2/venues/trending",
		/**
		 * @constant
		 */
		EVENTS_URL: "https://api.foursquare.com/v2/venues/{venue_id}/events",
		/**
		 * @constant
		 */
		HERENOW_URL: "https://api.foursquare.com/v2/venues/{venue_id}/herenow",
		/**
		 * @constant
		 */
		LINKS_URL: "https://api.foursquare.com/v2/venues/{venue_id}/links",
		/**
		 * @constant
		 */
		LISTED_URL: "https://api.foursquare.com/v2/venues/{venue_id}/listed",
		/**
		 * @constant
		 */
		MENU_URL: "https://api.foursquare.com/v2/venues/{venue_id}/menu",
		/**
		 * @constant
		 */
		PHOTOS_URL: "https://api.foursquare.com/v2/venues/{venue_id}/photos",
		/**
		 * @constant
		 */
		SIMILAR_URL: "https://api.foursquare.com/v2/venues/{venue_id}/similar",
		/**
		 * @constant
		 */
		STATS: "https://api.foursquare.com/v2/venues/{venue_id}/stats",
		/**
		 * @constant
		 */
		TIPS_URL: "https://api.foursquare.com/v2/venues/{venue_id}/tips",
		/**
		 * @constant
		 */
		EDIT_URL: "https://api.foursquare.com/v2/venues/{venue_id}/edit",
		/**
		 * @constant
		 */
		MARK_TODO_URL: "https://api.foursquare.com/v2/venues/{venue_id}/marktodo",
		/**
		 * @constant
		 */
		FLAG_URL: "https://api.foursquare.com/v2/venues/{venue_id}/flag",
		/**
		 * @constant
		 */
		PROPOSE_EDIT_URL: "https://api.foursquare.com/v2/venues/{venue_id}/proposeedit",
		
		venues: function(venueId, requestCallback)
		{
			var requestUrl = this.VENUES_URL.replace("{venue_id}", venueId) + client.requestQuery();
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		add: function(parameters, requestCallback)
		{
//			var parameters = {
//				name: null, 
//				address: null,
//				crossStreet: null, 
//				city: null, 
//				state: null, 
//				zip: null,
//				phone: null, 
//				ll: 0.0,0.0
//				primaryCategoryId
//			};
						
			var requestUrl = this.ADD_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback, "POST");
		},
		
		categories: function(requestCallback)
		{
			var requestUrl = this.CATEGORIES_URL + client.requestQuery();
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		explore: function(parameters, requestCallback)
		{
//			var parameters = {
//				ll, 
//				llAcc, 
//				altAcc, 
//				alt, 
//				radius, 
//				section, 
//				query, 
//				limit, 
//				intent, 
//				novelty
//			}				
			
			var requestUrl = this.EXPLORE_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		managed: function(requestCallback)
		{
			var requestUrl = this.MANAGED_URL + client.requestQuery();
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		search: function(parameters, requestCallback)
		{
//			var parameters = { 
//				ll, 
//				llAcc, 
//				altAcc, 
//				alt, 
//				query, 
//				limit, 
//				intent, 
//				categoryId, 
//				url, 
//				providerId, 
//				linkedId,
//				radius
//			}
			
			var requestUrl = this.SEARCH_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		suggestcompletion: function(parameters, requestCallback)
		{
//			var parameters = { 
//				ll, 
//				llAcc, 
//				altAcc, 
//				alt, 
//				query, 
//				limit
//			}			
			
			var requestUrl = this.SUGGESTIONCOMPLETION_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		timeseries: function()
		{
//			var parameters = { 
//				venueId, 
//				startAt, 
//				endAt 
//			}			
		
			var requestUrl = this.TIMESERIES_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		trending: function(parameters, requestCallback)
		{
//			var parameters = {
//				ll,
//				limit,
//				radius
//			}
			
			var requestUrl = this.TRENDING_URL + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
						
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		events: function(venueId, requestCallback)
		{
			var requestUrl = this.EVENTS_URL.replace("{venue_id}", venueId) + client.requestQuery();
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		herenow: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				limit,
//				radius,
//				afterTimestamp
//			}
			
			var requestUrl = this.HERENOW_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		links: function(venueId, requestCallback)
		{
			var requestUrl = this.LINKS_URL.replace("{venue_id}", venueId) + client.requestQuery();
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		listed: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				group,
//				limit,
//				offset
//			}	
		
			var requestUrl = this.LISTED_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);			
		},
		
		menu: function(venueId, requestCallback)
		{
			var requestUrl = this.MENU_URL.replace("{venue_id}", venueId) + client.requestQuery();			
			FourSquareUtils.doRequest(requestUrl, requestCallback);	
		},
		
		photos: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				group,
//				limit,
//				offset
//			}
			
			var requestUrl = this.PHOTOS_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		similar: function(requestCallback)
		{
			var requestUrl = this.SIMILAR_URL.replace("{venue_id}", venueId) + client.requestQuery();
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		stats: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				startAt,
//				endAt,
//			}
			var requestUrl = this.STATS_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		tips: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				sort,
//				limit,
//				offset
//			}
			
			var requestUrl = this.TIPS_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback);
		},
		
		edit: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				name,
//				address,
//				crossStreet,
//				city,
//				state,
//				zip, 
//				phone, 
//				ll,
//				categoryId,
//				twitter,
//				description,
//				url
//			}
			
			var requestUrl = this.EDIT_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback, "POST");
		},
		
		flag: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				problem
//			}
			
			var requestUrl = this.FLAG_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback, "POST");
		},
		
		marktodo: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				text
//			}
			
			var requestUrl = this.MARK_TODO_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
			
			FourSquareUtils.doRequest(requestUrl, requestCallback, "POST");
		},
		
		proposeedit: function(venueId, parameters, requestCallback)
		{
//			var parameters = {
//				name, 
//				address, 
//				crossStreet, 
//				city, 
//				state, 
//				zip, 
//				phone, 
//				ll, 
//				primaryCategoryId
//			}
			
			var requestUrl = this.PROPOSE_EDIT_URL.replace("{venue_id}", venueId) + client.requestQuery();
			requestUrl += FourSquareUtils.createQueryString("&", parameters);
						
			FourSquareUtils.doRequest(requestUrl, requestCallback, "POST");
		}
	}
};