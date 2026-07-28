CREATE ROLE chatbot_reader LOGIN PASSWORD 'STRONG_PASSWORD';

GRANT CONNECT ON DATABASE ftimer_prod TO chatbot_reader;

GRANT USAGE ON SCHEMA public TO chatbot_reader;

REVOKE CREATE ON SCHEMA public FROM chatbot_reader;