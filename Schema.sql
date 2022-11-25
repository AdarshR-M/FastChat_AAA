--
-- PostgreSQL database dump
--

-- Dumped from database version 14.6 (Homebrew)
-- Dumped by pg_dump version 14.6 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: groupmessages; Type: TABLE; Schema: public; Owner: anand
--

CREATE TABLE public.groupmessages (
    sender_id integer NOT NULL,
    group_id integer NOT NULL,
    "time" text NOT NULL,
    message text NOT NULL,
    receiver_id integer NOT NULL
);


ALTER TABLE public.groupmessages OWNER TO anand;

--
-- Name: groups; Type: TABLE; Schema: public; Owner: anand
--

CREATE TABLE public.groups (
    group_id integer NOT NULL,
    participants integer[] NOT NULL,
    admin_id integer NOT NULL
);


ALTER TABLE public.groups OWNER TO anand;

--
-- Name: groups_group_id_seq; Type: SEQUENCE; Schema: public; Owner: anand
--

CREATE SEQUENCE public.groups_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.groups_group_id_seq OWNER TO anand;

--
-- Name: groups_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anand
--

ALTER SEQUENCE public.groups_group_id_seq OWNED BY public.groups.group_id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: anand
--

CREATE TABLE public.messages (
    sender_id integer NOT NULL,
    receiver_id integer NOT NULL,
    "time" text NOT NULL,
    message text NOT NULL
);


ALTER TABLE public.messages OWNER TO anand;

--
-- Name: numclients; Type: TABLE; Schema: public; Owner: anand
--

CREATE TABLE public.numclients (
    server_id integer NOT NULL,
    num_clients integer NOT NULL
);


ALTER TABLE public.numclients OWNER TO anand;

--
-- Name: users; Type: TABLE; Schema: public; Owner: anand
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    password text NOT NULL,
    server_id integer NOT NULL,
    public_key text NOT NULL
);


ALTER TABLE public.users OWNER TO anand;

--
-- Name: groups group_id; Type: DEFAULT; Schema: public; Owner: anand
--

ALTER TABLE ONLY public.groups ALTER COLUMN group_id SET DEFAULT nextval('public.groups_group_id_seq'::regclass);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: anand
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (group_id);


--
-- Name: numclients numclients_pkey; Type: CONSTRAINT; Schema: public; Owner: anand
--

ALTER TABLE ONLY public.numclients
    ADD CONSTRAINT numclients_pkey PRIMARY KEY (server_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: anand
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- PostgreSQL database dump complete
--

