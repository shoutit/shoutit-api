-- Function: get_followings(text, text)

-- DROP FUNCTION get_followings(text, text);

CREATE OR REPLACE FUNCTION get_followings(p_userprofile_text text, p_shout_text text)
  RETURNS integer AS
$BODY$
BEGIN
	return (select count(*) from (
--	select distinct followship.stream_id
--	from "ShoutWebsite_followship" AS followship
--	where followship.follower_id = p_userprofile_id

	select regexp_split_to_table(p_userprofile_text, ',')
	intersect
	select regexp_split_to_table(p_shout_text, ',')
		
--	select distinct stream_id
--	from "ShoutWebsite_shout_Streams" AS shout_streams
--	INNER JOIN "ShoutWebsite_stream" AS stream ON
--	(shout_streams.stream_id = stream.id)
--	where shout_id = p_shout_id and stream."Type" <> 3
	) as subq);
END
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION get_followings(text, text) OWNER TO postgres;

