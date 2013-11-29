-- Function: max_followings(numeric, numeric)

-- DROP FUNCTION max_followings(numeric, numeric);

CREATE OR REPLACE FUNCTION max_followings(p_userprofile_id numeric, p_begin numeric)
  RETURNS integer AS
$BODY$
BEGIN
	return (select max(subq.rank) from(
		select distinct count(*) as rank
		from "shoutit_shout" as shout INNER JOIN "shoutit_shout_Streams" AS shout_streams ON (shout.id = shout_streams.shout_id)
		INNER JOIN "shoutit_stream" AS stream ON
		(shout_streams.stream_id = stream.id) INNER JOIN "shoutit_followship" AS followship ON
		(followship.stream_id = stream.id)
		where stream."Type" <> 3 and followship.follower_id = p_userprofile_id AND shout."IsMuted" = FALSE AND shout."IsDisabled" = FALSE AND EXTRACT (epoch from shout."DatePublished") > p_begin
		group by shout_id
		order by rank desc) as subq);
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION max_followings(numeric, numeric) OWNER TO postgres;

