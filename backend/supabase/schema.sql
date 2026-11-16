-- backend/app/db.py 가 쓰는 표 셋. 날짜와 시각은 글자(text)로 그대로 둔다. (D-050)
-- 여러 번 실행해도 된다. 이미 있는 표는 건드리지 않는다.

create table if not exists users (
    id bigint generated always as identity primary key,
    email text not null unique,
    password_hash text,
    created_at text not null
);
alter table users enable row level security;

create table if not exists sessions (
    id bigint generated always as identity primary key,
    user_id bigint not null references users(id) on delete cascade,
    token_hash text not null unique,
    expires_at text not null,
    created_at text not null
);
alter table sessions enable row level security;

create table if not exists tasks (
    id bigint generated always as identity primary key,
    title text not null,
    description text not null default '',
    status text not null check (status in ('TODO', 'IN_PROGRESS', 'DONE')),
    created_at text not null,
    updated_at text not null,
    owner_id bigint not null references users(id),
    priority text not null default 'NORMAL' check (priority in ('LOW', 'NORMAL', 'HIGH')),
    due_date text check (due_date is null or due_date ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
);
create index if not exists idx_tasks_owner_id on tasks(owner_id);
alter table tasks enable row level security;
