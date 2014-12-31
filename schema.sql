create table blames (
       sha text not null,
       repository text not null,
       filename text,
       author text,
       gained_lines integer default 0,
       lost_lines integer default 0
);

-- the full_blames contains a row for each filename at each commit, even if it didn't change --
create table full_blames (
       sha text not null,
       repository text not null,
       filename text,
       author text,
       lines integer not null
);

create table commits (
       sha text not null,
       repository text not null,
       topo_order integer not null,
       ts integer not null,
       author text
);
