create table channel(
	channel_id char(24) primary key,
	name text not null,
	customUrl text unique,
	published_date timestamp not null,
	thumbnail_url text unique,
	description text,
	country CHAR(2),
	keywords text,
	topic text,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP
);

create table video(
	video_id char(11) primary key,
	name text not null,
	published_date timestamp not null,
	thumbnail_url text unique,
	description text,
	tags text,
	topic text,
	categoryId smallint not null,
	duration VARCHAR(20) not null,
	dimension varchar(10)
);

create table video_log(
	video_id char(11) references video(video_id),
	view_count BIGINT not null default 0,
	like_count int not null default 0,
	comment_count int not null default 0,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	"date" date NULL
	
);

create table channel_log(
	channel_id char(24) references channel(channel_id),
	view_count BIGINT not null default 0,
	sub_count int not null default 0,
	video_count int not null default 0,
	created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
	"date" date NULL

);

create table status_code(
	status_id smallint not null primary key,
	name VARCHAR(20) unique not null,
	CHECK (status_id in (0,1,2))
);