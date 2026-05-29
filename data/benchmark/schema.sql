-- CQ-125 benchmark schema (PostgreSQL + PostGIS, structure only)
-- 11 tables actually referenced by golden_sql in CQ_125_questions.json.
-- No row data is included; reviewers do not need a populated database
-- to verify any number in the paper (all reductions are over JSONL).
-- Released for completeness so reviewers can independently inspect
-- column types, SRIDs, and primary keys referenced in gold SQL.

CREATE TABLE public.cq_osm_roads_2021 (
    "osm_id" text,
    "code" integer,
    "fclass" text,
    "name" text,
    "ref" text,
    "oneway" text,
    "maxspeed" integer,
    "layer" bigint,
    "bridge" text,
    "tunnel" text,
    "geometry" geometry(GEOMETRY, 4326)
);

-- approx rows: 50,366

CREATE TABLE public.cq_amap_poi_2024 (
    "ID" bigint,
    "名称" text,
    "地址" text,
    "电话" text,
    "类型" text,
    "区域ID" double precision,
    "经度wgs84" double precision,
    "纬度wgs84" double precision,
    "百度经度" double precision,
    "百度纬度" double precision,
    "更新时间" text,
    "geometry" geometry(POINT, 4326)
);

-- approx rows: 1,194,438

CREATE TABLE public.cq_buildings_2021 (
    "Id" integer,
    "Floor" integer,
    "geometry" geometry(GEOMETRY, 4326)
);

-- approx rows: 107,035

CREATE TABLE public.cq_land_use_dltb (
    "BSM" double precision,
    "YSDM" text,
    "DLBM" text,
    "DLMC" text,
    "QSDWDM" text,
    "QSDWMC" text,
    "ZLDWDM" text,
    "ZLDWMC" text,
    "TBMJ" double precision,
    "SHAPE_Length" double precision,
    "SHAPE_Area" double precision,
    "geometry" geometry(MULTIPOLYGON, 4326)
);

-- approx rows: 100,000

CREATE TABLE public.cq_historic_districts (
    "objectid_1" integer,
    "objectid" integer,
    "jqmc" varchar(50),
    "fwlx" varchar(50),
    "fwmc" varchar(50),
    "xzqmc" varchar(50),
    "fwkzyq" varchar(254),
    "fwmj" varchar(50),
    "bhbkydwwsl" integer,
    "bhbkydwwzj" numeric,
    "bhlsjzsl" integer,
    "bhlsjzmc" varchar(50),
    "bhlsjzzjzm" numeric,
    "bhlshjyssl" integer,
    "bhlshjysmc" varchar(50),
    "bhlsjxsl" integer,
    "bhlsjxzcd" integer,
    "bhlsjxmcjc" varchar(50),
    "bhfwzwhycm" integer,
    "bhqtfwzycs" integer,
    "bhqtfwzycm" varchar(50),
    "bz" varchar(254),
    "jj" varchar(254),
    "bsm" integer,
    "bhctfmjzsl" integer,
    "bhbkydwwmc" varchar(254),
    "bhctfmjzzj" numeric,
    "bhgsmmsl" integer,
    "bhgsmmmc" varchar(254),
    "bhfwzwhy_1" varchar(254),
    "tymj" numeric,
    "tycd" numeric,
    "shape_leng" numeric,
    "shape" geometry(GEOMETRY, 4490)
);

-- PRIMARY KEY (objectid_1)
-- approx rows: 20

CREATE TABLE public.cq_dltb (
    "objectid" integer,
    "bsm" numeric,
    "ysdm" varchar(20),
    "dlbm" varchar(20),
    "dlmc" varchar(50),
    "qsdwdm" varchar(20),
    "qsdwmc" varchar(100),
    "zldwdm" varchar(20),
    "zldwmc" varchar(100),
    "tbmj" numeric,
    "shape" geometry(GEOMETRY, 4610)
);

-- PRIMARY KEY (objectid)
-- approx rows: 101,657

CREATE TABLE public.cq_baidu_aoi_2024 (
    "objectid" integer,
    "uid" varchar(65536),
    "名称" varchar(65536),
    "地址" varchar(65536),
    "省份" numeric,
    "城市" varchar(65536),
    "区县" varchar(65536),
    "街镇乡" varchar(65536),
    "类型" varchar(65536),
    "第一分类" varchar(65536),
    "第二分类" varchar(65536),
    "评分" numeric,
    "更新时间" varchar(65536),
    "评论数" numeric,
    "开业时间" varchar(65536),
    "人均价格_元" numeric,
    "街道id" varchar(65536),
    "电话" varchar(65536),
    "创建时间" varchar(65536),
    "其他" varchar(65536),
    "高德分类" varchar(65536),
    "经度wgs84" numeric,
    "纬度wgs84" numeric,
    "shape" geometry(GEOMETRY, 4490)
);

-- PRIMARY KEY (objectid)
-- approx rows: 26,292

CREATE TABLE public.cq_district_population (
    "objectid" integer,
    "行政区划代码" integer,
    "区划名称" varchar(255),
    "数据来源" varchar(255),
    "年份" integer,
    "户籍总户数_万户_" numeric,
    "户籍总人口_万人_" numeric,
    "户籍城镇总人口_万人_" numeric,
    "户籍乡村总人口_万人_" numeric,
    "常住人口" numeric,
    "常住城镇人口" numeric,
    "城镇化率" numeric
);

-- PRIMARY KEY (objectid)
-- approx rows: -1

CREATE TABLE public.cq_baidu_search_index_2023 (
    "objectid" integer,
    "id" numeric,
    "odjsmc" varchar(255),
    "ddjsmc" varchar(255),
    "pcsscs" numeric,
    "ydsscs" numeric,
    "sszs" numeric,
    "shape" geometry(GEOMETRY, 4490)
);

-- PRIMARY KEY (objectid)
-- approx rows: 325

CREATE TABLE public.cq_unicom_commuting_2023 (
    "objectid" integer,
    "居住格网" integer,
    "工作格网" integer,
    "职住格网是否重合" integer,
    "性别" integer,
    "年龄" integer,
    "扩样前人口" integer,
    "扩样后人口" numeric
);

-- PRIMARY KEY (objectid)
-- approx rows: 2,120

CREATE TABLE public.cq_osm_roads (
    "objectid" integer,
    "osm_id" varchar(10),
    "code" smallint,
    "fclass" varchar(28),
    "name" varchar(100),
    "ref" varchar(20),
    "oneway" varchar(1),
    "maxspeed" smallint,
    "layer" numeric,
    "bridge" varchar(1),
    "tunnel" varchar(1),
    "shape" geometry(GEOMETRY, 4326)
);

-- PRIMARY KEY (objectid)
-- approx rows: 46,744
