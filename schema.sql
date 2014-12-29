create table blames (
       sha text not null,
       repository text not null,
       filename text,
       author text,
       gained_lines integer default 0,
       lost_lines integer default 0
);

