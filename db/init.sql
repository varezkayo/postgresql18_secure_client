-- Учебная учётная запись для демонстрации.
CREATE ROLE student LOGIN PASSWORD 'student_demo_password';

REVOKE ALL ON DATABASE lab_db FROM PUBLIC;
GRANT CONNECT ON DATABASE lab_db TO student;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO student;
