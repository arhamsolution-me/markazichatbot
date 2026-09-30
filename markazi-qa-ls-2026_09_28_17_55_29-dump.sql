--
-- PostgreSQL database dump
--

\restrict wDoXHYshzZJ0wzEBNDY3FHoIkET08XmdpB45HVHGxokQxL1RrTxYdtpdCgOUJXX

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
-- Name: invoice_status_enum; Type: TYPE; Schema: public; Owner: dbadmin
--

CREATE TYPE public.invoice_status_enum AS ENUM (
    'PAID',
    'PENDING',
    'DRAFT',
    'EXPIRED'
);


ALTER TYPE public.invoice_status_enum OWNER TO dbadmin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: invoice; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.invoice (
    id integer NOT NULL,
    "invoiceNo" character varying NOT NULL,
    status public.invoice_status_enum NOT NULL,
    "billedLicense" jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.invoice OWNER TO dbadmin;

--
-- Name: invoice_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.invoice_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.invoice_id_seq OWNER TO dbadmin;

--
-- Name: invoice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.invoice_id_seq OWNED BY public.invoice.id;


--
-- Name: license; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.license (
    id integer NOT NULL,
    configuration text NOT NULL
);


ALTER TABLE public.license OWNER TO dbadmin;

--
-- Name: license_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.license_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.license_id_seq OWNER TO dbadmin;

--
-- Name: license_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.license_id_seq OWNED BY public.license.id;


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
-- Name: service_providers; Type: TABLE; Schema: public; Owner: dbadmin
--

CREATE TABLE public.service_providers (
    id integer NOT NULL,
    configuration text NOT NULL
);


ALTER TABLE public.service_providers OWNER TO dbadmin;

--
-- Name: service_providers_id_seq; Type: SEQUENCE; Schema: public; Owner: dbadmin
--

CREATE SEQUENCE public.service_providers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.service_providers_id_seq OWNER TO dbadmin;

--
-- Name: service_providers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dbadmin
--

ALTER SEQUENCE public.service_providers_id_seq OWNED BY public.service_providers.id;


--
-- Name: invoice id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.invoice ALTER COLUMN id SET DEFAULT nextval('public.invoice_id_seq'::regclass);


--
-- Name: license id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.license ALTER COLUMN id SET DEFAULT nextval('public.license_id_seq'::regclass);


--
-- Name: migration_table id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.migration_table ALTER COLUMN id SET DEFAULT nextval('public.migration_table_id_seq'::regclass);


--
-- Name: service_providers id; Type: DEFAULT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.service_providers ALTER COLUMN id SET DEFAULT nextval('public.service_providers_id_seq'::regclass);


--
-- Data for Name: invoice; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.invoice (id, "invoiceNo", status, "billedLicense", created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: license; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.license (id, configuration) FROM stdin;
1	{"email":"hammad@gmail.com","erp":{"identifier":"SAP","metaData":[{"key":"serverURL","label":"URL","type":"string","required":true},{"key":"dbPassword","label":"Database Password","type":"string","required":true},{"key":"dbName","label":"Database name","type":"string","required":true},{"key":"userName","label":"Username","type":"string","required":true}]},"salesChannels":[{"identifier":"WOOCOMMERCE","name":"Woo Commerce","description":"Manage sales from your WooCommerce store","metaData":[{"key":"secretKey","label":"Secret Key","type":"string"},{"key":"consumerKey","label":"Consumer Key","type":"string"},{"key":"consumerSecret","label":"Consumer Secret","type":"string"}]},{"identifier":"SHOPIFY","name":"Shopify","description":"Manage sales from your WooCommerce store","metaData":[{"key":"secretKey","label":"Secret Key","type":"string"},{"key":"apiKey","label":"ApiKey","type":"string"}]}],"courierPartners":[{"identifier":"DHL","name":"DHL Express","description":"Fast, reliable international shipping","metaData":[{"key":"accountNumber","label":"Account Number","type":"string"},{"key":"apiKey","label":"API Key","type":"password"},{"key":"productionKey","label":"Production Key","type":"password"}]},{"identitifer":"blueex","name":"blueex","description":"Trusted local courier with COD","metaData":[{"key":"accountNumber","label":"Account Number","type":"string"},{"key":"apiKey","label":"API Key","type":"password"},{"key":"productionKey","label":"Production Key","type":"password"}]}],"noOfWarehouseAllowed":10,"noOfStaffAllowed":4,"noOfOrdersProcessingAllowed":4000,"licenseCharges":0,"channelAddons":[],"courierAddons":[]}
\.


--
-- Data for Name: migration_table; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.migration_table (id, "timestamp", name) FROM stdin;
1	1788946125773	SchemaUpdate1788946125773
\.


--
-- Data for Name: service_providers; Type: TABLE DATA; Schema: public; Owner: dbadmin
--

COPY public.service_providers (id, configuration) FROM stdin;
\.


--
-- Name: invoice_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.invoice_id_seq', 1, false);


--
-- Name: license_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.license_id_seq', 1, true);


--
-- Name: migration_table_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.migration_table_id_seq', 1, true);


--
-- Name: service_providers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dbadmin
--

SELECT pg_catalog.setval('public.service_providers_id_seq', 1, false);


--
-- Name: invoice PK_15d25c200d9bcd8a33f698daf18; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.invoice
    ADD CONSTRAINT "PK_15d25c200d9bcd8a33f698daf18" PRIMARY KEY (id);


--
-- Name: migration_table PK_2d2bf943d1902493395c05a4762; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.migration_table
    ADD CONSTRAINT "PK_2d2bf943d1902493395c05a4762" PRIMARY KEY (id);


--
-- Name: service_providers PK_73c86f1298c5285d76e66da2da9; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.service_providers
    ADD CONSTRAINT "PK_73c86f1298c5285d76e66da2da9" PRIMARY KEY (id);


--
-- Name: license PK_f168ac1ca5ba87286d03b2ef905; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.license
    ADD CONSTRAINT "PK_f168ac1ca5ba87286d03b2ef905" PRIMARY KEY (id);


--
-- Name: invoice UQ_7a07716f2519432623c404ee94b; Type: CONSTRAINT; Schema: public; Owner: dbadmin
--

ALTER TABLE ONLY public.invoice
    ADD CONSTRAINT "UQ_7a07716f2519432623c404ee94b" UNIQUE ("invoiceNo");


--
-- PostgreSQL database dump complete
--

\unrestrict wDoXHYshzZJ0wzEBNDY3FHoIkET08XmdpB45HVHGxokQxL1RrTxYdtpdCgOUJXX

