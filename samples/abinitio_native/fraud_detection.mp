{20100101|XXGpvertex|1|0|1000|{|}@1|Read Transactions|400000|300000|11000|11000|in|0.0|@@@1808|0|}}
{20100101|XXGpvertex|2|0|1002|{|}@1|Read Customer Ref|400000|100000|11000|11000|in|0.0|@@@1808|0|}}
{20100101|XXGpvertex|3|0|1004|{|}@1|Reformat|460000|420000|550000|53000|118000|69000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20100101|XXGpvertex|4|0|1006|{|}@1|Sort by Account|663000|49000|0|0|0|Sort by Segment Name|Ab Initio Software|Built-in 1.0:|1|100|0|6|32769|1|{1|}}
{20100101|XXGpvertex|5|0|1008|{|}@1|Rollup Summary|874000|39000|0|0|0|Rollup Summary Counts by Segment|Ab Initio Software|Built-in 2.0:|1|100|0|}}
{20100101|XXGpvertex|6|0|1010|{|}@1|Merge by Index|930000|270000|161000|271000|50000|41000|0|Merge by Index|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20100101|XXGpvertex|7|0|1012|{|}@1|Partition by Round-robin|304000|269000|124000|213000|50000|41000|0|Partition by Round-robin|Ab Initio Software|}}
{20100101|XXGpvertex|8|0|1014|{|}@1|Sort within Groups|1060000|230000|0|0|0|Sort within Groups|Ab Initio Software|Built-in 2.1.7:|1|100|0|}}
{20100101|XXGpvertex|9|0|1016|{|}@1|Filter High Risk|460000|420000|550000|53000|118000|69000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20100101|XXGpvertex|10|0|1018|{|}@1|Write Fraud Report|400000|500000|11000|11000|out|0.0|@@@2448|0|}}
{20100101|XXGpvertex|11|0|1020|{|}@1|Write Clean Output|400000|600000|11000|11000|out|0.0|@@@2448|0|}}
{20100101|XXGoport|101|0|1050|{@|{@|0|0|out|0.0|@@@2448|0|}}
{20100101|XXGoport|102|0|1052|{@|{@|0|0|out|0.0|@@@2448|0|}}
{20100101|XXGoport|103|0|1054|{@|{@|0|0|reject|0.0|count|reject|0|1168|0|}}
{20100101|XXGoport|104|0|1056|{@|{@|0|0|count|reject|0|1168|0|}}
{20100101|XXGoport|105|0|1058|{@|{@|0|0|error|0.0|@@@1176|0|}}
{20100101|XXGoport|106|0|1060|{@|{@|0|0|log|0.0|@@@1176|0|}}
{20100101|XXGiport|201|0|2000|{@|{@|0|0|in|0.0|@@@1808|0|}}
{20100101|XXGiport|202|0|2002|{@|{@|0|0|in|0.0|@@@1808|0|}}
{201020304|XXGedge|1|3|0|2050|{@|}}
{201020304|XXGedge|2|3|0|2052|{@|}}
{201020304|XXGedge|3|4|0|2054|{@|}}
{201020304|XXGedge|4|5|0|2056|{@|}}
{201020304|XXGedge|5|6|0|2058|{@|}}
{201020304|XXGedge|3|9|0|2060|{@|}}
{201020304|XXGedge|6|7|0|2062|{@|}}
{201020304|XXGedge|7|8|0|2064|{@|}}
{201020304|XXGedge|8|10|0|2066|{@|}}
{201020304|XXGedge|9|10|0|2068|{@|}}
{201020304|XXGedge|9|11|0|2070|{@|}}
{10160000S|XXGgraph|100|0|2130|0|{
COPYRIGHT 2010-2019 AB INITIO
ALL RIGHTS RESERVED
{30001002|XXparameter|DP_DML__|~ab_home/lib/dp/dp-back-end/dml|3|3|RFKc||{0|}}
{30001002|XXparameter|DP_XFR__|~ab_home/lib/dp/dp-back-end/xfr|3|3|RFKc||{0|}}
{30001002|XXparameter|INPUT_RECORD_FORMAT||7|1|RFKs1||{0|}}
{30001002|XXparameter|FIELDS_TO_IGNORE||3|3|FKc||{0|}}
