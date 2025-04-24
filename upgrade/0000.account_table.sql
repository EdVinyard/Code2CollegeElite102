-- all dates and times will be in the UTC time zone
SET time_zone = '+00:00';

create table if not exists account (
	-- an account number/identifier
    id int primary key auto_increment,

    -- account holder's full name
    full_name varchar(1024) character set utf8mb4 not null,

    -- can handle amounts up to +- $21,474,836.47
    balance_usd_cents int not null default 0,

    -- null means the account is active, otherwise indicates UTC date and time
    -- closed; the "(6)" gives us approx. the same resolution as the Python
    -- datetime type
    closed_at_utc timestamp(6)
    );
