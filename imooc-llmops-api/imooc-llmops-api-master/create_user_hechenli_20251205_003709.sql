-- 创建用户: hechenli (13935921582@163.com)
-- 创建时间: 2025-12-05 00:37:09
-- 密码哈希: 707d3db2fa83d630385e6cdb68cb34774b30c9b56fce0bfedb1332f65951967f
-- 盐值: 5d967fd77dfc0b8f3774b06dcbfff02a


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
    'hechenli',
    '13935921582@163.com',
    '',
    '707d3db2fa83d630385e6cdb68cb34774b30c9b56fce0bfedb1332f65951967f',
    '5d967fd77dfc0b8f3774b06dcbfff02a',
    CURRENT_TIMESTAMP,
    '127.0.0.1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
