"""Column names used across the project."""

########## RAW DATA COLUMN NAMES ##########

# dim_blocks
MALL_ID = "mall_id"
BLOCK_ID = "block_id"
BLOCK_TYPE = "block_type"
STORE_CODE = "store_code"
STORE_NAME = "store_name"
RETAILER_CODE = "retailer_code"
CAT_HIGH = "bl1_label"
CAT_MID = "bl2_label"
CAT_LOW = "bl3_label"
GLA = "gla"
GLA_CAT = "gla_category"

DIM_BLOCKS_COLUMNS = [
    MALL_ID,
    BLOCK_ID,
    BLOCK_TYPE,
    STORE_CODE,
    STORE_NAME,
    RETAILER_CODE,
    CAT_HIGH,
    CAT_MID,
    CAT_LOW,
    GLA,
    GLA_CAT,
]

# dim_malls
ID = "id"
COUNTRY = "country"
MALL_NAME = "mall_name"
OPENING_HOUR = "opening_hour"
CLOSING_HOUR = "closing_hour"

DIM_MALLS_COLUMNS = [
    ID,
    COUNTRY,
    MALL_NAME,
    OPENING_HOUR,
    CLOSING_HOUR,
]

# fact_stores
DATE = "date"
BLOCK_ID = "block_id"
RETAILER_ID = "retailer_id"
PEOPLE_IN = "people_in"
PEOPLE_WINDOW_FLOW = "people_window_flow"
STORE_AVG_DWELL_TIME = "store_average_dwell_time"
STORE_MED_DWELL_TIME = "store_median_dwell_time"
SHOPPING_AVG_DWELL_TIME = "shopping_average_dwell_time"
AVG_VISITED_STORES = "average_visited_stores"

FACT_STORES_COLUMNS = [
    DATE,
    MALL_ID,
    BLOCK_ID,
    STORE_CODE,
    RETAILER_ID,
    PEOPLE_IN,
    PEOPLE_WINDOW_FLOW,
    STORE_AVG_DWELL_TIME,
    STORE_MED_DWELL_TIME,
    SHOPPING_AVG_DWELL_TIME,
    AVG_VISITED_STORES,
]

# fact_malls
AVG_DWELL_TIME = "average_dwell_time"
DWELL_TIME_SAMPLE = "dwell_time_sample"
MED_DWELL_TIME = "median_dwell_time"

FACT_MALLS_COLUMNS = [
    DATE,
    MALL_ID,
    PEOPLE_IN,
    AVG_DWELL_TIME,
    DWELL_TIME_SAMPLE,
    MED_DWELL_TIME,
]

# fact_sri_scores
SRI_SCORE = "sri_score"

FACT_SRI_SCORES_COLUMNS = [
    STORE_CODE,
    SRI_SCORE,
]

# store_financials
CODSTR = "codstr"
CUR_CODE = "cur_code"
SALES_R12M = "sales_r12m"
TOTAL_COSTS_R12M = "total_costs_r12m"

STORE_FINANCIALS_COLUMNS = [
    CODSTR,
    CUR_CODE,
    SALES_R12M,
    TOTAL_COSTS_R12M,
]

# cross_visits
STORE_CODE_1 = "store_code_1"
STORE_CODE_2 = "store_code_2"
TOTAL_CROSS_VISITS = "total_cross_visits"

CROSS_VISITS_COLUMNS = [
    STORE_CODE_1,
    STORE_CODE_2,
    TOTAL_CROSS_VISITS,
]


########## INTERMEDIATE DATA COLUMN NAMES ##########


########## ENRICHED DATA COLUMN NAMES ##########

# category_affinities
CATEGORY_A = "cat_A"
CATEGORY_B = "cat_B"
AFFINITY = "avg_jaccard_strength"
NB_PAIRS = "nb_pairs"


########## MODEL FEATURES COLUMN NAMES ##########
MODEL_STORE_GLA = "gla"
MODEL_STORE_GLA_CAT = "gla_category"
MODEL_STORE_CATEGORY = "store_category"
MODEL_STORE_AVG_WINDOW_FLOW = "avg_window_flow"
MODEL_STORE_MEDIAN_WINDOW_FLOW = "median_window_flow"
MODEL_STORE_TOTAL_PEOPLE_IN = "total_people_in"
MODEL_STORE_TOTAL_WINDOW_FLOW = "total_window_flow"
MODEL_STORE_DAYS_RECORDED = "days_recorded"
MODEL_STORE_AVG_DWELL_TIME = "avg_dwell_time"
MODEL_STORE_NEIGHBORHOOD_SYNERGY = "neighborhood_synergy"
MODEL_STORE_NB_NEIGHBORS = "nb_neighbors"
MODEL_MALL_TOTAL_GLA = "mall_total_gla"
MODEL_MALL_STORE_COUNT = "mall_store_count"
MODEL_MALL_CATEGORY_SHARE = "mall_category_share"

# Targets
TARGET_CAPTURE_RATE = "capture_rate"
TARGET_SALES_PER_SQM = "sales_per_sqm"
TARGET_DWELL_TIME = "dwell_time"
