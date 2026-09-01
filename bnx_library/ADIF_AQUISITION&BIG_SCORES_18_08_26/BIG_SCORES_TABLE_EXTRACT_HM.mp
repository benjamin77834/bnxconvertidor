@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|9|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|368|rel_count|678|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_semantic_schema|9|1|1|Hnl|@{0|}}
{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
{30001002|XXparameter|!ab_compatibility|4.1.6.2|3|9|P|@{0|}}
{30001002|XXparameter|FILE_DATE|$(date +%Y%m%d%H%M%S)|3|9|RFK||{0|}}
{30001002|XXparameter|DB|$(if [[ `hostname \| awk -F "." '\{print $1\}'` == "sd-6dd4-7ac3" ]];then echo "gcgaeapmxcgnd_managed";  elif [[ `hostname \| awk -F "." '\{print $1\}'` == "sd-2635-e20b" ]]; then echo "gcgaeapmxcgnu_managed"; elif [[ `hostname \| awk -F "." '\{print $1\}'` == "jrgcg-mdwla03p" ]]; then echo "gcgaeapmxcgnp_managed"; else echo "NONE"; fi)|3|9|RK||{0|}}
{30001002|XXparameter|HIVE_LAYOUT|$(if [ `hostname \| awk -F "." '\{print $1\}'` == "sd-6dd4-7ac3" ];
then
echo "sd-ssan-53va"
else
echo "$\{HIVE_EXEC_LAYOUT\}"
fi )|3|9|RK||{0|}}
{30001002|XXparameter|MODELS|$(if [ -f "$AI_SERIAL/adif_file_big_table_scores_conf_param.txt" ];
then
echo `cat $AI_SERIAL/adif_file_big_table_scores_conf_param.txt \| awk -F "\|" '\{print $2\}'`
else
echo '"227938","230979","231078","207274","222566","227756","184527","P2986"'
fi )|3|9|RFK||{0|}}
{30001002|XXparameter|MONTHS_NUM|$(if [ -f "$AI_SERIAL/adif_file_big_table_scores_conf_param.txt" ];
then
echo `cat $AI_SERIAL/adif_file_big_table_scores_conf_param.txt \| awk -F "\|" '\{print $1\}'`
else
echo '5'
fi )|3|9|RFK||{0|}}
{30001002|XXparameter|MONGO_CRITERIA|\{model_id: \{ $in: [$\{MODELS\}]\}\}|3|3|RFKc||{0|}}
{30001002|XXparameter|COLLECTION|BIG_COLLECTION_SCORES|3|9|RFK||{0|}}
{30001002|XXparameter|MONGO_DBCFILE|$EAP_DB/cognitive_services_mongo.dbc|3|9|RFK||{0|}}
{30001002|XXparameter|_UseNewErrorLogDML|True|13|1|Hl||{0|}}
}}@0|@0|0|0|0|0|0|0|BIG_SCORES_TABLE_EXTRACT|lc80582|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|1734000|694000|7|}}
{2010703001|XXGgraphinfo|2|0|3|0|{@{}@1|4.0.2.4|{4|1|1|1|1|}Job 'BIG_SCORES_TABLE_EXTRACT_HM' Execution Status Report


Job "BIG_SCORES_TABLE_EXTRACT_HM" Execution started at Monday, July 29, 2024 10:38:41
Job completed successfully at Monday, July 29, 2024 10:44:09

------------------------------
Job Statistics:

Job status at termination: Done
Run time (wall clock): 0:05:27
Run performed by user jv21157
Total data moved through all flows: 8867 records (10602066 bytes)
Total CPU time (all processes): 8 seconds
Average CPU utilization across all nodes: 0.00 percent
||||@@33207807|}}
{2010705002|XXGrunsettings|3|0|5|0|{@{}@Home abinitio||||1|60|0|1|1|0|0|0|0|1|1|0|0|1|2|1|1|0|0|0|@16|}}
{2010242002|XXGface|4|0|7|0|{@{}@Arial|0|100|0|}}
{2010210004|XXGflow|5|0|9|0|{@{}@0|.5|.5|{0|}5549|19|}}
{2010210004|XXGflow|6|0|11|0|{@{}@0|.5|.5|{0|}5623|17|}}
{2010210004|XXGflow|7|0|13|0|{@{}@0|.5|.5|{0|}5609|17|}}
{2010243001|XXGwatcher|8|0|15|0|{@{}@1|100|-1||0|}}
{2010210004|XXGflow|9|0|17|0|{@{}@0|.5|.5|{0|}5611|17|}}
{2010210004|XXGflow|10|0|19|0|{@{}@0|.5|.5|{0|}5608|17|}}
{2010210004|XXGflow|11|0|21|0|{@{}@0|.5|.5|{0|}5633|17|}}
{2010243001|XXGwatcher|12|0|23|0|{@{}@1|10000|0||2|}}
{2010210004|XXGflow|13|0|25|0|{@{}@0|.5|.5|{0|}5631|17|}}
{2010210004|XXGflow|14|0|27|0|{@{}@0|.5|.5|{0|}5628|17|}}
{2010243001|XXGwatcher|15|0|29|0|{@{}@1|10000|0||2|}}
{2010210004|XXGflow|16|0|31|0|{@{}@0|.5|.5|{0|}5558|17|}}
{2010210004|XXGflow|17|0|33|0|{@{}@0|.5|.5|{0|}5625|17|}}
{2010210004|XXGflow|18|0|35|0|{@{}@0|.5|.5|{0|}5627|17|}}
{2010243001|XXGwatcher|19|0|37|0|{@{}@1|10000|0||2|}}
{2010210004|XXGflow|20|0|39|0|{@{}@0|.5|.5|{0|}5629|17|}}
{2010210004|XXGflow|21|0|41|0|{@{}@0|.5|.5|{0|}5562|17|}}
{2010210004|XXGflow|22|0|43|0|{@{}@0|.5|.5|{0|}5610|17|}}
{2010210004|XXGflow|23|0|45|0|{@{}@0|.5|.5|{0|}5581|17|}}
{2010600005|XXGgraph|24|0|47|0|{Subgraph created from graph "BIG_SCORES_TABLE_EXTRACT_HM"|{}@0|@225500|474500|0|0|0|0|5507|Clean Table|lc80582|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|968000|449000|7|}}
{2010210004|XXGflow|25|0|49|0|{@{}@0|.5|.5|{0|}4815|17|}}
{2010210004|XXGflow|26|0|51|0|{@{}@0|.5|.5|{0|}4814|17|}}
{2010210004|XXGflow|27|0|53|0|{@{}@0|.5|.5|{0|}4816|17|}}
{2010210004|XXGflow|28|0|55|0|{@{}@0|.5|.5|{0|}4817|17|}}
{2010501005|XXGpvertex|29|0|57|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Validate/Create_Data.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|num_records|1|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|$AI_DML/adif_mongo_big_collection_scores.dml|3|2|f$|@{0|}}
{30001002|XXparameter|transform|out::create(index) = begin

  out.model_id :: "222566";
  out.* :: random_value();
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout|$AI_MFS|3|2|$|@{0|}}
}}@0|Create Data|40000|81000|0|0|0|0|4813|Create Data|Ab Initio Software|Built-in 2.15.2:|1|100|0||6||1|1|{1|0|}}}
{2010203004|XXGoport|30|0|59|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|31|0|62|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|32|0|64|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|33|0|66|0|{Creates records according to a transform.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|Create_Data|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|num_records||1|2|RFO$|Number of records to generate|{0|}}
{30001002|XXparameter|num_records.display_name|num-records|3|9|P|@{0|}}
{30001002|XXparameter|transform|out::create(index) = begin
  out :: random_value();
end;|8|1|FOl|DML function|{0|}}
{30001002|XXparameter|identical_records|False|13|1|FKl|Whether to evaluate the transform once only, or once for each record|{0|}}
{30001002|XXparameter|identical_records.display_name|identical-records|3|9|P|@{0|}}
{30001002|XXparameter|identical_records.keyword|identical-records|3|9|P|@{0|}}
{30001002|XXparameter|identical_records_display_values|Evaluatetransformanewforeachrecord Evaluatetransformonceandusethatvalueforallrecords|3|2|H$||{0|}}
{30001002|XXparameter|identical_records_display_values.display_name|identical-records-display-values|3|9|P|@{0|}}
{30001002|XXparameter|start_index|1|1|2|F$|Value to pass as index on first call to create()|{0|}}
{30001002|XXparameter|start_index.display_name|start-index|3|9|P|@{0|}}
{30001002|XXparameter|start_index.condition|version 3.3.4.r13.0:|3|15|P?|@{0|}}
{30001002|XXparameter|start_index_non_default|value start-index 1 False default constant True|13|13|Rv|Automatically set to True if start-index != 1|{0|}}
{30001002|XXparameter|start_index_non_default.display_name|start-index-non-default|3|9|P|@{0|}}
{30001002|XXparameter|start_index_impl|sameas start-index default dollar_substitution 1|1|13|Kv|Passed for use as index on first call to create() only if not defaulted|{0|}}
{30001002|XXparameter|start_index_impl.display_name|start-index-impl|3|9|P|@{0|}}
{30001002|XXparameter|start_index_impl.keyword|start-index-impl|3|9|P|@{0|}}
{30001002|XXparameter|start_index_impl.condition|param start-index-non-default True|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|1|1|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_checkpoint|0|15|1|RFKl|Frequency of checkpoint records to log|{2|0|1|}}
{30001002|XXparameter|log_checkpoint.condition|version 3.0.4.r17: param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_checkpoint.update_clauses|update_value 1|3|9|P|@{0|}}
{30001002|XXparameter|log_computepoint|0|15|1|RFKl|Frequency of computepoint records to log|{2|0|1|}}
{30001002|XXparameter|log_computepoint.condition|version 3.0.4.r17: param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_computepoint.update_clauses|update_value 1|3|9|P|@{0|}}
{30001002|XXparameter|continuous|False|13|1|RFOl|Whether to produce checkpoints or computepoints.|{0|}}
{30001002|XXparameter|checkpoint_interval|1|1|2|FO$|Number of records between checkpoints, or 0 to indicate that no checkpoints are to be generated.|{0|}}
{30001002|XXparameter|checkpoint_interval.display_name|checkpoint-interval|3|9|P|@{0|}}
{30001002|XXparameter|checkpoint_interval.condition|param continuous True|3|15|P?|@{0|}}
{30001002|XXparameter|computepoint_interval|0|1|2|FO$|Number of records between computepoints, or 0 to indicate that no computepoints are to be generated.|{0|}}
{30001002|XXparameter|computepoint_interval.display_name|computepoint-interval|3|9|P|@{0|}}
{30001002|XXparameter|computepoint_interval.condition|param continuous True|3|15|P?|@{0|}}
{30001002|XXparameter|do_timed_checkpoints|False|13|1|FKl|Generate checkpoints at timed intervals|{0|}}
{30001002|XXparameter|do_timed_checkpoints.display_name|do-timed-checkpoints|3|9|P|@{0|}}
{30001002|XXparameter|do_timed_checkpoints.keyword|do-timed-checkpoints|3|9|P|@{0|}}
{30001002|XXparameter|do_timed_checkpoints.condition|param continuous True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|5|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::create(long index)|3|2|H$|Function taking integer index counting 1,2,3,4... to produce records on the output.|{0|}}
{30001002|XXparameter|continuous_analysis|continuous ? subscriber :|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, unsigned integer(8) in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, unsigned integer(8) in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, unsigned integer(8) in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,error,log::document()|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
}}@0|Create Data|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|34|0|68|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|35|0|71|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|36|0|74|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|37|0|77|0|{ it component can be remove one or many models depending the configuration in $MONGO_CRITERIA pameter defined |{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Database/Mongo/Update_Mongo_DB.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|DBConfigFile|$MONGO_DBCFILE|3|2|f$|@{0|}}
{30001002|XXparameter|collection|$\{COLLECTION\}|3|3|c|@{0|}}
{30001002|XXparameter|Layout|$AI_MFS|3|2|$|@{0|}}
{30001002|XXparameter|update_method|remove|3|1|l|@{0|}}
{30001002|XXparameter|in_metadata|///////////////////////////////////////////////////////////////////////
// This file was automatically generated by Ab Initio 
// on Thu Jun  1 13:41:59 2023
//
// !! WARNING: ANY EDITS WILL BE LOST UPON REGENERATION OF THIS FILE !!
//
// The following settings were used to generate the DML.
//  criteria: \{ \}
//  projection: \{ \}
//  skip_id: true
//  all: true
//  max_docs: 100
//
///////////////////////////////////////////////////////////////////////
record
  utf8 string(int) customer_id = NULL;
  utf8 string(int) model_id = NULL;
  little endian integer(4) score_model_tp = NULL;
  utf8 string(int) last_updated_date = NULL;
  record
    utf8 string(int) customer_seg = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") customer_seg_dt = NULL;
  end[int] CUSTOMER_SEGMENTS = NULL;
  record
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") credit_approved_dt = NULL;
    little endian integer(1) credit_approved_flag = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) credit_score_decile_val = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) credit_score_quartile_val = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) score = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_info_dt = NULL;
    utf8 string(int) score_name = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_process_dt = NULL;
  end[int] RISK_SCORES = NULL;
end;|3|1|l|@{0|}}
{30001002|XXparameter|criteria|$MONGO_CRITERIA|3|2|$|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
}}@0|Update Mongo|271000|71000|0|0|0|0|4818|Remove Models|Ab Initio Software|Built-in 3.2.1.r10:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|38|0|79|0|{@{}@0|0|0|0|out|0.0|@@@2192|0|}}
{2010203004|XXGoport|39|0|82|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|40|0|85|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|41|0|87|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|42|0|90|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|43|0|93|0|{Modifies records in a Mongo database via inserts, updates, or removes|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|db-mongo-update|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/db_v2/bin/db-mongo-update|3|2|H$||{0|}}
{30001002|XXparameter|DBConfigFile||22|2|RFOf$|Database Description File|{0|}}
{30001002|XXparameter|transform||8|1|FKl|DML Package containing transforms and data types|{0|}}
{30001002|XXparameter|transform.condition|version 4.1.5.r25:|3|15|P?|@{0|}}
{30001002|XXparameter|collection||24|3|RFKc|Mongo collection name|{0|}}
{30001002|XXparameter|update_method|insert|15|1|RFKl|.insert() .update() or ,remove()|{3|insert|update|remove|}}
{30001002|XXparameter|show_query|value update_method update True value update_method remove True default constant False|13|13|v||{0|}}
{30001002|XXparameter|criteria||3|1|FKl|Selection criteria for update|{0|}}
{30001002|XXparameter|criteria.condition|param_exact show_query True|3|15|P?|@{0|}}
{30001002|XXparameter|update||3|1|FKl|Modifications to apply|{0|}}
{30001002|XXparameter|update.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|upsert|False|13|1|FKl|Upsert parameter|{0|}}
{30001002|XXparameter|upsert.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|multi|False|13|1|FKl|True will update all documents matched by the selection criteria; False will update only one|{0|}}
{30001002|XXparameter|multi.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|justOne|False|13|1|FKl|False will remove all documents matched by the selection criteria; True will remove only one|{0|}}
{30001002|XXparameter|justOne.condition|param_exact update_method remove|3|15|P?|@{0|}}
{30001002|XXparameter|batch_update|value update_method insert False value update_method remove False value multi False True default constant False|13|13|v||{0|}}
{30001002|XXparameter|batch_remove|value update_method insert False value update_method update False value justOne False True default constant False|13|13|v||{0|}}
{30001002|XXparameter|enable_batch|value update_method insert True value batch_update True True value batch_remove True True default constant False|13|13|v||{0|}}
{30001002|XXparameter|batch|0|1|2|RFK$|Number of records to submit in batch|{0|}}
{30001002|XXparameter|batch.condition|param_exact enable_batch True|3|15|P?|@{0|}}
{30001002|XXparameter|unordered|False|13|1|FKl|True will submit documents unordered to Mongo if batch is greater than 0|{0|}}
{30001002|XXparameter|unordered.condition|param_exact enable_batch True version 3.2.7.2:|3|15|P?|@{0|}}
{30001002|XXparameter|json_input|False|13|1|RFKl|Upload documents to Mongo using JSON strings|{0|}}
{30001002|XXparameter|json_input.condition|version 3.3.5.r16:|3|15|P?|@{0|}}
{30001002|XXparameter|json_field||3|2|RFK$|Name of the field in the input record containing the JSON document to be uploaded|{0|}}
{30001002|XXparameter|json_field.condition|param_exact json_input True version 3.3.5.r16:|3|15|P?|@{0|}}
{30001002|XXparameter|verify_dml|True|13|1|FKl|Validate the in port DML against an existing Mongo record|{0|}}
{30001002|XXparameter|verify_dml.condition|param_exact update_method insert param_exact json_input False|3|15|P?|@{0|}}
{30001002|XXparameter|insert_null|True|13|1|FKl|True will insert NULL fields and vectors as null elements; False will skip those elements in the document|{0|}}
{30001002|XXparameter|insert_null.condition|param_exact json_input False version 3.2.3.r18:|3|15|P?|@{0|}}
{30001002|XXparameter|nullable_subrecords|True|13|1|FKl|True will treat NULL subrecords as null fields; False will process nested fields within the NULL subrecord as if they are individually NULL|{0|}}
{30001002|XXparameter|nullable_subrecords.condition|param_exact json_input False version 4.1.1.r9:|3|15|P?|@{0|}}
{30001002|XXparameter|continuous|False|13|1|RFKl|Enable component for Continuous>Flows operation|{0|}}
{30001002|XXparameter|commitTable||24|3|FKc|Collection in which to store commit progress|{0|}}
{30001002|XXparameter|transaction_group||3|2|FK$|Name of the transaction group for participation in a shared transaction. Graph folding must be enabled.|{0|}}
{30001002|XXparameter|transaction_group.condition|version 4.0.0.r1:|3|15|P?|@{0|}}
{30001002|XXparameter|use_field_level_encryption|False|13|1|RFKl|Enable client-side field level encryption.|{0|}}
{30001002|XXparameter|use_field_level_encryption.condition|version 4.1.2.r12:|3|15|P?|@{0|}}
{30001002|XXparameter|schema_map||3|2|FK$|JSON schema map for specifying local automatic encryption rules.|{0|}}
{30001002|XXparameter|schema_map.condition|param_exact use_field_level_encryption True version 4.1.2.r12:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|use_leading_checkpoint|value commitTable '' False value commitTable * True default constant False|13|13|v||{0|}}
{30001002|XXparameter|leadchkpt|-__ab__leading-checkpoint__ab__|3|2|O$||{0|}}
{30001002|XXparameter|leadchkpt.condition|param continuous False param use_leading_checkpoint True|3|15|P?|@{0|}}
{30001002|XXparameter|gendml_param_names|collection projection|3|2|$||{0|}}
{30001002|XXparameter|_ab_gendmlports|in|3|2|$|Port supports automatic metadata generation|{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|num_operations|5|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|kms_credentials_t kms_credentials "record string(int) kms_providers; datetime('YYYY-MM-DDTHH24:MI:SS-zo:ne') expiration = NULL; end"|3|2|H$|Type of kms_credentials|{0|}}
{30001002|XXparameter|operation1|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation5|optional kms_credentials::retrieve_kms_credentials()|3|2|H$|Optional provision of KMS credentials for CS-FLE|{0|}}
{30001002|XXparameter|operation5_analysis|optional kms_credentials::retrieve_kms_credentials()|3|2|H$|Optional provision of KMS credentials for CS-FLE|{0|}}
{30001002|XXparameter|override_mpname|value continuous True db-mongo-update-continuous value continuous False db-mongo-update|3|13|v||{0|}}
{30001002|XXparameter|override_mpname.display_name|override-mpname|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in; out=in|3|2|H$||{0|}}
{30001002|XXparameter|eme_dataset_mapping|@40|9|F|Location in which to create a dataset corresponding to this component.|{0|}}
{30001002|XXparameter|dataset_analysis|eme_dataset_mapping(table)=in,w|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|continuous ? nobatch,publisher : not_enabled|3|2|H$||{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|RFf$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912808|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|@15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
}}@0|Update Mongo|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|44|0|95|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2192|0|}}
{2010203004|XXGoport|45|0|98|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|46|0|101|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|47|0|104|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|48|0|107|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|49|0|112|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Trash.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Trash|560000|70500|0|0|0|0|4734|Trash|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010202004|XXGiport|50|0|114|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|51|0|117|0|{Ends a flow by discarding all input data records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|continuous_analysis|broadcast, publisher, fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Trash|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010202004|XXGiport|52|0|119|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|53|0|124|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Trash.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Trash|210000|365500|0|0|0|0|4800|Trash-1|Ab Initio Software|Built-in 1.0:|1|100|0||6||34817|1|{1|0|}}}
{2010202004|XXGiport|54|0|126|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|55|0|129|0|{Ends a flow by discarding all input data records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|continuous_analysis|broadcast, publisher, fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Trash|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010202004|XXGiport|56|0|131|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|57|0|136|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Trash.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Trash|380000|280500|0|0|0|0|4798|Trash-2|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010202004|XXGiport|58|0|138|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|59|0|141|0|{Ends a flow by discarding all input data records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|continuous_analysis|broadcast, publisher, fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Trash|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010202004|XXGiport|60|0|143|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|61|0|148|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Dedup_Sorted.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|key|\{model_id\}|3|2|$|@{0|}}
{30001002|XXparameter|dup_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Dedup Sorted|749000|215000|0|0|0|0|5564|Dedup Sorted|Ab Initio Software|Built-in 2.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|62|0|150|0|{@{}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|63|0|153|0|{@{}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|64|0|155|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|65|0|157|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|66|0|159|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|67|0|161|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|68|0|164|0|{Separates one specified data record in each group of data records from the rest of the records in the group.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|dedup|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Key on which to remove duplicates|{0|}}
{30001002|XXparameter|select||20|2|FK$|Optional select expression|{0|}}
{30001002|XXparameter|keep|first|15|1|FKl|Output record for a group of duplicates|{3|first|last|unique-only|}}
{30001002|XXparameter|package||8|1|FKl|Package containing transforms and data types|{0|}}
{30001002|XXparameter|package.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 2.11.1:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|NoHidePorts|out|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in; out=in; dup=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select); dup=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation1|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_operations|4|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|dup_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,dup,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1639787120|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: dup = in
metadata type: in = out
metadata type: in = dup|3|1|FHKl|@{0|}}
}}@0|Dedup Sorted|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|69|0|166|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|70|0|169|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|71|0|172|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|72|0|175|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|73|0|178|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|74|0|181|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010503005|XXGfvertex|75|0|184|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/ING_BIG_SCORES_LKP_test.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/ING_BIG_SCORES_LKP_test.dat|3|2|$|@{0|}}
}}@1|Output File|930000|235000|0|0|0|0|5626|last model date|Ab Initio Software|@1|10000|0||6||33025|-1|-1|}}
{2010202004|XXGiport|76|0|186|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|77|0|189|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table).|{6|uninterpreted|seqfile|parquet|orc|avro|texttable|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4\}|{8|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|write_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1639787116|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Output File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|78|0|191|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|79|0|194|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|filereject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
}}@1|@445000|68000|0|0|0|0|4014|Read Blocks|||1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|80|0|196|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|81|0|198|0|{@{}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|82|0|200|0|{@{}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|83|0|202|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|84|0|204|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|85|0|206|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|86|0|208|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010210004|XXGflow|87|0|210|0|{@{}@384|.5|.5|{0|}4017|20|}}
{2010501005|XXGpvertex|88|0|212|0|{Walks the directory tree starting from paths specified on the input flow.  Produces a list of files to be read as well as the files' block and address info.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|in0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|@60000|50000|0|0|0|0|4020|Find Files and Read Blocks|Ab Initio Software|Built-in 2.14:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|89|0|214|0|{@{}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010210004|XXGflow|90|0|216|0|{@{}@384|.5|.5|{0|}4019|17|}}
{2010203004|XXGoport|91|0|218|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|92|0|220|0|{@{}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|93|0|222|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
}}@1|Run Program|115000|224000|0|0|0|0|4026|Generate Partition Data|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|94|0|224|0|{@{}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010210004|XXGflow|95|0|226|0|{@{}@384|.5|.5|{0|}4025|17|}}
{2010202004|XXGiport|96|0|228|0|{@{}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010503005|XXGfvertex|97|0|230|0|{|{}@1|@209000|123000|0|0|0|0|4013|Partition Data|Ab Initio Software|@1|100|-1||6||33025|-1|-1|}}
{2010203004|XXGoport|98|0|232|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010210004|XXGflow|99|0|234|0|{@{}@384|.5|.5|{0|}4014|17|}}
{2010501005|XXGpvertex|100|0|242|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Join.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|key|\{model_id; last_updated_date descending\}|3|2|$|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|l|@{0|}}
{30001002|XXparameter|transform|/*Join transform*/
out::join(in0,in1)=
begin
out.* :: in1.*;
end;|3|1|l|@{0|}}
{30001002|XXparameter|in0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|unused0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in1_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject1_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|unused1_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@2|Join|719000|375000|0|0|0|0|5583|Join|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|101|0|244|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|102|0|247|0|{@{}@0|0|0|0|unused0|0.0|count|unused|0|1168|0|}}
{2010203004|XXGoport|103|0|249|0|{@{}@0|0|0|0|unused1|0.0|count|unused|1|1168|0|}}
{2010203004|XXGoport|104|0|251|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|105|0|253|0|{@{}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|106|0|255|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|107|0|257|0|{@{}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|108|0|259|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|109|0|261|0|{@{}@0|0|0|0|in0|0.0|count|in|0|1808|0|}}
{2010202004|XXGiport|110|0|264|0|{@{}@0|0|0|0|in1|0.0|count|in|1|1808|0|}}
{2010501005|XXGpvertex|111|0|267|0|{Performs inner, outer, and semi-joins with multiple flows of data records. It maximizes performance by loading input data records into main memory.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|?join|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|2|1|1|Fl|Number of inputs to join function|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|sorted_input|True|13|1|Fl|Set this parameter to False if the input is not sorted. In this case, JOIN processes the data in-memory without sorting it.|{0|}}
{30001002|XXparameter|sorted_input.display_name|sorted-input|3|9|P|@{0|}}
{30001002|XXparameter|sorted_input.condition|version 2.1:|3|15|P?|@{0|}}
{30001002|XXparameter|_min_count|2|1|2|FH$|Minimum number of inputs to join|{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field(s) on which to join|{0|}}
{30001002|XXparameter|transform||8|1|RFOl|Required DML function|{0|}}
{30001002|XXparameter|join_type|Inner Join (matching records required on all inputs)|15|1|Fl|Handling for duplicate and missing key values|{3|Inner Join (matching records required on all inputs)|Full Outer Join (use null for missing records)|Explicit|}}
{30001002|XXparameter|join_type.display_name|join-type|3|9|P|@{0|}}
{30001002|XXparameter|show_interface|True|13|1|Hl|Whether to show the interface parameter|{0|}}
{30001002|XXparameter|show_interface.update_clauses|update_value True|3|9|P|@{0|}}
{30001002|XXparameter|parameter_interface|version-3-2-2|15|1|Fl|Controls whether to use the legacy interface or the improved Co>Operating System Version 3.2.2 and later parameter interface.  Specifically, it controls whether to use the legacy record-required parameter with inverted booleans or the Version 3.2.2 record-match-required parameter with normal booleans. The choice of parameter-interface is compatible with all Co>Operating System versions except when count is greater than 5 in which case older Co>Operating Systems will fail with the version-3-2-2 interface.|{2|version-3-2-2|legacy|}}
{30001002|XXparameter|parameter_interface.display_name|parameter-interface|3|9|P|@{0|}}
{30001002|XXparameter|parameter_interface.condition|version 3.2: param show_interface True param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|parameter_interface.update_clauses|update_value legacy|3|9|P|@{0|}}
{30001002|XXparameter|parameter_interface_internal|value join-type Inner* legacy value join-type Full* legacy sameas parameter-interface default dollar_substitution version-3-2-2|3|13|v|Sets the value of the internal parameter interface|{0|}}
{30001002|XXparameter|parameter_interface_internal.display_name|parameter-interface-internal|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0|value join-type Inner* True value join-type Full* False default constant True|13|13|Fv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required0.display_name|record-match-required0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.index_name|record-match-required|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.condition|param parameter-interface-internal version-3-2-2 param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required1|value join-type Inner* True value join-type Full* False default constant True|13|13|Fv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required1.display_name|record-match-required1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.index_name|record-match-required|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.condition|param parameter-interface-internal version-3-2-2 param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|record_required0|value join-type Inner* False value join-type Full* True default constant False|13|13|Fv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required0.display_name|record-required0|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.index_name|record-required|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.condition|param parameter-interface-internal legacy param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|record_required1|value join-type Inner* False value join-type Full* True default constant False|13|13|Fv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required1.display_name|record-required1|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.index_name|record-required|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.condition|param parameter-interface-internal legacy param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|dedup0|False|13|1|Fl|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|dedup0.index_name|dedup|3|9|P|@{0|}}
{30001002|XXparameter|dedup1|False|13|1|Fl|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|dedup1.index_name|dedup|3|9|P|@{0|}}
{30001002|XXparameter|select0||20|2|F$|Filter expression before join function|{0|}}
{30001002|XXparameter|select0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|select0.index_name|select|3|9|P|@{0|}}
{30001002|XXparameter|select1||20|2|F$|Filter expression before join function|{0|}}
{30001002|XXparameter|select1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|select1.index_name|select|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0|value record-match-required F* True value record-match-required T* False value record-match-required f* True value record-match-required t* False value record-match-required 0 True value record-match-required 1 False default constant True|13|13|v|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not0.display_name|record-match-required-not0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.index_name|record-match-required-not|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.condition|param parameter-interface-internal version-3-2-2 version 3.2.1.r10:|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not1|value record-match-required F* True value record-match-required T* False value record-match-required f* True value record-match-required t* False value record-match-required 0 True value record-match-required 1 False default constant True|13|13|v|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not1.display_name|record-match-required-not1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.index_name|record-match-required-not|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.condition|param parameter-interface-internal version-3-2-2 version 3.2.1.r10:|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll0|value record-match-required0 F* True value record-match-required0 T* False value record-match-required0 f* True value record-match-required0 t* False value record-match-required0 0 True value record-match-required0 1 False default constant True|13|13|v|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not_unroll0.display_name|record-match-required-not-unroll0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll0.condition|param parameter-interface-internal version-3-2-2 version :3.2.1.r9|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll1|value record-match-required1 F* True value record-match-required1 T* False value record-match-required1 f* True value record-match-required1 t* False value record-match-required1 0 True value record-match-required1 1 False default constant True|13|13|v|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not_unroll1.display_name|record-match-required-not-unroll1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll1.condition|param parameter-interface-internal version-3-2-2 version :3.2.1.r9|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll2|value record-match-required2 F* True value record-match-required2 T* False value record-match-required2 f* True value record-match-required2 t* False value record-match-required2 0 True value record-match-required2 1 False default constant True|13|13|v|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not_unroll2.display_name|record-match-required-not-unroll2|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll2.condition|param parameter-interface-internal version-3-2-2 version :3.2.1.r9|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll3|value record-match-required3 F* True value record-match-required3 T* False value record-match-required3 f* True value record-match-required3 t* False value record-match-required3 0 True value record-match-required3 1 False default constant True|13|13|v|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not_unroll3.display_name|record-match-required-not-unroll3|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll3.condition|param parameter-interface-internal version-3-2-2 version :3.2.1.r9|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll4|value record-match-required4 F* True value record-match-required4 T* False value record-match-required4 f* True value record-match-required4 t* False value record-match-required4 0 True value record-match-required4 1 False default constant True|13|13|v|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not_unroll4.display_name|record-match-required-not-unroll4|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not_unroll4.condition|param parameter-interface-internal version-3-2-2 version :3.2.1.r9|3|15|P?|@{0|}}
{30001002|XXparameter|join_mpc_interface_3_2_supports_maximum_count_of_5_in_older_cooperating_systems|value record-match-required5 * True default constant False|13|13|Kv|Interface protection parameter|{0|}}
{30001002|XXparameter|join_mpc_interface_3_2_supports_maximum_count_of_5_in_older_cooperating_systems.display_name|join-mpc-interface-3-2-supports-maximum-count-of-5-in-older-cooperating-systems|3|9|P|@{0|}}
{30001002|XXparameter|join_mpc_interface_3_2_supports_maximum_count_of_5_in_older_cooperating_systems.keyword|join-mpc-interface-3-2-supports-maximum-count-of-5-in-older-cooperating-systems|3|9|P|@{0|}}
{30001002|XXparameter|join_mpc_interface_3_2_supports_maximum_count_of_5_in_older_cooperating_systems.condition|version :3.2.1.r9 param parameter-interface-internal version-3-2-2 param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0|value join-type Inner* False value join-type Full* False value record-match-required __AB_NoSuchValue True default constant False|13|13|Kv||{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.index_name|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.condition|param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1|value join-type Inner* False value join-type Full* False value record-match-required __AB_NoSuchValue True default constant False|13|13|Kv||{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.index_name|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.condition|param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|record_required_display_values|True(recordrequiredonthisinput) False(usenullformissingrecord)|3|2|H$||{0|}}
{30001002|XXparameter|record_required_display_values.display_name|record-required-display-values|3|9|P|@{0|}}
{30001002|XXparameter|dedup_display_values|Donotdedupthisinput Dedupthisinputbeforejoining|3|2|H$||{0|}}
{30001002|XXparameter|dedup_display_values.display_name|dedup-display-values|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_display_values|False(usenullformissingrecord) True(recordrequiredonthisinput)|3|2|H$||{0|}}
{30001002|XXparameter|record_match_required_display_values.display_name|record-match-required-display-values|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0|sameas record-required default constant False|13|13|ROv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_positional0.display_name|record-required-positional0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.index_name|record-required-positional|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.condition|param parameter-interface-internal legacy param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|record_required_positional1|sameas record-required default constant False|13|13|ROv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_positional1.display_name|record-required-positional1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.index_name|record-required-positional|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.condition|param parameter-interface-internal legacy param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_positional0|sameas record-match-required-not-unroll sameas record-match-required-not default constant True|13|13|ROv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_positional0.display_name|matchoptional-positional0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.index_name|matchoptional-positional|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.condition|param sorted-input True param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_positional1|sameas record-match-required-not-unroll sameas record-match-required-not default constant True|13|13|ROv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_positional1.display_name|matchoptional-positional1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.index_name|matchoptional-positional|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.condition|param sorted-input True param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_positional0|sameas dedup default constant False|13|13|ROv|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_positional0.display_name|dedup-positional0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.index_name|dedup-positional|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_positional1|sameas dedup default constant False|13|13|ROv|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_positional1.display_name|dedup-positional1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.index_name|dedup-positional|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|select_positional0|sameas select|20|13|Ov|Filter expression before join function|{0|}}
{30001002|XXparameter|select_positional0.display_name|select-positional0|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.index_name|select-positional|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|select_positional1|sameas select|20|13|Ov|Filter expression before join function|{0|}}
{30001002|XXparameter|select_positional1.display_name|select-positional1|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.index_name|select-positional|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|record_required_keyword0|sameas record-required default constant False|13|13|Kv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_keyword0.display_name|record-required-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.keyword|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.index_name|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.condition|param parameter-interface-internal legacy param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|record_required_keyword1|sameas record-required default constant False|13|13|Kv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_keyword1.display_name|record-required-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.keyword|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.index_name|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.condition|param parameter-interface-internal legacy param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_keyword0|sameas record-match-required-not-unroll sameas record-match-required-not default constant True|13|13|Kv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_keyword0.display_name|matchoptional-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.keyword|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.index_name|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.condition|param sorted-input False param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_keyword1|sameas record-match-required-not-unroll sameas record-match-required-not default constant True|13|13|Kv|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_keyword1.display_name|matchoptional-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.keyword|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.index_name|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.condition|param sorted-input False param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_keyword0|sameas dedup default constant False|13|13|Kv|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_keyword0.display_name|dedup-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.keyword|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.index_name|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_keyword1|sameas dedup default constant False|13|13|Kv|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_keyword1.display_name|dedup-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.keyword|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.index_name|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|select_keyword0|sameas select|20|13|Kv|Filter expression before join function|{0|}}
{30001002|XXparameter|select_keyword0.display_name|select-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.keyword|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.index_name|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|select_keyword1|sameas select|20|13|Kv|Filter expression before join function|{0|}}
{30001002|XXparameter|select_keyword1.display_name|select-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.keyword|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.index_name|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|override_key0||19|2|FK$|Alternate name(s) for join key(s)|{0|}}
{30001002|XXparameter|override_key0.display_name|override-key0|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.keyword|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.index_name|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.condition|version 2.1:|3|15|P?|@{0|}}
{30001002|XXparameter|override_key1||19|2|FK$|Alternate name(s) for join key(s)|{0|}}
{30001002|XXparameter|override_key1.display_name|override-key1|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.keyword|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.index_name|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.condition|version 2.1:|3|15|P?|@{0|}}
{30001002|XXparameter|driving|0|1|2|FK$|The largest input; all other inputs will be read into memory|{0|}}
{30001002|XXparameter|driving.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|maintain_order|False|13|1|FKl|Exit rather than spill to disk|{0|}}
{30001002|XXparameter|maintain_order.display_name|maintain-order|3|9|P|@{0|}}
{30001002|XXparameter|maintain_order.keyword|maintain-order|3|9|P|@{0|}}
{30001002|XXparameter|maintain_order.condition|version 2.2.2: param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|max_core|67108864|1|2|FK$|Maximum memory usage (for non-driving inputs before spilling to disk) in bytes|{0|}}
{30001002|XXparameter|max_core.display_name|max-core|3|9|P|@{0|}}
{30001002|XXparameter|max_core.keyword|max-core|3|9|P|@{0|}}
{30001002|XXparameter|max_core.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|max_memory|8388608|1|2|FK$|Maximum memory usage (before spilling to disk) in bytes|{0|}}
{30001002|XXparameter|max_memory.display_name|max-memory|3|9|P|@{0|}}
{30001002|XXparameter|max_memory.keyword|max-memory|3|9|P|@{0|}}
{30001002|XXparameter|max_memory.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort|False|13|1|FKl|Always check sort order on inputs|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 3.0.1.r9: param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|sql_null_comparisons|False|13|1|FKl|When matching against null fields, use SQL semantics instead of DML semantics|{0|}}
{30001002|XXparameter|sql_null_comparisons.display_name|sql-null-comparisons|3|9|P|@{0|}}
{30001002|XXparameter|sql_null_comparisons.keyword|sql-null-comparisons|3|9|P|@{0|}}
{30001002|XXparameter|sql_null_comparisons.condition|version 3.3.1.r3:|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_intermediate||15|1|Fl|Frequency of intermediate records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_intermediate.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|6|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::join(in[*])|3|2|H$|Join transform|{0|}}
{30001002|XXparameter|sorted_mpname|merge-join|3|2|H$||{0|}}
{30001002|XXparameter|sorted_mpname.display_name|sorted-mpname|3|9|P|@{0|}}
{30001002|XXparameter|memory_mpname|hash-join|3|2|H$||{0|}}
{30001002|XXparameter|memory_mpname.display_name|memory-mpname|3|9|P|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp max-memory max-core dedup singlematch dedup-keyword singlematch record-required matchoptional record-required-keyword matchoptional select-keyword select record-required-positional matchoptional dedup-positional singlematch matchoptional-keyword matchoptional matchoptional-positional matchoptional|3|2|H$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|unused_port_version|2.4.18:|3|2|H$|Version that unused ports became available|{0|}}
{30001002|XXparameter|unused_port_version.display_name|unused-port-version|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|legacy_xfr;reject*=in*; unused*=in*; error*=^error|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=join(*);unused=join(*)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|error_port_type error <parameter error0_metadata>|3|2|H$|Type for make_error output|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in[*])|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in[*])|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in[*])|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|5|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count in|3|1|l||{0|}}
{30001002|XXparameter|in0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|in1_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|unused0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|unused1_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|reject1_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|error1_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,unused[*],reject[*],error[*],log::document(in[*])|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1639787121|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: unused = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Join|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|112|0|269|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|113|0|272|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|unused0|0.0|count|unused|0|1168|0|}}
{2010203004|XXGoport|114|0|275|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|unused1|0.0|count|unused|1|1168|0|}}
{2010203004|XXGoport|115|0|278|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|116|0|281|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|117|0|284|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|118|0|287|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|119|0|290|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|120|0|293|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|select0||20|8|F=|Filter expression before join function|{0|}}
{30001002|XXparameter|select0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|select0.index_name|select|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0||13|8|F=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required0.display_name|record-match-required0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.index_name|record-match-required|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required0.condition|param parameter-interface-internal version-3-2-2 param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|dedup0||13|8|F=|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|dedup0.index_name|dedup|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0||13|8|RO=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_positional0.display_name|record-required-positional0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.index_name|record-required-positional|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional0.condition|param parameter-interface-internal legacy param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_keyword0||13|8|K=|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_keyword0.display_name|dedup-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.keyword|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.index_name|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword0.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|record_required0||13|8|F=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required0.display_name|record-required0|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.index_name|record-required|3|9|P|@{0|}}
{30001002|XXparameter|record_required0.condition|param parameter-interface-internal legacy param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_positional0||13|8|RO=|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_positional0.display_name|dedup-positional0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.index_name|dedup-positional|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional0.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|select_keyword0||20|8|K=|Filter expression before join function|{0|}}
{30001002|XXparameter|select_keyword0.display_name|select-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.keyword|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.index_name|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword0.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_positional0||13|8|RO=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_positional0.display_name|matchoptional-positional0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.index_name|matchoptional-positional|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional0.condition|param sorted-input True param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|record_required_keyword0||13|8|K=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_keyword0.display_name|record-required-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.keyword|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.index_name|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword0.condition|param parameter-interface-internal legacy param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_keyword0||13|8|K=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_keyword0.display_name|matchoptional-keyword0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.keyword|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.index_name|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword0.condition|param sorted-input False param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|override_key0||19|8|FK=|Alternate name(s) for join key(s)|{0|}}
{30001002|XXparameter|override_key0.display_name|override-key0|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.keyword|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.index_name|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key0.condition|version 2.1:|3|15|P?|@{0|}}
{30001002|XXparameter|select_positional0||20|8|O=|Filter expression before join function|{0|}}
{30001002|XXparameter|select_positional0.display_name|select-positional0|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.index_name|select-positional|3|9|P|@{0|}}
{30001002|XXparameter|select_positional0.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0||13|8|K=||{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.index_name|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0.condition|param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not0||13|8|=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not0.display_name|record-match-required-not0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.index_name|record-match-required-not|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not0.condition|param parameter-interface-internal version-3-2-2 version 3.2.1.r10:|3|15|P?|@{0|}}
}}@0|0|0|0|in0|0.0|count|in|0|1808|0|}}
{2010202004|XXGiport|121|0|311|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|select1||20|8|F=|Filter expression before join function|{0|}}
{30001002|XXparameter|select1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|select1.index_name|select|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1||13|8|F=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required1.display_name|record-match-required1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.index_name|record-match-required|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required1.condition|param parameter-interface-internal version-3-2-2 param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|dedup1||13|8|F=|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|dedup1.index_name|dedup|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1||13|8|RO=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_positional1.display_name|record-required-positional1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.index_name|record-required-positional|3|9|P|@{0|}}
{30001002|XXparameter|record_required_positional1.condition|param parameter-interface-internal legacy param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_keyword1||13|8|K=|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_keyword1.display_name|dedup-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.keyword|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.index_name|dedup-keyword|3|9|P|@{0|}}
{30001002|XXparameter|dedup_keyword1.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|record_required1||13|8|F=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required1.display_name|record-required1|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.index_name|record-required|3|9|P|@{0|}}
{30001002|XXparameter|record_required1.condition|param parameter-interface-internal legacy param join-type Explicit|3|15|P?|@{0|}}
{30001002|XXparameter|dedup_positional1||13|8|RO=|This controls the join behavior (full vs semi)|{0|}}
{30001002|XXparameter|dedup_positional1.display_name|dedup-positional1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.index_name|dedup-positional|3|9|P|@{0|}}
{30001002|XXparameter|dedup_positional1.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|select_keyword1||20|8|K=|Filter expression before join function|{0|}}
{30001002|XXparameter|select_keyword1.display_name|select-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.keyword|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.index_name|select-keyword|3|9|P|@{0|}}
{30001002|XXparameter|select_keyword1.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_positional1||13|8|RO=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_positional1.display_name|matchoptional-positional1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.index_name|matchoptional-positional|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_positional1.condition|param sorted-input True param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|record_required_keyword1||13|8|K=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_required_keyword1.display_name|record-required-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.keyword|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.index_name|record-required-keyword|3|9|P|@{0|}}
{30001002|XXparameter|record_required_keyword1.condition|param parameter-interface-internal legacy param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|matchoptional_keyword1||13|8|K=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|matchoptional_keyword1.display_name|matchoptional-keyword1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.keyword|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.index_name|matchoptional-keyword|3|9|P|@{0|}}
{30001002|XXparameter|matchoptional_keyword1.condition|param sorted-input False param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|override_key1||19|8|FK=|Alternate name(s) for join key(s)|{0|}}
{30001002|XXparameter|override_key1.display_name|override-key1|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.keyword|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.index_name|override-key|3|9|P|@{0|}}
{30001002|XXparameter|override_key1.condition|version 2.1:|3|15|P?|@{0|}}
{30001002|XXparameter|select_positional1||20|8|O=|Filter expression before join function|{0|}}
{30001002|XXparameter|select_positional1.display_name|select-positional1|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.index_name|select-positional|3|9|P|@{0|}}
{30001002|XXparameter|select_positional1.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1||13|8|K=||{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.index_name|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen|3|9|P|@{0|}}
{30001002|XXparameter|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1.condition|param parameter-interface-internal version-3-2-2|3|15|P?|@{0|}}
{30001002|XXparameter|record_match_required_not1||13|8|=|This controls the join behavior (outer vs inner)|{0|}}
{30001002|XXparameter|record_match_required_not1.display_name|record-match-required-not1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.index_name|record-match-required-not|3|9|P|@{0|}}
{30001002|XXparameter|record_match_required_not1.condition|param parameter-interface-internal version-3-2-2 version 3.2.1.r10:|3|15|P?|@{0|}}
}}@0|0|0|0|in1|0.0|count|in|1|1808|0|}}
{2010503005|XXGfvertex|122|0|329|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/ING_BIG_SCORES_LKP_test.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|mode|0x0001|3|2|$|@{0|}}
{30001002|XXparameter|read_metadata|$AI_DML/hive_big_table_scores_t_m.dml|3|2|f$|@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/ING_BIG_SCORES_LKP_test.dat|3|2|$|@{0|}}
}}@2|Output File|560000|375000|0|0|0|0|5624|last model date 2|Ab Initio Software|@1|10000|-1||6||33025|-1|-1|}}
{2010203004|XXGoport|123|0|331|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|124|0|334|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table).|{6|uninterpreted|seqfile|parquet|orc|avro|texttable|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4\}|{8|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|mpcmodtime|1639787116|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
}}@0|Output File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|125|0|336|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010600005|XXGgraph|126|0|346|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Hadoop/Read_Hive_Table.mp|3|2|Pf$|@{0|}}
{30001002|XXparameter|HIVE_LAYOUT|$\{HIVE_LAYOUT\}|3|9||@{0|}}
{30001002|XXparameter|FILE_FORMAT|parquet|3|9||@{0|}}
{30001002|XXparameter|OUTPUT_DML|$AI_DML/hive_big_table_scores_t_m.dml|3|2|f$|@{0|}}
{30001002|XXparameter|DATABASE|$\{DB\}|3|9||@{0|}}
{30001002|XXparameter|TABLE|big_table_scores_t_m|3|9||@{0|}}
{30001002|XXparameter|HOST_LIST|$\{HIVE_LAYOUT\}|3|9||@{0|}}
{30001002|XXparameter|HOST_DEPTH|1|3|9||@{0|}}
{30001002|XXparameter|READ_LAYOUT|$\{HIVE_LAYOUT\}|3|2|$|@{0|}}
{30001002|XXparameter|FILTER_EXPR|(date("YYYY-MM-DD"))(last_updated_date) >= date_add_months((date("YYYY-MM-DD"))today(),-$\{MONTHS_NUM\}) and model_id member [vector $MODELS]|3|9||@{0|}}
}}@0|@120000|211500|0|0|0|0|5528|Read Hive Table|Ab Initio|Created 11/21/2014 2:25:51 PM|1|100|0|@9|@4097|{0|}0|0|{0|}{0|}{0|}{0|}1.0|835000|407000|0|}}
{2010210004|XXGflow|127|0|349|0|{@{}@384|.5|.5|{0|}4035|17|}}
{2010501005|XXGpvertex|128|0|352|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|deselect_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|@399000|160000|0|0|0|0|4015|Filter Partitions|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|129|0|354|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|130|0|357|0|{@{}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|131|0|359|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|132|0|361|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|133|0|363|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|134|0|365|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010600005|XXGgraph|135|0|376|0|{COPYRIGHT AB INITIO
ALL RIGHTS RESERVED
USE AND DISCLOSURE IS RESTRICTED BY CONFIDENTIALITY & LICENSE CONDITIONS|{}@0|@590000|151000|0|0|0|0|4036|Read HDFS Files|Ab Initio|Created 8/26/2015 3:21:55 PM|1|100|0|@9|@1|{0|}0|0|{0|}{0|}{0|}{0|}1.0|739000|210000|0|}}
{2010501005|XXGpvertex|136|0|381|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|@242000|61000|249000|75000|132000|107000|4018|Partition Blocks|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|137|0|383|0|{@{}@380000|124000|11000|11000|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|138|0|386|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|139|0|388|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|140|0|390|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|141|0|392|0|{@{}@239000|124000|11000|11000|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|142|0|400|0|{@{}@0|0|0|0|out0|.5117370892018779|@@@14352|0|}}
{2010202004|XXGiport|143|0|403|0|{@{}@0|0|0|0|in0|.5044642857142857|@@@13840|0|}}
{2010600005|XXGgraph|144|0|407|0|{Subgraph created from graph "Read_Hive_Table"|{}@0|@39500|98500|0|0|0|0|4024|Validate HIVE_LAYOUT|Ab Initio|@1|100|-1|@9|@32769|{0|}0|0|{0|}{0|}{0|}{0|}1.0|298000|184000|2|}}
{2010210004|XXGflow|145|0|409|0|{@{}@0|.5|.5|{0|}4059|17|}}
{2010501005|XXGpvertex|146|0|411|0|{|{}@1|Create Data|66000|85000|0|0|0|0|4060|Perform Validation|Ab Initio Software|Built-in 2.15.2:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|147|0|413|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|148|0|416|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|149|0|418|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|150|0|420|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Trash|171000|80000|0|0|0|0|4058|Trash|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010202004|XXGiport|151|0|422|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|152|0|427|0|{@{}@0|0|0|0|out0|.6354916067146283|@@@14352|0|}}
{2010600005|XXGgraph|153|0|431|0|{Reads data sequentially from a Hadoop Distributed File System. Can optionally select data from a Hive partition using the query you provide. Only for batch graphs.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
{30001002|XXparameter|analysis_level|none|3|1|Kl|@{0|}}
{30001002|XXparameter|HIVE_LAYOUT|localhost|3|9|RFK|The host for generating partition data, which requires HIVE access.|{0|}}
{30001002|XXparameter|READ_LAYOUT||28|2|FK$|The URL for the read layout. This is overridden if HOST_LIST is set.|{0|}}
{30001002|XXparameter|FILE_FORMAT|texttable|15|9|RFK|The HIVE table format.|{6|texttable|seqfile|parquet|orc|rcfile|avro|}}
{30001002|XXparameter|OUTPUT_DML||7|1|RFKl|The output record DML.|{0|}}
{30001002|XXparameter|DATABASE|default|3|9|FK|The database name for generating partition data. This is ignored if PARTITION_DATA_PATH is set.|{0|}}
{30001002|XXparameter|TABLE||3|9|FK|The table name for generating partition data. This is ignored if PARTITION_DATA_PATH is set.|{0|}}
{30001002|XXparameter|FILTER_EXPR|1|20|1|RFKl|Expression to filter table partitions for read.|{0|}}
{30001002|XXparameter|READ_COLUMNS||3|2|FK$|A comma-separated list of column numbers to read from RCFile. Column numbers are zero-based.|{0|}}
{30001002|XXparameter|REFORMAT_XFR|out :: reformat(read, filename, in) =
begin
  out.* :1: read.*;
  out.* :: in._AB_read_hdfs_files_input_record.*;
end;|8|9|FK|Optional. Reformat XFR for data read.|{0|}}
{30001002|XXparameter|PARTITION_DATA_PATH||18|3|FKc|Optional. Path to an existing partition data file. When set, partition data generation is disabled and partition data will be fetched from this file instead.|{0|}}
{30001002|XXparameter|HDFS_FILE_SUFFIX||3|9|FK|Optional. Specify the suffix for the files to be read.|{0|}}
{30001002|XXparameter|BLOCK_PARTITION_XFR|include "~ab_home/include/log-event-type.dml";

let float load_balance_ratio = 0; // 0 means no load balancing; 1 means RR with block affinity (ignore hdfs locality)
let int initialized = 0;
let string(int) tuning = "tuning";
let string(int) debug = "debug";
let int locality_node_selected = 0;
let int block_count = 0;
let string(int) last_file = "_UNKNOWN_";
let int file_block = 0;

type ply_count_type = record
  int ply;
  int count;
end;

let ply_count_type[int] count_map = allocate();
let ply_count_type[int] matching_count = allocate();
let ply_count_type matching_count_min = allocate();
let ply_count_type global_count_min = allocate();

let int index = allocate();

index_out :: partition_index(in) =
begin
  let int num_matched;
  if (initialized == 0)
  begin
    count_map = for (let int i, i < number_of_downstream_partitions()) :
      [record ply i, count 0];
    initialized = 1;
  end
  
  matching_count =
  for (let host in in._AB_read_hdfs_files_hosts) :
    for (let ply in get_partitions(host)) :
      [record ply ply, count count_map[ply].count];

  num_matched = length_of(matching_count);

  if (string_compare(last_file, in._AB_read_hdfs_files_filename) == 0)
  begin
    write_to_log(event_type = debug, event_text = printf("file %s-%d: block hosts %s",
                 in._AB_read_hdfs_files_filename, file_block, string_join(in._AB_read_hdfs_files_hosts, " ")));
    file_block = file_block + 1;
  end
  else
    last_file = in._AB_read_hdfs_files_filename;

  if (num_matched > 0)
    matching_count_min = vector_min(matching_count, \{count\});
  global_count_min = vector_min(count_map, \{count\});
  
  if ((num_matched > 0) &&
      ( ((float)global_count_min.count + 1) / 
        ((float)matching_count_min.count + 1) >= load_balance_ratio)
     )
    begin
      index = matching_count_min.ply;
      locality_node_selected = locality_node_selected + 1;
    end
  else
    index = global_count_min.ply;

  count_map[index].count = count_map[index].count + 1;
  block_count = block_count + 1;

  index_out :: index;
end;

log_event_t log :: final_log_output() = 
begin 
   log.event_type :: tuning; 
   log.event_text :: printf("local block count = %d / total = %d", locality_node_selected, block_count);
end;|8|9|FK|Tranform package that partition HDFS file block for reads.|{0|}}
{30001002|XXparameter|HOST_LIST||3|9|FK|(Optional) A comma separated list of hosts to run on e.g. A, B, C. Setting this overrides READ_LAYOUT.|{0|}}
{30001002|XXparameter|HOST_DEPTH||1|9|FK|(Optional) The number of ways parallel to run on each host.|{0|}}
{30001002|XXparameter|SCHEMA_FILE||3|2|FK$|Location of schema file for reading avro files, prefix with file: or hdfs:. If not specified, data will be read using the schema in the data file.|{0|}}
{30001002|XXparameter|PARTITION_DML|$[begin
  result :: string_replace(OUTPUT_DML, "metadata type = hive_row_t;", "metadata type = hive_partition_t;");
end]|7|9|RK|@{0|}}
{30001002|XXparameter|USE_DML_DATES|$[begin
  let string(int) resultstr = "false";
  let dml_field_info_vec fields = record_info(dml_type_str = PARTITION_DML);
  for (let dml_field_info field in fields) begin
    if (field.form == "date" \|\| field.form == "datetime")
      resultstr = "true";
  end
  result :: resultstr;
end]|13|9|RK|@{0|}}
{30001002|XXparameter|LOGGING|False|13|1|RFKl|Log internal events|{0|}}
{30001002|XXparameter|REJECT_THRESHOLD|Abort on first reject|15|1|RFKl|When to abort if input records are rejected|{2|Abort on first reject|Never abort|}}
{30001002|XXparameter|ERROR_GROUP||3|9|FK|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|LOG_GROUP||3|9|FK|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|table|AB_PARAMETER_ENV|3|10|Kd|@{0|}}
{30001002|XXparameter|database|AB_PARAMETER_ENV|3|10|Kd|@{0|}}
{30001002|XXparameter|project_dir|AB_PARAMETER_ENV|3|10|Kd|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("out0", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$project_dir/catalog/db/hive/$database/$table", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|40|9|RFK|@{0|}}
{30001002|XXparameter|project_dir:eme|$PROJECT_DIR|3|9||@{0|}}
{30001002|XXparameter|project_dir:sandbox|$[ first_without_error(pdl_resolve_to_string("$PROJECT_DIR"),"no_sandbox_location") ]|3|9||@{0|}}
{30001002|XXparameter|table:eme|$[ if (TABLE!="") TABLE else force_error("Dependency analysis requires an input value for the TABLE parameter") ]|3|9||@{0|}}
{30001002|XXparameter|table:sandbox|$TABLE|3|9||@{0|}}
{30001002|XXparameter|database:eme|$[ if (DATABASE!="") DATABASE else force_error("Dependency analysis requires an input value for the DATABASE parameter") ]|3|9||@{0|}}
{30001002|XXparameter|database:sandbox|$DATABASE|3|9||@{0|}}
{30001002|XXparameter|INTERNAL_HIVE_LAYOUT|$[
if (string_index(HIVE_LAYOUT, "/") > 0)
  HIVE_LAYOUT
else
  string_concat("file://", HIVE_LAYOUT);
]|3|9|RK|@{0|}}
{30001002|XXparameter|DIRECTORY_WALK_GLOB_PATTERN|[!._]*|3|9|RFK|Globbing pattern used when listing contents of directories passed to reader. The default pattern excludes files beginning with . and _.|{0|}}
{30001002|XXparameter|PATH_GLOB_PATTERN|[!._]*|3|9|RFK|Globbing pattern used when listing contents of directories passed to reader. The default pattern excludes files beginning with . and _.|{0|}}
{30001002|XXparameter|mpcmodtime|1639787116|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|@15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
}}@0|@151500|113750|0|0|0|0|3326|Read_Hive_Table|||1|100|-1|@9|@32769|{0|}0|0|{0|}{0|}{0|}{0|}1.0|835000|407000|2|}}
{2010210004|XXGflow|154|0|433|0|{@{}@384|.5|.5|{0|}4014|17|}}
{2010210004|XXGflow|155|0|435|0|{@{}@384|.5|.5|{0|}4035|17|}}
{2010210004|XXGflow|156|0|437|0|{@{}@384|.5|.5|{0|}4025|17|}}
{2010501005|XXGpvertex|157|0|439|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Filter_by_Expression.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|select_expr||3|8|=|@{0|}}
{30001002|XXparameter|error_group||3|8|=|@{0|}}
{30001002|XXparameter|log_group||3|8|=|@{0|}}
{30001002|XXparameter|reject_threshold||3|8|=|@{0|}}
{30001002|XXparameter|logging||3|8|=|@{0|}}
}}@1|@399000|160000|0|0|0|0|4015|Filter Partitions|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|158|0|441|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|159|0|444|0|{@{}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|160|0|446|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|161|0|448|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|162|0|450|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|163|0|452|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|164|0|456|0|{Filters data records according to the specified DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|select-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|select_expr||20|2|RFO$|Filter expression|{0|}}
{30001002|XXparameter|select_expr.condition|param use_package False|3|15|P?|@{0|}}
{30001002|XXparameter|no_select_expr|-use_package|3|2|RO$|Replaces select_expr as the positional argument when use_package is true|{0|}}
{30001002|XXparameter|no_select_expr.condition|param use_package True|3|15|P?|@{0|}}
{30001002|XXparameter|use_package|False|13|1|Fl|If true, use the select() function defined in the package|{0|}}
{30001002|XXparameter|use_package.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|package||8|1|FKl|Package containing transforms and data types|{0|}}
{30001002|XXparameter|package.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|5|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|integer(8) select_out::select(in)|3|2|H$|Use this instead of the select_expr parameter when use_package is true.|{0|}}
{30001002|XXparameter|operation1.condition|version 2.16: param use_package True|3|15|P?|@{0|}}
{30001002|XXparameter|operation1_analysis|skip_missing integer(8) select_out::select(in)|3|2|H$||{0|}}
{30001002|XXparameter|operation1_analysis.condition|version 2.16: param use_package True|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in; out=in; deselect=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select_expr); deselect=filter(select_expr); out=filter_xfr(package.select_out); deselect=filter_xfr(package.select_out);|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|9|RFs||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|deselect_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,deselect,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1440616960|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: deselect = out
metadata type: out = deselect
metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out
metadata type: deselect = in
metadata type: in = deselect|3|1|FHKl|@{0|}}
}}@0|Filter by Expression|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|165|0|458|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|166|0|461|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|167|0|464|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|168|0|467|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|169|0|470|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|170|0|473|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|171|0|481|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Run_Program.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|commandline|hive-to-dml -partitions $[if (USE_DML_DATES) "" else "-integer_dates"] $DATABASE $TABLE|3|9||@{0|}}
{30001002|XXparameter|condition|$[ is_blank(PARTITION_DATA_PATH) ]|3|9||@{0|}}
{30001002|XXparameter|Layout|$INTERNAL_HIVE_LAYOUT|3|2|$|@{0|}}
}}@1|Run Program|115000|224000|0|0|0|0|4026|Generate Partition Data|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|172|0|483|0|{@{}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|173|0|486|0|{@{}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010501005|XXGpvertex|174|0|488|0|{Executes a standard UNIX or Windows program.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|filter|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|commandline||16|2|RFO$|Command line of UNIX or Windows program to execute|{0|}}
{30001002|XXparameter|NoHidePorts|in out|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=all_to_all(in)|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|9|RFs||{0|}}
{30001002|XXparameter|in_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1440616958|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Run Program|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|175|0|490|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|176|0|493|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010503005|XXGfvertex|177|0|496|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|condition|$[ not is_blank(PARTITION_DATA_PATH) ]|3|9||@{0|}}
{30001002|XXparameter|Layout|$PARTITION_DATA_PATH|3|2|$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$PARTITION_DATA_PATH", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|read_metadata|$\{PARTITION_DML\}|3|3|c|@{0|}}
}}@1|@209000|123000|0|0|0|0|4013|Partition Data|Ab Initio Software|@1|100|-1||6||33025|-1|-1|}}
{2010203004|XXGoport|178|0|498|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|179|0|501|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|9|RF||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1440616947|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|@0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|180|0|503|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010600005|XXGgraph|181|0|506|0|{COPYRIGHT AB INITIO
ALL RIGHTS RESERVED
USE AND DISCLOSURE IS RESTRICTED BY CONFIDENTIALITY & LICENSE CONDITIONS|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Hadoop/Internal/Read_HDFS_Files.mp|3|9|Pf|@{0|}}
{30001002|XXparameter|READ_LAYOUT||3|8|=|@{0|}}
{30001002|XXparameter|FILE_FORMAT||3|8|=|@{0|}}
{30001002|XXparameter|OUTPUT_DML||3|8|=|@{0|}}
{30001002|XXparameter|REFORMAT_XFR||3|8|=|@{0|}}
{30001002|XXparameter|HDFS_FILE_SUFFIX||3|8|=|@{0|}}
{30001002|XXparameter|BLOCK_PARTITION_XFR||3|8|=|@{0|}}
{30001002|XXparameter|HOST_LIST||3|8|=|@{0|}}
{30001002|XXparameter|HOST_DEPTH||3|8|=|@{0|}}
{30001002|XXparameter|READ_COLUMNS||3|8|=|@{0|}}
{30001002|XXparameter|SCHEMA_FILE||3|8|=|@{0|}}
{30001002|XXparameter|REJECT_THRESHOLD||3|8|=|@{0|}}
{30001002|XXparameter|LOGGING||3|8|=|@{0|}}
{30001002|XXparameter|ERROR_GROUP||3|8|=|@{0|}}
{30001002|XXparameter|LOG_GROUP||3|8|=|@{0|}}
{30001002|XXparameter|PATH_GLOB_PATTERN||3|8|=|@{0|}}
}}@0|@590000|151000|0|0|0|0|4036|Read HDFS Files|Ab Initio|Created 8/26/2015 3:21:55 PM|1|100|0|@9|@1|{0|}0|0|{0|}{0|}{0|}{0|}1.0|739000|210000|0|}}
{2010210004|XXGflow|182|0|508|0|{@{}@384|.5|.5|{0|}4019|17|}}
{2010210004|XXGflow|183|0|510|0|{@{}@384|.5|.5|{0|}4017|20|}}
{2010501005|XXGpvertex|184|0|512|0|{Walks the directory tree starting from paths specified on the input flow.  Produces a list of files to be read as well as the files' block and address info.|{}@1|@60000|50000|0|0|0|0|4020|Find Files and Read Blocks|Ab Initio Software|Built-in 2.14:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|185|0|514|0|{@{}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010203004|XXGoport|186|0|517|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|187|0|519|0|{@{}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|188|0|521|0|{|{}@1|@242000|61000|249000|75000|132000|107000|4018|Partition Blocks|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|189|0|523|0|{@{}@380000|124000|11000|11000|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|190|0|526|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|191|0|528|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|192|0|530|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|193|0|532|0|{@{}@239000|124000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|194|0|535|0|{|{}@1|@445000|68000|0|0|0|0|4014|Read Blocks|||1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|195|0|537|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|196|0|539|0|{@{}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|197|0|541|0|{@{}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|198|0|543|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|199|0|545|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|200|0|547|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|201|0|549|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|202|0|552|0|{@{}@0|0|0|0|out0|.5117370892018779|@@@14352|0|}}
{2010202004|XXGiport|203|0|555|0|{@{}@0|0|0|0|in0|.5044642857142857|@@@13840|0|}}
{2010600005|XXGgraph|204|0|559|0|{COPYRIGHT AB INITIO
ALL RIGHTS RESERVED
USE AND DISCLOSURE IS RESTRICTED BY CONFIDENTIALITY & LICENSE CONDITIONS
COPYRIGHT organizer/datasets/Hadoop/Read_HDFS.mp AB INITIO
ALL RIGHTS RESERVED
USE AND DISCLOSURE IS RESTRICTED BY CONFIDENTIALITY & LICENSE CONDITIONS|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
{30001002|XXparameter|analysis_level|none|3|1|Kl|@{0|}}
{30001002|XXparameter|READ_LAYOUT||28|2|FK$|The URL for the read layout. This is overrided if HOST_LIST is set.|{0|}}
{30001002|XXparameter|FILE_FORMAT|uninterpreted|15|9|FK|The input file format: 'uninterpreted' (read raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'rcfile' (RCFile format), 'avro' (Avro format), 'texttable' (Hive text table).|{7|uninterpreted|seqfile|parquet|orc|rcfile|avro|texttable|}}
{30001002|XXparameter|OUTPUT_DML||7|1|RFKl|The output record DML.|{0|}}
{30001002|XXparameter|REFORMAT_XFR||8|9|FK|Optional reformat XFR for data read.|{0|}}
{30001002|XXparameter|HDFS_FILE_SUFFIX||3|9|FK|As an option, specify the suffix for the files to be read.|{0|}}
{30001002|XXparameter|READ_BY_BLOCK|True|13|9|RFK|@{2|BLOCK|FILE|}}
{30001002|XXparameter|BLOCK_PARTITION_XFR|include "~ab_home/include/log-event-type.dml";

let float load_balance_ratio = 0; // 0 means no load balancing; 1 means RR with block affinity (ignore hdfs locality)
let int initialized = 0;
let string(int) tuning = "tuning";
let string(int) debug = "debug";
let int locality_node_selected = 0;
let int block_count = 0;
let string(int) last_file = "_UNKNOWN_";
let int file_block = 0;

type ply_count_type = record
  int ply;
  int bytes;
end;

let ply_count_type[int] bytes_map = allocate();
let ply_count_type[int] matching_bytes = allocate();
let ply_count_type matching_bytes_min = allocate();
let ply_count_type global_bytes_min = allocate();

let int index = allocate();

index_out :: partition_index(in) =
begin
  let int num_matched;
  if (initialized == 0)
  begin
    bytes_map = for (let int i, i < number_of_downstream_partitions()) :
      [record ply i, bytes 0];
    initialized = 1;
  end
  
  matching_bytes =
  for (let host in in._AB_read_hdfs_files_hosts) :
    for (let ply in get_partitions(host)) :
      [record ply ply, bytes bytes_map[ply].bytes];

  num_matched = length_of(matching_bytes);

  if (string_compare(last_file, in._AB_read_hdfs_files_filename) == 0)
  begin
    write_to_log(event_type = debug, event_text = printf("file %s-%d: block hosts %s",
                 in._AB_read_hdfs_files_filename, file_block, string_join(in._AB_read_hdfs_files_hosts, " ")));
    file_block = file_block + 1;
  end
  else
    last_file = in._AB_read_hdfs_files_filename;

  if (num_matched > 0)
    matching_bytes_min = vector_min(matching_bytes, \{bytes\});
  global_bytes_min = vector_min(bytes_map, \{bytes\});
  
  if ((num_matched > 0) &&
      ( ((float)global_bytes_min.bytes + 1) / 
        ((float)matching_bytes_min.bytes + 1) >= load_balance_ratio)
     )
    begin
      index = matching_bytes_min.ply;
      locality_node_selected = locality_node_selected + 1;
    end
  else
    index = global_bytes_min.ply;

  bytes_map[index].bytes = bytes_map[index].bytes + in._AB_read_hdfs_files_address.compr_size; // length of file/block stored here
  block_count = block_count + 1;

  index_out :: index;
end;

log_event_t log :: final_log_output() = 
begin 
   log.event_type :: tuning; 
   log.event_text :: printf("local block count = %d / total = %d", locality_node_selected, block_count);
end;|8|9|FK|Tranform package that partition HDFS file block for reads.|{0|}}
{30001002|XXparameter|HOST_LIST||3|9|FK|A comma separated list of hosts to run on e.g. localhost, another_host, one_more_host. If set, this overrides READ_LAYOUT.|{0|}}
{30001002|XXparameter|HOST_DEPTH||1|9|FK|The number of ways parallel to run on each host.|{0|}}
{30001002|XXparameter|READ_COLUMNS||3|2|FK$|A comma-separated list of column number to read from RC File. Column numbers are zero-based.|{0|}}
{30001002|XXparameter|SCHEMA_FILE||3|2|FK$|Location of schema file for reading avro files, prefix with file: or hdfs:. If not specified, data will be read using the schema in the data file.|{0|}}
{30001002|XXparameter|READ_LAYOUT_INTERNAL|$[begin
  let string(int) ret = "";
  if (is_null(HOST_LIST) or is_blank(HOST_LIST))
    begin
      ret = READ_LAYOUT;
    end
  else
    begin
      let string(int)[] host_list = string_split_no_empty(HOST_LIST, ",");
      ret = "-hosts " + string_join(for (let hc in host_list) :
        for (let i, i <  HOST_DEPTH) : string_lrtrim(hc), ' ' );
    end
  result :: ret;
end]|3|9|RK|@{0|}}
{30001002|XXparameter|HOSTS_LAYOUT|$[begin
  let string(int)[] host_list = string_split_no_empty(HOST_LIST, ",");
  result:: string_join(for (let hc in host_list) :
    for (let i, i <  HOST_DEPTH) : string_lrtrim(hc), ' ' );
end]|3|9|RK|The processed list of host names from HOST_LIST.|{0|}}
{30001002|XXparameter|READ_SPECIFICATION||7|8|K=|This is an optional record DML that is added to the read specification for each file read.|{0|}}
{30001002|XXparameter|COMPRESSED|$[(FILE_FORMAT == "compressed" \|\| FILE_FORMAT == "hadoop_compressed")]|13|9|RK|@{0|}}
{30001002|XXparameter|READ_FORMAT|$[if (FILE_FORMAT == "compressed") "uninterpreted" else FILE_FORMAT]|3|9|RK|@{0|}}
{30001002|XXparameter|REJECT_THRESHOLD|Abort on first reject|15|1|RFKl|When to abort if input records are rejected|{2|Abort on first reject|Never abort|}}
{30001002|XXparameter|LOGGING|False|13|1|RFKl|Log internal events|{0|}}
{30001002|XXparameter|ERROR_GROUP||3|9|FK|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|LOG_GROUP||3|9|FK|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|RMF_XFR|include "/~ab_home/include/readfiles-constants.dml";

$[begin
  let string(int) new_dml = "";
  let string(int) record_str = "type input_type ";
  if (string_index(OUTPUT_DML, "hive_file_t") > 0) begin
    record_str = record_str + "= hive_file_t";
    record_str = re_replace_first(OUTPUT_DML, "metadata\\\\stype\\\\s\\\\=\\\\shive_row_t", record_str);
  end else begin
    let dml_field_info_vec field_list = record_info(OUTPUT_DML);
    let dml_field_info partition_list = NULL;
    let string(int)[] field_names = allocate();

    // Locate partition fields.
    for (let field in field_list) begin
      field_names = vector_append(field_names, field.name);
      if (field.name == "get_partition_fields()")
          partition_list = field;
    end

    new_dml = OUTPUT_DML;

    if (not is_null(partition_list)) begin
      // Remove partition fields from DML.
      let string(int) trimmed = string_replace(string_replace(partition_list.default, "[vector", ""), "]", "");
      let string(int) filtered = string_replace(string_replace(trimmed, "\\"", ""), ",", "");
      if (not is_blank(filtered)) begin
        let partition_keys = string_split(filtered, " ");
        let matching_fields = vector_intersection(field_names, partition_keys);
        new_dml = remove_fields(OUTPUT_DML, matching_fields);
      end
    end

    // Update metadata type as input_type.
    if (is_null(re_get_match(new_dml, "metadata\\\\stype\\\\s")))
      record_str = record_str + " = " + new_dml + ";\\n";
    else
      record_str = re_replace_first(new_dml, "metadata\\\\stype\\\\s", record_str);
  end
  result :: record_str + "\\n" + REFORMAT_XFR;
end]

filename::get_filename(in)=
begin
  read_portion(in._AB_read_hdfs_files_address.file_offset,
               $[(COMPRESSED or !READ_BY_BLOCK) ? "0" : "in._AB_read_hdfs_files_address.compr_size"],
               SEARCH_TO_PATTERN_END);
  filename::in._AB_read_hdfs_files_filename;
end;|8|9|RFO|Package containing transforms and data types|{0|}}
{30001002|XXparameter|PATH_GLOB_PATTERN|[!._]*|3|9|RFK|Globbing pattern used when listing contents of directories passed to reader. The default pattern excludes files beginning with . and _.|{0|}}
{30001002|XXparameter|mpcmodtime|1536945688|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|@15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|_ab_semantic_schema|7|1|1|Hnl|@{0|}}
}}@0|@360500|84500|0|0|0|0|3737|Read_HDFS_Files|||1|100|-1|@9|@32769|{0|}0|0|{0|}{0|}{0|}{0|}1.0|739000|210000|2|}}
{2010210004|XXGflow|205|0|561|0|{@{}@384|.5|.5|{0|}4019|17|}}
{2010210004|XXGflow|206|0|563|0|{@{}@384|.5|.5|{0|}4017|20|}}
{2010501005|XXGpvertex|207|0|565|0|{Walks the directory tree starting from paths specified on the input flow.  Produces a list of files to be read as well as the files' block and address info.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Advanced/Procedural_Transform.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|transform|ignore::output_read_spec(filepath, info, in_record)=
begin
  let big endian integer(8) start_offset;
  let big endian integer(8) end_offset;
  let big endian integer(8) block_size;
  let bc_lookup_address_type address;
  if (!$\{COMPRESSED\} && $[READ_BY_BLOCK])
  begin
    block_size = first_defined(info.block_size, 0);
    for (let int idx, idx < length_of(info.host))
      begin 
        start_offset = math_min(idx * block_size, info.size);
        end_offset = math_min((idx+1) * block_size, info.size);
        address = [record file_offset (if (end_offset> start_offset) start_offset else 0)
                                                 compr_size (end_offset - start_offset)
                                                 byte_offset 0];
        write_record(0, [record _AB_read_hdfs_files_filename filepath
                                _AB_read_hdfs_files_address address 
                                _AB_read_hdfs_files_hosts info.host[idx]
                                _AB_read_hdfs_files_input_record in_record
                        ]);
      end;
    end;
  else
  begin
    // Compressed raw file cannot be read in parts.
    address = [record file_offset 0 compr_size info.size byte_offset 0]; 
    write_record(0, [record _AB_read_hdfs_files_filename filepath
                            _AB_read_hdfs_files_address address
                            _AB_read_hdfs_files_hosts info.host[0]
                            _AB_read_hdfs_files_input_record in_record
                    ]);
  end;
  ignore :: 0;
end;

ignore::traverse_directory(current_directory, in_record)=
begin
  let directory_listing_type dirlist = directory_listing(current_directory, $"PATH_GLOB_PATTERN");
  for (let shortpath in dirlist) 
    begin
      let fullpath = current_directory + "/" + shortpath;
      let file_information_type info = file_information(fullpath);
      if (info.found && info.file_type == "DIR ")
        traverse_directory(fullpath, in_record);
      else
      if (ends_with(shortpath, $"HDFS_FILE_SUFFIX"))
        output_read_spec(fullpath, info, in_record);
    end;
  ignore :: 0;
end;

out::process()=
begin
  let int have_data = 1;
  while (have_data) 
    begin
      let in_record = read_record(0);
      let string("") starting_path = first_defined(in_record._AB_read_hdfs_files_starting_path_, "");
      if (starting_path == "") have_data = 0; else 
      begin
        let file_information_type info = file_information(starting_path);
        if (info.found && info.file_type == "DIR ")
          traverse_directory(starting_path, in_record);
        else if (info.found && info.file_type == "HDFS")
          output_read_spec(starting_path, info, in_record);
        else
          force_error(starting_path + " not found.");    
      end;
    end;
  out :: 0;
end;|3|9||@{0|}}
{30001002|XXparameter|out0_metadata|$[begin
  let string(int) new_dml = "record\\nend;\\n";
  let string(int) read_spec_dml = READ_SPECIFICATION;
  
  new_dml = add_fields(new_dml,
    [ vector make_field("_AB_read_hdfs_files_filename", "string(\\"\\")"),
             make_field("_AB_read_hdfs_files_address", "bc_lookup_address_type"),
             make_field("_AB_read_hdfs_files_hosts", "string(\\"\\")[big endian integer(4)]")
    ]);
  
  new_dml = add_field(new_dml, "_AB_read_hdfs_files_input_record", read_spec_dml);
  new_dml = add_field(new_dml, "_AB_read_hdfs_files_filler", "string(32000)", "allocate()");
  result :: new_dml;
end]|3|9||@{0|}}
}}@1|@60000|50000|0|0|0|0|4020|Find Files and Read Blocks|Ab Initio Software|Built-in 2.14:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|208|0|567|0|{@{}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010203004|XXGoport|209|0|570|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|210|0|572|0|{@{}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|211|0|574|0|{Runs code translated into DML from a procedural language such as COBOL.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|proctrans|3|1|Hl||{0|}}
{30001002|XXparameter|image__||3|2|H$||{0|}}
{30001002|XXparameter|in_count|1|1|1|Fl|Number of inputs|{0|}}
{30001002|XXparameter|in_count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|out_count|1|1|1|Fl|Number of outputs|{0|}}
{30001002|XXparameter|out_count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform||8|1|RFOl|Transform|{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|1|1|2|H$|Number of process steps|{0|}}
{30001002|XXparameter|operation1|long out::process()|3|2|H$|process operation|{0|}}
{30001002|XXparameter|operation1_analysis|long process_out::process()|3|2|H$||{0|}}
{30001002|XXparameter|port_analysis|proctrans|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|transform_port|out|3|2|FHK$|port for debugger|{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Enable auto-deadlock buffering|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|continuous_analysis|publisher|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|9|RFs||{0|}}
{30001002|XXparameter|main_mp_port|in_count in out_count out|3|1|l||{0|}}
{30001002|XXparameter|in0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|log_metadata|record string("\|") node, timestamp, component, subcomponent, event_type; string("\|\\n") event_text; end|7|1|Fl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],log::document(in[*])|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1440517531|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: log = "record string(\\"\|\\") node, timestamp, component, subcomponent, event_type; string(\\"\|\\\\n\\") event_text; end"|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Procedural Transform|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|212|0|576|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010203004|XXGoport|213|0|579|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|214|0|582|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|215|0|585|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Partition_by_Expression.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|function|if (write_to_log(event_type="Hostname",event_text=(decimal(""))length_of(get_partitions("bwang-l")) )) 0|3|2|$|@{0|}}
{30001002|XXparameter|use_package|True|3|1|l|@{0|}}
{30001002|XXparameter|package||3|8|=|@{0|}}
{30001002|XXparameter|reject_threshold||3|8|=|@{0|}}
{30001002|XXparameter|logging||3|8|=|@{0|}}
{30001002|XXparameter|error_group||3|8|=|@{0|}}
{30001002|XXparameter|log_group||3|8|=|@{0|}}
}}@1|@242000|61000|249000|75000|132000|107000|4018|Partition Blocks|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|216|0|587|0|{@{}@380000|124000|11000|11000|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|217|0|590|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|218|0|592|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|219|0|594|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|220|0|596|0|{@{}@239000|124000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|221|0|599|0|{Distributes data records to its output flow partitions according to the specified DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|function-partition|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|function||20|2|RFO$|Function to partition on|{0|}}
{30001002|XXparameter|function.condition|param use_package False|3|15|P?|@{0|}}
{30001002|XXparameter|no_function|-use_package|3|2|RO$|Replaces function as the positional argument when use_package is true|{0|}}
{30001002|XXparameter|no_function.condition|param use_package True|3|15|P?|@{0|}}
{30001002|XXparameter|use_package|False|13|1|Fl|If true, use the flow() function defined in the package to specify the flow number.|{0|}}
{30001002|XXparameter|use_package.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|package||8|1|FKl|Package containing transforms and data types|{0|}}
{30001002|XXparameter|package.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|4|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|integer(8) index_out::partition_index(in)|3|2|H$|Use this instead of the function parameter when use_package is true.|{0|}}
{30001002|XXparameter|operation1.condition|version 2.16: param use_package True|3|15|P?|@{0|}}
{30001002|XXparameter|operation1_analysis|skip_missing integer(8) index_out::partition_index(in)|3|2|H$||{0|}}
{30001002|XXparameter|operation1_analysis.condition|version 2.16: param use_package True|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|reject_threshold.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|version 2.16: param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|version 2.16: param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit_keyword.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|logging.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|version 2.16: param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in;out=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|3|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|9|RFs||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1440517533|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Partition by Expression|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|222|0|601|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|223|0|604|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|224|0|607|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|225|0|610|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|226|0|613|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|227|0|621|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Read_Multiple_Files.mpc|3|9|Pf|@{0|}}
{30001002|XXparameter|transform||3|8|=|@{0|}}
{30001002|XXparameter|error_group||3|8|=|@{0|}}
{30001002|XXparameter|log_group||3|8|=|@{0|}}
{30001002|XXparameter|reject_threshold||3|8|=|@{0|}}
{30001002|XXparameter|interpret_hadoop_data|True|3|1|l|@{0|}}
{30001002|XXparameter|format|$\{READ_FORMAT\}|3|3|c|@{0|}}
{30001002|XXparameter|select_columns||3|8|=|@{0|}}
{30001002|XXparameter|schema_file||3|8|=|@{0|}}
{30001002|XXparameter|compressed|$COMPRESSED|3|9||@{0|}}
{30001002|XXparameter|logging||3|8|=|@{0|}}
{30001002|XXparameter|Layout|$[[record kind 67 subkind 87 parts [vector _interp_("$READ_LAYOUT_INTERNAL", "pdl")]]]|3|9||@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 0 datasets NULL]]|3|9||@{0|}}
{30001002|XXparameter|out_metadata||3|8|=|@{0|}}
{30001002|XXparameter|file_missing|Notify (Continue, with a reject record and error message)|3|1|l|@{0|}}
{30001002|XXparameter|file_unavailable|Notify (Continue, with a reject record and error message)|3|1|l|@{0|}}
}}@1|@445000|68000|0|0|0|0|4014|Read Blocks|||1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|228|0|623|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|229|0|625|0|{@{}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|230|0|627|0|{@{}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|231|0|629|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|232|0|631|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|233|0|633|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|234|0|635|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|235|0|638|0|{Sequentially reads from a list of input files.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|readfiles|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/readfiles|3|2|H$||{0|}}
{30001002|XXparameter|transform||8|1|RFOl|Package containing transforms and data types|{0|}}
{30001002|XXparameter|filter|None (Read all records)|15|1|Fl|Limits the number of records read from each file|{2|None (Read all records)|Range (Read a subset of records from each file)|}}
{30001002|XXparameter|skip_count|0|1|2|FK$|Number of initial records to skip|{0|}}
{30001002|XXparameter|skip_count.display_name|skip-count|3|9|P|@{0|}}
{30001002|XXparameter|skip_count.keyword|skip-count|3|9|P|@{0|}}
{30001002|XXparameter|skip_count.condition|param filter Range*|3|15|P?|@{0|}}
{30001002|XXparameter|read_count|0|1|2|FK$|Number of records to read from each file|{0|}}
{30001002|XXparameter|read_count.display_name|read-count|3|9|P|@{0|}}
{30001002|XXparameter|read_count.keyword|read-count|3|9|P|@{0|}}
{30001002|XXparameter|read_count.condition|param filter Range*|3|15|P?|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if the reformat transform rejects records read from input files|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|file_empty|Ignore (continue with no reject or error)|15|1|Fl|What to do if an input file is empty|{4|Fail (Stop processing)|Notify (Continue, with a reject record and error message)|Ignore (continue with no reject or error)|Accept (If reading as single record, produce length-only record with no data)|}}
{30001002|XXparameter|file_empty.display_name|file-empty|3|9|P|@{0|}}
{30001002|XXparameter|file_empty.condition|version 2.11.8.m11:|3|15|P?|@{0|}}
{30001002|XXparameter|file_empty_keyword|value file-empty F* Fail value file-empty N* Notify value file-empty I* Ignore value file-empty A* Accept default dollar_substitution Ignore|3|13|Kv|What to do if an input file is missing|{0|}}
{30001002|XXparameter|file_empty_keyword.condition|version 2.11.8.m11:|3|15|P?|@{0|}}
{30001002|XXparameter|file_missing|Fail (Stop processing)|15|1|Fl|What to do if an input file is missing|{3|Fail (Stop processing)|Notify (Continue, with a reject record and error message)|Ignore (continue with no reject or error)|}}
{30001002|XXparameter|file_missing.display_name|file-missing|3|9|P|@{0|}}
{30001002|XXparameter|file_missing.condition|version 2.11.8.m11:|3|15|P?|@{0|}}
{30001002|XXparameter|file_missing_keyword|value file-missing F* Fail value file-missing N* Notify value file-missing I* Ignore default dollar_substitution Fail|3|13|Kv|What to do if an input file is missing|{0|}}
{30001002|XXparameter|file_missing_keyword.condition|version 2.11.8.m11:|3|15|P?|@{0|}}
{30001002|XXparameter|file_unavailable|Fail (Stop processing)|15|1|Fl|What to do if the input file is not readable or is otherwise unavailable|{3|Fail (Stop processing)|Notify (Continue, with a reject record and error message)|Ignore (continue with no reject or error)|}}
{30001002|XXparameter|file_unavailable.display_name|file-unavailable|3|9|P|@{0|}}
{30001002|XXparameter|file_unavailable_keyword|value file-unavailable F* Fail value file-unavailable N* Notify value file-unavailable I* Ignore value file-unavailable A* Accept default dollar_substitution Fail|3|13|Kv|What to do if the input file is not readable or is otherwise unavailable|{0|}}
{30001002|XXparameter|filename_error|Fail (Stop processing)|15|1|Fl|What to do with an input record when get_filename() fails|{3|Fail (Stop processing)|Notify (Continue, with a reject record and error message)|Ignore (continue with no reject or error)|}}
{30001002|XXparameter|filename_error.display_name|filename-error|3|9|P|@{0|}}
{30001002|XXparameter|filename_error.condition|version 2.11.8.m11:|3|15|P?|@{0|}}
{30001002|XXparameter|filename_error_keyword|value filename-error F* Fail value filename-error N* Notify value filename-error I* Ignore default dollar_substitution Fail|3|13|Kv|What to do if an input file is missing|{0|}}
{30001002|XXparameter|filename_error_keyword.condition|version 2.11.8.m11:|3|15|P?|@{0|}}
{30001002|XXparameter|input_error|Fail (Stop processing)|15|1|Fl|What to do in case of error reading an input file|{3|Fail (Stop processing)|Notify (Continue, with a reject record and error message)|Ignore (continue with no reject or error)|}}
{30001002|XXparameter|input_error.display_name|input-error|3|9|P|@{0|}}
{30001002|XXparameter|input_error.condition|version 2.14.70:|3|15|P?|@{0|}}
{30001002|XXparameter|input_error_keyword|value input-error F* Fail value input-error N* Notify value input-error I* Ignore default dollar_substitution Fail|3|13|Kv|What to do in case of error reading an input file|{0|}}
{30001002|XXparameter|input_error_keyword.condition|version 2.14.70:|3|15|P?|@{0|}}
{30001002|XXparameter|stream_raw_data|False|13|1|FKl|If True, streams raw data from input files|{0|}}
{30001002|XXparameter|stream_raw_data.condition|version 3.2.1.r10.0:|3|15|P?|@{0|}}
{30001002|XXparameter|interpret_hadoop_data|False|13|1|Fl|If true, component will interpret data according to the selected Hadoop file format.|{0|}}
{30001002|XXparameter|interpret_hadoop_data.condition|version 3.2.2.r15.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|The input file format: 'uninterpreted' (read raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'rcfile' (RCFile format), 'avro' (Avro format), 'texttable' (Hive text table).|{7|uninterpreted|seqfile|parquet|orc|rcfile|avro|texttable|}}
{30001002|XXparameter|format.condition|param_exact interpret_hadoop_data True param_exact stream_raw_data False version 3.2.2.r15.0:|3|15|P?|@{0|}}
{30001002|XXparameter|select_columns_condition|value format rcfile True value format * False default constant False|13|13|v|Hidden condition for deciding select-columns visibility|{0|}}
{30001002|XXparameter|select_columns||3|2|FK$|A comma-separated list of column number to read from RC File. Column numbers are zero-based.|{0|}}
{30001002|XXparameter|select_columns.display_name|select-columns|3|9|P|@{0|}}
{30001002|XXparameter|select_columns.keyword|select-columns|3|9|P|@{0|}}
{30001002|XXparameter|select_columns.condition|param select_columns_condition True|3|15|P?|@{0|}}
{30001002|XXparameter|schema_file||3|2|FK$|Location of schema file for reading avro files, prefix with file: or hdfs:. If not specified, data will be read using the schema in the data file.|{0|}}
{30001002|XXparameter|schema_file.display_name|schema-file|3|9|P|@{0|}}
{30001002|XXparameter|schema_file.keyword|schema-file|3|9|P|@{0|}}
{30001002|XXparameter|schema_file.condition|param format avro|3|15|P?|@{0|}}
{30001002|XXparameter|compressed|False|13|1|FKl|If True, reads compressed input files|{0|}}
{30001002|XXparameter|compressed.condition|param_exact stream_raw_data False param_exact format uninterpreted version 2.12.2.m1:|3|15|P?|@{0|}}
{30001002|XXparameter|read_as_single_record|False|13|1|FKl|If True, reads each file as one record, adding an initial 8-byte size|{0|}}
{30001002|XXparameter|read_as_single_record.condition|param_exact stream_raw_data False param_exact read-blocks False param_exact format uninterpreted version 2.12.2.m5:|3|15|P?|@{0|}}
{30001002|XXparameter|read_blocks|False|13|1|FKl|If True, reads each file as a series of blocks, adding an initial 8-byte size to each block|{0|}}
{30001002|XXparameter|read_blocks.display_name|read-blocks|3|9|P|@{0|}}
{30001002|XXparameter|read_blocks.keyword|read-blocks|3|9|P|@{0|}}
{30001002|XXparameter|read_blocks.condition|param_exact stream_raw_data False param_exact read_as_single_record False param_exact format uninterpreted version 2.14.25:|3|15|P?|@{0|}}
{30001002|XXparameter|maximum_block_bytes|-1|1|2|FK$|Block size when read-blocks is True. A value of -1 reads the entire file.|{0|}}
{30001002|XXparameter|maximum_block_bytes.display_name|maximum-block-bytes|3|9|P|@{0|}}
{30001002|XXparameter|maximum_block_bytes.keyword|maximum-block-bytes|3|9|P|@{0|}}
{30001002|XXparameter|maximum_block_bytes.condition|param_exact read-blocks True version 2.14.25:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp file_empty_keyword file-empty file_missing_keyword file-missing file_unavailable_keyword file-unavailable filename_error_keyword filename-error input_error_keyword input-error|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_intermediate||15|1|Fl|Frequency of intermediate records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_intermediate.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_variables|1|1|2|H$|Number of data types in package|{0|}}
{30001002|XXparameter|variable1|optional input_type read <parameter out_metadata>|3|2|H$|Metadata for records read from input files|{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|filename_type filename "string('')"|3|2|H$|Metadata for get_filename result|{0|}}
{30001002|XXparameter|num_operations|9|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|filename::get_filename(in)|3|2|H$|extract filename from input record|{0|}}
{30001002|XXparameter|operation2|optional out::finished(read, filename, in)|3|2|H$|Check if done reading file|{0|}}
{30001002|XXparameter|operation2_analysis|optional long finished_out::finished(read, filename, in)|3|2|H$|Check if done reading file|{0|}}
{30001002|XXparameter|operation3|optional out::reformat(read, filename, in)|3|2|H$|Create output record|{0|}}
{30001002|XXparameter|operation3_analysis|optional out::reformat(read, filename, in optional)|3|2|H$||{0|}}
{30001002|XXparameter|operation4|optional read::repair_input(void(integer(4)) rawbytes, filename)|3|2|H$|Repair malformed input record from file|{0|}}
{30001002|XXparameter|type1_analysis|filename_type filename "string('')"|3|2|H$||{0|}}
{30001002|XXparameter|variable1_analysis|optional input_type read <parameter out_metadata>|3|2|H$||{0|}}
{30001002|XXparameter|port_analysis|reject=^read ; out=^read; filereject=in|3|2|H$||{0|}}
{30001002|XXparameter|dataset_analysis|eme_dataset(file)=read,r|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|type2|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation5|optional out::output_for_error(error_info, read)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation6|optional error::make_error(error_info, read)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation7|optional log_event::log_error(error_info, read)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation8|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation9|optional integer(8) out::output_select(out)|3|2|H$|Select output record.|{0|}}
{30001002|XXparameter|operation9.condition|version 3.2.1.r10.0:|3|15|P?|@{0|}}
{30001002|XXparameter|operation9_analysis|integer(8) output_select_out::output_select(out)|3|2|H$|Select output record.|{0|}}
{30001002|XXparameter|operation9_analysis.condition|version 3.2.1.r10.0:|3|15|P?|@{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|9|RFs||{0|}}
{30001002|XXparameter|eme_dataset_mapping|@40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|filereject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|fileerror_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,filereject,fileerror,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1473966398|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: filereject = in
metadata type: fileerror = remote("$AB_HOME/include/error-info.dml")
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|@15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|_ab_semantic_schema|6|1|1|Hnl|@{0|}}
}}@0|Read Multiple Files|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|236|0|640|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|237|0|643|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|238|0|646|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|239|0|649|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|240|0|652|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|241|0|655|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|242|0|658|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|243|0|669|0|{@{}@0|0|0|0|out0|.5117370892018779|@@@14352|0|}}
{2010202004|XXGiport|244|0|672|0|{@{}@0|0|0|0|in0|.5044642857142857|@@@13840|0|}}
{2010600005|XXGgraph|245|0|691|0|{Subgraph created from graph "Read_Hive_Table"|{}@0|@39500|98500|0|0|0|0|4024|Validate HIVE_LAYOUT|Ab Initio|@1|100|-1|@9|@32769|{0|}0|0|{0|}{0|}{0|}{0|}1.0|298000|184000|2|}}
{2010210004|XXGflow|246|0|693|0|{@{}@0|.5|.5|{0|}4059|17|}}
{2010501005|XXGpvertex|247|0|695|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Validate/Create_Data.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|transform|let x = if (number_of_partitions() > 1) force_abort("HIVE_LAYOUT must be serial. (Input value: " + $"HIVE_LAYOUT" + ")") else 0;

out::create(index) = begin
  out :: 0;
end;|3|9||@{0|}}
{30001002|XXparameter|num_records|0|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|int;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|=|@{0|}}
}}@1|Create Data|66000|85000|0|0|0|0|4060|Perform Validation|Ab Initio Software|Built-in 2.15.2:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|248|0|697|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|249|0|700|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|250|0|702|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|251|0|704|0|{Creates records according to a transform.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|Create_Data|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|num_records||1|2|RFO$|Number of records to generate|{0|}}
{30001002|XXparameter|num_records.display_name|num-records|3|9|P|@{0|}}
{30001002|XXparameter|transform|out::create(index) = begin
  out :: random_value();
end;|8|1|FOl|DML function|{0|}}
{30001002|XXparameter|identical_records|False|13|1|FKl|Whether to evaluate the transform once only, or once for each record|{0|}}
{30001002|XXparameter|identical_records.display_name|identical-records|3|9|P|@{0|}}
{30001002|XXparameter|identical_records.keyword|identical-records|3|9|P|@{0|}}
{30001002|XXparameter|identical_records_display_values|Evaluatetransformanewforeachrecord Evaluatetransformonceandusethatvalueforallrecords|3|2|H$||{0|}}
{30001002|XXparameter|identical_records_display_values.display_name|identical-records-display-values|3|9|P|@{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|1|1|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_checkpoint|0|15|1|RFKl|Frequency of checkpoint records to log|{2|0|1|}}
{30001002|XXparameter|log_checkpoint.condition|version 3.0.4.r17: param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_checkpoint.update_clauses|update_value 1|3|9|P|@{0|}}
{30001002|XXparameter|log_computepoint|0|15|1|RFKl|Frequency of computepoint records to log|{2|0|1|}}
{30001002|XXparameter|log_computepoint.condition|version 3.0.4.r17: param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_computepoint.update_clauses|update_value 1|3|9|P|@{0|}}
{30001002|XXparameter|continuous|False|13|1|RFOl|Whether to produce checkpoints or computepoints.|{0|}}
{30001002|XXparameter|checkpoint_interval|1|1|2|FO$|Number of records between checkpoints, or 0 to indicate that no checkpoints are to be generated.|{0|}}
{30001002|XXparameter|checkpoint_interval.display_name|checkpoint-interval|3|9|P|@{0|}}
{30001002|XXparameter|checkpoint_interval.condition|param continuous True|3|15|P?|@{0|}}
{30001002|XXparameter|computepoint_interval|0|1|2|FO$|Number of records between computepoints, or 0 to indicate that no computepoints are to be generated.|{0|}}
{30001002|XXparameter|computepoint_interval.display_name|computepoint-interval|3|9|P|@{0|}}
{30001002|XXparameter|computepoint_interval.condition|param continuous True|3|15|P?|@{0|}}
{30001002|XXparameter|do_timed_checkpoints|False|13|1|FKl|Generate checkpoints at timed intervals|{0|}}
{30001002|XXparameter|do_timed_checkpoints.display_name|do-timed-checkpoints|3|9|P|@{0|}}
{30001002|XXparameter|do_timed_checkpoints.keyword|do-timed-checkpoints|3|9|P|@{0|}}
{30001002|XXparameter|do_timed_checkpoints.condition|param continuous True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|5|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::create(unsigned long index)|3|2|H$|Function taking integer index counting 1,2,3,4... to produce records on the output.|{0|}}
{30001002|XXparameter|continuous_analysis|continuous ? subscriber :|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,error,log::document()|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1500578697|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
}}@0|Create Data|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|252|0|706|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|253|0|709|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|254|0|712|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|255|0|716|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Trash.mpc|3|2|Pf$|@{0|}}
}}@1|Trash|171000|80000|0|0|0|0|4058|Trash|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010202004|XXGiport|256|0|718|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|257|0|721|0|{Ends a flow by discarding all input data records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|continuous_analysis|broadcast, publisher, fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1500578696|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Trash|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010202004|XXGiport|258|0|723|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|259|0|726|0|{@{}@0|0|0|0|out0|.6354916067146283|@@@14352|0|}}
{2010501005|XXGpvertex|260|0|729|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Replicate.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Replicate|606000|250000|0|0|0|0|5559|Replicate|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|261|0|731|0|{@{}@0|0|0|0|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|262|0|735|0|{@{}@0|0|0|0|in|0.0|@@@1812|0|}}
{2010501005|XXGpvertex|263|0|738|0|{Arbitrarily combines all the data records it receives into a single flow and writes a copy of that flow to each of its output flows.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|NoHidePorts|in out|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=exact(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|broadcast, publisher|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1639787119|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Replicate|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|264|0|740|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|265|0|743|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1812|0|}}
{2010600005|XXGgraph|266|0|749|0|{Subgraph created from graph "BIG_SCORES_TABLE_EXTRACT"|{}@0|@1076000|560000|0|0|0|0|5607|Risk_scores Rejected|lc80582|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|278000|458000|7|}}
{2010503005|XXGfvertex|267|0|751|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL_LOG/bcs_risk_scores_rej_$\{FILE_DATE\}.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL_LOG/bcs_risk_scores_rej_$\{FILE_DATE\}.dat|3|2|$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
}}@2|Output File|38000|218000|0|0|0|0|4540|bcs_risk_rej|Ab Initio Software|@1|100|0||6||32897|-1|-1|}}
{2010202004|XXGiport|268|0|753|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|269|0|755|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|create_directories|False|13|1|FKl|If True, create any parent directories as necessary|{0|}}
{30001002|XXparameter|create_directories.display_name|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.keyword|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.condition|version 4.1.1.r9.0:|3|15|P?|@{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table), 'hadoop_compressed' (Compressed raw data).|{7|uninterpreted|seqfile|parquet|orc|avro|texttable|hadoop_compressed|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZOP\}, hadoop_compressed=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO,LZOP\}|{9|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|LZOP|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|write_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1675912808|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Output File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|270|0|757|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|271|0|760|0|{Add all functionality about RISK_MODEL string to convert to a vector.
add a new |{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|transform0|out::reformat(in)=
begin
//let string("\|")[int] risk=string_split(string_replace(string_replace(string_replace_first(string_replace(string_filter_out(in.risk_score,"[\{\}\}]"),'"DISTRIBUTION_MEASURES":',''),'"',''),'":',':'),',"',','),',');
//let string("\|")[int] cus_seg=string_split(string_replace(string_replace(string_replace_first(string_replace(string_filter_out(in.customer_segments,"[\{\}\}]"),'"$date": ',''),'"',''),'":',':'),',"',','),',');

let string("\|")[int] risk=string_split(string_filter_out(string_replace(string_replace(string_filter_out(in.risk_scores,"[\{\}\}]"),'"$numberDecimal":',''),'"$date":',' '),'"/'),',');
let string("\|")[int] cus_seg=string_split(string_filter_out(string_replace(string_filter_out(in.customer_segments,"[\{\}\}]"),'"$date":',' '),'"/'),',');

let string("\|")[int] customer_seg =string_split(cus_seg[0],":");
let string("\|")[int] customer_seg_dt =string_split(string_filter_out(cus_seg[1],"Z"),": ");

let record
utf8 string(int) customer_seg = NULL;
datetime("YYYY-MM-DD-HH24.MI.SS.NNN") customer_seg_dt = NULL;
end[int] CUSTOMER_SEGMENTS = NULL;

CUSTOMER_SEGMENTS=[vector [record customer_seg customer_seg[1],customer_seg_dt (datetime("YYYY-MM-DD-HH24:MI:SS.NNN"))(datetime("YYYY-MM-DDTHH24:MI:SS")) customer_seg_dt[1]]];

out.customer_id :: in.customer_id;
out.model_id :: in.model_id;
out.RISK_SCORES1 :: in.risk_scores;
out.CUSTOMER_SEGMENTS :: CUSTOMER_SEGMENTS;
out.last_updated_date:: (date("YYYY-MM-DD")) (string("\|")) in.last_updated_date;
out.length_risk_scores :: if( in.model_id == "P2986" )length_of(risk)/4
                          else length_of(risk)/8;
out.score_model_tp :: in.model_type_execution;

end;|3|1|l|@{0|}}
{30001002|XXparameter|out0_metadata|$AI_DML/adif_rftm_cus_seg_func_out.dml|3|2|f$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_threshold|Never abort|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@2|Reformat|887000|370500|0|0|0|0|5630|cust_seg func|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|272|0|762|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|273|0|765|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|274|0|768|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|275|0|770|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|276|0|772|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|277|0|775|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|1|1|1|Fl|Number of reformat transforms|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform0||8|1|FOl|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
{30001002|XXparameter|select||20|2|FK$|Filter expression before reformatting|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|output_index||8|1|FKl|Output index computation|{0|}}
{30001002|XXparameter|output_index.display_name|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index.keyword|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_index_port.display_name|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port.keyword|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_signature|int output_index_out::output_index(in)|3|2|H$|Function returning index of output port|{0|}}
{30001002|XXparameter|output_index_signature.display_name|output-index_signature|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes||8|1|FKl|Output index vector computation|{0|}}
{30001002|XXparameter|output_indexes.display_name|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes.keyword|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_indexes_port.display_name|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port.keyword|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_signature|int[int] output_indexes_out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
{30001002|XXparameter|output_indexes_signature.display_name|output-indexes_signature|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|7|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|legacy_xfr;reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|event_info_t event_info "record int event_type; end"|3|2|H$|Information about the kind of event that happened|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional out::output_at_event(event_info)|3|2|H$|Function to allow the output of an additional record at event|{0|}}
{30001002|XXparameter|operation7|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|6|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1639787121|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Reformat|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|278|0|777|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|279|0|781|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|280|0|784|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|281|0|787|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|282|0|790|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010503005|XXGfvertex|283|0|796|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL_LOG/neuro_risk_scores_rej_$\{FILE_DATE\}.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL_LOG/neuro_risk_scores_rej_$\{FILE_DATE\}.dat|3|2|$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
}}@2|Output File|178000|218000|0|0|0|0|4537|neuro_rej|Ab Initio Software|@1|10000|0||6||33153|-1|-1|}}
{2010202004|XXGiport|284|0|798|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|285|0|800|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|create_directories|False|13|1|FKl|If True, create any parent directories as necessary|{0|}}
{30001002|XXparameter|create_directories.display_name|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.keyword|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.condition|version 4.1.1.r9.0:|3|15|P?|@{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table), 'hadoop_compressed' (Compressed raw data).|{7|uninterpreted|seqfile|parquet|orc|avro|texttable|hadoop_compressed|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZOP\}, hadoop_compressed=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO,LZOP\}|{9|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|LZOP|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|write_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1675912808|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Output File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|286|0|802|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010202004|XXGiport|287|0|806|0|{@{}@0|0|0|0|in0|.1474820143884892|@@@12816|0|}}
{2010202004|XXGiport|288|0|810|0|{@{}@0|0|0|0|in1|.7517985611510791|@@@12816|0|}}
{2010501005|XXGpvertex|289|0|814|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Sort/Sort.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|key|\{last_updated_date descending\}|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Sort|316000|210000|0|0|0|0|5551|Sort \{last_update_date desc\}|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|290|0|816|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|291|0|819|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|292|0|822|0|{Orders your data according to a key specifier.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-sort|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field to sort on|{0|}}
{30001002|XXparameter|max_core|100663296|1|2|FK$|maximum memory usage (before spilling to disk) in bytes|{0|}}
{30001002|XXparameter|max_core.display_name|max-core|3|9|P|@{0|}}
{30001002|XXparameter|max_core.keyword|max-core|3|9|P|@{0|}}
{30001002|XXparameter|max_core.update_clauses|retain_old_default|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1639787120|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Sort|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|293|0|824|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|294|0|827|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|295|0|833|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Database/Mongo/Update_Mongo_DB.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|DBConfigFile|$\{MONGO_DBCFILE\}|3|3|fc|@{0|}}
{30001002|XXparameter|collection|$\{COLLECTION\}|3|3|c|@{0|}}
{30001002|XXparameter|verify_dml|False|3|1|l|@{0|}}
{30001002|XXparameter|unordered|True|3|1|l|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@2|Update Mongo|1576000|245000|0|0|0|0|5634|Update Mongo bcs|Ab Initio Software|Built-in 3.2.1.r10:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|296|0|835|0|{@{}@0|0|0|0|out|0.0|@@@2192|0|}}
{2010203004|XXGoport|297|0|837|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|298|0|839|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|299|0|841|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|300|0|843|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|301|0|846|0|{Modifies records in a Mongo database via inserts, updates, or removes|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|db-mongo-update|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/db_v2/bin/db-mongo-update|3|2|H$||{0|}}
{30001002|XXparameter|DBConfigFile||22|2|RFOf$|Database Description File|{0|}}
{30001002|XXparameter|transform||8|1|FKl|DML Package containing transforms and data types|{0|}}
{30001002|XXparameter|transform.condition|version 4.1.5.r25:|3|15|P?|@{0|}}
{30001002|XXparameter|collection||24|3|RFKc|Mongo collection name|{0|}}
{30001002|XXparameter|update_method|insert|15|1|RFKl|.insert() .update() or ,remove()|{3|insert|update|remove|}}
{30001002|XXparameter|show_query|value update_method update True value update_method remove True default constant False|13|13|v||{0|}}
{30001002|XXparameter|criteria||3|1|FKl|Selection criteria for update|{0|}}
{30001002|XXparameter|criteria.condition|param_exact show_query True|3|15|P?|@{0|}}
{30001002|XXparameter|update||3|1|FKl|Modifications to apply|{0|}}
{30001002|XXparameter|update.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|upsert|False|13|1|FKl|Upsert parameter|{0|}}
{30001002|XXparameter|upsert.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|multi|False|13|1|FKl|True will update all documents matched by the selection criteria; False will update only one|{0|}}
{30001002|XXparameter|multi.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|justOne|False|13|1|FKl|False will remove all documents matched by the selection criteria; True will remove only one|{0|}}
{30001002|XXparameter|justOne.condition|param_exact update_method remove|3|15|P?|@{0|}}
{30001002|XXparameter|batch_update|value update_method insert False value update_method remove False value multi False True default constant False|13|13|v||{0|}}
{30001002|XXparameter|batch_remove|value update_method insert False value update_method update False value justOne False True default constant False|13|13|v||{0|}}
{30001002|XXparameter|enable_batch|value update_method insert True value batch_update True True value batch_remove True True default constant False|13|13|v||{0|}}
{30001002|XXparameter|batch|0|1|2|RFK$|Number of records to submit in batch|{0|}}
{30001002|XXparameter|batch.condition|param_exact enable_batch True|3|15|P?|@{0|}}
{30001002|XXparameter|unordered|False|13|1|FKl|True will submit documents unordered to Mongo if batch is greater than 0|{0|}}
{30001002|XXparameter|unordered.condition|param_exact enable_batch True version 3.2.7.2:|3|15|P?|@{0|}}
{30001002|XXparameter|json_input|False|13|1|RFKl|Upload documents to Mongo using JSON strings|{0|}}
{30001002|XXparameter|json_input.condition|version 3.3.5.r16:|3|15|P?|@{0|}}
{30001002|XXparameter|json_field||3|2|RFK$|Name of the field in the input record containing the JSON document to be uploaded|{0|}}
{30001002|XXparameter|json_field.condition|param_exact json_input True version 3.3.5.r16:|3|15|P?|@{0|}}
{30001002|XXparameter|verify_dml|True|13|1|FKl|Validate the in port DML against an existing Mongo record|{0|}}
{30001002|XXparameter|verify_dml.condition|param_exact update_method insert param_exact json_input False|3|15|P?|@{0|}}
{30001002|XXparameter|insert_null|True|13|1|FKl|True will insert NULL fields and vectors as null elements; False will skip those elements in the document|{0|}}
{30001002|XXparameter|insert_null.condition|param_exact json_input False version 3.2.3.r18:|3|15|P?|@{0|}}
{30001002|XXparameter|nullable_subrecords|True|13|1|FKl|True will treat NULL subrecords as null fields; False will process nested fields within the NULL subrecord as if they are individually NULL|{0|}}
{30001002|XXparameter|nullable_subrecords.condition|param_exact json_input False version 4.1.1.r9:|3|15|P?|@{0|}}
{30001002|XXparameter|continuous|False|13|1|RFKl|Enable component for Continuous>Flows operation|{0|}}
{30001002|XXparameter|commitTable||24|3|FKc|Collection in which to store commit progress|{0|}}
{30001002|XXparameter|transaction_group||3|2|FK$|Name of the transaction group for participation in a shared transaction. Graph folding must be enabled.|{0|}}
{30001002|XXparameter|transaction_group.condition|version 4.0.0.r1:|3|15|P?|@{0|}}
{30001002|XXparameter|use_field_level_encryption|False|13|1|RFKl|Enable client-side field level encryption.|{0|}}
{30001002|XXparameter|use_field_level_encryption.condition|version 4.1.2.r12:|3|15|P?|@{0|}}
{30001002|XXparameter|schema_map||3|2|FK$|JSON schema map for specifying local automatic encryption rules.|{0|}}
{30001002|XXparameter|schema_map.condition|param_exact use_field_level_encryption True version 4.1.2.r12:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|use_leading_checkpoint|value commitTable '' False value commitTable * True default constant False|13|13|v||{0|}}
{30001002|XXparameter|leadchkpt|-__ab__leading-checkpoint__ab__|3|2|O$||{0|}}
{30001002|XXparameter|leadchkpt.condition|param continuous False param use_leading_checkpoint True|3|15|P?|@{0|}}
{30001002|XXparameter|gendml_param_names|collection projection|3|2|$||{0|}}
{30001002|XXparameter|_ab_gendmlports|in|3|2|$|Port supports automatic metadata generation|{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|num_operations|5|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|kms_credentials_t kms_credentials "record string(int) kms_providers; datetime('YYYY-MM-DDTHH24:MI:SS-zo:ne') expiration = NULL; end"|3|2|H$|Type of kms_credentials|{0|}}
{30001002|XXparameter|operation1|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation5|optional kms_credentials::retrieve_kms_credentials()|3|2|H$|Optional provision of KMS credentials for CS-FLE|{0|}}
{30001002|XXparameter|operation5_analysis|optional kms_credentials::retrieve_kms_credentials()|3|2|H$|Optional provision of KMS credentials for CS-FLE|{0|}}
{30001002|XXparameter|override_mpname|value continuous True db-mongo-update-continuous value continuous False db-mongo-update|3|13|v||{0|}}
{30001002|XXparameter|override_mpname.display_name|override-mpname|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in; out=in|3|2|H$||{0|}}
{30001002|XXparameter|eme_dataset_mapping|@40|9|F|Location in which to create a dataset corresponding to this component.|{0|}}
{30001002|XXparameter|dataset_analysis|eme_dataset_mapping(table)=in,w|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|continuous ? nobatch,publisher : not_enabled|3|2|H$||{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912808|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|@15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
}}@0|Update Mongo|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|302|0|848|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|out|0.0|@@@2192|0|}}
{2010203004|XXGoport|303|0|851|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|304|0|854|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|305|0|857|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|306|0|860|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|307|0|864|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out0_metadata|$AI_DML/adif_mongo_big_collection_scores.dml|3|2|f$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@2|Reformat|1356000|237000|0|0|0|0|5592|rfm dml mongo bcs|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|308|0|866|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|309|0|869|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|310|0|871|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|311|0|873|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|312|0|875|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|313|0|878|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|1|1|1|Fl|Number of reformat transforms|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform0||8|1|FOl|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
{30001002|XXparameter|select||20|2|FK$|Filter expression before reformatting|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|output_index||8|1|FKl|Output index computation|{0|}}
{30001002|XXparameter|output_index.display_name|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index.keyword|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_index_port.display_name|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port.keyword|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_signature|int output_index_out::output_index(in)|3|2|H$|Function returning index of output port|{0|}}
{30001002|XXparameter|output_index_signature.display_name|output-index_signature|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes||8|1|FKl|Output index vector computation|{0|}}
{30001002|XXparameter|output_indexes.display_name|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes.keyword|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_indexes_port.display_name|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port.keyword|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_signature|int[int] output_indexes_out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
{30001002|XXparameter|output_indexes_signature.display_name|output-indexes_signature|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|7|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|legacy_xfr;reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|event_info_t event_info "record int event_type; end"|3|2|H$|Information about the kind of event that happened|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional out::output_at_event(event_info)|3|2|H$|Function to allow the output of an additional record at event|{0|}}
{30001002|XXparameter|operation7|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|6|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Reformat|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|314|0|880|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|315|0|884|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|316|0|887|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|317|0|890|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|318|0|893|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|319|0|897|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|transform1|/*Reformat operation*/


out::reformat(in)=
begin

let string("\|")[int] risk=string_split(string_filter_out(string_replace(string_replace(string_filter_out(in.RISK_SCORES1,"[\{\}\}]"),'"$numberDecimal":',''),'"$date":',' '),'"/'),',');


let decimal("\|", allow_exponent)[int] score =allocate();
let string("\|")[int] score_info_dt =allocate();
let string("\|")[int] score_name =allocate();
let string("\|")[int] score_process_dt =allocate();
let decimal("\|", allow_exponent) score_final = allocate();
let little endian integer(1) credit_flag= allocate();

let decimal(10) risk_length = length_of(risk);
let decimal(10) risk_index=0;
let decimal(10) count_bucle=risk_length/4;
let decimal(3) length_risk_scores = in.length_risk_scores-1;

let decimal(2) i=allocate();

let record
    
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) score = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_info_dt = NULL;
    utf8 string(int) score_name = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_process_dt = NULL;
end[100] RISK_SCORES=allocate();

   i=0;
  for(i, i<count_bucle)
  begin       
  
    score =string_split(risk[risk_index],":");
    score_info_dt =string_split(string_filter_out(risk[risk_index+1],"Z"),": ");
    score_name =string_split(risk[risk_index+2],":");
    score_process_dt =string_split(string_filter_out(risk[risk_index+3],"Z"),": ");
    score_final = if((string("\|")) score[1] =='') NULL else score[1];
    

    RISK_SCORES[i].score = score_final;
    RISK_SCORES[i].score_info_dt = (datetime("YYYY-MM-DD-HH24:MI:SS.NNN"))(datetime("YYYY-MM-DDTHH24:MI:SS")) score_info_dt[1];
    RISK_SCORES[i].score_name = score_name[1];
    RISK_SCORES[i].score_process_dt = (datetime("YYYY-MM-DD-HH24:MI:SS.NNN"))(datetime("YYYY-MM-DDTHH24:MI:SS")) score_process_dt[1];
      
    risk_index = risk_index+4;
  end
  
out.RISK_SCORES :: vector_slice(RISK_SCORES,0,length_risk_scores);

out.* :: in.*;

end;|3|1|l|@{0|}}
{30001002|XXparameter|transform0|/*Reformat operation*/


out::reformat(in)=
begin

let string("\|")[int] risk=string_split(string_filter_out(string_replace(string_replace(string_filter_out(in.RISK_SCORES1,"[\{\}\}]"),'"$numberDecimal":',''),'"$date":',' '),'"/'),',');

let string("\|")[int] credit_approved_dt =allocate();
let string("\|")[int] credit_approved_flag =allocate();
let decimal("\|", allow_exponent)[int] credit_score_decile_val =allocate();
let decimal("\|", allow_exponent)[int] credit_score_quartile_val =allocate();
let decimal("\|", allow_exponent)[int] score =allocate();
let string("\|")[int] score_info_dt =allocate();
let string("\|")[int] score_name =allocate();
let string("\|")[int] score_process_dt =allocate();
let decimal("\|", allow_exponent) score_final = allocate();
let little endian integer(1) credit_flag= allocate();

let decimal(10) risk_length = length_of(risk);
let decimal(10) risk_index=0;
let decimal(10) count_bucle=risk_length/8;
let decimal(3) length_risk_scores = in.length_risk_scores-1;

let decimal(2) i=allocate();

let record
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") credit_approved_dt = NULL;
    little endian integer(1) credit_approved_flag= NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) credit_score_decile_val = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) credit_score_quartile_val = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) score = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_info_dt = NULL;
    utf8 string(int) score_name = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_process_dt = NULL;
end[100] RISK_SCORES=allocate();

   i=0;
  for(i, i<count_bucle)
  begin       

    credit_approved_dt =string_split(string_filter_out(risk[risk_index],"Z"),": ");
    credit_approved_flag =string_split(risk[risk_index+1],":");
    credit_score_decile_val =string_split(risk[risk_index+2],":");
    credit_score_quartile_val =string_split(risk[risk_index+3],":");
    score =string_split(risk[risk_index+4],":");
    score_info_dt =string_split(string_filter_out(risk[risk_index+5],"Z"),": ");
    score_name =string_split(risk[risk_index+6],":");
    score_process_dt =string_split(string_filter_out(risk[risk_index+7],"Z"),": ");
    credit_flag= if(credit_approved_flag[1]=='true') 1 else 0;
    score_final = if((string("\|")) score[1] =='') NULL else score[1];
    
    RISK_SCORES[i].credit_approved_dt = (datetime("YYYY-MM-DD-HH24:MI:SS.NNN"))(datetime("YYYY-MM-DDTHH24:MI:SS")) credit_approved_dt[1];
    RISK_SCORES[i].credit_approved_flag = credit_flag;
    RISK_SCORES[i].credit_score_decile_val = credit_score_decile_val[1];
    RISK_SCORES[i].credit_score_quartile_val = credit_score_quartile_val[1];
    RISK_SCORES[i].score = score_final;
    RISK_SCORES[i].score_info_dt = (datetime("YYYY-MM-DD-HH24:MI:SS.NNN"))(datetime("YYYY-MM-DDTHH24:MI:SS")) score_info_dt[1];
    RISK_SCORES[i].score_name = score_name[1];
    RISK_SCORES[i].score_process_dt = (datetime("YYYY-MM-DD-HH24:MI:SS.NNN"))(datetime("YYYY-MM-DDTHH24:MI:SS")) score_process_dt[1];
      
    risk_index = risk_index+8;
  end
  
  
out.RISK_SCORES :: vector_slice(RISK_SCORES,0,length_risk_scores);

out.* :: in.*;

end;|3|1|l|@{0|}}
{30001002|XXparameter|output_index|/*Function returning index of output port*/
output_index_out::output_index(in)=
begin
output_index_out :: if(in.model_id =="P2986") 1
else 0;
end;



/*
Camelot 	227938	1
Camelot ST	230979	1
PIL Line Taken	231078	32
PIL Response	207274	8
INTL	        222566	1
RPS	        227756	1
LOP Line Taken	184527	12
Neurolands	P2986	6  -> port_1
*/|3|1|l|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject1_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_threshold|Never abort|3|1|l|@{0|}}
{30001002|XXparameter|out0_metadata|$AI_DML/BIG_SCORES_FINAL_FILE.dml|3|2|f$|@{0|}}
{30001002|XXparameter|out1_metadata|$AI_DML/NEURONALS_FINAL_FILE.dml|3|2|f$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@2|Reformat|1063000|370000|0|0|0|0|5612|risk_scores func|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|320|0|899|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|321|0|902|0|{@{}@0|0|0|0|out1|0.0|count|out|1|2448|0|}}
{2010203004|XXGoport|322|0|905|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|323|0|908|0|{@{}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|324|0|911|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|325|0|913|0|{@{}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|326|0|915|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|327|0|917|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|328|0|920|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|2|1|1|Fl|Number of reformat transforms|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform0||8|1|FOl|Reformat transform|{0|}}
{30001002|XXparameter|transform1||8|1|FOl|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
{30001002|XXparameter|select||20|2|FK$|Filter expression before reformatting|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|output_index||8|1|FKl|Output index computation|{0|}}
{30001002|XXparameter|output_index.display_name|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index.keyword|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_index_port.display_name|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port.keyword|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_signature|int output_index_out::output_index(in)|3|2|H$|Function returning index of output port|{0|}}
{30001002|XXparameter|output_index_signature.display_name|output-index_signature|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes||8|1|FKl|Output index vector computation|{0|}}
{30001002|XXparameter|output_indexes.display_name|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes.keyword|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_indexes_port.display_name|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port.keyword|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_signature|int[int] output_indexes_out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
{30001002|XXparameter|output_indexes_signature.display_name|output-indexes_signature|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|7|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|legacy_xfr;reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|event_info_t event_info "record int event_type; end"|3|2|H$|Information about the kind of event that happened|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional out::output_at_event(event_info)|3|2|H$|Function to allow the output of an additional record at event|{0|}}
{30001002|XXparameter|operation7|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|6|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out1_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject1_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|error1_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
{30001002|XXparameter|transform1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|transform1.index_name|transform|3|9|P|@{0|}}
}}@0|Reformat|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|329|0|922|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|330|0|926|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform1||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|transform1.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out1|0.0|count|out|1|2448|0|}}
{2010203004|XXGoport|331|0|930|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|332|0|933|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|333|0|936|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|334|0|939|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|335|0|942|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|336|0|945|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|337|0|955|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Database/Mongo/Update_Mongo_DB.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|DBConfigFile|$MONGO_DBCFILE|3|2|f$|@{0|}}
{30001002|XXparameter|collection|$\{COLLECTION\}|3|3|c|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|@3|9||@{0|}}
{30001002|XXparameter|verify_dml|False|3|1|l|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@3|Update Mongo|1561000|550000|0|0|0|0|5632|Update Mongo neurolands|Ab Initio Software|Built-in 3.2.1.r10:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|338|0|957|0|{@{}@0|0|0|0|out|0.0|@@@2192|0|}}
{2010203004|XXGoport|339|0|959|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|340|0|961|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|341|0|963|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|342|0|965|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|343|0|968|0|{Modifies records in a Mongo database via inserts, updates, or removes|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|db-mongo-update|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/db_v2/bin/db-mongo-update|3|2|H$||{0|}}
{30001002|XXparameter|DBConfigFile||22|2|RFOf$|Database Description File|{0|}}
{30001002|XXparameter|transform||8|1|FKl|DML Package containing transforms and data types|{0|}}
{30001002|XXparameter|transform.condition|version 4.1.5.r25:|3|15|P?|@{0|}}
{30001002|XXparameter|collection||24|3|RFKc|Mongo collection name|{0|}}
{30001002|XXparameter|update_method|insert|15|1|RFKl|.insert() .update() or ,remove()|{3|insert|update|remove|}}
{30001002|XXparameter|show_query|value update_method update True value update_method remove True default constant False|13|13|v||{0|}}
{30001002|XXparameter|criteria||3|1|FKl|Selection criteria for update|{0|}}
{30001002|XXparameter|criteria.condition|param_exact show_query True|3|15|P?|@{0|}}
{30001002|XXparameter|update||3|1|FKl|Modifications to apply|{0|}}
{30001002|XXparameter|update.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|upsert|False|13|1|FKl|Upsert parameter|{0|}}
{30001002|XXparameter|upsert.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|multi|False|13|1|FKl|True will update all documents matched by the selection criteria; False will update only one|{0|}}
{30001002|XXparameter|multi.condition|param_exact update_method update|3|15|P?|@{0|}}
{30001002|XXparameter|justOne|False|13|1|FKl|False will remove all documents matched by the selection criteria; True will remove only one|{0|}}
{30001002|XXparameter|justOne.condition|param_exact update_method remove|3|15|P?|@{0|}}
{30001002|XXparameter|batch_update|value update_method insert False value update_method remove False value multi False True default constant False|13|13|v||{0|}}
{30001002|XXparameter|batch_remove|value update_method insert False value update_method update False value justOne False True default constant False|13|13|v||{0|}}
{30001002|XXparameter|enable_batch|value update_method insert True value batch_update True True value batch_remove True True default constant False|13|13|v||{0|}}
{30001002|XXparameter|batch|0|1|2|RFK$|Number of records to submit in batch|{0|}}
{30001002|XXparameter|batch.condition|param_exact enable_batch True|3|15|P?|@{0|}}
{30001002|XXparameter|unordered|False|13|1|FKl|True will submit documents unordered to Mongo if batch is greater than 0|{0|}}
{30001002|XXparameter|unordered.condition|param_exact enable_batch True version 3.2.7.2:|3|15|P?|@{0|}}
{30001002|XXparameter|json_input|False|13|1|RFKl|Upload documents to Mongo using JSON strings|{0|}}
{30001002|XXparameter|json_input.condition|version 3.3.5.r16:|3|15|P?|@{0|}}
{30001002|XXparameter|json_field||3|2|RFK$|Name of the field in the input record containing the JSON document to be uploaded|{0|}}
{30001002|XXparameter|json_field.condition|param_exact json_input True version 3.3.5.r16:|3|15|P?|@{0|}}
{30001002|XXparameter|verify_dml|True|13|1|FKl|Validate the in port DML against an existing Mongo record|{0|}}
{30001002|XXparameter|verify_dml.condition|param_exact update_method insert param_exact json_input False|3|15|P?|@{0|}}
{30001002|XXparameter|insert_null|True|13|1|FKl|True will insert NULL fields and vectors as null elements; False will skip those elements in the document|{0|}}
{30001002|XXparameter|insert_null.condition|param_exact json_input False version 3.2.3.r18:|3|15|P?|@{0|}}
{30001002|XXparameter|nullable_subrecords|True|13|1|FKl|True will treat NULL subrecords as null fields; False will process nested fields within the NULL subrecord as if they are individually NULL|{0|}}
{30001002|XXparameter|nullable_subrecords.condition|param_exact json_input False version 4.1.1.r9:|3|15|P?|@{0|}}
{30001002|XXparameter|continuous|False|13|1|RFKl|Enable component for Continuous>Flows operation|{0|}}
{30001002|XXparameter|commitTable||24|3|FKc|Collection in which to store commit progress|{0|}}
{30001002|XXparameter|transaction_group||3|2|FK$|Name of the transaction group for participation in a shared transaction. Graph folding must be enabled.|{0|}}
{30001002|XXparameter|transaction_group.condition|version 4.0.0.r1:|3|15|P?|@{0|}}
{30001002|XXparameter|use_field_level_encryption|False|13|1|RFKl|Enable client-side field level encryption.|{0|}}
{30001002|XXparameter|use_field_level_encryption.condition|version 4.1.2.r12:|3|15|P?|@{0|}}
{30001002|XXparameter|schema_map||3|2|FK$|JSON schema map for specifying local automatic encryption rules.|{0|}}
{30001002|XXparameter|schema_map.condition|param_exact use_field_level_encryption True version 4.1.2.r12:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|use_leading_checkpoint|value commitTable '' False value commitTable * True default constant False|13|13|v||{0|}}
{30001002|XXparameter|leadchkpt|-__ab__leading-checkpoint__ab__|3|2|O$||{0|}}
{30001002|XXparameter|leadchkpt.condition|param continuous False param use_leading_checkpoint True|3|15|P?|@{0|}}
{30001002|XXparameter|gendml_param_names|collection projection|3|2|$||{0|}}
{30001002|XXparameter|_ab_gendmlports|in|3|2|$|Port supports automatic metadata generation|{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|num_operations|5|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|kms_credentials_t kms_credentials "record string(int) kms_providers; datetime('YYYY-MM-DDTHH24:MI:SS-zo:ne') expiration = NULL; end"|3|2|H$|Type of kms_credentials|{0|}}
{30001002|XXparameter|operation1|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation5|optional kms_credentials::retrieve_kms_credentials()|3|2|H$|Optional provision of KMS credentials for CS-FLE|{0|}}
{30001002|XXparameter|operation5_analysis|optional kms_credentials::retrieve_kms_credentials()|3|2|H$|Optional provision of KMS credentials for CS-FLE|{0|}}
{30001002|XXparameter|override_mpname|value continuous True db-mongo-update-continuous value continuous False db-mongo-update|3|13|v||{0|}}
{30001002|XXparameter|override_mpname.display_name|override-mpname|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in; out=in|3|2|H$||{0|}}
{30001002|XXparameter|eme_dataset_mapping|@40|9|F|Location in which to create a dataset corresponding to this component.|{0|}}
{30001002|XXparameter|dataset_analysis|eme_dataset_mapping(table)=in,w|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|continuous ? nobatch,publisher : not_enabled|3|2|H$||{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912808|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|@15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
}}@0|Update Mongo|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|344|0|970|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|out|0.0|@@@2192|0|}}
{2010203004|XXGoport|345|0|973|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|346|0|976|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|347|0|979|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|348|0|982|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|349|0|986|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|out0_metadata|$AI_DML/adif_mong_big_collection_neurolands.dml|3|2|f$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@3|Reformat|1353000|541000|0|0|0|0|5594|rfm dml mongo neuro|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|350|0|988|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|351|0|991|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|352|0|993|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|353|0|995|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|354|0|997|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|355|0|1000|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|1|1|1|Fl|Number of reformat transforms|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform0||8|1|FOl|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
{30001002|XXparameter|select||20|2|FK$|Filter expression before reformatting|{0|}}
{30001002|XXparameter|error_group||3|2|F$|Optional group name identifying a Handle Errors component to which errors can be directed.|{0|}}
{30001002|XXparameter|error_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|log_group||3|2|F$|Optional group name of a Handle Logs component to which log output can be directed.|{0|}}
{30001002|XXparameter|log_group.condition|version 2.16:|3|15|P?|@{0|}}
{30001002|XXparameter|reject_threshold|Abort on first reject|15|1|Fl|When to abort if input records are rejected|{3|Abort on first reject|Never abort|Use limit/ramp|}}
{30001002|XXparameter|reject_threshold.display_name|reject-threshold|3|9|P|@{0|}}
{30001002|XXparameter|limit|0|1|2|F$|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|limit.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|ramp|0.0|2|2|F$|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp.condition|param reject-threshold Use*|3|15|P?|@{0|}}
{30001002|XXparameter|limit_keyword|value reject-threshold Never* 0 value reject-threshold Abort* 0 sameas limit default dollar_substitution 0|1|13|Kv|Maximum rejected records before failure|{0|}}
{30001002|XXparameter|ramp_keyword|value reject-threshold Never* 99.0 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword.condition|version :2.12.999.m999|3|15|P?|@{0|}}
{30001002|XXparameter|ramp_keyword2|value reject-threshold Never* -1 value reject-threshold Abort* 0.0 sameas ramp default dollar_substitution 0.0|2|13|Kv|Rate of rejected records|{0|}}
{30001002|XXparameter|ramp_keyword2.condition|version 2.13:|3|15|P?|@{0|}}
{30001002|XXparameter|keyword_map|limit_keyword limit ramp_keyword ramp ramp_keyword2 ramp|3|2|$||{0|}}
{30001002|XXparameter|keyword_map.display_name|keyword-map|3|9|P|@{0|}}
{30001002|XXparameter|output_index||8|1|FKl|Output index computation|{0|}}
{30001002|XXparameter|output_index.display_name|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index.keyword|output-index|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_index_port.display_name|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_port.keyword|output-index_port|3|9|P|@{0|}}
{30001002|XXparameter|output_index_signature|int output_index_out::output_index(in)|3|2|H$|Function returning index of output port|{0|}}
{30001002|XXparameter|output_index_signature.display_name|output-index_signature|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes||8|1|FKl|Output index vector computation|{0|}}
{30001002|XXparameter|output_indexes.display_name|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes.keyword|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_indexes_port.display_name|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port.keyword|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_signature|int[int] output_indexes_out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
{30001002|XXparameter|output_indexes_signature.display_name|output-indexes_signature|3|9|P|@{0|}}
{30001002|XXparameter|logging|False|13|1|Fl|Log internal events|{0|}}
{30001002|XXparameter|log|log_concat|3|13|Kv|Special log parameter|{0|}}
{30001002|XXparameter|log.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_input||15|1|Fl|Frequency of input records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_input.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_output||15|1|Fl|Frequency of output records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_output.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|log_reject||15|1|Fl|Frequency of reject records to log|{7| |1|10|100|1000|10000|100000|}}
{30001002|XXparameter|log_reject.condition|param logging True|3|15|P?|@{0|}}
{30001002|XXparameter|num_operations|7|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|legacy_xfr;reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|event_info_t event_info "record int event_type; end"|3|2|H$|Information about the kind of event that happened|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional out::output_at_event(event_info)|3|2|H$|Function to allow the output of an additional record at event|{0|}}
{30001002|XXparameter|operation7|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|6|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Reformat|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|356|0|1002|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|357|0|1006|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|358|0|1009|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|359|0|1012|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|360|0|1015|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010600005|XXGgraph|361|0|1023|0|{Subgraph created from graph "BIG_SCORES_TABLE_EXTRACT"|{}@0|@904000|553000|0|0|0|0|5573|cust seg rejected|lc80582|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|166000|316000|7|}}
{2010503005|XXGfvertex|362|0|1025|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL_LOG/bcs_cust_seg_rej_$\{FILE_DATE\}.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL_LOG/bcs_cust_seg_rej_$\{FILE_DATE\}.dat|3|2|$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
}}@2|Output File|54000|195000|0|0|0|0|4516|models rejected|Ab Initio Software|@1|10000|0||6||33153|-1|-1|}}
{2010202004|XXGiport|363|0|1027|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|364|0|1029|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|create_directories|False|13|1|FKl|If True, create any parent directories as necessary|{0|}}
{30001002|XXparameter|create_directories.display_name|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.keyword|create-directories|3|9|P|@{0|}}
{30001002|XXparameter|create_directories.condition|version 4.1.1.r9.0:|3|15|P?|@{0|}}
{30001002|XXparameter|translate_format|False|13|1|Fl|If true, translate the file format.|{0|}}
{30001002|XXparameter|translate_format.condition|version 4.0.0.r1.0:|3|15|P?|@{0|}}
{30001002|XXparameter|format|uninterpreted|15|1|FKl|'uninterpreted' (raw data), 'seqfile' (Hadoop sequence file), 'parquet' (Parquet format), 'orc' (ORC format), 'avro' (Avro format), 'texttable' (Hive text table), 'hadoop_compressed' (Compressed raw data).|{7|uninterpreted|seqfile|parquet|orc|avro|texttable|hadoop_compressed|}}
{30001002|XXparameter|format.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoopy_condition|value format uninterpreted False value format * True default constant False|13|13|Hv|Hidden condition for deciding hadoop-codec visibility|{0|}}
{30001002|XXparameter|hadoopy_condition.condition|param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|hadoop_codec|Uncompressed|15|1|FKl|Compression for writing hadoop specific file format. orc=\{ZLIB,SNAPPY,LZO\}, parquet=\{GZIP,SNAPPY,LZO\}, seqfile=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO\}, avro=\{SNAPPY,Deflate,BZIP2\}, texttable=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZOP\}, hadoop_compressed=\{GZIP,SNAPPY,Deflate,BZIP2,LZ4,LZO,LZOP\}|{9|Uncompressed|GZIP|SNAPPY|Deflate|BZIP2|ZLIB|LZ4|LZO|LZOP|}}
{30001002|XXparameter|hadoop_codec.display_name|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.keyword|hadoop-codec|3|9|P|@{0|}}
{30001002|XXparameter|hadoop_codec.condition|param_exact hadoopy_condition True param_exact translate_format True|3|15|P?|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed only_last_key_instance orc_file|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url||28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|either_or|value block_compressed True True sameas keep_on_disk default constant True|13|13|v|Either B-C or K-o-D|{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|mode lookup version 2.15.5.r34: param_exact either_or True|3|15|P?|@{0|}}
{30001002|XXparameter|only_last_key_instance|False|13|1|Fl|Match only the last instance of each key|{0|}}
{30001002|XXparameter|only_last_key_instance.condition|mode lookup version 3.0.2.r12.0:|3|15|P?|@{0|}}
{30001002|XXparameter|orc_file|False|13|1|Fl|Set to true if it is Hive ORC file|{0|}}
{30001002|XXparameter|orc_file.condition|mode lookup version 3.2.2.r15.0: param_exact direct_addressed True param_exact block_compressed False|3|15|P?|@{0|}}
{30001002|XXparameter|Layout||28|2|RF$||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|write_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1675912808|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Output File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|365|0|1031|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010202004|XXGiport|366|0|1035|0|{@{}@0|0|0|0|in0|.4578313253012048|@@@12816|0|}}
{2010110002|XXGconstant|367|0|1044|0|{@{}@{1|6947524|}}}
{2010002001|XXGdirectory_object_object|0|1|2|0|{XXGgraph|}0|1|}
{2010704001|XXGgraph_graphinfo_graphinfo|1|0|2|0|{}1|2|}
{2010706001|XXGgraphinfo_runsettings_runsettings|2|0|4|0|{}2|3|}
{2010109001|XXGobject_property_value|3|0|6|0|{0|legend_face|92|}2|4|}
{2010604001|XXGgraph_flow_flow|4|0|8|0|{Flow_1|}1|5|}
{2010604001|XXGgraph_flow_flow|5|0|10|0|{Flow_10|}1|6|}
{2010604001|XXGgraph_flow_flow|6|0|12|0|{Flow_11|}1|7|}
{2010244001|XXGflow_watcher_watcher|7|0|14|0|{}7|8|}
{2010604001|XXGgraph_flow_flow|8|0|16|0|{Flow_12|}1|9|}
{2010604001|XXGgraph_flow_flow|9|0|18|0|{Flow_13|}1|10|}
{2010604001|XXGgraph_flow_flow|10|0|20|0|{Flow_14|}1|11|}
{2010244001|XXGflow_watcher_watcher|11|0|22|0|{}11|12|}
{2010604001|XXGgraph_flow_flow|12|0|24|0|{Flow_15|}1|13|}
{2010604001|XXGgraph_flow_flow|13|0|26|0|{Flow_2|}1|14|}
{2010244001|XXGflow_watcher_watcher|14|0|28|0|{}14|15|}
{2010604001|XXGgraph_flow_flow|15|0|30|0|{Flow_3|}1|16|}
{2010604001|XXGgraph_flow_flow|16|0|32|0|{Flow_4|}1|17|}
{2010604001|XXGgraph_flow_flow|17|0|34|0|{Flow_5|}1|18|}
{2010244001|XXGflow_watcher_watcher|18|0|36|0|{}18|19|}
{2010604001|XXGgraph_flow_flow|19|0|38|0|{Flow_6|}1|20|}
{2010604001|XXGgraph_flow_flow|20|0|40|0|{Flow_7|}1|21|}
{2010604001|XXGgraph_flow_flow|21|0|42|0|{Flow_8|}1|22|}
{2010604001|XXGgraph_flow_flow|22|0|44|0|{Flow_9|}1|23|}
{2010601001|XXGgraph_vertex_vertex|23|0|46|0|{Clean_Table|}1|24|}
{2010604001|XXGgraph_flow_flow|24|0|48|0|{Flow_1|}24|25|}
{2010604001|XXGgraph_flow_flow|25|0|50|0|{Flow_17|}24|26|}
{2010604001|XXGgraph_flow_flow|26|0|52|0|{Flow_2|}24|27|}
{2010604001|XXGgraph_flow_flow|27|0|54|0|{Flow_3|}24|28|}
{2010601001|XXGgraph_vertex_vertex|28|0|56|0|{Create_Data|}24|29|}
{2010212001|XXGvertex_oport_oport|29|0|58|0|{0|out|}29|30|}
{2010213001|XXGoport_dst_flow|30|0|60|0|{0|}30|26|}
{2010212001|XXGvertex_oport_oport|31|0|61|0|{1|error|}29|31|}
{2010212001|XXGvertex_oport_oport|32|0|63|0|{2|log|}29|32|}
{2010007001|XXGobject_proto_object|33|0|65|0|{}29|33|}
{2010212001|XXGvertex_oport_oport|34|0|67|0|{0|out|}33|34|}
{2010006001|XXGobject_psameas_object|35|0|69|0|{metadata|out_metadata|1|0|}34|33|}
{2010212001|XXGvertex_oport_oport|36|0|70|0|{1|error|}33|35|}
{2010006001|XXGobject_psameas_object|37|0|72|0|{metadata|error_metadata|1|0|}35|33|}
{2010212001|XXGvertex_oport_oport|38|0|73|0|{2|log|}33|36|}
{2010006001|XXGobject_psameas_object|39|0|75|0|{metadata|log_metadata|1|0|}36|33|}
{2010601001|XXGgraph_vertex_vertex|40|0|76|0|{Remove_Models|}24|37|}
{2010212001|XXGvertex_oport_oport|41|0|78|0|{0|out|}37|38|}
{2010213001|XXGoport_dst_flow|42|0|80|0|{0|}38|25|}
{2010212001|XXGvertex_oport_oport|43|0|81|0|{1|reject|}37|39|}
{2010213001|XXGoport_dst_flow|44|0|83|0|{0|}39|27|}
{2010212001|XXGvertex_oport_oport|45|0|84|0|{2|error|}37|40|}
{2010212001|XXGvertex_oport_oport|46|0|86|0|{3|log|}37|41|}
{2010213001|XXGoport_dst_flow|47|0|88|0|{0|}41|28|}
{2010211001|XXGvertex_iport_iport|48|0|89|0|{0|in|}37|42|}
{2010214001|XXGiport_src_flow|49|0|91|0|{0|}42|26|}
{2010007001|XXGobject_proto_object|50|0|92|0|{}37|43|}
{2010212001|XXGvertex_oport_oport|51|0|94|0|{0|out|}43|44|}
{2010006001|XXGobject_psameas_object|52|0|96|0|{metadata|out_metadata|1|0|}44|43|}
{2010212001|XXGvertex_oport_oport|53|0|97|0|{1|reject|}43|45|}
{2010006001|XXGobject_psameas_object|54|0|99|0|{metadata|reject_metadata|1|0|}45|43|}
{2010212001|XXGvertex_oport_oport|55|0|100|0|{2|error|}43|46|}
{2010006001|XXGobject_psameas_object|56|0|102|0|{metadata|error_metadata|1|0|}46|43|}
{2010212001|XXGvertex_oport_oport|57|0|103|0|{3|log|}43|47|}
{2010006001|XXGobject_psameas_object|58|0|105|0|{metadata|log_metadata|1|0|}47|43|}
{2010211001|XXGvertex_iport_iport|59|0|106|0|{0|in|}43|48|}
{2010006001|XXGobject_psameas_object|60|0|108|0|{metadata|in_metadata|1|0|}48|43|}
{2010006001|XXGobject_psameas_object|61|0|109|0|{out_metadata|in_metadata|0|0|}37|37|}
{2010006001|XXGobject_psameas_object|62|0|110|0|{reject_metadata|in_metadata|0|0|}37|37|}
{2010601001|XXGgraph_vertex_vertex|63|0|111|0|{Trash|}24|49|}
{2010211001|XXGvertex_iport_iport|64|0|113|0|{0|in|}49|50|}
{2010214001|XXGiport_src_flow|65|0|115|0|{0|}50|25|}
{2010007001|XXGobject_proto_object|66|0|116|0|{}49|51|}
{2010211001|XXGvertex_iport_iport|67|0|118|0|{0|in|}51|52|}
{2010006001|XXGobject_psameas_object|68|0|120|0|{metadata|in_metadata|1|0|}52|51|}
{2010006001|XXGobject_psameas_object|69|0|121|0|{Layout|Layout|0|0|}49|37|}
{2010006001|XXGobject_psameas_object|70|0|122|0|{in_metadata|in_metadata|0|0|}49|37|}
{2010601001|XXGgraph_vertex_vertex|71|0|123|0|{Trash_1|}24|53|}
{2010211001|XXGvertex_iport_iport|72|0|125|0|{0|in|}53|54|}
{2010214001|XXGiport_src_flow|73|0|127|0|{0|}54|27|}
{2010007001|XXGobject_proto_object|74|0|128|0|{}53|55|}
{2010211001|XXGvertex_iport_iport|75|0|130|0|{0|in|}55|56|}
{2010006001|XXGobject_psameas_object|76|0|132|0|{metadata|in_metadata|1|0|}56|55|}
{2010006001|XXGobject_psameas_object|77|0|133|0|{Layout|Layout|0|0|}53|37|}
{2010006001|XXGobject_psameas_object|78|0|134|0|{in_metadata|in_metadata|0|0|}53|37|}
{2010601001|XXGgraph_vertex_vertex|79|0|135|0|{Trash_2|}24|57|}
{2010211001|XXGvertex_iport_iport|80|0|137|0|{0|in|}57|58|}
{2010214001|XXGiport_src_flow|81|0|139|0|{0|}58|28|}
{2010007001|XXGobject_proto_object|82|0|140|0|{}57|59|}
{2010211001|XXGvertex_iport_iport|83|0|142|0|{0|in|}59|60|}
{2010006001|XXGobject_psameas_object|84|0|144|0|{metadata|in_metadata|1|0|}60|59|}
{2010006001|XXGobject_psameas_object|85|0|145|0|{Layout|Layout|0|0|}57|37|}
{2010006001|XXGobject_psameas_object|86|0|146|0|{in_metadata|log_metadata|0|0|}57|37|}
{2010601001|XXGgraph_vertex_vertex|87|0|147|0|{Dedup_Sorted|}1|61|}
{2010212001|XXGvertex_oport_oport|88|0|149|0|{0|out|}61|62|}
{2010213001|XXGoport_dst_flow|89|0|151|0|{0|}62|17|}
{2010212001|XXGvertex_oport_oport|90|0|152|0|{1|dup|}61|63|}
{2010212001|XXGvertex_oport_oport|91|0|154|0|{2|reject|}61|64|}
{2010212001|XXGvertex_oport_oport|92|0|156|0|{3|error|}61|65|}
{2010212001|XXGvertex_oport_oport|93|0|158|0|{4|log|}61|66|}
{2010211001|XXGvertex_iport_iport|94|0|160|0|{0|in|}61|67|}
{2010214001|XXGiport_src_flow|95|0|162|0|{0|}67|21|}
{2010007001|XXGobject_proto_object|96|0|163|0|{}61|68|}
{2010212001|XXGvertex_oport_oport|97|0|165|0|{0|out|}68|69|}
{2010006001|XXGobject_psameas_object|98|0|167|0|{metadata|out_metadata|1|0|}69|68|}
{2010212001|XXGvertex_oport_oport|99|0|168|0|{1|dup|}68|70|}
{2010006001|XXGobject_psameas_object|100|0|170|0|{metadata|dup_metadata|1|0|}70|68|}
{2010212001|XXGvertex_oport_oport|101|0|171|0|{2|reject|}68|71|}
{2010006001|XXGobject_psameas_object|102|0|173|0|{metadata|reject_metadata|1|0|}71|68|}
{2010212001|XXGvertex_oport_oport|103|0|174|0|{3|error|}68|72|}
{2010006001|XXGobject_psameas_object|104|0|176|0|{metadata|error_metadata|1|0|}72|68|}
{2010212001|XXGvertex_oport_oport|105|0|177|0|{4|log|}68|73|}
{2010006001|XXGobject_psameas_object|106|0|179|0|{metadata|log_metadata|1|0|}73|68|}
{2010211001|XXGvertex_iport_iport|107|0|180|0|{0|in|}68|74|}
{2010006001|XXGobject_psameas_object|108|0|182|0|{metadata|in_metadata|1|0|}74|68|}
{2010006001|XXGobject_psameas_object|109|0|183|0|{Layout|Layout|0|0|}61|75|}
{2010211001|XXGvertex_iport_iport|110|0|185|0|{0|write|}75|76|}
{2010214001|XXGiport_src_flow|111|0|187|0|{0|}76|17|}
{2010007001|XXGobject_proto_object|112|0|188|0|{}75|77|}
{2010211001|XXGvertex_iport_iport|113|0|190|0|{0|write|}77|78|}
{2010006001|XXGobject_psameas_object|114|0|192|0|{metadata|write_metadata|1|0|}78|77|}
{2010006001|XXGobject_psameas_object|115|0|193|0|{write_metadata|out_metadata|0|0|}75|79|}
{2010212001|XXGvertex_oport_oport|116|0|195|0|{0|out|}79|80|}
{2010212001|XXGvertex_oport_oport|117|0|197|0|{1|filereject|}79|81|}
{2010212001|XXGvertex_oport_oport|118|0|199|0|{2|fileerror|}79|82|}
{2010212001|XXGvertex_oport_oport|119|0|201|0|{3|reject|}79|83|}
{2010212001|XXGvertex_oport_oport|120|0|203|0|{4|error|}79|84|}
{2010212001|XXGvertex_oport_oport|121|0|205|0|{5|log|}79|85|}
{2010211001|XXGvertex_iport_iport|122|0|207|0|{0|in|}79|86|}
{2010214001|XXGiport_src_flow|123|0|209|0|{0|}86|87|}
{2010006001|XXGobject_psameas_object|124|0|211|0|{filereject_metadata|out0_metadata|0|0|}79|88|}
{2010212001|XXGvertex_oport_oport|125|0|213|0|{0|out0|}88|89|}
{2010213001|XXGoport_dst_flow|126|0|215|0|{0|}89|90|}
{2010212001|XXGvertex_oport_oport|127|0|217|0|{1|log|}88|91|}
{2010211001|XXGvertex_iport_iport|128|0|219|0|{0|in0|}88|92|}
{2010006001|XXGobject_psameas_object|129|0|221|0|{Layout|Layout|0|0|}88|93|}
{2010212001|XXGvertex_oport_oport|130|0|223|0|{0|out|}93|94|}
{2010213001|XXGoport_dst_flow|131|0|225|0|{0|}94|95|}
{2010211001|XXGvertex_iport_iport|132|0|227|0|{0|in|}93|96|}
{2010006001|XXGobject_psameas_object|133|0|229|0|{out_metadata|read_metadata|0|0|}93|97|}
{2010212001|XXGvertex_oport_oport|134|0|231|0|{0|read|}97|98|}
{2010213001|XXGoport_dst_flow|135|0|233|0|{0|}98|99|}
{2010006001|XXGobject_psameas_object|136|0|235|0|{in0_metadata|read_metadata|0|0|}88|97|}
{2010006001|XXGobject_psameas_object|137|0|236|0|{in_metadata|out0_metadata|0|0|}79|88|}
{2010006001|XXGobject_psameas_object|138|0|237|0|{dup_metadata|out_metadata|0|0|}61|79|}
{2010006001|XXGobject_psameas_object|139|0|238|0|{in_metadata|out_metadata|0|0|}61|79|}
{2010006001|XXGobject_psameas_object|140|0|239|0|{out_metadata|out_metadata|0|0|}61|79|}
{2010006001|XXGobject_psameas_object|141|0|240|0|{reject_metadata|out_metadata|0|0|}61|79|}
{2010601001|XXGgraph_vertex_vertex|142|0|241|0|{Join|}1|100|}
{2010212001|XXGvertex_oport_oport|143|0|243|0|{0|out|}100|101|}
{2010213001|XXGoport_dst_flow|144|0|245|0|{0|}101|18|}
{2010212001|XXGvertex_oport_oport|145|0|246|0|{1|unused0|}100|102|}
{2010212001|XXGvertex_oport_oport|146|0|248|0|{2|unused1|}100|103|}
{2010212001|XXGvertex_oport_oport|147|0|250|0|{3|reject0|}100|104|}
{2010212001|XXGvertex_oport_oport|148|0|252|0|{4|reject1|}100|105|}
{2010212001|XXGvertex_oport_oport|149|0|254|0|{5|error0|}100|106|}
{2010212001|XXGvertex_oport_oport|150|0|256|0|{6|error1|}100|107|}
{2010212001|XXGvertex_oport_oport|151|0|258|0|{7|log|}100|108|}
{2010211001|XXGvertex_iport_iport|152|0|260|0|{0|in0|}100|109|}
{2010214001|XXGiport_src_flow|153|0|262|0|{0|}109|6|}
{2010211001|XXGvertex_iport_iport|154|0|263|0|{1|in1|}100|110|}
{2010214001|XXGiport_src_flow|155|0|265|0|{0|}110|23|}
{2010007001|XXGobject_proto_object|156|0|266|0|{}100|111|}
{2010212001|XXGvertex_oport_oport|157|0|268|0|{0|out|}111|112|}
{2010006001|XXGobject_psameas_object|158|0|270|0|{metadata|out_metadata|1|0|}112|111|}
{2010212001|XXGvertex_oport_oport|159|0|271|0|{1|unused0|}111|113|}
{2010006001|XXGobject_psameas_object|160|0|273|0|{metadata|unused0_metadata|1|0|}113|111|}
{2010212001|XXGvertex_oport_oport|161|0|274|0|{2|unused1|}111|114|}
{2010006001|XXGobject_psameas_object|162|0|276|0|{metadata|unused1_metadata|1|0|}114|111|}
{2010212001|XXGvertex_oport_oport|163|0|277|0|{3|reject0|}111|115|}
{2010006001|XXGobject_psameas_object|164|0|279|0|{metadata|reject0_metadata|1|0|}115|111|}
{2010212001|XXGvertex_oport_oport|165|0|280|0|{4|reject1|}111|116|}
{2010006001|XXGobject_psameas_object|166|0|282|0|{metadata|reject1_metadata|1|0|}116|111|}
{2010212001|XXGvertex_oport_oport|167|0|283|0|{5|error0|}111|117|}
{2010006001|XXGobject_psameas_object|168|0|285|0|{metadata|error0_metadata|1|0|}117|111|}
{2010212001|XXGvertex_oport_oport|169|0|286|0|{6|error1|}111|118|}
{2010006001|XXGobject_psameas_object|170|0|288|0|{metadata|error1_metadata|1|0|}118|111|}
{2010212001|XXGvertex_oport_oport|171|0|289|0|{7|log|}111|119|}
{2010006001|XXGobject_psameas_object|172|0|291|0|{metadata|log_metadata|1|0|}119|111|}
{2010211001|XXGvertex_iport_iport|173|0|292|0|{0|in0|}111|120|}
{2010006001|XXGobject_psameas_object|174|0|294|0|{YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|175|0|295|0|{dedup0|dedup0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|176|0|296|0|{dedup_keyword0|dedup_keyword0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|177|0|297|0|{dedup_positional0|dedup_positional0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|178|0|298|0|{matchoptional_keyword0|matchoptional_keyword0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|179|0|299|0|{matchoptional_positional0|matchoptional_positional0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|180|0|300|0|{metadata|in0_metadata|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|181|0|301|0|{override_key0|override_key0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|182|0|302|0|{record_match_required0|record_match_required0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|183|0|303|0|{record_match_required_not0|record_match_required_not0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|184|0|304|0|{record_required0|record_required0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|185|0|305|0|{record_required_keyword0|record_required_keyword0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|186|0|306|0|{record_required_positional0|record_required_positional0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|187|0|307|0|{select0|select0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|188|0|308|0|{select_keyword0|select_keyword0|1|0|}120|111|}
{2010006001|XXGobject_psameas_object|189|0|309|0|{select_positional0|select_positional0|1|0|}120|111|}
{2010211001|XXGvertex_iport_iport|190|0|310|0|{1|in1|}111|121|}
{2010006001|XXGobject_psameas_object|191|0|312|0|{YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|192|0|313|0|{dedup1|dedup1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|193|0|314|0|{dedup_keyword1|dedup_keyword1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|194|0|315|0|{dedup_positional1|dedup_positional1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|195|0|316|0|{matchoptional_keyword1|matchoptional_keyword1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|196|0|317|0|{matchoptional_positional1|matchoptional_positional1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|197|0|318|0|{metadata|in1_metadata|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|198|0|319|0|{override_key1|override_key1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|199|0|320|0|{record_match_required1|record_match_required1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|200|0|321|0|{record_match_required_not1|record_match_required_not1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|201|0|322|0|{record_required1|record_required1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|202|0|323|0|{record_required_keyword1|record_required_keyword1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|203|0|324|0|{record_required_positional1|record_required_positional1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|204|0|325|0|{select1|select1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|205|0|326|0|{select_keyword1|select_keyword1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|206|0|327|0|{select_positional1|select_positional1|1|0|}121|111|}
{2010006001|XXGobject_psameas_object|207|0|328|0|{Layout|Layout|0|0|}100|122|}
{2010212001|XXGvertex_oport_oport|208|0|330|0|{0|read|}122|123|}
{2010213001|XXGoport_dst_flow|209|0|332|0|{0|}123|6|}
{2010007001|XXGobject_proto_object|210|0|333|0|{}122|124|}
{2010212001|XXGvertex_oport_oport|211|0|335|0|{0|read|}124|125|}
{2010006001|XXGobject_psameas_object|212|0|337|0|{metadata|read_metadata|1|0|}125|124|}
{2010006001|XXGobject_psameas_object|213|0|338|0|{in0_metadata|read_metadata|0|0|}100|122|}
{2010006001|XXGobject_psameas_object|214|0|339|0|{in1_metadata|out_metadata|0|0|}100|79|}
{2010006001|XXGobject_psameas_object|215|0|340|0|{out_metadata|read_metadata|0|0|}100|122|}
{2010006001|XXGobject_psameas_object|216|0|341|0|{reject0_metadata|read_metadata|0|0|}100|122|}
{2010006001|XXGobject_psameas_object|217|0|342|0|{reject1_metadata|out_metadata|0|0|}100|79|}
{2010006001|XXGobject_psameas_object|218|0|343|0|{unused0_metadata|read_metadata|0|0|}100|122|}
{2010006001|XXGobject_psameas_object|219|0|344|0|{unused1_metadata|out_metadata|0|0|}100|79|}
{2010601001|XXGgraph_vertex_vertex|220|0|345|0|{Read_Hive_Table|}1|126|}
{2010604001|XXGgraph_flow_flow|221|0|347|0|{Flow_1|}126|99|}
{2010604001|XXGgraph_flow_flow|222|0|348|0|{Flow_2|}126|127|}
{2010604001|XXGgraph_flow_flow|223|0|350|0|{Flow_3|}126|95|}
{2010601001|XXGgraph_vertex_vertex|224|0|351|0|{Filter_Partitions|}126|128|}
{2010212001|XXGvertex_oport_oport|225|0|353|0|{0|out|}128|129|}
{2010213001|XXGoport_dst_flow|226|0|355|0|{0|}129|127|}
{2010212001|XXGvertex_oport_oport|227|0|356|0|{1|deselect|}128|130|}
{2010212001|XXGvertex_oport_oport|228|0|358|0|{2|reject|}128|131|}
{2010212001|XXGvertex_oport_oport|229|0|360|0|{3|error|}128|132|}
{2010212001|XXGvertex_oport_oport|230|0|362|0|{4|log|}128|133|}
{2010211001|XXGvertex_iport_iport|231|0|364|0|{0|in|}128|134|}
{2010214001|XXGiport_src_flow|232|0|366|0|{0|}134|99|}
{2010214001|XXGiport_src_flow|233|0|367|0|{1|}134|95|}
{2010006001|XXGobject_psameas_object|234|0|368|0|{Layout|Layout|0|0|}128|93|}
{2010006001|XXGobject_psameas_object|235|0|369|0|{deselect_metadata|read_metadata|0|0|}128|97|}
{2010006001|XXGobject_psameas_object|236|0|370|0|{in_metadata|read_metadata|0|0|}128|97|}
{2010006001|XXGobject_psameas_object|237|0|371|0|{out_metadata|read_metadata|0|0|}128|97|}
{2010006001|XXGobject_psameas_object|238|0|372|0|{reject_metadata|read_metadata|0|0|}128|97|}
{2010601001|XXGgraph_vertex_vertex|239|0|373|0|{Generate_Partition_Data|}126|93|}
{2010601001|XXGgraph_vertex_vertex|240|0|374|0|{Partition_Data|}126|97|}
{2010601001|XXGgraph_vertex_vertex|241|0|375|0|{Read_HDFS_Files|}126|135|}
{2010604001|XXGgraph_flow_flow|242|0|377|0|{Flow_1|}135|90|}
{2010604001|XXGgraph_flow_flow|243|0|378|0|{Flow_8|}135|87|}
{2010601001|XXGgraph_vertex_vertex|244|0|379|0|{Find_Files_and_Read_Blocks|}135|88|}
{2010601001|XXGgraph_vertex_vertex|245|0|380|0|{Partition_Blocks|}135|136|}
{2010212001|XXGvertex_oport_oport|246|0|382|0|{0|out|}136|137|}
{2010213001|XXGoport_dst_flow|247|0|384|0|{0|}137|87|}
{2010212001|XXGvertex_oport_oport|248|0|385|0|{1|reject|}136|138|}
{2010212001|XXGvertex_oport_oport|249|0|387|0|{2|error|}136|139|}
{2010212001|XXGvertex_oport_oport|250|0|389|0|{3|log|}136|140|}
{2010211001|XXGvertex_iport_iport|251|0|391|0|{0|in|}136|141|}
{2010214001|XXGiport_src_flow|252|0|393|0|{0|}141|90|}
{2010006001|XXGobject_psameas_object|253|0|394|0|{Layout|Layout|0|0|}136|93|}
{2010006001|XXGobject_psameas_object|254|0|395|0|{in_metadata|out0_metadata|0|0|}136|88|}
{2010006001|XXGobject_psameas_object|255|0|396|0|{out_metadata|out0_metadata|0|0|}136|88|}
{2010006001|XXGobject_psameas_object|256|0|397|0|{reject_metadata|out0_metadata|0|0|}136|88|}
{2010601001|XXGgraph_vertex_vertex|257|0|398|0|{Read_Blocks|}135|79|}
{2010212001|XXGvertex_oport_oport|258|0|399|0|{0|out0|}135|142|}
{2010216002|XXGoport_binding_oport|259|0|401|0|{.5|.5|{0|}3965|}142|80|}
{2010211001|XXGvertex_iport_iport|260|0|402|0|{0|in0|}135|143|}
{2010215002|XXGiport_binding_iport|261|0|404|0|{.5|.5|{0|}3964|}143|92|}
{2010214001|XXGiport_src_flow|262|0|405|0|{0|}143|127|}
{2010601001|XXGgraph_vertex_vertex|263|0|406|0|{Validate_HIVE_LAYOUT|}126|144|}
{2010604001|XXGgraph_flow_flow|264|0|408|0|{Flow_4|}144|145|}
{2010601001|XXGgraph_vertex_vertex|265|0|410|0|{Perform_Validation|}144|146|}
{2010212001|XXGvertex_oport_oport|266|0|412|0|{0|out|}146|147|}
{2010213001|XXGoport_dst_flow|267|0|414|0|{0|}147|145|}
{2010212001|XXGvertex_oport_oport|268|0|415|0|{1|error|}146|148|}
{2010212001|XXGvertex_oport_oport|269|0|417|0|{2|log|}146|149|}
{2010601001|XXGgraph_vertex_vertex|270|0|419|0|{Trash|}144|150|}
{2010211001|XXGvertex_iport_iport|271|0|421|0|{0|in|}150|151|}
{2010214001|XXGiport_src_flow|272|0|423|0|{0|}151|145|}
{2010006001|XXGobject_psameas_object|273|0|424|0|{Layout|Layout|0|0|}150|93|}
{2010006001|XXGobject_psameas_object|274|0|425|0|{in_metadata|out_metadata|0|0|}150|146|}
{2010212001|XXGvertex_oport_oport|275|0|426|0|{0|out0|}126|152|}
{2010216002|XXGoport_binding_oport|276|0|428|0|{.5|.5|{0|}4034|}152|142|}
{2010213001|XXGoport_dst_flow|277|0|429|0|{0|}152|5|}
{2010007001|XXGobject_proto_object|278|0|430|0|{}126|153|}
{2010604001|XXGgraph_flow_flow|279|0|432|0|{Flow_1|}153|154|}
{2010604001|XXGgraph_flow_flow|280|0|434|0|{Flow_2|}153|155|}
{2010604001|XXGgraph_flow_flow|281|0|436|0|{Flow_3|}153|156|}
{2010601001|XXGgraph_vertex_vertex|282|0|438|0|{Filter_Partitions|}153|157|}
{2010212001|XXGvertex_oport_oport|283|0|440|0|{0|out|}157|158|}
{2010213001|XXGoport_dst_flow|284|0|442|0|{0|}158|155|}
{2010212001|XXGvertex_oport_oport|285|0|443|0|{1|deselect|}157|159|}
{2010212001|XXGvertex_oport_oport|286|0|445|0|{2|reject|}157|160|}
{2010212001|XXGvertex_oport_oport|287|0|447|0|{3|error|}157|161|}
{2010212001|XXGvertex_oport_oport|288|0|449|0|{4|log|}157|162|}
{2010211001|XXGvertex_iport_iport|289|0|451|0|{0|in|}157|163|}
{2010214001|XXGiport_src_flow|290|0|453|0|{0|}163|154|}
{2010214001|XXGiport_src_flow|291|0|454|0|{1|}163|156|}
{2010007001|XXGobject_proto_object|292|0|455|0|{}157|164|}
{2010212001|XXGvertex_oport_oport|293|0|457|0|{0|out|}164|165|}
{2010006001|XXGobject_psameas_object|294|0|459|0|{metadata|out_metadata|1|0|}165|164|}
{2010212001|XXGvertex_oport_oport|295|0|460|0|{1|deselect|}164|166|}
{2010006001|XXGobject_psameas_object|296|0|462|0|{metadata|deselect_metadata|1|0|}166|164|}
{2010212001|XXGvertex_oport_oport|297|0|463|0|{2|reject|}164|167|}
{2010006001|XXGobject_psameas_object|298|0|465|0|{metadata|reject_metadata|1|0|}167|164|}
{2010212001|XXGvertex_oport_oport|299|0|466|0|{3|error|}164|168|}
{2010006001|XXGobject_psameas_object|300|0|468|0|{metadata|error_metadata|1|0|}168|164|}
{2010212001|XXGvertex_oport_oport|301|0|469|0|{4|log|}164|169|}
{2010006001|XXGobject_psameas_object|302|0|471|0|{metadata|log_metadata|1|0|}169|164|}
{2010211001|XXGvertex_iport_iport|303|0|472|0|{0|in|}164|170|}
{2010006001|XXGobject_psameas_object|304|0|474|0|{metadata|in_metadata|1|0|}170|164|}
{2010006001|XXGobject_psameas_object|305|0|475|0|{error_group|ERROR_GROUP|1|0|}157|153|}
{2010006001|XXGobject_psameas_object|306|0|476|0|{log_group|LOG_GROUP|1|0|}157|153|}
{2010006001|XXGobject_psameas_object|307|0|477|0|{logging|LOGGING|1|0|}157|153|}
{2010006001|XXGobject_psameas_object|308|0|478|0|{reject_threshold|REJECT_THRESHOLD|1|0|}157|153|}
{2010006001|XXGobject_psameas_object|309|0|479|0|{select_expr|FILTER_EXPR|1|0|}157|153|}
{2010601001|XXGgraph_vertex_vertex|310|0|480|0|{Generate_Partition_Data|}153|171|}
{2010212001|XXGvertex_oport_oport|311|0|482|0|{0|out|}171|172|}
{2010213001|XXGoport_dst_flow|312|0|484|0|{0|}172|156|}
{2010211001|XXGvertex_iport_iport|313|0|485|0|{0|in|}171|173|}
{2010007001|XXGobject_proto_object|314|0|487|0|{}171|174|}
{2010212001|XXGvertex_oport_oport|315|0|489|0|{0|out|}174|175|}
{2010006001|XXGobject_psameas_object|316|0|491|0|{metadata|out_metadata|1|0|}175|174|}
{2010211001|XXGvertex_iport_iport|317|0|492|0|{0|in|}174|176|}
{2010006001|XXGobject_psameas_object|318|0|494|0|{metadata|in_metadata|1|0|}176|174|}
{2010601001|XXGgraph_vertex_vertex|319|0|495|0|{Partition_Data|}153|177|}
{2010212001|XXGvertex_oport_oport|320|0|497|0|{0|read|}177|178|}
{2010213001|XXGoport_dst_flow|321|0|499|0|{0|}178|154|}
{2010007001|XXGobject_proto_object|322|0|500|0|{}177|179|}
{2010212001|XXGvertex_oport_oport|323|0|502|0|{0|read|}179|180|}
{2010006001|XXGobject_psameas_object|324|0|504|0|{metadata|read_metadata|1|0|}180|179|}
{2010601001|XXGgraph_vertex_vertex|325|0|505|0|{Read_HDFS_Files|}153|181|}
{2010604001|XXGgraph_flow_flow|326|0|507|0|{Flow_1|}181|182|}
{2010604001|XXGgraph_flow_flow|327|0|509|0|{Flow_8|}181|183|}
{2010601001|XXGgraph_vertex_vertex|328|0|511|0|{Find_Files_and_Read_Blocks|}181|184|}
{2010212001|XXGvertex_oport_oport|329|0|513|0|{0|out0|}184|185|}
{2010213001|XXGoport_dst_flow|330|0|515|0|{0|}185|182|}
{2010212001|XXGvertex_oport_oport|331|0|516|0|{1|log|}184|186|}
{2010211001|XXGvertex_iport_iport|332|0|518|0|{0|in0|}184|187|}
{2010601001|XXGgraph_vertex_vertex|333|0|520|0|{Partition_Blocks|}181|188|}
{2010212001|XXGvertex_oport_oport|334|0|522|0|{0|out|}188|189|}
{2010213001|XXGoport_dst_flow|335|0|524|0|{0|}189|183|}
{2010212001|XXGvertex_oport_oport|336|0|525|0|{1|reject|}188|190|}
{2010212001|XXGvertex_oport_oport|337|0|527|0|{2|error|}188|191|}
{2010212001|XXGvertex_oport_oport|338|0|529|0|{3|log|}188|192|}
{2010211001|XXGvertex_iport_iport|339|0|531|0|{0|in|}188|193|}
{2010214001|XXGiport_src_flow|340|0|533|0|{0|}193|182|}
{2010601001|XXGgraph_vertex_vertex|341|0|534|0|{Read_Blocks|}181|194|}
{2010212001|XXGvertex_oport_oport|342|0|536|0|{0|out|}194|195|}
{2010212001|XXGvertex_oport_oport|343|0|538|0|{1|filereject|}194|196|}
{2010212001|XXGvertex_oport_oport|344|0|540|0|{2|fileerror|}194|197|}
{2010212001|XXGvertex_oport_oport|345|0|542|0|{3|reject|}194|198|}
{2010212001|XXGvertex_oport_oport|346|0|544|0|{4|error|}194|199|}
{2010212001|XXGvertex_oport_oport|347|0|546|0|{5|log|}194|200|}
{2010211001|XXGvertex_iport_iport|348|0|548|0|{0|in|}194|201|}
{2010214001|XXGiport_src_flow|349|0|550|0|{0|}201|183|}
{2010212001|XXGvertex_oport_oport|350|0|551|0|{0|out0|}181|202|}
{2010216002|XXGoport_binding_oport|351|0|553|0|{.5|.5|{0|}3965|}202|195|}
{2010211001|XXGvertex_iport_iport|352|0|554|0|{0|in0|}181|203|}
{2010215002|XXGiport_binding_iport|353|0|556|0|{.5|.5|{0|}3964|}203|187|}
{2010214001|XXGiport_src_flow|354|0|557|0|{0|}203|155|}
{2010007001|XXGobject_proto_object|355|0|558|0|{}181|204|}
{2010604001|XXGgraph_flow_flow|356|0|560|0|{Flow_1|}204|205|}
{2010604001|XXGgraph_flow_flow|357|0|562|0|{Flow_8|}204|206|}
{2010601001|XXGgraph_vertex_vertex|358|0|564|0|{Find_Files_and_Read_Blocks|}204|207|}
{2010212001|XXGvertex_oport_oport|359|0|566|0|{0|out0|}207|208|}
{2010213001|XXGoport_dst_flow|360|0|568|0|{0|}208|205|}
{2010212001|XXGvertex_oport_oport|361|0|569|0|{1|log|}207|209|}
{2010211001|XXGvertex_iport_iport|362|0|571|0|{0|in0|}207|210|}
{2010007001|XXGobject_proto_object|363|0|573|0|{}207|211|}
{2010212001|XXGvertex_oport_oport|364|0|575|0|{0|out0|}211|212|}
{2010006001|XXGobject_psameas_object|365|0|577|0|{metadata|out0_metadata|1|0|}212|211|}
{2010212001|XXGvertex_oport_oport|366|0|578|0|{1|log|}211|213|}
{2010006001|XXGobject_psameas_object|367|0|580|0|{metadata|log_metadata|1|0|}213|211|}
{2010211001|XXGvertex_iport_iport|368|0|581|0|{0|in0|}211|214|}
{2010006001|XXGobject_psameas_object|369|0|583|0|{metadata|in0_metadata|1|0|}214|211|}
{2010601001|XXGgraph_vertex_vertex|370|0|584|0|{Partition_Blocks|}204|215|}
{2010212001|XXGvertex_oport_oport|371|0|586|0|{0|out|}215|216|}
{2010213001|XXGoport_dst_flow|372|0|588|0|{0|}216|206|}
{2010212001|XXGvertex_oport_oport|373|0|589|0|{1|reject|}215|217|}
{2010212001|XXGvertex_oport_oport|374|0|591|0|{2|error|}215|218|}
{2010212001|XXGvertex_oport_oport|375|0|593|0|{3|log|}215|219|}
{2010211001|XXGvertex_iport_iport|376|0|595|0|{0|in|}215|220|}
{2010214001|XXGiport_src_flow|377|0|597|0|{0|}220|205|}
{2010007001|XXGobject_proto_object|378|0|598|0|{}215|221|}
{2010212001|XXGvertex_oport_oport|379|0|600|0|{0|out|}221|222|}
{2010006001|XXGobject_psameas_object|380|0|602|0|{metadata|out_metadata|1|0|}222|221|}
{2010212001|XXGvertex_oport_oport|381|0|603|0|{1|reject|}221|223|}
{2010006001|XXGobject_psameas_object|382|0|605|0|{metadata|reject_metadata|1|0|}223|221|}
{2010212001|XXGvertex_oport_oport|383|0|606|0|{2|error|}221|224|}
{2010006001|XXGobject_psameas_object|384|0|608|0|{metadata|error_metadata|1|0|}224|221|}
{2010212001|XXGvertex_oport_oport|385|0|609|0|{3|log|}221|225|}
{2010006001|XXGobject_psameas_object|386|0|611|0|{metadata|log_metadata|1|0|}225|221|}
{2010211001|XXGvertex_iport_iport|387|0|612|0|{0|in|}221|226|}
{2010006001|XXGobject_psameas_object|388|0|614|0|{metadata|in_metadata|1|0|}226|221|}
{2010006001|XXGobject_psameas_object|389|0|615|0|{error_group|ERROR_GROUP|1|0|}215|204|}
{2010006001|XXGobject_psameas_object|390|0|616|0|{log_group|LOG_GROUP|1|0|}215|204|}
{2010006001|XXGobject_psameas_object|391|0|617|0|{logging|LOGGING|1|0|}215|204|}
{2010006001|XXGobject_psameas_object|392|0|618|0|{package|BLOCK_PARTITION_XFR|1|0|}215|204|}
{2010006001|XXGobject_psameas_object|393|0|619|0|{reject_threshold|REJECT_THRESHOLD|1|0|}215|204|}
{2010601001|XXGgraph_vertex_vertex|394|0|620|0|{Read_Blocks|}204|227|}
{2010212001|XXGvertex_oport_oport|395|0|622|0|{0|out|}227|228|}
{2010212001|XXGvertex_oport_oport|396|0|624|0|{1|filereject|}227|229|}
{2010212001|XXGvertex_oport_oport|397|0|626|0|{2|fileerror|}227|230|}
{2010212001|XXGvertex_oport_oport|398|0|628|0|{3|reject|}227|231|}
{2010212001|XXGvertex_oport_oport|399|0|630|0|{4|error|}227|232|}
{2010212001|XXGvertex_oport_oport|400|0|632|0|{5|log|}227|233|}
{2010211001|XXGvertex_iport_iport|401|0|634|0|{0|in|}227|234|}
{2010214001|XXGiport_src_flow|402|0|636|0|{0|}234|206|}
{2010007001|XXGobject_proto_object|403|0|637|0|{}227|235|}
{2010212001|XXGvertex_oport_oport|404|0|639|0|{0|out|}235|236|}
{2010006001|XXGobject_psameas_object|405|0|641|0|{metadata|out_metadata|1|0|}236|235|}
{2010212001|XXGvertex_oport_oport|406|0|642|0|{1|filereject|}235|237|}
{2010006001|XXGobject_psameas_object|407|0|644|0|{metadata|filereject_metadata|1|0|}237|235|}
{2010212001|XXGvertex_oport_oport|408|0|645|0|{2|fileerror|}235|238|}
{2010006001|XXGobject_psameas_object|409|0|647|0|{metadata|fileerror_metadata|1|0|}238|235|}
{2010212001|XXGvertex_oport_oport|410|0|648|0|{3|reject|}235|239|}
{2010006001|XXGobject_psameas_object|411|0|650|0|{metadata|reject_metadata|1|0|}239|235|}
{2010212001|XXGvertex_oport_oport|412|0|651|0|{4|error|}235|240|}
{2010006001|XXGobject_psameas_object|413|0|653|0|{metadata|error_metadata|1|0|}240|235|}
{2010212001|XXGvertex_oport_oport|414|0|654|0|{5|log|}235|241|}
{2010006001|XXGobject_psameas_object|415|0|656|0|{metadata|log_metadata|1|0|}241|235|}
{2010211001|XXGvertex_iport_iport|416|0|657|0|{0|in|}235|242|}
{2010006001|XXGobject_psameas_object|417|0|659|0|{metadata|in_metadata|1|0|}242|235|}
{2010006001|XXGobject_psameas_object|418|0|660|0|{error_group|ERROR_GROUP|1|0|}227|204|}
{2010006001|XXGobject_psameas_object|419|0|661|0|{log_group|LOG_GROUP|1|0|}227|204|}
{2010006001|XXGobject_psameas_object|420|0|662|0|{logging|LOGGING|1|0|}227|204|}
{2010006001|XXGobject_psameas_object|421|0|663|0|{out_metadata|OUTPUT_DML|1|0|}227|204|}
{2010006001|XXGobject_psameas_object|422|0|664|0|{reject_threshold|REJECT_THRESHOLD|1|0|}227|204|}
{2010006001|XXGobject_psameas_object|423|0|665|0|{schema_file|SCHEMA_FILE|1|0|}227|204|}
{2010006001|XXGobject_psameas_object|424|0|666|0|{select_columns|READ_COLUMNS|1|0|}227|204|}
{2010006001|XXGobject_psameas_object|425|0|667|0|{transform|RMF_XFR|1|0|}227|204|}
{2010212001|XXGvertex_oport_oport|426|0|668|0|{0|out0|}204|243|}
{2010216002|XXGoport_binding_oport|427|0|670|0|{.5|.5|{0|}3965|}243|228|}
{2010211001|XXGvertex_iport_iport|428|0|671|0|{0|in0|}204|244|}
{2010215002|XXGiport_binding_iport|429|0|673|0|{.5|.5|{0|}3964|}244|210|}
{2010006001|XXGobject_psameas_object|430|0|674|0|{READ_SPECIFICATION|in0_metadata|0|0|}204|207|}
{2010006001|XXGobject_psameas_object|431|0|675|0|{BLOCK_PARTITION_XFR|BLOCK_PARTITION_XFR|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|432|0|676|0|{ERROR_GROUP|ERROR_GROUP|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|433|0|677|0|{FILE_FORMAT|FILE_FORMAT|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|434|0|678|0|{HDFS_FILE_SUFFIX|HDFS_FILE_SUFFIX|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|435|0|679|0|{HOST_DEPTH|HOST_DEPTH|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|436|0|680|0|{HOST_LIST|HOST_LIST|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|437|0|681|0|{LOGGING|LOGGING|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|438|0|682|0|{LOG_GROUP|LOG_GROUP|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|439|0|683|0|{OUTPUT_DML|OUTPUT_DML|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|440|0|684|0|{PATH_GLOB_PATTERN|PATH_GLOB_PATTERN|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|441|0|685|0|{READ_COLUMNS|READ_COLUMNS|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|442|0|686|0|{READ_LAYOUT|READ_LAYOUT|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|443|0|687|0|{REFORMAT_XFR|REFORMAT_XFR|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|444|0|688|0|{REJECT_THRESHOLD|REJECT_THRESHOLD|1|0|}181|153|}
{2010006001|XXGobject_psameas_object|445|0|689|0|{SCHEMA_FILE|SCHEMA_FILE|1|0|}181|153|}
{2010601001|XXGgraph_vertex_vertex|446|0|690|0|{Validate_HIVE_LAYOUT|}153|245|}
{2010604001|XXGgraph_flow_flow|447|0|692|0|{Flow_4|}245|246|}
{2010601001|XXGgraph_vertex_vertex|448|0|694|0|{Perform_Validation|}245|247|}
{2010212001|XXGvertex_oport_oport|449|0|696|0|{0|out|}247|248|}
{2010213001|XXGoport_dst_flow|450|0|698|0|{0|}248|246|}
{2010212001|XXGvertex_oport_oport|451|0|699|0|{1|error|}247|249|}
{2010212001|XXGvertex_oport_oport|452|0|701|0|{2|log|}247|250|}
{2010007001|XXGobject_proto_object|453|0|703|0|{}247|251|}
{2010212001|XXGvertex_oport_oport|454|0|705|0|{0|out|}251|252|}
{2010006001|XXGobject_psameas_object|455|0|707|0|{metadata|out_metadata|1|0|}252|251|}
{2010212001|XXGvertex_oport_oport|456|0|708|0|{1|error|}251|253|}
{2010006001|XXGobject_psameas_object|457|0|710|0|{metadata|error_metadata|1|0|}253|251|}
{2010212001|XXGvertex_oport_oport|458|0|711|0|{2|log|}251|254|}
{2010006001|XXGobject_psameas_object|459|0|713|0|{metadata|log_metadata|1|0|}254|251|}
{2010006001|XXGobject_psameas_object|460|0|714|0|{Layout|Layout|0|0|}247|171|}
{2010601001|XXGgraph_vertex_vertex|461|0|715|0|{Trash|}245|255|}
{2010211001|XXGvertex_iport_iport|462|0|717|0|{0|in|}255|256|}
{2010214001|XXGiport_src_flow|463|0|719|0|{0|}256|246|}
{2010007001|XXGobject_proto_object|464|0|720|0|{}255|257|}
{2010211001|XXGvertex_iport_iport|465|0|722|0|{0|in|}257|258|}
{2010006001|XXGobject_psameas_object|466|0|724|0|{metadata|in_metadata|1|0|}258|257|}
{2010212001|XXGvertex_oport_oport|467|0|725|0|{0|out0|}153|259|}
{2010216002|XXGoport_binding_oport|468|0|727|0|{.5|.5|{0|}4034|}259|202|}
{2010601001|XXGgraph_vertex_vertex|469|0|728|0|{Replicate|}1|260|}
{2010212001|XXGvertex_oport_oport|470|0|730|0|{0|out|}260|261|}
{2010213001|XXGoport_dst_flow|471|0|732|0|{0|}261|21|}
{2010213001|XXGoport_dst_flow|472|0|733|0|{1|}261|23|}
{2010211001|XXGvertex_iport_iport|473|0|734|0|{0|in|}260|262|}
{2010214001|XXGiport_src_flow|474|0|736|0|{0|}262|16|}
{2010007001|XXGobject_proto_object|475|0|737|0|{}260|263|}
{2010212001|XXGvertex_oport_oport|476|0|739|0|{0|out|}263|264|}
{2010006001|XXGobject_psameas_object|477|0|741|0|{metadata|out_metadata|1|0|}264|263|}
{2010211001|XXGvertex_iport_iport|478|0|742|0|{0|in|}263|265|}
{2010006001|XXGobject_psameas_object|479|0|744|0|{metadata|in_metadata|1|0|}265|263|}
{2010006001|XXGobject_psameas_object|480|0|745|0|{Layout|Layout|0|0|}260|75|}
{2010006001|XXGobject_psameas_object|481|0|746|0|{in_metadata|out_metadata|0|0|}260|79|}
{2010006001|XXGobject_psameas_object|482|0|747|0|{out_metadata|out_metadata|0|0|}260|79|}
{2010601001|XXGgraph_vertex_vertex|483|0|748|0|{Risk_scores_Rejected|}1|266|}
{2010601001|XXGgraph_vertex_vertex|484|0|750|0|{bcs_risk_rej|}266|267|}
{2010211001|XXGvertex_iport_iport|485|0|752|0|{0|write|}267|268|}
{2010007001|XXGobject_proto_object|486|0|754|0|{}267|269|}
{2010211001|XXGvertex_iport_iport|487|0|756|0|{0|write|}269|270|}
{2010006001|XXGobject_psameas_object|488|0|758|0|{metadata|write_metadata|1|0|}270|269|}
{2010006001|XXGobject_psameas_object|489|0|759|0|{write_metadata|out0_metadata|0|0|}267|271|}
{2010212001|XXGvertex_oport_oport|490|0|761|0|{0|out0|}271|272|}
{2010213001|XXGoport_dst_flow|491|0|763|0|{0|}272|14|}
{2010212001|XXGvertex_oport_oport|492|0|764|0|{1|reject0|}271|273|}
{2010213001|XXGoport_dst_flow|493|0|766|0|{0|}273|20|}
{2010212001|XXGvertex_oport_oport|494|0|767|0|{2|error0|}271|274|}
{2010212001|XXGvertex_oport_oport|495|0|769|0|{3|log|}271|275|}
{2010211001|XXGvertex_iport_iport|496|0|771|0|{0|in|}271|276|}
{2010214001|XXGiport_src_flow|497|0|773|0|{0|}276|18|}
{2010007001|XXGobject_proto_object|498|0|774|0|{}271|277|}
{2010212001|XXGvertex_oport_oport|499|0|776|0|{0|out0|}277|278|}
{2010006001|XXGobject_psameas_object|500|0|778|0|{metadata|out0_metadata|1|0|}278|277|}
{2010006001|XXGobject_psameas_object|501|0|779|0|{transform0|transform0|1|0|}278|277|}
{2010212001|XXGvertex_oport_oport|502|0|780|0|{1|reject0|}277|279|}
{2010006001|XXGobject_psameas_object|503|0|782|0|{metadata|reject0_metadata|1|0|}279|277|}
{2010212001|XXGvertex_oport_oport|504|0|783|0|{2|error0|}277|280|}
{2010006001|XXGobject_psameas_object|505|0|785|0|{metadata|error0_metadata|1|0|}280|277|}
{2010212001|XXGvertex_oport_oport|506|0|786|0|{3|log|}277|281|}
{2010006001|XXGobject_psameas_object|507|0|788|0|{metadata|log_metadata|1|0|}281|277|}
{2010211001|XXGvertex_iport_iport|508|0|789|0|{0|in|}277|282|}
{2010006001|XXGobject_psameas_object|509|0|791|0|{metadata|in_metadata|1|0|}282|277|}
{2010006001|XXGobject_psameas_object|510|0|792|0|{Layout|Layout|0|0|}271|122|}
{2010006001|XXGobject_psameas_object|511|0|793|0|{in_metadata|read_metadata|0|0|}271|122|}
{2010006001|XXGobject_psameas_object|512|0|794|0|{reject0_metadata|read_metadata|0|0|}271|122|}
{2010601001|XXGgraph_vertex_vertex|513|0|795|0|{neuro_rej|}266|283|}
{2010211001|XXGvertex_iport_iport|514|0|797|0|{0|write|}283|284|}
{2010007001|XXGobject_proto_object|515|0|799|0|{}283|285|}
{2010211001|XXGvertex_iport_iport|516|0|801|0|{0|write|}285|286|}
{2010006001|XXGobject_psameas_object|517|0|803|0|{metadata|write_metadata|1|0|}286|285|}
{2010006001|XXGobject_psameas_object|518|0|804|0|{write_metadata|out0_metadata|0|0|}283|271|}
{2010211001|XXGvertex_iport_iport|519|0|805|0|{0|in0|}266|287|}
{2010215002|XXGiport_binding_iport|520|0|807|0|{.5|.5|{0|}4538|}287|268|}
{2010214001|XXGiport_src_flow|521|0|808|0|{0|}287|22|}
{2010211001|XXGvertex_iport_iport|522|0|809|0|{1|in1|}266|288|}
{2010215002|XXGiport_binding_iport|523|0|811|0|{.5|.5|{0|}4539|}288|284|}
{2010214001|XXGiport_src_flow|524|0|812|0|{0|}288|9|}
{2010601001|XXGgraph_vertex_vertex|525|0|813|0|{Sort_last_update_date_desc_|}1|289|}
{2010212001|XXGvertex_oport_oport|526|0|815|0|{0|out|}289|290|}
{2010213001|XXGoport_dst_flow|527|0|817|0|{0|}290|16|}
{2010211001|XXGvertex_iport_iport|528|0|818|0|{0|in|}289|291|}
{2010214001|XXGiport_src_flow|529|0|820|0|{0|}291|5|}
{2010007001|XXGobject_proto_object|530|0|821|0|{}289|292|}
{2010212001|XXGvertex_oport_oport|531|0|823|0|{0|out|}292|293|}
{2010006001|XXGobject_psameas_object|532|0|825|0|{metadata|out_metadata|1|0|}293|292|}
{2010211001|XXGvertex_iport_iport|533|0|826|0|{0|in|}292|294|}
{2010006001|XXGobject_psameas_object|534|0|828|0|{metadata|in_metadata|1|0|}294|292|}
{2010006001|XXGobject_psameas_object|535|0|829|0|{Layout|Layout|0|0|}289|75|}
{2010006001|XXGobject_psameas_object|536|0|830|0|{in_metadata|out_metadata|0|0|}289|79|}
{2010006001|XXGobject_psameas_object|537|0|831|0|{out_metadata|out_metadata|0|0|}289|79|}
{2010601001|XXGgraph_vertex_vertex|538|0|832|0|{Update_Mongo_bcs|}1|295|}
{2010212001|XXGvertex_oport_oport|539|0|834|0|{0|out|}295|296|}
{2010212001|XXGvertex_oport_oport|540|0|836|0|{1|reject|}295|297|}
{2010212001|XXGvertex_oport_oport|541|0|838|0|{2|error|}295|298|}
{2010212001|XXGvertex_oport_oport|542|0|840|0|{3|log|}295|299|}
{2010211001|XXGvertex_iport_iport|543|0|842|0|{0|in|}295|300|}
{2010214001|XXGiport_src_flow|544|0|844|0|{0|}300|11|}
{2010007001|XXGobject_proto_object|545|0|845|0|{}295|301|}
{2010212001|XXGvertex_oport_oport|546|0|847|0|{0|out|}301|302|}
{2010006001|XXGobject_psameas_object|547|0|849|0|{metadata|out_metadata|1|0|}302|301|}
{2010212001|XXGvertex_oport_oport|548|0|850|0|{1|reject|}301|303|}
{2010006001|XXGobject_psameas_object|549|0|852|0|{metadata|reject_metadata|1|0|}303|301|}
{2010212001|XXGvertex_oport_oport|550|0|853|0|{2|error|}301|304|}
{2010006001|XXGobject_psameas_object|551|0|855|0|{metadata|error_metadata|1|0|}304|301|}
{2010212001|XXGvertex_oport_oport|552|0|856|0|{3|log|}301|305|}
{2010006001|XXGobject_psameas_object|553|0|858|0|{metadata|log_metadata|1|0|}305|301|}
{2010211001|XXGvertex_iport_iport|554|0|859|0|{0|in|}301|306|}
{2010006001|XXGobject_psameas_object|555|0|861|0|{metadata|in_metadata|1|0|}306|301|}
{2010006001|XXGobject_psameas_object|556|0|862|0|{Layout|Layout|0|0|}295|122|}
{2010006001|XXGobject_psameas_object|557|0|863|0|{in_metadata|out0_metadata|0|0|}295|307|}
{2010212001|XXGvertex_oport_oport|558|0|865|0|{0|out0|}307|308|}
{2010213001|XXGoport_dst_flow|559|0|867|0|{0|}308|11|}
{2010212001|XXGvertex_oport_oport|560|0|868|0|{1|reject0|}307|309|}
{2010212001|XXGvertex_oport_oport|561|0|870|0|{2|error0|}307|310|}
{2010212001|XXGvertex_oport_oport|562|0|872|0|{3|log|}307|311|}
{2010211001|XXGvertex_iport_iport|563|0|874|0|{0|in|}307|312|}
{2010214001|XXGiport_src_flow|564|0|876|0|{0|}312|10|}
{2010007001|XXGobject_proto_object|565|0|877|0|{}307|313|}
{2010212001|XXGvertex_oport_oport|566|0|879|0|{0|out0|}313|314|}
{2010006001|XXGobject_psameas_object|567|0|881|0|{metadata|out0_metadata|1|0|}314|313|}
{2010006001|XXGobject_psameas_object|568|0|882|0|{transform0|transform0|1|0|}314|313|}
{2010212001|XXGvertex_oport_oport|569|0|883|0|{1|reject0|}313|315|}
{2010006001|XXGobject_psameas_object|570|0|885|0|{metadata|reject0_metadata|1|0|}315|313|}
{2010212001|XXGvertex_oport_oport|571|0|886|0|{2|error0|}313|316|}
{2010006001|XXGobject_psameas_object|572|0|888|0|{metadata|error0_metadata|1|0|}316|313|}
{2010212001|XXGvertex_oport_oport|573|0|889|0|{3|log|}313|317|}
{2010006001|XXGobject_psameas_object|574|0|891|0|{metadata|log_metadata|1|0|}317|313|}
{2010211001|XXGvertex_iport_iport|575|0|892|0|{0|in|}313|318|}
{2010006001|XXGobject_psameas_object|576|0|894|0|{metadata|in_metadata|1|0|}318|313|}
{2010006001|XXGobject_psameas_object|577|0|895|0|{Layout|Layout|0|0|}307|122|}
{2010006001|XXGobject_psameas_object|578|0|896|0|{in_metadata|out0_metadata|0|0|}307|319|}
{2010212001|XXGvertex_oport_oport|579|0|898|0|{0|out0|}319|320|}
{2010213001|XXGoport_dst_flow|580|0|900|0|{0|}320|10|}
{2010212001|XXGvertex_oport_oport|581|0|901|0|{1|out1|}319|321|}
{2010213001|XXGoport_dst_flow|582|0|903|0|{0|}321|7|}
{2010212001|XXGvertex_oport_oport|583|0|904|0|{2|reject0|}319|322|}
{2010213001|XXGoport_dst_flow|584|0|906|0|{0|}322|22|}
{2010212001|XXGvertex_oport_oport|585|0|907|0|{3|reject1|}319|323|}
{2010213001|XXGoport_dst_flow|586|0|909|0|{0|}323|9|}
{2010212001|XXGvertex_oport_oport|587|0|910|0|{4|error0|}319|324|}
{2010212001|XXGvertex_oport_oport|588|0|912|0|{5|error1|}319|325|}
{2010212001|XXGvertex_oport_oport|589|0|914|0|{6|log|}319|326|}
{2010211001|XXGvertex_iport_iport|590|0|916|0|{0|in|}319|327|}
{2010214001|XXGiport_src_flow|591|0|918|0|{0|}327|14|}
{2010007001|XXGobject_proto_object|592|0|919|0|{}319|328|}
{2010212001|XXGvertex_oport_oport|593|0|921|0|{0|out0|}328|329|}
{2010006001|XXGobject_psameas_object|594|0|923|0|{metadata|out0_metadata|1|0|}329|328|}
{2010006001|XXGobject_psameas_object|595|0|924|0|{transform0|transform0|1|0|}329|328|}
{2010212001|XXGvertex_oport_oport|596|0|925|0|{1|out1|}328|330|}
{2010006001|XXGobject_psameas_object|597|0|927|0|{metadata|out1_metadata|1|0|}330|328|}
{2010006001|XXGobject_psameas_object|598|0|928|0|{transform1|transform1|1|0|}330|328|}
{2010212001|XXGvertex_oport_oport|599|0|929|0|{2|reject0|}328|331|}
{2010006001|XXGobject_psameas_object|600|0|931|0|{metadata|reject0_metadata|1|0|}331|328|}
{2010212001|XXGvertex_oport_oport|601|0|932|0|{3|reject1|}328|332|}
{2010006001|XXGobject_psameas_object|602|0|934|0|{metadata|reject1_metadata|1|0|}332|328|}
{2010212001|XXGvertex_oport_oport|603|0|935|0|{4|error0|}328|333|}
{2010006001|XXGobject_psameas_object|604|0|937|0|{metadata|error0_metadata|1|0|}333|328|}
{2010212001|XXGvertex_oport_oport|605|0|938|0|{5|error1|}328|334|}
{2010006001|XXGobject_psameas_object|606|0|940|0|{metadata|error1_metadata|1|0|}334|328|}
{2010212001|XXGvertex_oport_oport|607|0|941|0|{6|log|}328|335|}
{2010006001|XXGobject_psameas_object|608|0|943|0|{metadata|log_metadata|1|0|}335|328|}
{2010211001|XXGvertex_iport_iport|609|0|944|0|{0|in|}328|336|}
{2010006001|XXGobject_psameas_object|610|0|946|0|{metadata|in_metadata|1|0|}336|328|}
{2010006001|XXGobject_psameas_object|611|0|947|0|{Layout|Layout|0|0|}319|122|}
{2010006001|XXGobject_psameas_object|612|0|948|0|{in_metadata|out0_metadata|0|0|}319|271|}
{2010006001|XXGobject_psameas_object|613|0|949|0|{reject0_metadata|out0_metadata|0|0|}319|271|}
{2010006001|XXGobject_psameas_object|614|0|950|0|{reject1_metadata|out0_metadata|0|0|}319|271|}
{2010006001|XXGobject_psameas_object|615|0|951|0|{reject0_metadata|out0_metadata|0|0|}307|319|}
{2010006001|XXGobject_psameas_object|616|0|952|0|{out_metadata|out0_metadata|0|0|}295|307|}
{2010006001|XXGobject_psameas_object|617|0|953|0|{reject_metadata|out0_metadata|0|0|}295|307|}
{2010601001|XXGgraph_vertex_vertex|618|0|954|0|{Update_Mongo_neurolands|}1|337|}
{2010212001|XXGvertex_oport_oport|619|0|956|0|{0|out|}337|338|}
{2010212001|XXGvertex_oport_oport|620|0|958|0|{1|reject|}337|339|}
{2010212001|XXGvertex_oport_oport|621|0|960|0|{2|error|}337|340|}
{2010212001|XXGvertex_oport_oport|622|0|962|0|{3|log|}337|341|}
{2010211001|XXGvertex_iport_iport|623|0|964|0|{0|in|}337|342|}
{2010214001|XXGiport_src_flow|624|0|966|0|{0|}342|13|}
{2010007001|XXGobject_proto_object|625|0|967|0|{}337|343|}
{2010212001|XXGvertex_oport_oport|626|0|969|0|{0|out|}343|344|}
{2010006001|XXGobject_psameas_object|627|0|971|0|{metadata|out_metadata|1|0|}344|343|}
{2010212001|XXGvertex_oport_oport|628|0|972|0|{1|reject|}343|345|}
{2010006001|XXGobject_psameas_object|629|0|974|0|{metadata|reject_metadata|1|0|}345|343|}
{2010212001|XXGvertex_oport_oport|630|0|975|0|{2|error|}343|346|}
{2010006001|XXGobject_psameas_object|631|0|977|0|{metadata|error_metadata|1|0|}346|343|}
{2010212001|XXGvertex_oport_oport|632|0|978|0|{3|log|}343|347|}
{2010006001|XXGobject_psameas_object|633|0|980|0|{metadata|log_metadata|1|0|}347|343|}
{2010211001|XXGvertex_iport_iport|634|0|981|0|{0|in|}343|348|}
{2010006001|XXGobject_psameas_object|635|0|983|0|{metadata|in_metadata|1|0|}348|343|}
{2010006001|XXGobject_psameas_object|636|0|984|0|{Layout|Layout|0|0|}337|122|}
{2010006001|XXGobject_psameas_object|637|0|985|0|{in_metadata|out0_metadata|0|0|}337|349|}
{2010212001|XXGvertex_oport_oport|638|0|987|0|{0|out0|}349|350|}
{2010213001|XXGoport_dst_flow|639|0|989|0|{0|}350|13|}
{2010212001|XXGvertex_oport_oport|640|0|990|0|{1|reject0|}349|351|}
{2010212001|XXGvertex_oport_oport|641|0|992|0|{2|error0|}349|352|}
{2010212001|XXGvertex_oport_oport|642|0|994|0|{3|log|}349|353|}
{2010211001|XXGvertex_iport_iport|643|0|996|0|{0|in|}349|354|}
{2010214001|XXGiport_src_flow|644|0|998|0|{0|}354|7|}
{2010007001|XXGobject_proto_object|645|0|999|0|{}349|355|}
{2010212001|XXGvertex_oport_oport|646|0|1001|0|{0|out0|}355|356|}
{2010006001|XXGobject_psameas_object|647|0|1003|0|{metadata|out0_metadata|1|0|}356|355|}
{2010006001|XXGobject_psameas_object|648|0|1004|0|{transform0|transform0|1|0|}356|355|}
{2010212001|XXGvertex_oport_oport|649|0|1005|0|{1|reject0|}355|357|}
{2010006001|XXGobject_psameas_object|650|0|1007|0|{metadata|reject0_metadata|1|0|}357|355|}
{2010212001|XXGvertex_oport_oport|651|0|1008|0|{2|error0|}355|358|}
{2010006001|XXGobject_psameas_object|652|0|1010|0|{metadata|error0_metadata|1|0|}358|355|}
{2010212001|XXGvertex_oport_oport|653|0|1011|0|{3|log|}355|359|}
{2010006001|XXGobject_psameas_object|654|0|1013|0|{metadata|log_metadata|1|0|}359|355|}
{2010211001|XXGvertex_iport_iport|655|0|1014|0|{0|in|}355|360|}
{2010006001|XXGobject_psameas_object|656|0|1016|0|{metadata|in_metadata|1|0|}360|355|}
{2010006001|XXGobject_psameas_object|657|0|1017|0|{Layout|Layout|0|0|}349|122|}
{2010006001|XXGobject_psameas_object|658|0|1018|0|{in_metadata|out1_metadata|0|0|}349|319|}
{2010006001|XXGobject_psameas_object|659|0|1019|0|{reject0_metadata|out1_metadata|0|0|}349|319|}
{2010006001|XXGobject_psameas_object|660|0|1020|0|{reject_metadata|out0_metadata|0|0|}337|349|}
{2010601001|XXGgraph_vertex_vertex|661|0|1021|0|{cust_seg_func|}1|271|}
{2010601001|XXGgraph_vertex_vertex|662|0|1022|0|{cust_seg_rejected|}1|361|}
{2010601001|XXGgraph_vertex_vertex|663|0|1024|0|{models_rejected|}361|362|}
{2010211001|XXGvertex_iport_iport|664|0|1026|0|{0|write|}362|363|}
{2010007001|XXGobject_proto_object|665|0|1028|0|{}362|364|}
{2010211001|XXGvertex_iport_iport|666|0|1030|0|{0|write|}364|365|}
{2010006001|XXGobject_psameas_object|667|0|1032|0|{metadata|write_metadata|1|0|}365|364|}
{2010006001|XXGobject_psameas_object|668|0|1033|0|{write_metadata|read_metadata|0|0|}362|122|}
{2010211001|XXGvertex_iport_iport|669|0|1034|0|{0|in0|}361|366|}
{2010215002|XXGiport_binding_iport|670|0|1036|0|{.5|.5|{0|}4517|}366|363|}
{2010214001|XXGiport_src_flow|671|0|1037|0|{0|}366|20|}
{2010601001|XXGgraph_vertex_vertex|672|0|1038|0|{last_model_date|}1|75|}
{2010601001|XXGgraph_vertex_vertex|673|0|1039|0|{last_model_date_2|}1|122|}
{2010601001|XXGgraph_vertex_vertex|674|0|1040|0|{rfm_dml_mongo_bcs|}1|307|}
{2010601001|XXGgraph_vertex_vertex|675|0|1041|0|{rfm_dml_mongo_neuro|}1|349|}
{2010601001|XXGgraph_vertex_vertex|676|0|1042|0|{risk_scores_func|}1|319|}
{2010109001|XXGobject_property_value|677|0|1043|0|{0|TrackingThumbprint|72|}1|367|}
