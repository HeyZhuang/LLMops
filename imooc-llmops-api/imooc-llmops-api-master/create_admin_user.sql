-- 默认管理员账号
-- 用户名: admin
-- 邮箱: admin@llmops.local
-- 密码: admin123
-- 创建时间: 2025-12-05 11:17:49


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
    'admin',
    'admin@llmops.local',
    '',
    '04106dfd3107465e00bc1248c23d4c53b34d7afdd51639cf73b7bfc1f33d4fd5',
    '3574704ed2093658762f54842b50e90d',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
