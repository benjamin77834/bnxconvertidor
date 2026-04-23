{20190601|XXGpvertex|1|0|1000|{|}@1|Read Transactions Raw|400000|300000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|2|0|1002|{|}@1|Read Customer Master|400000|100000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|3|0|1004|{|}@1|Read Account Balances|400000|200000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|4|0|1006|{|}@1|Read Exchange Rates|400000|250000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|5|0|1008|{|}@1|Read Branch Reference|400000|350000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|6|0|1010|{|}@1|Read Product Catalog|400000|450000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|7|0|1012|{|}@1|Read Blacklist|400000|550000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|8|0|1014|{|}@1|Read Historical Fraud|400000|650000|11000|11000|in|0.0|@@@1808|0|}}
{20190601|XXGpvertex|10|0|1020|{|}@1|Reformat Clean Transactions|460000|420000|550000|53000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20190601|XXGpvertex|11|0|1022|{|}@1|Reformat Normalize Amounts|460000|420000|550000|53000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20190601|XXGpvertex|12|0|1024|{|}@1|Sort by Customer ID|663000|49000|0|0|0|Sort by Segment Name|Ab Initio Software|Built-in 1.0:|1|100|0|6|32769|1|{1|}}
{20190601|XXGpvertex|13|0|1026|{|}@1|Sort by Account Number|663000|49000|0|0|0|Sort by Segment Name|Ab Initio Software|Built-in 1.0:|1|100|0|6|32769|1|{1|}}
{20190601|XXGpvertex|14|0|1028|{|}@1|Sort by Transaction Date|663000|49000|0|0|0|Sort by Segment Name|Ab Initio Software|Built-in 1.0:|1|100|0|6|32769|1|{1|}}
{20190601|XXGpvertex|15|0|1030|{|}@1|Dedup Remove Duplicates|663000|49000|0|0|0|Remove Duplicates|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|20|0|1040|{|}@1|Merge Customer Data|930000|270000|161000|271000|50000|41000|0|Merge by Index|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|21|0|1042|{|}@1|Join Account Balances|930000|270000|161000|271000|50000|41000|0|Merge by Index|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|22|0|1044|{|}@1|Lookup Exchange Rate|930000|270000|161000|271000|50000|41000|0|Lookup|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|23|0|1046|{|}@1|Lookup Branch Info|930000|270000|161000|271000|50000|41000|0|Lookup|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|24|0|1048|{|}@1|Lookup Product Details|930000|270000|161000|271000|50000|41000|0|Lookup|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|25|0|1050|{|}@1|Join Blacklist Check|930000|270000|161000|271000|50000|41000|0|Merge by Index|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|26|0|1052|{|}@1|Join Historical Patterns|930000|270000|161000|271000|50000|41000|0|Merge by Index|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|30|0|1060|{|}@1|Reformat Calculate Risk Score|460000|420000|550000|53000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20190601|XXGpvertex|31|0|1062|{|}@1|Reformat Currency Conversion|460000|420000|550000|53000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20190601|XXGpvertex|32|0|1064|{|}@1|Reformat Enrich Metadata|460000|420000|550000|53000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20190601|XXGpvertex|33|0|1066|{|}@1|Reformat Compute Velocity|460000|420000|550000|53000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20190601|XXGpvertex|34|0|1068|{|}@1|Reformat Flag Anomalies|460000|420000|550000|53000|0|Reformat|Ab Initio Software|Built-in 1.0:|1|100|0|6|}}
{20190601|XXGpvertex|40|0|1080|{|}@1|Filter High Risk Transactions|460000|420000|550000|53000|0|Filter|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|41|0|1082|{|}@1|Filter Blacklisted Accounts|460000|420000|550000|53000|0|Filter|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|42|0|1084|{|}@1|Filter International Transfers|460000|420000|550000|53000|0|Filter|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|50|0|1100|{|}@1|Rollup Daily Totals by Customer|874000|39000|0|0|0|Rollup Summary Counts by Segment|Ab Initio Software|Built-in 2.0:|1|100|0|}}
{20190601|XXGpvertex|51|0|1102|{|}@1|Rollup Monthly Totals by Branch|874000|39000|0|0|0|Rollup Summary Counts by Segment|Ab Initio Software|Built-in 2.0:|1|100|0|}}
{20190601|XXGpvertex|52|0|1104|{|}@1|Rollup Risk Summary by Region|874000|39000|0|0|0|Rollup Summary Counts by Segment|Ab Initio Software|Built-in 2.0:|1|100|0|}}
{20190601|XXGpvertex|53|0|1106|{|}@1|Rollup Fraud Counts by Type|874000|39000|0|0|0|Rollup Summary Counts by Segment|Ab Initio Software|Built-in 2.0:|1|100|0|}}
{20190601|XXGpvertex|60|0|1120|{|}@1|Partition by Region|304000|269000|124000|213000|50000|41000|0|Partition by Round-robin|Ab Initio Software|}}
{20190601|XXGpvertex|61|0|1122|{|}@1|Partition by Risk Level|304000|269000|124000|213000|50000|41000|0|Partition by Round-robin|Ab Initio Software|}}
{20190601|XXGpvertex|62|0|1124|{|}@1|Sort within Groups Final|1060000|230000|0|0|0|Sort within Groups|Ab Initio Software|Built-in 2.1.7:|1|100|0|}}
{20190601|XXGpvertex|63|0|1126|{|}@1|Concatenate Alert Streams|1060000|230000|0|0|0|Concatenate|Ab Initio Software|Built-in 1.0:|1|100|0|}}
{20190601|XXGpvertex|70|0|1140|{|}@1|Write Fraud Alerts|400000|500000|11000|11000|out|0.0|@@@2448|0|}}
{20190601|XXGpvertex|71|0|1142|{|}@1|Write Risk Report|400000|600000|11000|11000|out|0.0|@@@2448|0|}}
{20190601|XXGpvertex|72|0|1144|{|}@1|Write Clean Transactions|400000|700000|11000|11000|out|0.0|@@@2448|0|}}
{20190601|XXGpvertex|73|0|1146|{|}@1|Write Daily Summary|400000|800000|11000|11000|out|0.0|@@@2448|0|}}
{20190601|XXGpvertex|74|0|1148|{|}@1|Write Monthly Report|400000|900000|11000|11000|out|0.0|@@@2448|0|}}
{20190601|XXGpvertex|75|0|1150|{|}@1|Write Blacklist Matches|400000|950000|11000|11000|out|0.0|@@@2448|0|}}
{20190601|XXGpvertex|76|0|1152|{|}@1|Write Audit Log|400000|1000000|11000|11000|out|0.0|@@@2448|0|}}
{20190601|XXGpvertex|77|0|1154|{|}@1|Write Error Records|400000|1050000|11000|11000|out|0.0|@@@2448|0|}}
{201020304|XXGedge|1|10|0|3000|{@|}}
{201020304|XXGedge|10|11|0|3002|{@|}}
{201020304|XXGedge|11|12|0|3004|{@|}}
{201020304|XXGedge|12|14|0|3006|{@|}}
{201020304|XXGedge|14|15|0|3008|{@|}}
{201020304|XXGedge|15|20|0|3010|{@|}}
{201020304|XXGedge|2|20|0|3012|{@|}}
{201020304|XXGedge|20|21|0|3014|{@|}}
{201020304|XXGedge|3|21|0|3016|{@|}}
{201020304|XXGedge|21|22|0|3018|{@|}}
{201020304|XXGedge|4|22|0|3020|{@|}}
{201020304|XXGedge|22|23|0|3022|{@|}}
{201020304|XXGedge|5|23|0|3024|{@|}}
{201020304|XXGedge|23|24|0|3026|{@|}}
{201020304|XXGedge|6|24|0|3028|{@|}}
{201020304|XXGedge|24|25|0|3030|{@|}}
{201020304|XXGedge|7|25|0|3032|{@|}}
{201020304|XXGedge|25|26|0|3034|{@|}}
{201020304|XXGedge|8|26|0|3036|{@|}}
{201020304|XXGedge|26|30|0|3038|{@|}}
{201020304|XXGedge|30|31|0|3040|{@|}}
{201020304|XXGedge|31|32|0|3042|{@|}}
{201020304|XXGedge|32|33|0|3044|{@|}}
{201020304|XXGedge|33|34|0|3046|{@|}}
{201020304|XXGedge|34|40|0|3048|{@|}}
{201020304|XXGedge|34|41|0|3050|{@|}}
{201020304|XXGedge|34|42|0|3052|{@|}}
{201020304|XXGedge|40|50|0|3054|{@|}}
{201020304|XXGedge|40|53|0|3056|{@|}}
{201020304|XXGedge|41|63|0|3058|{@|}}
{201020304|XXGedge|42|63|0|3060|{@|}}
{201020304|XXGedge|50|60|0|3062|{@|}}
{201020304|XXGedge|51|60|0|3064|{@|}}
{201020304|XXGedge|60|62|0|3066|{@|}}
{201020304|XXGedge|62|70|0|3068|{@|}}
{201020304|XXGedge|52|61|0|3070|{@|}}
{201020304|XXGedge|53|61|0|3072|{@|}}
{201020304|XXGedge|61|71|0|3074|{@|}}
{201020304|XXGedge|34|72|0|3076|{@|}}
{201020304|XXGedge|50|73|0|3078|{@|}}
{201020304|XXGedge|51|74|0|3080|{@|}}
{201020304|XXGedge|63|75|0|3082|{@|}}
{201020304|XXGedge|26|76|0|3084|{@|}}
{201020304|XXGedge|15|77|0|3086|{@|}}
{201020304|XXGedge|11|13|0|3088|{@|}}
{201020304|XXGedge|13|51|0|3090|{@|}}
{201020304|XXGedge|13|52|0|3092|{@|}}
{10160000S|XXGgraph|100|0|5000|0|{
COPYRIGHT 2010-2019 AB INITIO SOFTWARE LLC
ALL RIGHTS RESERVED
USE AND DISCLOSURE IS RESTRICTED BY CONFIDENTIALITY & LICENSE CONDITIONS
{30001002|XXparameter|DP_DML__|~ab_home/lib/dp/dp-back-end/dml|3|3|RFKc||{0|}}
{30001002|XXparameter|DP_XFR__|~ab_home/lib/dp/dp-back-end/xfr|3|3|RFKc||{0|}}
{30001002|XXparameter|INPUT_RECORD_FORMAT||7|1|RFKs1||{0|}}
{30001002|XXparameter|DB_CONNECTION|jdbc:oracle:thin:@//dbhost:1521/BANKDB|3|3|RFKc||{0|}}
{30001002|XXparameter|S3_OUTPUT_PATH|s3://datalake/fraud-detection/output|3|3|RFKc||{0|}}
{30001002|XXparameter|KAFKA_BROKERS|kafka-prod:9092|3|3|RFKc||{0|}}
{30001002|XXparameter|MAX_RISK_THRESHOLD|0.85|3|3|RFKc||{0|}}
{30001002|XXparameter|BATCH_DATE|2019-06-01|3|3|RFKc||{0|}}
