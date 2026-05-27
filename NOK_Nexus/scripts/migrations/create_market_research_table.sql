-- 市场调研表
CREATE TABLE market_researches (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 调研信息
    city VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(200) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,

    -- 时间戳（自动填充）
    research_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- 备注
    remark TEXT,

    -- 状态
    status SMALLINT DEFAULT 1,

    -- 审计字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id),
    updated_by BIGINT REFERENCES users(id)
);

-- 索引
CREATE INDEX idx_research_user ON market_researches(user_id);
CREATE INDEX idx_research_city ON market_researches(city);
CREATE INDEX idx_research_manufacturer ON market_researches(manufacturer);
CREATE INDEX idx_research_date ON market_researches(research_date);
CREATE INDEX idx_research_created_at ON market_researches(created_at);

-- 注释
COMMENT ON TABLE market_researches IS '市场调研表';
COMMENT ON COLUMN market_researches.id IS '主键 ID';
COMMENT ON COLUMN market_researches.user_id IS '创建人 ID';
COMMENT ON COLUMN market_researches.city IS '调研城市';
COMMENT ON COLUMN market_researches.manufacturer IS '厂商名称';
COMMENT ON COLUMN market_researches.product_name IS '商品名称';
COMMENT ON COLUMN market_researches.price IS '调研价格';
COMMENT ON COLUMN market_researches.research_date IS '调研日期';
COMMENT ON COLUMN market_researches.remark IS '备注信息';
COMMENT ON COLUMN market_researches.status IS '状态 0-删除 1-正常';
COMMENT ON COLUMN market_researches.created_at IS '创建时间';
COMMENT ON COLUMN market_researches.updated_at IS '更新时间';
COMMENT ON COLUMN market_researches.created_by IS '创建人';
COMMENT ON COLUMN market_researches.updated_by IS '更新人';
