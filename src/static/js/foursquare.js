var fs_client = null;

function SetUpFoursquareClient() {
    fs_client = new FourSquareClient("OHK5WCHEXIFGFLQ2MG4CWNCA3BIF4QS3QOLXT4H0TMASHDZQ",
        "R1COJBNHS0HDSADBX0D1QSGBHWYFZBXVA0WE0THNY2ZSZEEM",
        "https://www.shoutit.com/oauth2callback/foursquare/", true);
}



function SetUpFqBusinessSearchField(id, source_type, additional_source, selection_callback) {
//    $(function findExistingItems(items, source, source_id) {
//        return $.grep(items, function(i){
//            return (i.source_id == source_id);
//        });
//    });

    $(function() {
        $(id).autocomplete({
            minLength: 0,
            source: function(req, add) {
                function fs(places){
					var ll = user_lat + ',' + user_lng;
                    fs_client.venuesClient.search({"ll":ll, "query" : $(id).val()}, {
                        onSuccess: function(data)
                        {
                            var i = 0;
                            if (!places)
                                places = [];
                            var venues = data.response.venues;
                            
                            for (i = 0; i < venues.length; i++) {
                                if ($.grep(places, function(item) {return item.source_id == venues[i].id}).length == 0)
                                    if (venues[i].location.city !== undefined)
                                        places.push({
                                            label: venues[i].name,
                                            desc: venues[i].location.address,
                                            cat: venues[i].categories.length > 0 ? venues[i].categories[0].id : null,
                                            location: venues[i].location.lat + ", " + venues[i].location.lng,
                                            lat: venues[i].location.lat,
                                            lng: venues[i].location.lng,
                                            city: venues[i].location.city,
                                            country: venues[i].location.cc,
                                            source: source_type,
                                            source_id: venues[i].id,
                                            username: null
                                        });
                            }
                            add(places);
                        },
                        onFailure: function(data)
                        {}
                    });
                }

                if (additional_source) {
                    additional_source({
                        onSuccess: function(items) {
                            var places = [];
                            for (i = 0; i < items.length; i++) {
                                places.push(items[i]);
                            }
                            fs(places);
                        },
                        onFailure: function(data) {}
                    });
                } else {
                    fs([]);
                }
            },
            focus: function( event, ui ) {
                $(id).val( ui.item.label );
                return false;
            },
            select: function( event, ui ) {
                if (selection_callback != null)
                    selection_callback(ui.item);
//                $(id).val( ui.item.label );
                return false;
            }
        }).data( "autocomplete" )._renderItem = function( ul, item ) {
            return $( "<li></li>" )
                .data( "item.autocomplete", item )
                .append( "<a>" + item.label + "<br>" + item.desc + "</a><hr />" )
                .appendTo( ul );
        };
    });
}