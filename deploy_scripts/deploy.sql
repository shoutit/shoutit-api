-- Function: get_followings(text, text)

-- DROP FUNCTION get_followings(text, text);

CREATE OR REPLACE FUNCTION get_followings(p_profile_text text, p_shout_text text)
  RETURNS integer AS
$BODY$
BEGIN
	return (select count(*) from (
--	select distinct followship.stream_id
--	from "shoutit_followship" AS followship
--	where followship.follower_id = p_profile_id

	select regexp_split_to_table(p_profile_text, ',')
	intersect
	select regexp_split_to_table(p_shout_text, ',')

--	select distinct stream_id
--	from "shoutit_shout_Streams" AS shout_streams
--	INNER JOIN "shoutit_stream" AS stream ON
--	(shout_streams.stream_id = stream.id)
--	where shout_id = p_shout_id and stream."Type" <> 3
	) as subq);
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION get_followings(text, text) OWNER TO postgres;


-- Function: normalized_distance(double precision, double precision, double precision, double precision)

-- DROP FUNCTION normalized_distance(double precision, double precision, double precision, double precision);

CREATE OR REPLACE FUNCTION normalized_distance(lat1 double precision, long1 double precision, lat2 double precision, long2 double precision)
  RETURNS double precision AS
$BODY$
DECLARE
	degrees_to_radians double precision = PI() / 180.0;
	phi1 double precision;
	phi2 double precision;
	theta1 double precision;
	theta2 double precision;
	cosine double precision;
	arc double precision;
BEGIN
	phi1 := (90.0 - lat1) * degrees_to_radians;
	phi2 := (90.0 - lat2) * degrees_to_radians;
	theta1 := long1 * degrees_to_radians;
	theta2 := long2 * degrees_to_radians;
	cosine := SIN(phi1) * SIN(phi2) * COS(theta1 - theta2) + COS(phi1) * COS(phi2);
	IF cosine >= 1.0 THEN
		RETURN 0.0;
	ELSE
		arc := acos(cosine);
		RETURN arc / pi();
	END IF;
	--multiply the result by pi * radius of earth to get the actual distance(approx.)
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION normalized_distance(double precision, double precision, double precision, double precision) OWNER TO postgres;

-- Function: max_followings(numeric, numeric)

-- DROP FUNCTION max_followings(numeric, numeric);

CREATE OR REPLACE FUNCTION max_followings(p_profile_id numeric, p_begin numeric)
  RETURNS integer AS
$BODY$
BEGIN
	return (select max(subq.rank) from(
		select distinct count(*) as rank
		from "shoutit_shout" as shout INNER JOIN "shoutit_shout_Streams" AS shout_streams ON (shout.id = shout_streams.shout_id)
		INNER JOIN "shoutit_stream" AS stream ON
		(shout_streams.stream_id = stream.id) INNER JOIN "shoutit_followship" AS followship ON
		(followship.stream_id = stream.id)
		where stream."Type" <> 3 and followship.follower_id = p_profile_id AND shout."IsMuted" = FALSE AND shout."IsDisabled" = FALSE AND EXTRACT (epoch from shout."DatePublished") > p_begin
		group by shout_id
		order by rank desc) as subq);
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION max_followings(numeric, numeric) OWNER TO postgres;


