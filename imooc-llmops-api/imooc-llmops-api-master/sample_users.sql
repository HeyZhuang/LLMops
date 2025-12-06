-- LLMOps 示例用户账号
-- 创建时间: 2025-12-05
-- 注意: 这些是示例账号，密码已经过哈希处理

-- 1. 管理员账号
-- 用户名: admin
-- 邮箱: admin@llmops.local  
-- 密码: admin123
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
    'chenkaizhuang',
    '13363581668@163.com',
    '',
    'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3',
    'salt123',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 2. 测试用户1
-- 用户名: testuser
-- 邮箱: test@llmops.local
-- 密码: test123
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
    'ccckz',
    'ccckz@protonmail.com',
    '',
    'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f',
    'salt456',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 3. 开发者账号
-- 用户名: developer
-- 邮箱: dev@llmops.local
-- 密码: dev123
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
    'hhhcl',
    '384914780@qq.com',
    '',
    '2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b',
    'salt789',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 查询创建的用户
SELECT id, name, email, created_at FROM account ORDER BY created_at DESC;
