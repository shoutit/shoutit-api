-- Function: max_followings(uuid, numeric)
CREATE OR REPLACE FUNCTION max_followings(p_profile_id UUID , p_begin NUMERIC)
	RETURNS INTEGER AS
	$BODY$
	BEGIN
		RETURN (SELECT
							max(subq.rank)
						FROM (

									 SELECT DISTINCT
										 count(*) AS rank
									 FROM "shoutit_post" AS post INNER JOIN "shoutit_post_Streams" AS post_streams ON (post.uuid = post_streams.id)
										 INNER JOIN "shoutit_stream" AS stream ON
																														 (post_streams.stream_id = stream.uuid)
										 INNER JOIN "shoutit_followship" AS followship ON (followship.stream_id = stream.uuid)
									 WHERE
										 stream."type" <> 3 AND followship.follower_id = p_profile_id AND post."muted" = FALSE AND post."is_disabled" = FALSE
										 AND
										 EXTRACT(EPOCH FROM post."date_published") > p_begin
									 GROUP BY post_id
									 ORDER BY rank DESC) AS subq);
	END
	$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;
ALTER FUNCTION max_followings( NUMERIC, NUMERIC )
OWNER TO syron;
