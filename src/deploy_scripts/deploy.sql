-- Function: get_followings(text, text)
CREATE OR REPLACE FUNCTION get_followings(p_profile_text TEXT, p_shout_text TEXT)
	RETURNS INTEGER AS
	$BODY$
	BEGIN
		RETURN (SELECT
							count(*)
						FROM (
									 SELECT
										 regexp_split_to_table(p_profile_text, ',')
									 INTERSECT
									 SELECT
										 regexp_split_to_table(p_shout_text, ',')
								 ) AS subq);
	END
	$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;
ALTER FUNCTION get_followings( TEXT, TEXT )
OWNER TO syron;


-- Function: normalized_distance(double precision, double precision, double precision, double precision)
CREATE OR REPLACE FUNCTION normalized_distance(lat1 DOUBLE PRECISION, long1 DOUBLE PRECISION, lat2 DOUBLE PRECISION, long2 DOUBLE PRECISION)
	RETURNS DOUBLE PRECISION AS
	$BODY$
	DECLARE
		degrees_to_radians DOUBLE PRECISION = PI() / 180.0;
		phi1               DOUBLE PRECISION;
		phi2               DOUBLE PRECISION;
		theta1             DOUBLE PRECISION;
		theta2             DOUBLE PRECISION;
		cosine             DOUBLE PRECISION;
		arc                DOUBLE PRECISION;
	BEGIN
		phi1 := (90.0 - lat1) * degrees_to_radians;
		phi2 := (90.0 - lat2) * degrees_to_radians;
		theta1 := long1 * degrees_to_radians;
		theta2 := long2 * degrees_to_radians;
		cosine := SIN(phi1) * SIN(phi2) * COS(theta1 - theta2) + COS(phi1) * COS(phi2);
		IF cosine >= 1.0
		THEN
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
ALTER FUNCTION normalized_distance( DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION )
OWNER TO syron;




