DROP FUNCTION IF EXISTS set_users_permissions();
DROP TABLE IF EXISTS "shoutit_userpermission";
DROP TABLE IF EXISTS "shoutit_permission";
DROP SEQUENCE IF EXISTS "shoutit_userpermission_id_seq";
DROP SEQUENCE IF EXISTS "shoutit_permission_id_seq";

CREATE TABLE "shoutit_permission" (id integer NOT NULL, name character varying(512) NOT NULL);
ALTER TABLE public."shoutit_permission" OWNER TO postgres;
CREATE SEQUENCE "shoutit_permission_id_seq" START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
ALTER TABLE public."shoutit_permission_id_seq" OWNER TO postgres;
ALTER SEQUENCE "shoutit_permission_id_seq" OWNED BY "shoutit_permission".id;
SELECT pg_catalog.setval('"shoutit_permission_id_seq"', 14, true);
ALTER TABLE "shoutit_permission" ALTER COLUMN id SET DEFAULT nextval('"shoutit_permission_id_seq"'::regclass);
INSERT INTO "shoutit_permission" VALUES (1, 'USE_SHOUT_IT');
INSERT INTO "shoutit_permission" VALUES (2, 'SHOUT_MORE');
INSERT INTO "shoutit_permission" VALUES (3, 'SHOUT_REQUEST');
INSERT INTO "shoutit_permission" VALUES (4, 'SHOUT_OFFER');
INSERT INTO "shoutit_permission" VALUES (5, 'FOLLOW_TAG');
INSERT INTO "shoutit_permission" VALUES (6, 'FOLLOW_USER');
INSERT INTO "shoutit_permission" VALUES (7, 'ACTIVATED');
INSERT INTO "shoutit_permission" VALUES (8, 'SEND_MESSAGE');

INSERT INTO "shoutit_permission" VALUES (9, 'SHOUT_DEAL');
INSERT INTO "shoutit_permission" VALUES (10, 'POST_EXPERIENCE');
INSERT INTO "shoutit_permission" VALUES (11, 'SHARE_EXPERIENCE');
INSERT INTO "shoutit_permission" VALUES (12, 'COMMENT_ON_POST');
INSERT INTO "shoutit_permission" VALUES (13, 'ADD_GALLERY_ITEM');
INSERT INTO "shoutit_permission" VALUES (14, 'REPORT');

ALTER TABLE ONLY "shoutit_permission" ADD CONSTRAINT "shoutit_permission_name_key" UNIQUE (name);
ALTER TABLE ONLY "shoutit_permission" ADD CONSTRAINT "shoutit_permission_pkey" PRIMARY KEY (id);

CREATE TABLE "shoutit_userpermission" (id integer NOT NULL, user_id integer NOT NULL, permission_id integer NOT NULL, date_given timestamp with time zone NOT NULL);
ALTER TABLE public."shoutit_userpermission" OWNER TO postgres;
CREATE SEQUENCE "shoutit_userpermission_id_seq" START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
ALTER TABLE public."shoutit_userpermission_id_seq" OWNER TO postgres;
ALTER SEQUENCE "shoutit_userpermission_id_seq" OWNED BY "shoutit_userpermission".id;
ALTER TABLE "shoutit_userpermission" ALTER COLUMN id SET DEFAULT nextval('"shoutit_userpermission_id_seq"'::regclass);
ALTER TABLE ONLY "shoutit_userpermission" ADD CONSTRAINT "shoutit_userpermission_pkey" PRIMARY KEY (id);
CREATE INDEX "shoutit_userpermission_permission_id" ON "shoutit_userpermission" USING btree (permission_id);
CREATE INDEX "shoutit_userpermission_user_id" ON "shoutit_userpermission" USING btree (user_id);
ALTER TABLE ONLY "shoutit_userpermission" ADD CONSTRAINT "shoutit_userpermission_permission_id_fkey" FOREIGN KEY (permission_id) REFERENCES "shoutit_permission"(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE ONLY "shoutit_userpermission" ADD CONSTRAINT "shoutit_userpermission_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;

CREATE OR REPLACE FUNCTION give_permission(uid INT, pid INT) RETURNS VOID AS
$BODY$
BEGIN
	INSERT INTO "shoutit_userpermission" (user_id, permission_id, date_given) (
		SELECT uid,  pid, CURRENT_TIMESTAMP WHERE NOT EXISTS (
			SELECT 1 FROM "shoutit_userpermission" WHERE user_id = uid AND permission_id = pid
		)
	);
END
$BODY$
LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION set_users_permissions() RETURNS INT AS
$BODY$
DECLARE
    r RECORD;
    shouts INT;
BEGIN
    FOR r IN SELECT au.id, au.is_active, COALESCE(shouts.shouts_count, 0) shouts_count FROM auth_user au LEFT OUTER JOIN (SELECT "OwnerUser_id" id, COUNT(*) shouts_count FROM "shoutit_post" GROUP BY "OwnerUser_id") AS shouts ON au.id = shouts.id
    LOOP
        IF r.is_active THEN
            PERFORM give_permission(r.id, 1);
            PERFORM give_permission(r.id, 2);
            PERFORM give_permission(r.id, 3);
            PERFORM give_permission(r.id, 4);
            PERFORM give_permission(r.id, 5);
            PERFORM give_permission(r.id, 6);
            PERFORM give_permission(r.id, 7);
            PERFORM give_permission(r.id, 8);
            PERFORM give_permission(r.id, 10);
            PERFORM give_permission(r.id, 11);
            PERFORM give_permission(r.id, 12);
            PERFORM give_permission(r.id, 14);
        ELSE
            PERFORM give_permission(r.id, 1);
            PERFORM give_permission(r.id, 3);
            PERFORM give_permission(r.id, 4);
            PERFORM give_permission(r.id, 5);
            IF r.shouts_count < 5 THEN
                PERFORM give_permission(r.id, 2);
            END IF;
        END IF;
    END LOOP;
    RETURN 0;
END
$BODY$
LANGUAGE 'plpgsql' ;

SELECT * FROM set_users_permissions();
DROP FUNCTION IF EXISTS set_users_permissions();
DROP FUNCTION IF EXISTS give_permission(INT, INT);