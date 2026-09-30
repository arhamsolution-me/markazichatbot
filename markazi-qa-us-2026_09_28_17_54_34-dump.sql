--
-- PostgreSQL database dump
--

\restrict Uz4dVBgCjhpZJfD63CAszpIM5Y9beJrH64Ob1E3BHsOxHBAVKYYD1sFlEabe2l0

-- Dumped from database version 18.4 (Ubuntu 18.4-1.pgdg24.04+1)
-- Dumped by pg_dump version 18.6 (Ubuntu 18.6-1.pgdg24.04+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: users_gender_enum; Type: TYPE; Schema: public; Owner: dbadmin
--

CREATE TYPE public.users_gender_enum AS ENUM (
    'MALE',
    'FEMALE',
    'OTHER'
);


ALTER TYPE public.users_gender_enum OWNER TO dbadmin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: migration_table; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.migration_table (
    id integer NOT NULL,
    "timestamp" bigint NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.migration_table OWNER TO dbadmin;

--
-- Name: migration_table_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.migration_table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.migration_table_id_seq OWNER TO dbadmin;

--
-- Name: migration_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.migration_table_id_seq OWNED BY public.migration_table.id;


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.permissions (
    id integer NOT NULL,
    module character varying(500) NOT NULL,
    permission character varying(500) NOT NULL,
    slug character varying(500) NOT NULL,
    description text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.permissions OWNER TO dbadmin;

--
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.permissions_id_seq OWNER TO dbadmin;

--
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.permissions_id_seq OWNED BY public.permissions.id;


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.role_permissions (
    id integer NOT NULL,
    slug character varying(500) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    role integer
);


ALTER TABLE public.role_permissions OWNER TO dbadmin;

--
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.role_permissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.role_permissions_id_seq OWNER TO dbadmin;

--
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    title character varying(500) NOT NULL,
    description character varying(500),
    "isActive" boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.roles OWNER TO dbadmin;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO dbadmin;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: theme_settings; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.theme_settings (
    id integer NOT NULL,
    logo character varying NOT NULL,
    "brandColorsSettings" jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.theme_settings OWNER TO dbadmin;

--
-- Name: theme_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.theme_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.theme_settings_id_seq OWNER TO dbadmin;

--
-- Name: theme_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.theme_settings_id_seq OWNED BY public.theme_settings.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.users (
    id integer NOT NULL,
    "staffId" character varying(100),
    name character varying(500) NOT NULL,
    email character varying(500) NOT NULL,
    password character varying,
    "isPlatformAdmin" boolean DEFAULT false NOT NULL,
    "resetToken" text,
    "resetTokenTime" timestamp without time zone,
    "cellNo" character varying(500),
    "profilePicture" character varying(500),
    gender public.users_gender_enum,
    dob date,
    "locationId" integer,
    "isActive" boolean DEFAULT true NOT NULL,
    "isPasswordResetAfterFirstLogin" boolean DEFAULT false NOT NULL,
    "accountActivationResetToken" text,
    "accountActivationResetTokenTime" timestamp without time zone,
    "hasOnboarded" boolean DEFAULT false NOT NULL,
    "onboardingProgress" jsonb,
    "isVendorAdmin" boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    "roleId" integer
);


ALTER TABLE public.users OWNER TO dbadmin;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO dbadmin;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: widgets; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.widgets (
    id integer NOT NULL,
    title character varying(500),
    description character varying(500),
    key character varying(500),
    icon character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    "userId" integer,
    "xAxis" real,
    "yAxis" real,
    height real,
    width real
);


ALTER TABLE public.widgets OWNER TO dbadmin;

--
-- Name: widgets_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.widgets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.widgets_id_seq OWNER TO dbadmin;

--
-- Name: widgets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.widgets_id_seq OWNED BY public.widgets.id;


--
-- Name: migration_table id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.migration_table ALTER COLUMN id SET DEFAULT nextval('public.migration_table_id_seq'::regclass);


--
-- Name: permissions id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.permissions ALTER COLUMN id SET DEFAULT nextval('public.permissions_id_seq'::regclass);


--
-- Name: role_permissions id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: theme_settings id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.theme_settings ALTER COLUMN id SET DEFAULT nextval('public.theme_settings_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: widgets id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.widgets ALTER COLUMN id SET DEFAULT nextval('public.widgets_id_seq'::regclass);


--
-- Data for Name: migration_table; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.migration_table (id, "timestamp", name) FROM stdin;
1	1785841531275	SchemaUpdate1785841531275
2	1785841531296	SchemaUpdate1785841531296
3	1785841531302	SchemaUpdate1785841531302
4	1786433273561	SchemaUpdate1786433273561
5	1787903088955	SchemaUpdate1787903088955
6	1788963835462	SchemaUpdate1788963835462
7	1789971527860	SchemaUpdate1789971527860
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.permissions (id, module, permission, slug, description, created_at, updated_at) FROM stdin;
1	Warehouses	View Warehouses	view_warehouses	View list of warehouses.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
2	Warehouses	Configure Warehouses	configure_warehouses	View and manage configure warehouses.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
3	Warehouses	Edit Warehouses	edit_warehouses	Edit warehouse details.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
4	Warehouses	Addons Warehouses	addons_warehouses	View and manage warehouse addons.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
5	Sales Channel	View Channel	view_channel	View list of sales channels.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
6	Sales Channel	Edit Channel	edit_channel	Edit sales channel details.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
7	Sales Channel	Addons Channel	addons_channel	View and manage sales channel addons.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
8	Settings	View Courier Configuration	view_courier_configuration	View and manage courier configurations.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
9	Settings	Edit Courier Configuration	edit_courier_configuration	Edit courier configuration settings.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
10	Settings	View Duplicate Order	view_duplicate_order	View and manage duplicate order settings.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
11	Settings	Edit Duplicate Order	edit_duplicate_order	Edit duplicate order settings.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
12	Settings	View Notification Setting	view_notification_setting	View and manage notification settings.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
13	Settings	Edit Notification Setting	edit_notification_setting	Edit notification settings.	2026-09-23 11:37:00.962775	2026-09-23 11:37:00.962775
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.role_permissions (id, slug, created_at, updated_at, role) FROM stdin;
44	view_channel	2026-09-28 17:43:59.759277	2026-09-28 17:43:59.759277	1
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.roles (id, title, description, "isActive", created_at, updated_at) FROM stdin;
1	Staff Admin	\N	t	2026-09-23 11:40:21.708593	2026-09-23 11:40:21.708593
\.


--
-- Data for Name: theme_settings; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.theme_settings (id, logo, "brandColorsSettings", created_at, updated_at) FROM stdin;
1	uploads/2026/09/23/2495ed87-8068-44c4-8821-0931efa5e7b1-Screenshot.jpg	{"headerText": "#FFFFFF", "bodyTextColor": "#555555", "ctaButtonColor": "#2c5ebe", "buttonTextColor": "#FFFFFF", "headerBackground": "#7C0566"}	2026-09-23 16:51:37.486229	2026-09-23 16:51:37.486229
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.users (id, "staffId", name, email, password, "isPlatformAdmin", "resetToken", "resetTokenTime", "cellNo", "profilePicture", gender, dob, "locationId", "isActive", "isPasswordResetAfterFirstLogin", "accountActivationResetToken", "accountActivationResetTokenTime", "hasOnboarded", "onboardingProgress", "isVendorAdmin", created_at, updated_at, "roleId") FROM stdin;
1	\N	QA Team	khizra.israr@synavos.com	$2b$10$2qlIYnJzGJG9P380cX5zi.XY44NhqbfSPzLXNOp80boAIHtVb043a	t	1790155717557	2026-09-23 09:28:37.557	\N	\N	\N	\N	\N	t	t	\N	\N	f	\N	f	2026-09-23 11:37:00.962775	2026-09-23 14:28:37.569072	\N
4	12	John	john@gmail.com	$2b$10$eZkqyHjJZ1YXSAKFNWVAs.I5ce24lutmOe/dQOYdceTr0cB0pBvAW	f	\N	\N	+923091429887	\N	\N	\N	9	t	f	1790250743680	2026-09-24 11:52:23.68	f	\N	f	2026-09-24 16:52:23.681419	2026-09-24 16:52:51.799421	1
5	13	Ahsan	ahsan.amin@synavos.com	\N	f	\N	\N	+923091235663	\N	\N	\N	11	t	f	1790258915411	2026-09-24 14:08:35.411	f	\N	f	2026-09-24 19:08:35.412996	2026-09-24 19:09:45.706024	1
2	\N	QA Team	khizra.israr+1@synavos.com	$2b$10$dnMTnQlbuDxumsSAHP3ZZu89Xh5shggFVdySGxCCsCYkw6vFaNSym	t	\N	\N	\N	\N	\N	\N	\N	t	t	\N	\N	t	\N	t	2026-09-23 11:37:00.962775	2026-09-28 11:38:35.519762	\N
3	11	Mike	mike@gmail.com	$2b$10$K7jUG01dXVutxvleDCpR1eae1xlKFBC6VYeiB4rL8QfiYvgqKXZxy	f	\N	\N	+923091345667	\N	\N	\N	216513	t	f	1790145653456	2026-09-23 06:40:53.456	f	\N	f	2026-09-23 11:40:53.457249	2026-09-28 11:43:58.439663	1
\.


--
-- Data for Name: widgets; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.widgets (id, title, description, key, icon, created_at, updated_at, "userId", "xAxis", "yAxis", height, width) FROM stdin;
71	ORDERS_BY_CHANNELS	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	14.5	3	12
72	ORDER_DISTRIBUTION_BY_COURIERS	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	4	2.5	3	4
73	TOP_PERFORMING_STAFF	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	11.5	3	12
74	ORDER_DISTRIBUTION_BY_CHANNELS	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	8	2.5	3	4
75	ORDERS_ANALYSIS	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	5.5	3	12
76	LICENSE_OVERVIEW	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	1	1.5	12
77	OVERVIEW	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	0	1	12
78	TOP_TRENDING_WAREHOUSES	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	17.5	3	12
79	ORDER_DISTRIBUTION_BY_STATUS	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	2.5	3	4
80	ORDERS_BY_COURIERS	\N	\N	\N	2026-09-25 11:16:32.365906	2026-09-25 11:16:32.365906	2	0	8.5	3	12
\.


--
-- Name: migration_table_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.migration_table_id_seq', 7, true);


--
-- Name: permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.permissions_id_seq', 13, true);


--
-- Name: role_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.role_permissions_id_seq', 44, true);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.roles_id_seq', 1, true);


--
-- Name: theme_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.theme_settings_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.users_id_seq', 5, true);


--
-- Name: widgets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.widgets_id_seq', 80, true);


--
-- Name: migration_table PK_2d2bf943d1902493395c05a4762; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.migration_table
    ADD CONSTRAINT "PK_2d2bf943d1902493395c05a4762" PRIMARY KEY (id);


--
-- Name: theme_settings PK_4837c055b288cfab501eac406e0; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.theme_settings
    ADD CONSTRAINT "PK_4837c055b288cfab501eac406e0" PRIMARY KEY (id);


--
-- Name: role_permissions PK_84059017c90bfcb701b8fa42297; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT "PK_84059017c90bfcb701b8fa42297" PRIMARY KEY (id);


--
-- Name: permissions PK_920331560282b8bd21bb02290df; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT "PK_920331560282b8bd21bb02290df" PRIMARY KEY (id);


--
-- Name: users PK_a3ffb1c0c8416b9fc6f907b7433; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "PK_a3ffb1c0c8416b9fc6f907b7433" PRIMARY KEY (id);


--
-- Name: roles PK_c1433d71a4838793a49dcad46ab; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT "PK_c1433d71a4838793a49dcad46ab" PRIMARY KEY (id);


--
-- Name: widgets PK_da23136dbcfc91424451e24b725; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT "PK_da23136dbcfc91424451e24b725" PRIMARY KEY (id);


--
-- Name: users UQ_49f3f7c914660260c4c6de15686; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "UQ_49f3f7c914660260c4c6de15686" UNIQUE ("staffId");


--
-- Name: users FK_368e146b785b574f42ae9e53d5e; Type: FK CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "FK_368e146b785b574f42ae9e53d5e" FOREIGN KEY ("roleId") REFERENCES public.roles(id);


--
-- Name: widgets FK_58473818e25132d03d9572c322e; Type: FK CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT "FK_58473818e25132d03d9572c322e" FOREIGN KEY ("userId") REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: role_permissions FK_5d5086bd299f773d403574cf1c8; Type: FK CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT "FK_5d5086bd299f773d403574cf1c8" FOREIGN KEY (role) REFERENCES public.roles(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Uz4dVBgCjhpZJfD63CAszpIM5Y9beJrH64Ob1E3BHsOxHBAVKYYD1sFlEabe2l0

