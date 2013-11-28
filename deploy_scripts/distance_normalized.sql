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