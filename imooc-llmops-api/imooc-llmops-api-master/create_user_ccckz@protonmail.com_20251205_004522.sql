-- 创建用户: ccckz@protonmail.com (ccckz@protonmail.com)
-- 创建时间: 2025-12-05 00:45:22
-- 密码哈希: db9dca7d981c50663f5032d708dd9b6521d5514357984bb97b1d94cdebcc5ffa
-- 盐值: 523a8dff29f715522530ed145e70eda6


-- 创建用户账号
INSERT INTO account (
    name, 
    email, 
    avatar, 
    password, 
    password_salt,
    last_login_at,
    last_login_ip,
    updated_at,
    created_at
) VALUES (
    'ccckz@protonmail.com',
    'ccckz@protonmail.com',
    '',
    'db9dca7d981c50663f5032d708dd9b6521d5514357984bb97b1d94cdebcc5ffa',
    '523a8dff29f715522530ed145e70eda6',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
