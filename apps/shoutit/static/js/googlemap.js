/**
 * Created by Syrex.
 * Date: 10/15/11
 * Time: 5:03 PM
 */

var image =  new google.maps.MarkerImage('/static/new_design/img/map-pin.png',new google.maps.Size(24, 27),new google.maps.Point(0,0),new google.maps.Point(12, 14));
var offer_image =  new google.maps.MarkerImage('/static/new_design/img/map-pin-offer.png',new google.maps.Size(24, 27),new google.maps.Point(0,0),new google.maps.Point(12, 14));
var request_image =  new google.maps.MarkerImage('/static/new_design/img/map-pin-request.png',new google.maps.Size(24, 27),new google.maps.Point(0,0),new google.maps.Point(12, 14));
var shadow = new google.maps.MarkerImage('/static/new_design/img/map-pin-shadow.png',new google.maps.Size(42,27),new google.maps.Point(0,0),new google.maps.Point(10,15));
var geocoder = new google.maps.Geocoder();

function GoogleMap(ID,location_id){

	this.ID = ID
	this.myOptions = {
		zoom: 10,
		mapTypeId: google.maps.MapTypeId.ROADMAP,
		panControl: false,
		zoomControl: true,
		zoomControlOptions: {
			style: google.maps.ZoomControlStyle.SMALL
		},
		mapTypeControl: false,
		scaleControl: false,
		streetViewControl: false,
		overviewMapControl: false,
		styles: [
			{ stylers: [{ saturation: -87 }]},
//            { elementType: "labels", stylers: [{ visibility: "simplified" }] },
//            { featureType: "poi", stylers: [{ visibility: "simplified" }] },
			{ featureType: "road", stylers: [{ lightness: 31 }, { hue: "#8ab736" }, { saturation: 5 }] },
			{ featureType: "water", stylers: [{ lightness: -5 }] }
		],
		scrollwheel: false,
		minZoom: 3
	};
	this.Map = new google.maps.Map($(this.ID)[0], this.myOptions);

	this.shoutStyles = [
		{ elementType: "geometry", stylers: [
			{ lightness: 45 },
			{ saturation: 33 },
			{ hue: "#007fff" }
		] },
		{ featureType: "road.local", stylers: [
			{ visibility: "off" }
		] },
		{ },
		{ elementType: "labels", stylers: [
			{ saturation: -50 },
			{ lightness: 34 },
			{ hue: "#004cff" }
		] }
	];
	//this.Map.setOptions({styles: this.shoutStyles});

	this.AddMarker = new google.maps.Marker({
		map: this.Map,
		draggable: true,
		animation: google.maps.Animation.DROP,
		icon: image,
		shadow : shadow
	});
//    google.maps.event.addListener(this.AddMarker, 'dragend', MarkerDragEnd);
	this.location_id = location_id;
	this.city_id = null;
	this.country_id = null;
	this.address_id = null;

	this.lat_lon = null;
	this.shouts = [];
	this.markers = [];
	this.oldInfowindow = null;
	this.isViewInfoWindow = false;

	this.center = null;
	this.DownLeft = null;
	this.UpRight = null;
	this.MapBounds = null;
	this.autocomplete = null;
}

GoogleMap.prototype.refreshLocation = function (lat,lng) {
	point = new google.maps.LatLng(lat,lng);
	this.AddMarker.setPosition(point);
	this.Map.setCenter(point);
}

GoogleMap.prototype.CreateProfileMap = function (Lat,Lng,search_input_id,city_id,country_id){
	var googleMap = this;
	googleMap.city_id = city_id;
	googleMap.country_id = country_id;

	google.maps.event.addListener(this.Map, 'click', function (event) { MapClick(event,googleMap) });
	google.maps.event.addListener(this.AddMarker, 'dragend', function() { MarkerDragEnd(googleMap) });

	point = new google.maps.LatLng(parseFloat(Lat), parseFloat(Lng));
	this.Map.setCenter(point);
	this.AddMarker.setPosition(point);
	setLocation(Lat,Lng,googleMap);

	googleMap.autocomplete = new google.maps.places.Autocomplete($('#'+search_input_id)[0]);
	googleMap.autocomplete.setTypes(['geocode']);
	googleMap.autocomplete.bindTo('bounds', googleMap.Map);
	google.maps.event.addListener(googleMap.autocomplete, 'place_changed', function() {autoCompleteSearchChanged(googleMap)});
}

GoogleMap.prototype.CreateShoutMap = function (search_input_id,city_id,country_id,address_id, lat, lng, shoutType) {
	var googleMap = this;
	googleMap.city_id = city_id;
	googleMap.country_id = country_id;
	googleMap.address_id = address_id;


	google.maps.event.addListener(this.Map, 'click', function (event) { MapClick(event,googleMap); });
	google.maps.event.addListener(this.AddMarker, 'dragend', function() { MarkerDragEnd(googleMap) });

	if (lat === undefined && lng === undefined) {
		requestAjaxily({
			url: '/xhr/clientLatLng/',
			googleMap : this,
			successCallback: function (data) {
				var location =  data.data.location;
				location_details = location.split(' ');
				point = new google.maps.LatLng(parseFloat(location_details[0]), parseFloat(location_details[1]));
				this.googleMap.Map.setCenter(point);
				this.googleMap.AddMarker.setPosition(point);
				if (shoutType !== undefined && shoutType == 'buy')
					this.googleMap.AddMarker.setIcon(request_image);
				else if (shoutType !== undefined && shoutType == 'sell')
					this.googleMap.AddMarker.setIcon(offer_image);
				setLocation(parseFloat(location_details[0]), parseFloat(location_details[1]),this.googleMap);
			}
		});
	} else {
		point = new google.maps.LatLng(lat, lng);
		googleMap.Map.setCenter(point);
		googleMap.AddMarker.setPosition(point);
		if (shoutType !== undefined && shoutType == 'buy')
			googleMap.AddMarker.setIcon(request_image);
		else if (shoutType !== undefined && shoutType == 'sell')
			googleMap.AddMarker.setIcon(offer_image);
		setLocation(lat, lng, googleMap);
	}
	googleMap.autocomplete = new google.maps.places.Autocomplete($('#'+search_input_id)[0]);
	googleMap.autocomplete.setTypes(['geocode']);
	googleMap.autocomplete.bindTo('bounds', googleMap.Map);
	google.maps.event.addListener(googleMap.autocomplete, 'place_changed', function (){ autoCompleteSearchChanged(googleMap) });
}

GoogleMap.prototype.CreateViewShoutMap = function (Lat,Lng,shoutType){
	var googleMap = this;
	point = new google.maps.LatLng(parseFloat(Lat), parseFloat(Lng));
	this.Map.setCenter(point);
	this.AddMarker.setPosition(point);
	if (shoutType !== undefined && shoutType == 0)
		this.AddMarker.setIcon(request_image);
	else if (shoutType !== undefined && shoutType == 1)
		this.AddMarker.setIcon(offer_image);
	this.AddMarker.draggable = false;
}


GoogleMap.prototype.CreateLandingMap = function(lat,lng){
	var googleMap = this;

	google.maps.event.addListener(this.Map, 'idle', function () {BoundChanged(googleMap)} );
	google.maps.event.addListener(this.Map, 'click' , function(){
		if (this.oldInfowindow)
			this.oldInfowindow.close();
	});

	if (lat == 0 && lng==0)
	requestAjaxily({
		url: '/xhr/clientLatLng/',
		googleMap : this,
		successCallback: function (data) {
			var location =  data.data.location;
			location_details = location.split(' ');
			point = new google.maps.LatLng(parseFloat(location_details[0]), parseFloat(location_details[1]));
			this.googleMap.Map.setCenter(point);
//            BoundChanged(this.googleMap);
		}
	});
	else{
		point = new google.maps.LatLng(parseFloat(lat), parseFloat(lng));
		googleMap.Map.setCenter(point);
	}
}

	function BoundChanged (googleMap){
		if (googleMap.isViewInfoWindow){
			googleMap.isViewInfoWindow = false;
			return;
		}

		var post_data;
		MapBounds = googleMap.Map.getBounds();
		if (MapBounds == undefined)
			return;
		UpRight = MapBounds.getNorthEast();
		DownLeft = MapBounds.getSouthWest();
		post_data = {DownLeftLat: DownLeft.lat(), DownLeftLng : DownLeft.lng() ,
					 UpRightLat: UpRight.lat(), UpRightLng : UpRight.lng(), Zoom:googleMap.Map.getZoom()
		};

		requestAjaxily({
			url: '/xhr/loadShouts/',
			data: post_data,
			type: 'GET',
			successCallback: function (data) {
				var locations =  data.data.locations;
				var shoutsId = data.data.shoutsId;
				var shoutsTypes = data.data.shoutsTypes;

				for (var i=0;i< googleMap.markers.length;i++)
					googleMap.markers[i].setMap(null);
				googleMap.markers = [];

				for(var i=0;i<locations.length;i++){
					googleMap.lat_lon = locations[i].split(' ');
					lat = googleMap.lat_lon[0];
					lon = googleMap.lat_lon[1];
					point = new google.maps.LatLng(lat = parseFloat(lat), lon=parseFloat(lon));
					addMarker(point,shoutsId[i],googleMap,shoutsTypes[i])
				}
			}
		});
	}

	function addMarker (point,shoutsId,googleMap,shoutType) {
		Marker = new google.maps.Marker({
			map: googleMap.Map,
			position : point
//            ,animation: google.maps.Animation.BOUNCE
			,icon: image
			,shadow : shadow
//                DROP BOUNCE
		});
		if (shoutType !== undefined) {
			if (shoutType === 0)
				Marker.setIcon(request_image);
			else if (shoutType === 1)
				Marker.setIcon(offer_image);
		}
		googleMap.markers.push(Marker);

		var infowindow = new google.maps.InfoWindow({
			position: point,
			title :  ""+shoutsId
		});

		google.maps.event.addListener(Marker, 'click', function() {
			googleMap.isViewInfoWindow = true;
			if (googleMap.oldInfowindow)
				googleMap.oldInfowindow.close();
			var post_data = {shoutId: infowindow.title}
			requestAjaxily({
					url: '/xhr/loadShout/' + infowindow.title,
					data: post_data,
					type: 'GET',
					successCallback: function(data){
						infowindow.content = data.data.html;
						infowindow.open(googleMap.Map);
						googleMap.oldInfowindow = infowindow;
						$('.pd').prettyDate();
					}
				}
			);
		});
	}

	function MarkerDragEnd(googleMap) {
		var pos = googleMap.AddMarker.getPosition();
		setLocation(pos.lat(),pos.lng(),googleMap);
		googleMap.Map.setCenter(pos);
	}

	function MapClick(event,googleMap) {
		var myLatLng = event.latLng;
		var lat = myLatLng.lat();
		var lng = myLatLng.lng();
		point = new google.maps.LatLng(lat,lng);
		googleMap.AddMarker.setOptions({
			animation : google.maps.Animation.DROP,
			position: point
		});
		googleMap.AddMarker.setAnimation(google.maps.Animation.DROP);
		setLocation(point.lat(),point.lng(),googleMap);
//        googleMap.Map.setCenter(point);
	}

	function autoCompleteSearchChanged(googleMap) {
		var place = googleMap.autocomplete.getPlace();
		if (place.geometry.viewport) {
			googleMap.Map.fitBounds(place.geometry.viewport);
		} else {
			googleMap.Map.setCenter(place.geometry.location);
		}
		googleMap.Map.setZoom(7);
		googleMap.AddMarker.setPosition(place.geometry.location);
		setLocation(googleMap.AddMarker.getPosition().lat(), googleMap.AddMarker.getPosition().lng(),googleMap);
	}

	function setLocation(lat,lng,googleMap){
		var id_location = '#'+googleMap.location_id;
		var id_city = '#'+googleMap.city_id;
		var id_country = '#'+googleMap.country_id;
		var id_address = '#'+googleMap.address_id;
		$(id_location).val(lat+','+lng);

//        googleMap.AddMarker.getPosition()
		getLocationInfoByLatLng(lat,lng, function (info) {
			if (info == null)
				$(id_location).val("Error");
			else{
				if ($(id_address).length != 0)
					$(id_address).val(info['address']);
				if ($(id_country).length != 0)
					$(id_country).val(info['country']);
				if ($(id_city).length != 0)
					$(id_city).val(info['city']);
			}
		});
	}

	function getLocationInfoByLatLng(lat,lng,f){
		var point = new google.maps.LatLng(lat,lng);
		var info = {'country':null,'city':null, 'address': null};
		geocoder.geocode({'latLng': point}, function(results, status) {
			if (status == google.maps.GeocoderStatus.OK) {
				info['address'] = results[0]['formatted_address'];

				var locality = null;
				var postal_town = null;
				var administrative_area_level_1 = null;

				for (var i = results.length-1;i >= 0;i--){
					for (var j=0; j< results[i]['address_components'].length; j++)
						if ( $.inArray('country', results[i]['address_components'][j]['types']) != -1 )
							info['country'] = results[i]['address_components'][j]['short_name'];
						else if( $.inArray('locality', results[i]['address_components'][j]['types']) != -1 )
							locality = results[i]['address_components'][j]['long_name'];
						else if ( $.inArray('postal_town', results[i]['address_components'][j]['types']) != -1 )
							postal_town = results[i]['address_components'][j]['long_name'];
						else if ( $.inArray('administrative_area_level_1', results[i]['address_components'][j]['types']) != -1 )
							administrative_area_level_1 = results[i]['address_components'][j]['long_name'];
				}
//                for (var i = results.length-1;i >= 0;i--){
//                    for (var type in results[i]['types'])
//                        if (results[i]['types'][type] == 'country')
//                            info['country'] = results[i]['address_components'][0]['short_name'];
//                        else if(results[i]['types'][type] == 'locality')
//                            locality = results[i]['address_components'][0]['long_name'];
//                        else if (results[i]['types'][type] == 'postal_town')
//                            postal_town = results[i]['address_components'][0]['long_name'];
//                        else if (results[i]['types'][type] == 'administrative_area_level_1')
//                            administrative_area_level_1 = results[i]['address_components'][0]['long_name'];
//                }

				if (info['country'] == null)
					info['country'] = 'AE';
				if (locality != null)
					info['city'] = locality;
				else if (postal_town != null)
					info['city'] = postal_town
				else if (administrative_area_level_1 != null)
					info['city'] = administrative_area_level_1
				else
					info['city'] = 'Dubai'
			} else {
				alert("Location Not Valid");
				info = null;
			}
			f(info);
		});
	}



//      geocoder.geocode({'latLng': point}, function(results, status) {
//            if (status == google.maps.GeocoderStatus.OK) {
//                info['address'] = results[0]['formatted_address'];
//
//                var addressComponents = results[(results.length == 1) ? 0 : (results.length-2)]['address_components'];
//                var len = addressComponents.length;
//
//                if (addressComponents[len-1]['types'][0] == 'country'){
//                    info['country'] = addressComponents[len-1]['short_name'];
//                    info['city'] = addressComponents[(len>=2) ? len-2 : len-1]['long_name'];
//                }else{
//                    if (len>=2){
//                        info['country'] = addressComponents[len-2]['short_name'];
//                        info['city'] = addressComponents[(len>=3)? len-3 : len-2]['long_name'];
//                    }
//                }
//                if (info['country'] == null)
//                    info['country'] = 'AE';
//                if (info['city'] == null)
//                    info['city'] = 'Dubai';
//            } else {
//                alert("Location Not Valid");
//                info = null;
//            }
//            f(info);
//        });


//var Map = null;
//var AddMarker = null;
//
//var lat_lon;
//var shouts = [];
//var markers = [];
//var oldInfowindow;
//var isViewInfoWindow = false;
//
//var center;
//var DownLeft;
//var UpRight;
//var MapBounds;
//
//var image =  new google.maps.MarkerImage('/static/new_design/img/map-pin.png',new google.maps.Size(24, 27),new google.maps.Point(0,0),new google.maps.Point(12, 14));
//var shadow = new google.maps.MarkerImage('/static/new_design/img/map-pin-shadow.png',new google.maps.Size(42,27),new google.maps.Point(0,0),new google.maps.Point(10,15));
//
//    function setLocation(lat,lng){
//        document.getElementById('id_location').value = lat+','+lng;
//        geocoder.geocode({'latLng': AddMarker.getPosition()}, function(results, status) {
//            if (status == google.maps.GeocoderStatus.OK) {
//            } else {
//                alert("Location Not Valide");
//            }
//        });
//    }
//
//    function refreshLocation(lat,lng) {
//        if (AddMarker != 'undefined'){
//            point = new google.maps.LatLng(lat,lng);
//            AddMarker.setPosition(point);
//            Map.setCenter(point);
//        }
//    }
//
////var mc;
//var geocoder;
//
//    function CreateMap(id){
//        var myOptions = {
//            zoom: 10,
//            mapTypeId: google.maps.MapTypeId.ROADMAP,
//            panControl: false,
//            zoomControl: true,
//            zoomControlOptions: {
//                style: google.maps.ZoomControlStyle.SMALL
//			},
//            mapTypeControl: false,
//            scaleControl: false,
//            streetViewControl: false,
//            overviewMapControl: false,
//            scrollwheel: false,
//            minZoom: 3
//        };
//
//
//		var shoutStyles = [
//			{ elementType: "geometry", stylers: [
//				{ lightness: 45 },
//				{ saturation: 33 },
//				{ hue: "#007fff" }
//			] },
//			{ featureType: "road.local", stylers: [
//				{ visibility: "off" }
//			] },
//			{ },
//			{ elementType: "labels", stylers: [
//				{ saturation: -50 },
//				{ lightness: 34 },
//				{ hue: "#004cff" }
//			] }
//		];
//
//
//		Map = new google.maps.Map(document.getElementById(id), myOptions);
////		Map.setOptions({styles: shoutStyles});
//        AddMarker = new google.maps.Marker({
//            map: Map,
//            draggable: true,
//            animation: google.maps.Animation.DROP
//        });
//        google.maps.event.addListener(AddMarker, 'dragend', MarkerDragEnd);
//        geocoder = new google.maps.Geocoder();
//    }
//
//    function CreateProfileMap(Lat,Lng,id){
//        CreateMap(id);
//        google.maps.event.addListener(Map, 'click', MapClick);
//
//        point = new google.maps.LatLng(parseFloat(Lat), parseFloat(Lng));
//        Map.setCenter(point);
//        AddMarker.setPosition(point);
//        setLocation(Lat,Lng);
//    }
//
//	function CreateShoutMap(id) {
//        CreateMap(id);
//        google.maps.event.addListener(Map, 'click', MapClick);
//
//        requestAjaxily({
//            url: '/xhr/clientLatLng/',
//            successCallback: function (data) {
//                var location =  data.data.location;
//                location_details = location.split(' ');
//                point = new google.maps.LatLng(parseFloat(location_details[0]), parseFloat(location_details[1]));
//                Map.setCenter(point);
//                AddMarker.setPosition(point);
//                setLocation(parseFloat(location_details[0]), parseFloat(location_details[1]));
//            }
//        });
//	}
//
//    function CreateLandingMap(id,lat,lng){
//        CreateMap(id);
//        google.maps.event.addListener(Map, 'idle', BoundChanged);
//        google.maps.event.addListener(Map, 'click' , function(){
//            if (oldInfowindow)
//            oldInfowindow.close();
//        });
//
//        if (lat == null || lng ==null)
//        requestAjaxily({
//            url: '/xhr/clientLatLng/',
//            successCallback: function (data) {
//                var location =  data.data.location;
//                location_details = location.split(' ');
//                point = new google.maps.LatLng(parseFloat(location_details[0]), parseFloat(location_details[1]));
//                Map.setCenter(point);
//            }
//        });
//        else{
//            point = new google.maps.LatLng(parseFloat(lat), parseFloat(lng));
//            Map.setCenter(point);
//        }
//    }
//
//    function BoundChanged(e){
//        if (isViewInfoWindow){
//            isViewInfoWindow = false;
//            return;
//        }
//
//        var post_data;
//        MapBounds = Map.getBounds();
//        if (MapBounds == undefined)
//            return;
//        UpRight = MapBounds.getNorthEast();
//        DownLeft = MapBounds.getSouthWest();
//        post_data = {DownLeftLat: DownLeft.lat(), DownLeftLng : DownLeft.lng() ,
//                     UpRightLat: UpRight.lat(), UpRightLng : UpRight.lng(), Zoom:Map.getZoom()
//        };
//
//        requestAjaxily({
//            url: '/xhr/loadShouts/',
//            data: post_data,
//            type: 'GET',
//            successCallback: function (data) {
//                var locations =  data.data.locations;
//                var shoutsId = data.data.shoutsId;
//
//                for (var i=0;i<markers.length;i++)
//                    markers[i].setMap(null);
//                markers = [];
//
//                for(var i=0;i<locations.length;i++){
//                    lat_lon = locations[i].split(' ');
//                    lat = lat_lon[0];
//                    lon = lat_lon[1];
//                    point = new google.maps.LatLng(lat = parseFloat(lat), lon=parseFloat(lon));
//                    addMarker(point,shoutsId[i])
//                }
//            }
//        });
//    }
//
//    function addMarker(point,shoutId) {
//        Marker = new google.maps.Marker({
//            map: Map,
//            position : point
////            ,animation: google.maps.Animation.BOUNCE
//            ,icon: image
//            ,shadow : shadow
////            ,shape :shape
////                DROP BOUNCE
//        });
//
//        markers.push(Marker);
//        var infowindow = new google.maps.InfoWindow({
//            position: point
//            ,title :  ""+shoutId
//        });
//
//        google.maps.event.addListener(Marker, 'click', function() {
//            isViewInfoWindow = true;
//            if (oldInfowindow)
//                oldInfowindow.close();
//            var post_data = {shoutId: infowindow.title}
//            requestAjaxily({
//                    url: '/xhr/loadShout',
//                    data: post_data,
//                    type: 'GET',
//                    successCallback: function(data){
//                        infowindow.content = data.data.shout;
//                        infowindow.open(Map);
//                        oldInfowindow = infowindow;
//                        $('.pd').prettyDate();
//                    }
//                }
//            );
//        });
//
//    }
//    function MarkerDragEnd() {
//        var pos = AddMarker.getPosition();
//        setLocation(pos.lat(),pos.lng());
//        Map.setCenter(pos);
//    }
//
//    function MapClick(event) {
//        var myLatLng = event.latLng;
//        var lat = myLatLng.lat();
//        var lng = myLatLng.lng();
//        point = new google.maps.LatLng(lat,lng);
//        AddMarker.setOptions({
//            animation : google.maps.Animation.DROP,
//            position: point
//        });
//        AddMarker.setAnimation(google.maps.Animation.DROP);
//        setLocation(point.lat(),point.lng());
//    }