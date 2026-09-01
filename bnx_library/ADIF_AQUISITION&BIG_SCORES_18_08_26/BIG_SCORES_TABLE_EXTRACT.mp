@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|9|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|349|rel_count|650|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_semantic_schema|9|1|1|Hnl|@{0|}}
{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
{30001002|XXparameter|!ab_compatibility|4.1.6.2|3|9|P|@{0|}}
{30001002|XXparameter|FILE_DATE|$[(date("YYYYMMDD"))now()]|3|9|RK||{0|}}
{30001002|XXparameter|DB|$(if [[ `hostname \| awk -F "." '\{print $1\}'` == "sd-6dd4-7ac3" ]];then echo "gcgaeapmxcgnd_managed";  elif [[ `hostname \| awk -F "." '\{print $1\}'` == "sd-2635-e20b" ]]; then echo "gcgaeapmxcgnu_managed"; elif [[ `hostname \| awk -F "." '\{print $1\}'` == "jrgcg-mdwla03p" ]]; then echo "gcgaeapmxcgnp_managed"; else echo "NONE"; fi)|3|9|RK||{0|}}
{30001002|XXparameter|HIVE_LAYOUT|$(if [ `hostname \| awk -F "." '\{print $1\}'` == "sd-6dd4-7ac3" ];
then
echo "sd-ssan-53va"
else
echo "$\{HIVE_EXEC_LAYOUT\}"
fi )|3|9|RK||{0|}}
{30001002|XXparameter|MODELS|$(if [ -f "$AI_SERIAL/ing_file_big_table_scores_conf_param.txt" ];
then
echo `cat $AI_SERIAL/ing_file_big_table_scores_conf_param.txt \| awk -F "\|" '\{print $2\}'`
else
echo '"227938","230979","231078","207274","222566","227756","184527","P2986"'
fi )|3|9|RK||{0|}}
{30001002|XXparameter|MONTHS_NUM|$(if [ -f "$AI_SERIAL/ing_file_big_table_scores_conf_param.txt" ];
then
echo `cat $AI_SERIAL/ing_file_big_table_scores_conf_param.txt \| awk -F "\|" '\{print $1\}'`
else
echo '5'
fi )|3|9|RK||{0|}}
{30001002|XXparameter|_UseNewErrorLogDML|True|13|1|Hl||{0|}}
}}@0|@0|0|0|0|0|0|0|BIG_SCORES_TABLE_EXTRACT|lc80582|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|1665000|836000|7|}}
{2010703001|XXGgraphinfo|2|0|3|0|{@{}@1|4.0.2.4|{3|1|1|1|}Job 'BIG_SCORES_TABLE_EXTRACT' Execution Status Report

Job completed successfully at Wednesday, December 27, 2023 15:17:48
Run performed by user jv21157
||||@@33207807|}}
{2010705002|XXGrunsettings|3|0|5|0|{@{}@Home abinitio||||1|60|0|1|1|0|0|0|0|1|1|0|0|1|2|1|1|0|0|0|@16|}}
{2010242002|XXGface|4|0|7|0|{@{}@Arial|0|100|0|}}
{2010210004|XXGflow|5|0|9|0|{@{}@0|.5|.5|{0|}4466|17|}}
{2010243001|XXGwatcher|6|0|11|0|{@{}@1|100|-1||2|}}
{2010210004|XXGflow|7|0|13|0|{@{}@0|.5|.5|{0|}4548|17|}}
{2010210004|XXGflow|8|0|15|0|{@{}@0|.5|.5|{0|}4522|17|}}
{2010210004|XXGflow|9|0|17|0|{@{}@0|.5|.5|{0|}4467|20|}}
{2010210004|XXGflow|10|0|19|0|{@{}@0|.5|.5|{0|}4557|1043|}}
{2010210004|XXGflow|11|0|21|0|{@{}@0|.5|.5|{0|}4558|1043|}}
{2010210004|XXGflow|12|0|23|0|{@{}@0|.5|.5|{0|}4568|19|}}
{2010210004|XXGflow|13|0|25|0|{@{}@0|.5|.5|{0|}4565|1043|}}
{2010210004|XXGflow|14|0|27|0|{@{}@0|.5|.5|{0|}4563|17|}}
{2010243001|XXGwatcher|15|0|29|0|{@{}@1|1000|0||2|}}
{2010210004|XXGflow|16|0|31|0|{@{}@0|.5|.5|{0|}4566|1043|}}
{2010210004|XXGflow|17|0|33|0|{@{}@0|.5|.5|{0|}4487|17|}}
{2010210004|XXGflow|18|0|35|0|{@{}@0|.5|.5|{0|}4546|17|}}
{2010210004|XXGflow|19|0|37|0|{@{}@0|.5|.5|{0|}4562|17|}}
{2010210004|XXGflow|20|0|39|0|{@{}@0|.5|.5|{0|}4520|17|}}
{2010210004|XXGflow|21|0|41|0|{@{}@0|.5|.5|{0|}4543|17|}}
{2010210004|XXGflow|22|0|43|0|{@{}@0|.5|.5|{0|}4541|17|}}
{2010210004|XXGflow|23|0|45|0|{@{}@0|.5|.5|{0|}4549|17|}}
{2010243001|XXGwatcher|24|0|47|0|{@{}@1|1000|-1||2|}}
{2010503005|XXGfvertex|25|0|49|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$EDW_INBOX/BIG_TABLE_SCORES_$FILE_DATE.txt", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|write_metadata|$AI_DML/BIG_SCORES_FINAL_FILE.dml|3|2|f$|@{0|}}
{30001002|XXparameter|Layout|file:$EDW_INBOX/BIG_TABLE_SCORES_$FILE_DATE.txt|3|2|$|@{0|}}
}}@1|Output File|1561000|455000|0|0|0|0|4521|ALL_MODELS|Ab Initio Software|@1|100|0||6||33025|-1|-1|}}
{2010202004|XXGiport|26|0|51|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|27|0|54|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010202004|XXGiport|28|0|56|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|29|0|59|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Dedup_Sorted.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|key|\{model_id\}|3|2|$|@{0|}}
{30001002|XXparameter|dup_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Dedup Sorted|850000|220000|0|0|0|0|4544|Dedup Sorted|Ab Initio Software|Built-in 2.0:|1|100|0||6||1|1|{1|0|}}}
{2010203004|XXGoport|30|0|61|0|{@{}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|31|0|64|0|{@{}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|32|0|66|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|33|0|68|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|34|0|70|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|35|0|72|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|36|0|75|0|{Separates one specified data record in each group of data records from the rest of the records in the group.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|dedup|3|1|Hl||{0|}}
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
{2010203004|XXGoport|37|0|77|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|38|0|80|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|39|0|83|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|40|0|86|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|41|0|89|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|42|0|92|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010503005|XXGfvertex|43|0|95|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_MFS/BIG_SCORES_LKP.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|mfile:$AI_MFS/BIG_SCORES_LKP.dat|3|2|$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
}}@0|Output File|1056000|235000|0|0|0|0|4547|Output File-1|Ab Initio Software|@1|100|-1||6||33025|-1|-1|}}
{2010202004|XXGiport|44|0|97|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|45|0|100|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010202004|XXGiport|46|0|102|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|47|0|105|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|filereject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
}}@0|@445000|68000|0|0|0|0|4014|Read Blocks|||1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|48|0|107|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|49|0|109|0|{@{}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|50|0|111|0|{@{}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|51|0|113|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|52|0|115|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|53|0|117|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|54|0|119|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010210004|XXGflow|55|0|121|0|{@{}@384|.5|.5|{0|}4017|20|}}
{2010501005|XXGpvertex|56|0|123|0|{Walks the directory tree starting from paths specified on the input flow.  Produces a list of files to be read as well as the files' block and address info.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|in0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|@60000|50000|0|0|0|0|4020|Find Files and Read Blocks|Ab Initio Software|Built-in 2.14:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|57|0|125|0|{@{}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010210004|XXGflow|58|0|127|0|{@{}@384|.5|.5|{0|}4019|17|}}
{2010203004|XXGoport|59|0|129|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|60|0|131|0|{@{}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|61|0|133|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
}}@0|Run Program|115000|224000|0|0|0|0|4026|Generate Partition Data|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|62|0|135|0|{@{}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010210004|XXGflow|63|0|137|0|{@{}@384|.5|.5|{0|}4025|17|}}
{2010202004|XXGiport|64|0|139|0|{@{}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010503005|XXGfvertex|65|0|141|0|{|{}@0|@209000|123000|0|0|0|0|4013|Partition Data|Ab Initio Software|@1|100|-1||6||33025|-1|-1|}}
{2010203004|XXGoport|66|0|143|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010210004|XXGflow|67|0|145|0|{@{}@384|.5|.5|{0|}4014|17|}}
{2010501005|XXGpvertex|68|0|153|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Join.mpc|3|2|Pf$|@{0|}}
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
}}@1|Join|849000|500000|0|0|0|0|4551|Join|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|69|0|155|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|70|0|158|0|{@{}@0|0|0|0|unused0|0.0|count|unused|0|1168|0|}}
{2010203004|XXGoport|71|0|160|0|{@{}@0|0|0|0|unused1|0.0|count|unused|1|1168|0|}}
{2010203004|XXGoport|72|0|162|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|73|0|164|0|{@{}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|74|0|166|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|75|0|168|0|{@{}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|76|0|170|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|77|0|172|0|{@{}@0|0|0|0|in0|0.0|count|in|0|1808|0|}}
{2010202004|XXGiport|78|0|175|0|{@{}@0|0|0|0|in1|0.0|count|in|1|1808|0|}}
{2010501005|XXGpvertex|79|0|178|0|{Performs inner, outer, and semi-joins with multiple flows of data records. It maximizes performance by loading input data records into main memory.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|?join|3|1|Hl||{0|}}
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
{2010203004|XXGoport|80|0|180|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|81|0|183|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|unused0|0.0|count|unused|0|1168|0|}}
{2010203004|XXGoport|82|0|186|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|unused1|0.0|count|unused|1|1168|0|}}
{2010203004|XXGoport|83|0|189|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|84|0|192|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|85|0|195|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|86|0|198|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|87|0|201|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|88|0|204|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
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
{2010202004|XXGiport|89|0|222|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
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
{2010503005|XXGfvertex|90|0|240|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_MFS/BIG_SCORES_LKP.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|mode|0x0001|3|2|$|@{0|}}
{30001002|XXparameter|read_metadata|$AI_DML/hive_big_table_scores_t_m.dml|3|2|f$|@{0|}}
{30001002|XXparameter|Layout|mfile:$AI_MFS/BIG_SCORES_LKP.dat|3|2|$|@{0|}}
}}@1|Output File|815000|415000|0|0|0|0|4545|Output File-3|Ab Initio Software|@1|100|-1||6||33025|-1|-1|}}
{2010203004|XXGoport|91|0|242|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|92|0|245|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010203004|XXGoport|93|0|247|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010501005|XXGpvertex|94|0|257|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Merge.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|key|\{model_id\}|3|2|$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Merge|1423000|465000|0|0|0|0|4452|Merge|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|95|0|259|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|96|0|262|0|{@{}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010501005|XXGpvertex|97|0|265|0|{Combines data records from multiple flow partitions that have been sorted according to the key specifier, and maintains the sort order.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-merge|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field to merge on|{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 3.1.2.r10:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Merge|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|98|0|267|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|99|0|270|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010501005|XXGpvertex|100|0|276|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Merge.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|key|\{model_id\}|3|2|$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Merge|1438000|590000|0|0|0|0|4497|Merge-1|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|101|0|278|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|102|0|281|0|{@{}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010501005|XXGpvertex|103|0|284|0|{Combines data records from multiple flow partitions that have been sorted according to the key specifier, and maintains the sort order.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-merge|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field to merge on|{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 3.1.2.r10:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Merge|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|104|0|286|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|105|0|289|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010503005|XXGfvertex|106|0|292|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$EDW_INBOX/NEUROLANDS_$FILE_DATE.txt", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|write_metadata|$AI_DML/NEURONALS_FINAL_FILE.dml|3|2|f$|@{0|}}
{30001002|XXparameter|Layout|file:$EDW_INBOX/NEUROLANDS_$FILE_DATE.txt|3|2|$|@{0|}}
}}@1|Output File|1566000|580000|0|0|0|0|4523|NEUROLANDS|Ab Initio Software|@1|100|0||6||33025|-1|-1|}}
{2010202004|XXGiport|107|0|294|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|108|0|297|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010202004|XXGiport|109|0|299|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|110|0|307|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Partition_by_Key.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|key|\{model_id\}|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Partition by Key|287000|250000|0|0|0|0|4445|Partition by Key|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|111|0|309|0|{@{}@0|0|0|0|out|0.0|@@@2322|0|}}
{2010202004|XXGiport|112|0|312|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|113|0|315|0|{Distributes data records to its output flow partitions according to key values.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|hash-partition|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field to partition on|{0|}}
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
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Partition by Key|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|114|0|317|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2322|0|}}
{2010202004|XXGiport|115|0|320|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010600005|XXGgraph|116|0|326|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Hadoop/Read_Hive_Table.mp|3|2|Pf$|@{0|}}
{30001002|XXparameter|HIVE_LAYOUT|$\{HIVE_LAYOUT\}|3|9||@{0|}}
{30001002|XXparameter|FILE_FORMAT|parquet|3|9||@{0|}}
{30001002|XXparameter|OUTPUT_DML|$AI_DML/hive_big_table_scores_t_m.dml|3|2|f$|@{0|}}
{30001002|XXparameter|DATABASE|$\{DB\}|3|9||@{0|}}
{30001002|XXparameter|TABLE|big_table_scores_t_m|3|9||@{0|}}
{30001002|XXparameter|HOST_LIST|$\{HIVE_LAYOUT\}|3|9||@{0|}}
{30001002|XXparameter|HOST_DEPTH|1|3|9||@{0|}}
{30001002|XXparameter|READ_LAYOUT|$\{HIVE_LAYOUT\}|3|2|$|@{0|}}
{30001002|XXparameter|FILTER_EXPR|(date("YYYY-MM-DD"))(last_updated_date) >= date_add_months((date("YYYY-MM-DD"))today(),-$\{MONTHS_NUM\}) and model_id member [vector $MODELS]|3|9||@{0|}}
}}@0|@45000|216500|0|0|0|0|4456|Read Hive Table|Ab Initio|Created 11/21/2014 2:25:51 PM|1|100|0|@9|@4097|{0|}0|0|{0|}{0|}{0|}{0|}1.0|835000|407000|0|}}
{2010210004|XXGflow|117|0|329|0|{@{}@384|.5|.5|{0|}4035|17|}}
{2010501005|XXGpvertex|118|0|332|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|deselect_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|@399000|160000|0|0|0|0|4015|Filter Partitions|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|119|0|334|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|120|0|337|0|{@{}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|121|0|339|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|122|0|341|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|123|0|343|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|124|0|345|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010600005|XXGgraph|125|0|356|0|{COPYRIGHT AB INITIO
ALL RIGHTS RESERVED
USE AND DISCLOSURE IS RESTRICTED BY CONFIDENTIALITY & LICENSE CONDITIONS|{}@0|@590000|151000|0|0|0|0|4036|Read HDFS Files|Ab Initio|Created 8/26/2015 3:21:55 PM|1|100|0|@9|@1|{0|}0|0|{0|}{0|}{0|}{0|}1.0|739000|210000|0|}}
{2010501005|XXGpvertex|126|0|361|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|@242000|61000|249000|75000|132000|107000|4018|Partition Blocks|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|127|0|363|0|{@{}@380000|124000|11000|11000|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|128|0|366|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|129|0|368|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|130|0|370|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|131|0|372|0|{@{}@239000|124000|11000|11000|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|132|0|380|0|{@{}@0|0|0|0|out0|.5117370892018779|@@@14352|0|}}
{2010202004|XXGiport|133|0|383|0|{@{}@0|0|0|0|in0|.5044642857142857|@@@13840|0|}}
{2010600005|XXGgraph|134|0|387|0|{Subgraph created from graph "Read_Hive_Table"|{}@0|@39500|98500|0|0|0|0|4024|Validate HIVE_LAYOUT|Ab Initio|@1|100|-1|@9|@32769|{0|}0|0|{0|}{0|}{0|}{0|}1.0|298000|184000|2|}}
{2010210004|XXGflow|135|0|389|0|{@{}@0|.5|.5|{0|}4059|17|}}
{2010501005|XXGpvertex|136|0|391|0|{|{}@0|Create Data|66000|85000|0|0|0|0|4060|Perform Validation|Ab Initio Software|Built-in 2.15.2:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|137|0|393|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|138|0|396|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|139|0|398|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|140|0|400|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Trash|171000|80000|0|0|0|0|4058|Trash|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010202004|XXGiport|141|0|402|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|142|0|407|0|{@{}@0|0|0|0|out0|.6354916067146283|@@@14352|0|}}
{2010600005|XXGgraph|143|0|411|0|{Reads data sequentially from a Hadoop Distributed File System. Can optionally select data from a Hive partition using the query you provide. Only for batch graphs.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
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
{2010210004|XXGflow|144|0|413|0|{@{}@384|.5|.5|{0|}4014|17|}}
{2010210004|XXGflow|145|0|415|0|{@{}@384|.5|.5|{0|}4035|17|}}
{2010210004|XXGflow|146|0|417|0|{@{}@384|.5|.5|{0|}4025|17|}}
{2010501005|XXGpvertex|147|0|419|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Filter_by_Expression.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|select_expr||3|8|=|@{0|}}
{30001002|XXparameter|error_group||3|8|=|@{0|}}
{30001002|XXparameter|log_group||3|8|=|@{0|}}
{30001002|XXparameter|reject_threshold||3|8|=|@{0|}}
{30001002|XXparameter|logging||3|8|=|@{0|}}
}}@0|@399000|160000|0|0|0|0|4015|Filter Partitions|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|148|0|421|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|149|0|424|0|{@{}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|150|0|426|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|151|0|428|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|152|0|430|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|153|0|432|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|154|0|436|0|{Filters data records according to the specified DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|select-transform|3|1|Hl||{0|}}
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
{2010203004|XXGoport|155|0|438|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|156|0|441|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|157|0|444|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|158|0|447|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|159|0|450|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|160|0|453|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|161|0|461|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Run_Program.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|commandline|hive-to-dml -partitions $[if (USE_DML_DATES) "" else "-integer_dates"] $DATABASE $TABLE|3|9||@{0|}}
{30001002|XXparameter|condition|$[ is_blank(PARTITION_DATA_PATH) ]|3|9||@{0|}}
{30001002|XXparameter|Layout|$INTERNAL_HIVE_LAYOUT|3|2|$|@{0|}}
}}@0|Run Program|115000|224000|0|0|0|0|4026|Generate Partition Data|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|162|0|463|0|{@{}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|163|0|466|0|{@{}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010501005|XXGpvertex|164|0|468|0|{Executes a standard UNIX or Windows program.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|filter|3|1|Hl||{0|}}
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
{2010203004|XXGoport|165|0|470|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|166|0|473|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010503005|XXGfvertex|167|0|476|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|condition|$[ not is_blank(PARTITION_DATA_PATH) ]|3|9||@{0|}}
{30001002|XXparameter|Layout|$PARTITION_DATA_PATH|3|2|$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$PARTITION_DATA_PATH", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|read_metadata|$\{PARTITION_DML\}|3|3|c|@{0|}}
}}@0|@209000|123000|0|0|0|0|4013|Partition Data|Ab Initio Software|@1|100|-1||6||33025|-1|-1|}}
{2010203004|XXGoport|168|0|478|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|169|0|481|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010203004|XXGoport|170|0|483|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010600005|XXGgraph|171|0|486|0|{COPYRIGHT AB INITIO
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
{2010210004|XXGflow|172|0|488|0|{@{}@384|.5|.5|{0|}4019|17|}}
{2010210004|XXGflow|173|0|490|0|{@{}@384|.5|.5|{0|}4017|20|}}
{2010501005|XXGpvertex|174|0|492|0|{Walks the directory tree starting from paths specified on the input flow.  Produces a list of files to be read as well as the files' block and address info.|{}@0|@60000|50000|0|0|0|0|4020|Find Files and Read Blocks|Ab Initio Software|Built-in 2.14:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|175|0|494|0|{@{}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010203004|XXGoport|176|0|497|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|177|0|499|0|{@{}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|178|0|501|0|{|{}@0|@242000|61000|249000|75000|132000|107000|4018|Partition Blocks|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|179|0|503|0|{@{}@380000|124000|11000|11000|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|180|0|506|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|181|0|508|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|182|0|510|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|183|0|512|0|{@{}@239000|124000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|184|0|515|0|{|{}@0|@445000|68000|0|0|0|0|4014|Read Blocks|||1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|185|0|517|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|186|0|519|0|{@{}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|187|0|521|0|{@{}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|188|0|523|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|189|0|525|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|190|0|527|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|191|0|529|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|192|0|532|0|{@{}@0|0|0|0|out0|.5117370892018779|@@@14352|0|}}
{2010202004|XXGiport|193|0|535|0|{@{}@0|0|0|0|in0|.5044642857142857|@@@13840|0|}}
{2010600005|XXGgraph|194|0|539|0|{COPYRIGHT AB INITIO
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
{2010210004|XXGflow|195|0|541|0|{@{}@384|.5|.5|{0|}4019|17|}}
{2010210004|XXGflow|196|0|543|0|{@{}@384|.5|.5|{0|}4017|20|}}
{2010501005|XXGpvertex|197|0|545|0|{Walks the directory tree starting from paths specified on the input flow.  Produces a list of files to be read as well as the files' block and address info.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Advanced/Procedural_Transform.mpc|3|2|Pf$|@{0|}}
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
}}@0|@60000|50000|0|0|0|0|4020|Find Files and Read Blocks|Ab Initio Software|Built-in 2.14:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|198|0|547|0|{@{}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010203004|XXGoport|199|0|550|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|200|0|552|0|{@{}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|201|0|554|0|{Runs code translated into DML from a procedural language such as COBOL.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|proctrans|3|1|Hl||{0|}}
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
{2010203004|XXGoport|202|0|556|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out0|0.0|out_count|out|0|2193|0|}}
{2010203004|XXGoport|203|0|559|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|204|0|562|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in0|0.0|in_count|in|0|1553|0|}}
{2010501005|XXGpvertex|205|0|565|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Partition_by_Expression.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|function|if (write_to_log(event_type="Hostname",event_text=(decimal(""))length_of(get_partitions("bwang-l")) )) 0|3|2|$|@{0|}}
{30001002|XXparameter|use_package|True|3|1|l|@{0|}}
{30001002|XXparameter|package||3|8|=|@{0|}}
{30001002|XXparameter|reject_threshold||3|8|=|@{0|}}
{30001002|XXparameter|logging||3|8|=|@{0|}}
{30001002|XXparameter|error_group||3|8|=|@{0|}}
{30001002|XXparameter|log_group||3|8|=|@{0|}}
}}@0|@242000|61000|249000|75000|132000|107000|4018|Partition Blocks|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|206|0|567|0|{@{}@380000|124000|11000|11000|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|207|0|570|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|208|0|572|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|209|0|574|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|210|0|576|0|{@{}@239000|124000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|211|0|579|0|{Distributes data records to its output flow partitions according to the specified DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|function-partition|3|1|Hl||{0|}}
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
{2010203004|XXGoport|212|0|581|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|213|0|584|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|214|0|587|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|215|0|590|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|216|0|593|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|217|0|601|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Read_Multiple_Files.mpc|3|9|Pf|@{0|}}
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
}}@0|@445000|68000|0|0|0|0|4014|Read Blocks|||1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|218|0|603|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|219|0|605|0|{@{}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|220|0|607|0|{@{}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|221|0|609|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|222|0|611|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|223|0|613|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|224|0|615|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|225|0|618|0|{Sequentially reads from a list of input files.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|readfiles|3|1|Hl||{0|}}
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
{2010203004|XXGoport|226|0|620|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|227|0|623|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|filereject|0.0|@@@1168|0|}}
{2010203004|XXGoport|228|0|626|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|fileerror|0.0|@@@1168|0|}}
{2010203004|XXGoport|229|0|629|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|230|0|632|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|231|0|635|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|232|0|638|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|233|0|649|0|{@{}@0|0|0|0|out0|.5117370892018779|@@@14352|0|}}
{2010202004|XXGiport|234|0|652|0|{@{}@0|0|0|0|in0|.5044642857142857|@@@13840|0|}}
{2010600005|XXGgraph|235|0|671|0|{Subgraph created from graph "Read_Hive_Table"|{}@0|@39500|98500|0|0|0|0|4024|Validate HIVE_LAYOUT|Ab Initio|@1|100|-1|@9|@32769|{0|}0|0|{0|}{0|}{0|}{0|}1.0|298000|184000|2|}}
{2010210004|XXGflow|236|0|673|0|{@{}@0|.5|.5|{0|}4059|17|}}
{2010501005|XXGpvertex|237|0|675|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Validate/Create_Data.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|transform|let x = if (number_of_partitions() > 1) force_abort("HIVE_LAYOUT must be serial. (Input value: " + $"HIVE_LAYOUT" + ")") else 0;

out::create(index) = begin
  out :: 0;
end;|3|9||@{0|}}
{30001002|XXparameter|num_records|0|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|int;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|=|@{0|}}
}}@0|Create Data|66000|85000|0|0|0|0|4060|Perform Validation|Ab Initio Software|Built-in 2.15.2:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|238|0|677|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|239|0|680|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|240|0|682|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|241|0|684|0|{Creates records according to a transform.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|Create_Data|3|1|Hl||{0|}}
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
{2010203004|XXGoport|242|0|686|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|243|0|689|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|244|0|692|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|245|0|696|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Trash.mpc|3|2|Pf$|@{0|}}
}}@0|Trash|171000|80000|0|0|0|0|4058|Trash|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010202004|XXGiport|246|0|698|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|247|0|701|0|{Ends a flow by discarding all input data records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
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
{2010202004|XXGiport|248|0|703|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010203004|XXGoport|249|0|706|0|{@{}@0|0|0|0|out0|.6354916067146283|@@@14352|0|}}
{2010501005|XXGpvertex|250|0|709|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Replicate.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Replicate|737000|250000|0|0|0|0|4542|Replicate|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|251|0|711|0|{@{}@0|0|0|0|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|252|0|715|0|{@{}@0|0|0|0|in|0.0|@@@1812|0|}}
{2010501005|XXGpvertex|253|0|718|0|{Arbitrarily combines all the data records it receives into a single flow and writes a copy of that flow to each of its output flows.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
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
{2010203004|XXGoport|254|0|720|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|255|0|723|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1812|0|}}
{2010600005|XXGgraph|256|0|729|0|{Subgraph created from graph "BIG_SCORES_TABLE_EXTRACT"|{}@0|@1201000|700000|0|0|0|0|4567|Risk_scores Rejected|lc80582|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|278000|343000|7|}}
{2010210004|XXGflow|257|0|731|0|{@{}@0|.5|.5|{0|}4507|17|}}
{2010210004|XXGflow|258|0|733|0|{@{}@0|.5|.5|{0|}4509|17|}}
{2010501005|XXGpvertex|259|0|735|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Merge.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|key|\{model_id; last_updated_date descending\}|3|2|$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Merge|69000|79000|0|0|0|0|4503|Merge-3|Ab Initio Software|Built-in 1.0:|1|100|0||6||32897|1|{1|0|}}}
{2010203004|XXGoport|260|0|737|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|261|0|740|0|{@{}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010501005|XXGpvertex|262|0|742|0|{Combines data records from multiple flow partitions that have been sorted according to the key specifier, and maintains the sort order.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-merge|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field to merge on|{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 3.1.2.r10:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Merge|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|263|0|744|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|264|0|747|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010503005|XXGfvertex|265|0|750|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL_LOG/bcs_risk_scores_rej.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL_LOG/bcs_risk_scores_rej.dat|3|2|$|@{0|}}
}}@1|Output File|53000|205000|0|0|0|0|4508|bcs_risk_rej|Ab Initio Software|@1|100|0||6||32897|-1|-1|}}
{2010202004|XXGiport|266|0|752|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|267|0|755|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010202004|XXGiport|268|0|757|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|269|0|760|0|{Add all functionality about RISK_MODEL string to convert to a vector.
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
{30001002|XXparameter|out0_metadata|///////////////////////////////////////////////////////////////////////
// This file was automatically generated by Ab Initio 
// on Fri Feb 17 22:02:03 2023
//
// !! WARNING: ANY EDITS WILL BE LOST UPON REGENERATION OF THIS FILE !!
//
// The following settings were used to generate the DML.
//  criteria: \{ \}
//  projection: \{ \}
//  max_docs: 100
//
///////////////////////////////////////////////////////////////////////
record
  utf8 string(int) customer_id = NULL;
  utf8 string(int) model_id = NULL;
  little endian integer(4) score_model_tp = NULL;
  record
    utf8 string(int) customer_seg = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") customer_seg_dt = NULL;
  end[int] CUSTOMER_SEGMENTS = NULL;
  utf8 string(int) RISK_SCORES1;
  /*record
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") credit_approved_dt = NULL;
    little endian integer(1) credit_approved_flag = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) credit_score_decile_val = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) credit_score_quartile_val = NULL;
    decimal("\\x01", maximum_length=42, sign_reserved, allow_exponent) score = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_info_dt = NULL;
    utf8 string(int) score_name = NULL;
    datetime("YYYY-MM-DD-HH24.MI.SS.NNN") score_process_dt = NULL;
  end[int] RISK_SCORES = NULL; */
  decimal(3)length_risk_scores;
  utf8 string(int) last_updated_date = NULL;
end;|3|1|l|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_threshold|Never abort|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Reformat|1007000|500500|0|0|0|0|4564|cust_seg func|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|270|0|762|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|271|0|765|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|272|0|768|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|273|0|770|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|274|0|772|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|275|0|775|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
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
{2010203004|XXGoport|276|0|777|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|277|0|781|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|278|0|784|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|279|0|787|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|280|0|790|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|281|0|798|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Merge.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|key|\{model_id; length_risk_scores descending\}|3|2|$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Merge|174000|89000|0|0|0|0|4505|Merge-4|Ab Initio Software|Built-in 1.0:|1|100|0||6||32897|1|{1|0|}}}
{2010203004|XXGoport|282|0|800|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|283|0|803|0|{@{}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010501005|XXGpvertex|284|0|805|0|{Combines data records from multiple flow partitions that have been sorted according to the key specifier, and maintains the sort order.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-merge|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field to merge on|{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 3.1.2.r10:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Merge|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|285|0|807|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|286|0|810|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010503005|XXGfvertex|287|0|813|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL_LOG/neuro_risk_scores_rej.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL_LOG/neuro_risk_scores_rej.dat|3|2|$|@{0|}}
}}@1|Output File|158000|205000|0|0|0|0|4510|neuro_rej|Ab Initio Software|@1|100|0||6||32897|-1|-1|}}
{2010202004|XXGiport|288|0|815|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|289|0|818|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010202004|XXGiport|290|0|820|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010202004|XXGiport|291|0|828|0|{@{}@0|0|0|0|in0|0.0|@@@8720|0|}}
{2010202004|XXGiport|292|0|832|0|{@{}@0|0|0|0|in1|0.0|@@@8720|0|}}
{2010501005|XXGpvertex|293|0|836|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Run_Program.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|commandline|ksh $AI_BIN/adif_big_collection_score_remove_temp_files.ksh|3|2|$|@{0|}}
{30001002|XXparameter|Layout|$AI_SERIAL|3|2|$|@{0|}}
}}@0|Run Program|190000|465000|0|0|0|0|4512|Run Program|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|294|0|838|0|{@{}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|295|0|840|0|{@{}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010501005|XXGpvertex|296|0|842|0|{Executes a standard UNIX or Windows program.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|filter|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|commandline||16|2|RFO$|Command line of UNIX or Windows program to execute|{0|}}
{30001002|XXparameter|NoHidePorts|in out|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=all_to_all(in)|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Run Program|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|297|0|844|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|298|0|847|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010501005|XXGpvertex|299|0|850|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Sort/Sort.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|key|\{model_id\}|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Sort|417000|230000|0|0|0|0|4469|Sort|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|300|0|852|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|301|0|855|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|302|0|858|0|{Orders your data according to a key specifier.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-sort|3|1|Hl||{0|}}
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
{2010203004|XXGoport|303|0|860|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|304|0|863|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|305|0|869|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Sort/Sort_within_Groups.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|major_key|\{model_id\}|3|2|$|@{0|}}
{30001002|XXparameter|minor_key|\{last_updated_date descending\}|3|2|$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Sort within Groups|558000|215000|0|0|0|0|4489|Sort within Groups|Ab Initio Software|Built-in 2.1.7:|1|100|0||6||1|1|{1|0|}}}
{2010203004|XXGoport|306|0|871|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|307|0|874|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|308|0|877|0|{Refines the sorting of data records already sorted according to one key specifier: it sorts the records within the groups formed by the first sort according to a second key specifier.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|sort-groups|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|major_key||19|2|RFK$|Input is assumed to be sorted on this key|{0|}}
{30001002|XXparameter|major_key.display_name|major-key|3|9|P|@{0|}}
{30001002|XXparameter|major_key.keyword|major-key|3|9|P|@{0|}}
{30001002|XXparameter|minor_key||19|2|RFK$|Input will be sorted within groups on this key|{0|}}
{30001002|XXparameter|minor_key.display_name|minor-key|3|9|P|@{0|}}
{30001002|XXparameter|minor_key.keyword|minor-key|3|9|P|@{0|}}
{30001002|XXparameter|max_core|10485760|1|2|FK$|maximum memory usage in bytes|{0|}}
{30001002|XXparameter|max_core.display_name|max-core|3|9|P|@{0|}}
{30001002|XXparameter|max_core.keyword|max-core|3|9|P|@{0|}}
{30001002|XXparameter|allow_unsorted|false|13|1|FKl|Allows input not sorted by major key|{0|}}
{30001002|XXparameter|allow_unsorted.display_name|allow-unsorted|3|9|P|@{0|}}
{30001002|XXparameter|allow_unsorted.keyword|allow-unsorted|3|9|P|@{0|}}
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
}}@0|Sort within Groups|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|309|0|879|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|310|0|882|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|311|0|888|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Run_Program.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|Layout|$AI_SERIAL|3|2|$|@{0|}}
{30001002|XXparameter|commandline|ksh $AI_BIN/adif_mail_extraction_summary.ksh|3|2|$|@{0|}}
}}@2|Run Program|453000|465000|0|0|0|0|4552|Summary extraction|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|312|0|890|0|{@{}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|313|0|892|0|{@{}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010501005|XXGpvertex|314|0|894|0|{Executes a standard UNIX or Windows program.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|filter|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|commandline||16|2|RFO$|Command line of UNIX or Windows program to execute|{0|}}
{30001002|XXparameter|NoHidePorts|in out|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=all_to_all(in)|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Run Program|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|315|0|896|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|out|0.0|@@@2260|0|}}
{2010202004|XXGiport|316|0|899|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|in|0.0|@@@1732|0|}}
{2010600005|XXGgraph|317|0|903|0|{Subgraph created from graph "BIG_SCORES_TABLE_EXTRACT"|{}@0|@1019000|703000|0|0|0|0|4569|cust seg rejected|lc80582|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|166000|316000|7|}}
{2010210004|XXGflow|318|0|905|0|{@{}@0|.5|.5|{0|}4508|17|}}
{2010501005|XXGpvertex|319|0|907|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Merge.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|key|\{model_id; last_updated_date descending\}|3|2|$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Merge|60000|79000|0|0|0|0|4506|Merge-2|Ab Initio Software|Built-in 1.0:|1|100|0||6||32897|1|{1|0|}}}
{2010203004|XXGoport|320|0|909|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|321|0|912|0|{@{}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010501005|XXGpvertex|322|0|914|0|{Combines data records from multiple flow partitions that have been sorted according to the key specifier, and maintains the sort order.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-merge|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|key||19|2|RFO$|Field to merge on|{0|}}
{30001002|XXparameter|check_sort|True|13|1|FKl|Abort on first record that is out of sorted order|{0|}}
{30001002|XXparameter|check_sort.display_name|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.keyword|check-sort|3|9|P|@{0|}}
{30001002|XXparameter|check_sort.condition|version 3.1.2.r10:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1675912812|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Merge|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|323|0|916|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|324|0|919|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@50963|0|}}
{2010503005|XXGfvertex|325|0|922|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL_LOG/bcs_cust_seg_rej.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL_LOG/bcs_cust_seg_rej.dat|3|2|$|@{0|}}
}}@1|Output File|44000|185000|0|0|0|0|4509|models rejected|Ab Initio Software|@1|100|-1||6||33153|-1|-1|}}
{2010202004|XXGiport|326|0|924|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|327|0|927|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{2010202004|XXGiport|328|0|929|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010202004|XXGiport|329|0|936|0|{@{}@0|0|0|0|in0|0.0|@@@8720|0|}}
{2010501005|XXGpvertex|330|0|940|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
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
{30001002|XXparameter|out0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out1_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_threshold|Never abort|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Reformat|1183000|500000|0|0|0|0|4561|risk_scores func|Ab Initio Software|Built-in 1.0:|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|331|0|942|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|332|0|945|0|{@{}@0|0|0|0|out1|0.0|count|out|1|2448|0|}}
{2010203004|XXGoport|333|0|948|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|334|0|951|0|{@{}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|335|0|954|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|336|0|956|0|{@{}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|337|0|958|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|338|0|960|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|339|0|963|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
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
{2010203004|XXGoport|340|0|965|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|341|0|969|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform1||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform1.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform1.index_value|1|3|9|P|@{0|}}
{30001002|XXparameter|transform1.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out1|0.0|count|out|1|2448|0|}}
{2010203004|XXGoport|342|0|973|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|343|0|976|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|344|0|979|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|345|0|982|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|346|0|985|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|347|0|988|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010110002|XXGconstant|348|0|997|0|{@{}@{1|1981395|}}}
{2010002001|XXGdirectory_object_object|0|1|2|0|{XXGgraph|}0|1|}
{2010704001|XXGgraph_graphinfo_graphinfo|1|0|2|0|{}1|2|}
{2010706001|XXGgraphinfo_runsettings_runsettings|2|0|4|0|{}2|3|}
{2010109001|XXGobject_property_value|3|0|6|0|{0|legend_face|92|}2|4|}
{2010604001|XXGgraph_flow_flow|4|0|8|0|{Flow_1|}1|5|}
{2010244001|XXGflow_watcher_watcher|5|0|10|0|{}5|6|}
{2010604001|XXGgraph_flow_flow|6|0|12|0|{Flow_10|}1|7|}
{2010604001|XXGgraph_flow_flow|7|0|14|0|{Flow_11|}1|8|}
{2010604001|XXGgraph_flow_flow|8|0|16|0|{Flow_12|}1|9|}
{2010604001|XXGgraph_flow_flow|9|0|18|0|{Flow_13|}1|10|}
{2010604001|XXGgraph_flow_flow|10|0|20|0|{Flow_14|}1|11|}
{2010604001|XXGgraph_flow_flow|11|0|22|0|{Flow_18|}1|12|}
{2010604001|XXGgraph_flow_flow|12|0|24|0|{Flow_19|}1|13|}
{2010604001|XXGgraph_flow_flow|13|0|26|0|{Flow_2|}1|14|}
{2010244001|XXGflow_watcher_watcher|14|0|28|0|{}14|15|}
{2010604001|XXGgraph_flow_flow|15|0|30|0|{Flow_20|}1|16|}
{2010604001|XXGgraph_flow_flow|16|0|32|0|{Flow_3|}1|17|}
{2010604001|XXGgraph_flow_flow|17|0|34|0|{Flow_4|}1|18|}
{2010604001|XXGgraph_flow_flow|18|0|36|0|{Flow_5|}1|19|}
{2010604001|XXGgraph_flow_flow|19|0|38|0|{Flow_6|}1|20|}
{2010604001|XXGgraph_flow_flow|20|0|40|0|{Flow_7|}1|21|}
{2010604001|XXGgraph_flow_flow|21|0|42|0|{Flow_8|}1|22|}
{2010604001|XXGgraph_flow_flow|22|0|44|0|{Flow_9|}1|23|}
{2010244001|XXGflow_watcher_watcher|23|0|46|0|{}23|24|}
{2010601001|XXGgraph_vertex_vertex|24|0|48|0|{ALL_MODELS|}1|25|}
{2010211001|XXGvertex_iport_iport|25|0|50|0|{0|write|}25|26|}
{2010214001|XXGiport_src_flow|26|0|52|0|{0|}26|20|}
{2010007001|XXGobject_proto_object|27|0|53|0|{}25|27|}
{2010211001|XXGvertex_iport_iport|28|0|55|0|{0|write|}27|28|}
{2010006001|XXGobject_psameas_object|29|0|57|0|{metadata|write_metadata|1|0|}28|27|}
{2010601001|XXGgraph_vertex_vertex|30|0|58|0|{Dedup_Sorted|}1|29|}
{2010212001|XXGvertex_oport_oport|31|0|60|0|{0|out|}29|30|}
{2010213001|XXGoport_dst_flow|32|0|62|0|{0|}30|18|}
{2010212001|XXGvertex_oport_oport|33|0|63|0|{1|dup|}29|31|}
{2010212001|XXGvertex_oport_oport|34|0|65|0|{2|reject|}29|32|}
{2010212001|XXGvertex_oport_oport|35|0|67|0|{3|error|}29|33|}
{2010212001|XXGvertex_oport_oport|36|0|69|0|{4|log|}29|34|}
{2010211001|XXGvertex_iport_iport|37|0|71|0|{0|in|}29|35|}
{2010214001|XXGiport_src_flow|38|0|73|0|{0|}35|21|}
{2010007001|XXGobject_proto_object|39|0|74|0|{}29|36|}
{2010212001|XXGvertex_oport_oport|40|0|76|0|{0|out|}36|37|}
{2010006001|XXGobject_psameas_object|41|0|78|0|{metadata|out_metadata|1|0|}37|36|}
{2010212001|XXGvertex_oport_oport|42|0|79|0|{1|dup|}36|38|}
{2010006001|XXGobject_psameas_object|43|0|81|0|{metadata|dup_metadata|1|0|}38|36|}
{2010212001|XXGvertex_oport_oport|44|0|82|0|{2|reject|}36|39|}
{2010006001|XXGobject_psameas_object|45|0|84|0|{metadata|reject_metadata|1|0|}39|36|}
{2010212001|XXGvertex_oport_oport|46|0|85|0|{3|error|}36|40|}
{2010006001|XXGobject_psameas_object|47|0|87|0|{metadata|error_metadata|1|0|}40|36|}
{2010212001|XXGvertex_oport_oport|48|0|88|0|{4|log|}36|41|}
{2010006001|XXGobject_psameas_object|49|0|90|0|{metadata|log_metadata|1|0|}41|36|}
{2010211001|XXGvertex_iport_iport|50|0|91|0|{0|in|}36|42|}
{2010006001|XXGobject_psameas_object|51|0|93|0|{metadata|in_metadata|1|0|}42|36|}
{2010006001|XXGobject_psameas_object|52|0|94|0|{Layout|Layout|0|0|}29|43|}
{2010211001|XXGvertex_iport_iport|53|0|96|0|{0|write|}43|44|}
{2010214001|XXGiport_src_flow|54|0|98|0|{0|}44|18|}
{2010007001|XXGobject_proto_object|55|0|99|0|{}43|45|}
{2010211001|XXGvertex_iport_iport|56|0|101|0|{0|write|}45|46|}
{2010006001|XXGobject_psameas_object|57|0|103|0|{metadata|write_metadata|1|0|}46|45|}
{2010006001|XXGobject_psameas_object|58|0|104|0|{write_metadata|out_metadata|0|0|}43|47|}
{2010212001|XXGvertex_oport_oport|59|0|106|0|{0|out|}47|48|}
{2010212001|XXGvertex_oport_oport|60|0|108|0|{1|filereject|}47|49|}
{2010212001|XXGvertex_oport_oport|61|0|110|0|{2|fileerror|}47|50|}
{2010212001|XXGvertex_oport_oport|62|0|112|0|{3|reject|}47|51|}
{2010212001|XXGvertex_oport_oport|63|0|114|0|{4|error|}47|52|}
{2010212001|XXGvertex_oport_oport|64|0|116|0|{5|log|}47|53|}
{2010211001|XXGvertex_iport_iport|65|0|118|0|{0|in|}47|54|}
{2010214001|XXGiport_src_flow|66|0|120|0|{0|}54|55|}
{2010006001|XXGobject_psameas_object|67|0|122|0|{filereject_metadata|out0_metadata|0|0|}47|56|}
{2010212001|XXGvertex_oport_oport|68|0|124|0|{0|out0|}56|57|}
{2010213001|XXGoport_dst_flow|69|0|126|0|{0|}57|58|}
{2010212001|XXGvertex_oport_oport|70|0|128|0|{1|log|}56|59|}
{2010211001|XXGvertex_iport_iport|71|0|130|0|{0|in0|}56|60|}
{2010006001|XXGobject_psameas_object|72|0|132|0|{Layout|Layout|0|0|}56|61|}
{2010212001|XXGvertex_oport_oport|73|0|134|0|{0|out|}61|62|}
{2010213001|XXGoport_dst_flow|74|0|136|0|{0|}62|63|}
{2010211001|XXGvertex_iport_iport|75|0|138|0|{0|in|}61|64|}
{2010006001|XXGobject_psameas_object|76|0|140|0|{out_metadata|read_metadata|0|0|}61|65|}
{2010212001|XXGvertex_oport_oport|77|0|142|0|{0|read|}65|66|}
{2010213001|XXGoport_dst_flow|78|0|144|0|{0|}66|67|}
{2010006001|XXGobject_psameas_object|79|0|146|0|{in0_metadata|read_metadata|0|0|}56|65|}
{2010006001|XXGobject_psameas_object|80|0|147|0|{in_metadata|out0_metadata|0|0|}47|56|}
{2010006001|XXGobject_psameas_object|81|0|148|0|{dup_metadata|out_metadata|0|0|}29|47|}
{2010006001|XXGobject_psameas_object|82|0|149|0|{in_metadata|out_metadata|0|0|}29|47|}
{2010006001|XXGobject_psameas_object|83|0|150|0|{out_metadata|out_metadata|0|0|}29|47|}
{2010006001|XXGobject_psameas_object|84|0|151|0|{reject_metadata|out_metadata|0|0|}29|47|}
{2010601001|XXGgraph_vertex_vertex|85|0|152|0|{Join|}1|68|}
{2010212001|XXGvertex_oport_oport|86|0|154|0|{0|out|}68|69|}
{2010213001|XXGoport_dst_flow|87|0|156|0|{0|}69|19|}
{2010212001|XXGvertex_oport_oport|88|0|157|0|{1|unused0|}68|70|}
{2010212001|XXGvertex_oport_oport|89|0|159|0|{2|unused1|}68|71|}
{2010212001|XXGvertex_oport_oport|90|0|161|0|{3|reject0|}68|72|}
{2010212001|XXGvertex_oport_oport|91|0|163|0|{4|reject1|}68|73|}
{2010212001|XXGvertex_oport_oport|92|0|165|0|{5|error0|}68|74|}
{2010212001|XXGvertex_oport_oport|93|0|167|0|{6|error1|}68|75|}
{2010212001|XXGvertex_oport_oport|94|0|169|0|{7|log|}68|76|}
{2010211001|XXGvertex_iport_iport|95|0|171|0|{0|in0|}68|77|}
{2010214001|XXGiport_src_flow|96|0|173|0|{0|}77|7|}
{2010211001|XXGvertex_iport_iport|97|0|174|0|{1|in1|}68|78|}
{2010214001|XXGiport_src_flow|98|0|176|0|{0|}78|23|}
{2010007001|XXGobject_proto_object|99|0|177|0|{}68|79|}
{2010212001|XXGvertex_oport_oport|100|0|179|0|{0|out|}79|80|}
{2010006001|XXGobject_psameas_object|101|0|181|0|{metadata|out_metadata|1|0|}80|79|}
{2010212001|XXGvertex_oport_oport|102|0|182|0|{1|unused0|}79|81|}
{2010006001|XXGobject_psameas_object|103|0|184|0|{metadata|unused0_metadata|1|0|}81|79|}
{2010212001|XXGvertex_oport_oport|104|0|185|0|{2|unused1|}79|82|}
{2010006001|XXGobject_psameas_object|105|0|187|0|{metadata|unused1_metadata|1|0|}82|79|}
{2010212001|XXGvertex_oport_oport|106|0|188|0|{3|reject0|}79|83|}
{2010006001|XXGobject_psameas_object|107|0|190|0|{metadata|reject0_metadata|1|0|}83|79|}
{2010212001|XXGvertex_oport_oport|108|0|191|0|{4|reject1|}79|84|}
{2010006001|XXGobject_psameas_object|109|0|193|0|{metadata|reject1_metadata|1|0|}84|79|}
{2010212001|XXGvertex_oport_oport|110|0|194|0|{5|error0|}79|85|}
{2010006001|XXGobject_psameas_object|111|0|196|0|{metadata|error0_metadata|1|0|}85|79|}
{2010212001|XXGvertex_oport_oport|112|0|197|0|{6|error1|}79|86|}
{2010006001|XXGobject_psameas_object|113|0|199|0|{metadata|error1_metadata|1|0|}86|79|}
{2010212001|XXGvertex_oport_oport|114|0|200|0|{7|log|}79|87|}
{2010006001|XXGobject_psameas_object|115|0|202|0|{metadata|log_metadata|1|0|}87|79|}
{2010211001|XXGvertex_iport_iport|116|0|203|0|{0|in0|}79|88|}
{2010006001|XXGobject_psameas_object|117|0|205|0|{YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|118|0|206|0|{dedup0|dedup0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|119|0|207|0|{dedup_keyword0|dedup_keyword0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|120|0|208|0|{dedup_positional0|dedup_positional0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|121|0|209|0|{matchoptional_keyword0|matchoptional_keyword0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|122|0|210|0|{matchoptional_positional0|matchoptional_positional0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|123|0|211|0|{metadata|in0_metadata|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|124|0|212|0|{override_key0|override_key0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|125|0|213|0|{record_match_required0|record_match_required0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|126|0|214|0|{record_match_required_not0|record_match_required_not0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|127|0|215|0|{record_required0|record_required0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|128|0|216|0|{record_required_keyword0|record_required_keyword0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|129|0|217|0|{record_required_positional0|record_required_positional0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|130|0|218|0|{select0|select0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|131|0|219|0|{select_keyword0|select_keyword0|1|0|}88|79|}
{2010006001|XXGobject_psameas_object|132|0|220|0|{select_positional0|select_positional0|1|0|}88|79|}
{2010211001|XXGvertex_iport_iport|133|0|221|0|{1|in1|}79|89|}
{2010006001|XXGobject_psameas_object|134|0|223|0|{YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1|YourGdeCannotUseJoinParameterInterfaceVersion322WithLegacyCodegen1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|135|0|224|0|{dedup1|dedup1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|136|0|225|0|{dedup_keyword1|dedup_keyword1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|137|0|226|0|{dedup_positional1|dedup_positional1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|138|0|227|0|{matchoptional_keyword1|matchoptional_keyword1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|139|0|228|0|{matchoptional_positional1|matchoptional_positional1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|140|0|229|0|{metadata|in1_metadata|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|141|0|230|0|{override_key1|override_key1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|142|0|231|0|{record_match_required1|record_match_required1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|143|0|232|0|{record_match_required_not1|record_match_required_not1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|144|0|233|0|{record_required1|record_required1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|145|0|234|0|{record_required_keyword1|record_required_keyword1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|146|0|235|0|{record_required_positional1|record_required_positional1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|147|0|236|0|{select1|select1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|148|0|237|0|{select_keyword1|select_keyword1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|149|0|238|0|{select_positional1|select_positional1|1|0|}89|79|}
{2010006001|XXGobject_psameas_object|150|0|239|0|{Layout|Layout|0|0|}68|90|}
{2010212001|XXGvertex_oport_oport|151|0|241|0|{0|read|}90|91|}
{2010213001|XXGoport_dst_flow|152|0|243|0|{0|}91|7|}
{2010007001|XXGobject_proto_object|153|0|244|0|{}90|92|}
{2010212001|XXGvertex_oport_oport|154|0|246|0|{0|read|}92|93|}
{2010006001|XXGobject_psameas_object|155|0|248|0|{metadata|read_metadata|1|0|}93|92|}
{2010006001|XXGobject_psameas_object|156|0|249|0|{in0_metadata|read_metadata|0|0|}68|90|}
{2010006001|XXGobject_psameas_object|157|0|250|0|{in1_metadata|out_metadata|0|0|}68|47|}
{2010006001|XXGobject_psameas_object|158|0|251|0|{out_metadata|read_metadata|0|0|}68|90|}
{2010006001|XXGobject_psameas_object|159|0|252|0|{reject0_metadata|read_metadata|0|0|}68|90|}
{2010006001|XXGobject_psameas_object|160|0|253|0|{reject1_metadata|out_metadata|0|0|}68|47|}
{2010006001|XXGobject_psameas_object|161|0|254|0|{unused0_metadata|read_metadata|0|0|}68|90|}
{2010006001|XXGobject_psameas_object|162|0|255|0|{unused1_metadata|out_metadata|0|0|}68|47|}
{2010601001|XXGgraph_vertex_vertex|163|0|256|0|{Merge|}1|94|}
{2010212001|XXGvertex_oport_oport|164|0|258|0|{0|out|}94|95|}
{2010213001|XXGoport_dst_flow|165|0|260|0|{0|}95|20|}
{2010211001|XXGvertex_iport_iport|166|0|261|0|{0|in|}94|96|}
{2010214001|XXGiport_src_flow|167|0|263|0|{0|}96|10|}
{2010007001|XXGobject_proto_object|168|0|264|0|{}94|97|}
{2010212001|XXGvertex_oport_oport|169|0|266|0|{0|out|}97|98|}
{2010006001|XXGobject_psameas_object|170|0|268|0|{metadata|out_metadata|1|0|}98|97|}
{2010211001|XXGvertex_iport_iport|171|0|269|0|{0|in|}97|99|}
{2010006001|XXGobject_psameas_object|172|0|271|0|{metadata|in_metadata|1|0|}99|97|}
{2010006001|XXGobject_psameas_object|173|0|272|0|{Layout|Layout|0|0|}94|25|}
{2010006001|XXGobject_psameas_object|174|0|273|0|{in_metadata|write_metadata|0|0|}94|25|}
{2010006001|XXGobject_psameas_object|175|0|274|0|{out_metadata|write_metadata|0|0|}94|25|}
{2010601001|XXGgraph_vertex_vertex|176|0|275|0|{Merge_1|}1|100|}
{2010212001|XXGvertex_oport_oport|177|0|277|0|{0|out|}100|101|}
{2010213001|XXGoport_dst_flow|178|0|279|0|{0|}101|8|}
{2010211001|XXGvertex_iport_iport|179|0|280|0|{0|in|}100|102|}
{2010214001|XXGiport_src_flow|180|0|282|0|{0|}102|11|}
{2010007001|XXGobject_proto_object|181|0|283|0|{}100|103|}
{2010212001|XXGvertex_oport_oport|182|0|285|0|{0|out|}103|104|}
{2010006001|XXGobject_psameas_object|183|0|287|0|{metadata|out_metadata|1|0|}104|103|}
{2010211001|XXGvertex_iport_iport|184|0|288|0|{0|in|}103|105|}
{2010006001|XXGobject_psameas_object|185|0|290|0|{metadata|in_metadata|1|0|}105|103|}
{2010006001|XXGobject_psameas_object|186|0|291|0|{Layout|Layout|0|0|}100|106|}
{2010211001|XXGvertex_iport_iport|187|0|293|0|{0|write|}106|107|}
{2010214001|XXGiport_src_flow|188|0|295|0|{0|}107|8|}
{2010007001|XXGobject_proto_object|189|0|296|0|{}106|108|}
{2010211001|XXGvertex_iport_iport|190|0|298|0|{0|write|}108|109|}
{2010006001|XXGobject_psameas_object|191|0|300|0|{metadata|write_metadata|1|0|}109|108|}
{2010006001|XXGobject_psameas_object|192|0|301|0|{in_metadata|write_metadata|0|0|}100|106|}
{2010006001|XXGobject_psameas_object|193|0|302|0|{out_metadata|write_metadata|0|0|}100|106|}
{2010601001|XXGgraph_vertex_vertex|194|0|303|0|{NEUROLANDS|}1|106|}
{2010601001|XXGgraph_vertex_vertex|195|0|304|0|{Output_File_1|}1|43|}
{2010601001|XXGgraph_vertex_vertex|196|0|305|0|{Output_File_3|}1|90|}
{2010601001|XXGgraph_vertex_vertex|197|0|306|0|{Partition_by_Key|}1|110|}
{2010212001|XXGvertex_oport_oport|198|0|308|0|{0|out|}110|111|}
{2010213001|XXGoport_dst_flow|199|0|310|0|{0|}111|9|}
{2010211001|XXGvertex_iport_iport|200|0|311|0|{0|in|}110|112|}
{2010214001|XXGiport_src_flow|201|0|313|0|{0|}112|5|}
{2010007001|XXGobject_proto_object|202|0|314|0|{}110|113|}
{2010212001|XXGvertex_oport_oport|203|0|316|0|{0|out|}113|114|}
{2010006001|XXGobject_psameas_object|204|0|318|0|{metadata|out_metadata|1|0|}114|113|}
{2010211001|XXGvertex_iport_iport|205|0|319|0|{0|in|}113|115|}
{2010006001|XXGobject_psameas_object|206|0|321|0|{metadata|in_metadata|1|0|}115|113|}
{2010006001|XXGobject_psameas_object|207|0|322|0|{Layout|Layout|0|0|}110|47|}
{2010006001|XXGobject_psameas_object|208|0|323|0|{in_metadata|out_metadata|0|0|}110|47|}
{2010006001|XXGobject_psameas_object|209|0|324|0|{out_metadata|out_metadata|0|0|}110|47|}
{2010601001|XXGgraph_vertex_vertex|210|0|325|0|{Read_Hive_Table|}1|116|}
{2010604001|XXGgraph_flow_flow|211|0|327|0|{Flow_1|}116|67|}
{2010604001|XXGgraph_flow_flow|212|0|328|0|{Flow_2|}116|117|}
{2010604001|XXGgraph_flow_flow|213|0|330|0|{Flow_3|}116|63|}
{2010601001|XXGgraph_vertex_vertex|214|0|331|0|{Filter_Partitions|}116|118|}
{2010212001|XXGvertex_oport_oport|215|0|333|0|{0|out|}118|119|}
{2010213001|XXGoport_dst_flow|216|0|335|0|{0|}119|117|}
{2010212001|XXGvertex_oport_oport|217|0|336|0|{1|deselect|}118|120|}
{2010212001|XXGvertex_oport_oport|218|0|338|0|{2|reject|}118|121|}
{2010212001|XXGvertex_oport_oport|219|0|340|0|{3|error|}118|122|}
{2010212001|XXGvertex_oport_oport|220|0|342|0|{4|log|}118|123|}
{2010211001|XXGvertex_iport_iport|221|0|344|0|{0|in|}118|124|}
{2010214001|XXGiport_src_flow|222|0|346|0|{0|}124|67|}
{2010214001|XXGiport_src_flow|223|0|347|0|{1|}124|63|}
{2010006001|XXGobject_psameas_object|224|0|348|0|{Layout|Layout|0|0|}118|61|}
{2010006001|XXGobject_psameas_object|225|0|349|0|{deselect_metadata|read_metadata|0|0|}118|65|}
{2010006001|XXGobject_psameas_object|226|0|350|0|{in_metadata|read_metadata|0|0|}118|65|}
{2010006001|XXGobject_psameas_object|227|0|351|0|{out_metadata|read_metadata|0|0|}118|65|}
{2010006001|XXGobject_psameas_object|228|0|352|0|{reject_metadata|read_metadata|0|0|}118|65|}
{2010601001|XXGgraph_vertex_vertex|229|0|353|0|{Generate_Partition_Data|}116|61|}
{2010601001|XXGgraph_vertex_vertex|230|0|354|0|{Partition_Data|}116|65|}
{2010601001|XXGgraph_vertex_vertex|231|0|355|0|{Read_HDFS_Files|}116|125|}
{2010604001|XXGgraph_flow_flow|232|0|357|0|{Flow_1|}125|58|}
{2010604001|XXGgraph_flow_flow|233|0|358|0|{Flow_8|}125|55|}
{2010601001|XXGgraph_vertex_vertex|234|0|359|0|{Find_Files_and_Read_Blocks|}125|56|}
{2010601001|XXGgraph_vertex_vertex|235|0|360|0|{Partition_Blocks|}125|126|}
{2010212001|XXGvertex_oport_oport|236|0|362|0|{0|out|}126|127|}
{2010213001|XXGoport_dst_flow|237|0|364|0|{0|}127|55|}
{2010212001|XXGvertex_oport_oport|238|0|365|0|{1|reject|}126|128|}
{2010212001|XXGvertex_oport_oport|239|0|367|0|{2|error|}126|129|}
{2010212001|XXGvertex_oport_oport|240|0|369|0|{3|log|}126|130|}
{2010211001|XXGvertex_iport_iport|241|0|371|0|{0|in|}126|131|}
{2010214001|XXGiport_src_flow|242|0|373|0|{0|}131|58|}
{2010006001|XXGobject_psameas_object|243|0|374|0|{Layout|Layout|0|0|}126|61|}
{2010006001|XXGobject_psameas_object|244|0|375|0|{in_metadata|out0_metadata|0|0|}126|56|}
{2010006001|XXGobject_psameas_object|245|0|376|0|{out_metadata|out0_metadata|0|0|}126|56|}
{2010006001|XXGobject_psameas_object|246|0|377|0|{reject_metadata|out0_metadata|0|0|}126|56|}
{2010601001|XXGgraph_vertex_vertex|247|0|378|0|{Read_Blocks|}125|47|}
{2010212001|XXGvertex_oport_oport|248|0|379|0|{0|out0|}125|132|}
{2010216002|XXGoport_binding_oport|249|0|381|0|{.5|.5|{0|}3965|}132|48|}
{2010211001|XXGvertex_iport_iport|250|0|382|0|{0|in0|}125|133|}
{2010215002|XXGiport_binding_iport|251|0|384|0|{.5|.5|{0|}3964|}133|60|}
{2010214001|XXGiport_src_flow|252|0|385|0|{0|}133|117|}
{2010601001|XXGgraph_vertex_vertex|253|0|386|0|{Validate_HIVE_LAYOUT|}116|134|}
{2010604001|XXGgraph_flow_flow|254|0|388|0|{Flow_4|}134|135|}
{2010601001|XXGgraph_vertex_vertex|255|0|390|0|{Perform_Validation|}134|136|}
{2010212001|XXGvertex_oport_oport|256|0|392|0|{0|out|}136|137|}
{2010213001|XXGoport_dst_flow|257|0|394|0|{0|}137|135|}
{2010212001|XXGvertex_oport_oport|258|0|395|0|{1|error|}136|138|}
{2010212001|XXGvertex_oport_oport|259|0|397|0|{2|log|}136|139|}
{2010601001|XXGgraph_vertex_vertex|260|0|399|0|{Trash|}134|140|}
{2010211001|XXGvertex_iport_iport|261|0|401|0|{0|in|}140|141|}
{2010214001|XXGiport_src_flow|262|0|403|0|{0|}141|135|}
{2010006001|XXGobject_psameas_object|263|0|404|0|{Layout|Layout|0|0|}140|61|}
{2010006001|XXGobject_psameas_object|264|0|405|0|{in_metadata|out_metadata|0|0|}140|136|}
{2010212001|XXGvertex_oport_oport|265|0|406|0|{0|out0|}116|142|}
{2010216002|XXGoport_binding_oport|266|0|408|0|{.5|.5|{0|}4034|}142|132|}
{2010213001|XXGoport_dst_flow|267|0|409|0|{0|}142|5|}
{2010007001|XXGobject_proto_object|268|0|410|0|{}116|143|}
{2010604001|XXGgraph_flow_flow|269|0|412|0|{Flow_1|}143|144|}
{2010604001|XXGgraph_flow_flow|270|0|414|0|{Flow_2|}143|145|}
{2010604001|XXGgraph_flow_flow|271|0|416|0|{Flow_3|}143|146|}
{2010601001|XXGgraph_vertex_vertex|272|0|418|0|{Filter_Partitions|}143|147|}
{2010212001|XXGvertex_oport_oport|273|0|420|0|{0|out|}147|148|}
{2010213001|XXGoport_dst_flow|274|0|422|0|{0|}148|145|}
{2010212001|XXGvertex_oport_oport|275|0|423|0|{1|deselect|}147|149|}
{2010212001|XXGvertex_oport_oport|276|0|425|0|{2|reject|}147|150|}
{2010212001|XXGvertex_oport_oport|277|0|427|0|{3|error|}147|151|}
{2010212001|XXGvertex_oport_oport|278|0|429|0|{4|log|}147|152|}
{2010211001|XXGvertex_iport_iport|279|0|431|0|{0|in|}147|153|}
{2010214001|XXGiport_src_flow|280|0|433|0|{0|}153|144|}
{2010214001|XXGiport_src_flow|281|0|434|0|{1|}153|146|}
{2010007001|XXGobject_proto_object|282|0|435|0|{}147|154|}
{2010212001|XXGvertex_oport_oport|283|0|437|0|{0|out|}154|155|}
{2010006001|XXGobject_psameas_object|284|0|439|0|{metadata|out_metadata|1|0|}155|154|}
{2010212001|XXGvertex_oport_oport|285|0|440|0|{1|deselect|}154|156|}
{2010006001|XXGobject_psameas_object|286|0|442|0|{metadata|deselect_metadata|1|0|}156|154|}
{2010212001|XXGvertex_oport_oport|287|0|443|0|{2|reject|}154|157|}
{2010006001|XXGobject_psameas_object|288|0|445|0|{metadata|reject_metadata|1|0|}157|154|}
{2010212001|XXGvertex_oport_oport|289|0|446|0|{3|error|}154|158|}
{2010006001|XXGobject_psameas_object|290|0|448|0|{metadata|error_metadata|1|0|}158|154|}
{2010212001|XXGvertex_oport_oport|291|0|449|0|{4|log|}154|159|}
{2010006001|XXGobject_psameas_object|292|0|451|0|{metadata|log_metadata|1|0|}159|154|}
{2010211001|XXGvertex_iport_iport|293|0|452|0|{0|in|}154|160|}
{2010006001|XXGobject_psameas_object|294|0|454|0|{metadata|in_metadata|1|0|}160|154|}
{2010006001|XXGobject_psameas_object|295|0|455|0|{error_group|ERROR_GROUP|1|0|}147|143|}
{2010006001|XXGobject_psameas_object|296|0|456|0|{log_group|LOG_GROUP|1|0|}147|143|}
{2010006001|XXGobject_psameas_object|297|0|457|0|{logging|LOGGING|1|0|}147|143|}
{2010006001|XXGobject_psameas_object|298|0|458|0|{reject_threshold|REJECT_THRESHOLD|1|0|}147|143|}
{2010006001|XXGobject_psameas_object|299|0|459|0|{select_expr|FILTER_EXPR|1|0|}147|143|}
{2010601001|XXGgraph_vertex_vertex|300|0|460|0|{Generate_Partition_Data|}143|161|}
{2010212001|XXGvertex_oport_oport|301|0|462|0|{0|out|}161|162|}
{2010213001|XXGoport_dst_flow|302|0|464|0|{0|}162|146|}
{2010211001|XXGvertex_iport_iport|303|0|465|0|{0|in|}161|163|}
{2010007001|XXGobject_proto_object|304|0|467|0|{}161|164|}
{2010212001|XXGvertex_oport_oport|305|0|469|0|{0|out|}164|165|}
{2010006001|XXGobject_psameas_object|306|0|471|0|{metadata|out_metadata|1|0|}165|164|}
{2010211001|XXGvertex_iport_iport|307|0|472|0|{0|in|}164|166|}
{2010006001|XXGobject_psameas_object|308|0|474|0|{metadata|in_metadata|1|0|}166|164|}
{2010601001|XXGgraph_vertex_vertex|309|0|475|0|{Partition_Data|}143|167|}
{2010212001|XXGvertex_oport_oport|310|0|477|0|{0|read|}167|168|}
{2010213001|XXGoport_dst_flow|311|0|479|0|{0|}168|144|}
{2010007001|XXGobject_proto_object|312|0|480|0|{}167|169|}
{2010212001|XXGvertex_oport_oport|313|0|482|0|{0|read|}169|170|}
{2010006001|XXGobject_psameas_object|314|0|484|0|{metadata|read_metadata|1|0|}170|169|}
{2010601001|XXGgraph_vertex_vertex|315|0|485|0|{Read_HDFS_Files|}143|171|}
{2010604001|XXGgraph_flow_flow|316|0|487|0|{Flow_1|}171|172|}
{2010604001|XXGgraph_flow_flow|317|0|489|0|{Flow_8|}171|173|}
{2010601001|XXGgraph_vertex_vertex|318|0|491|0|{Find_Files_and_Read_Blocks|}171|174|}
{2010212001|XXGvertex_oport_oport|319|0|493|0|{0|out0|}174|175|}
{2010213001|XXGoport_dst_flow|320|0|495|0|{0|}175|172|}
{2010212001|XXGvertex_oport_oport|321|0|496|0|{1|log|}174|176|}
{2010211001|XXGvertex_iport_iport|322|0|498|0|{0|in0|}174|177|}
{2010601001|XXGgraph_vertex_vertex|323|0|500|0|{Partition_Blocks|}171|178|}
{2010212001|XXGvertex_oport_oport|324|0|502|0|{0|out|}178|179|}
{2010213001|XXGoport_dst_flow|325|0|504|0|{0|}179|173|}
{2010212001|XXGvertex_oport_oport|326|0|505|0|{1|reject|}178|180|}
{2010212001|XXGvertex_oport_oport|327|0|507|0|{2|error|}178|181|}
{2010212001|XXGvertex_oport_oport|328|0|509|0|{3|log|}178|182|}
{2010211001|XXGvertex_iport_iport|329|0|511|0|{0|in|}178|183|}
{2010214001|XXGiport_src_flow|330|0|513|0|{0|}183|172|}
{2010601001|XXGgraph_vertex_vertex|331|0|514|0|{Read_Blocks|}171|184|}
{2010212001|XXGvertex_oport_oport|332|0|516|0|{0|out|}184|185|}
{2010212001|XXGvertex_oport_oport|333|0|518|0|{1|filereject|}184|186|}
{2010212001|XXGvertex_oport_oport|334|0|520|0|{2|fileerror|}184|187|}
{2010212001|XXGvertex_oport_oport|335|0|522|0|{3|reject|}184|188|}
{2010212001|XXGvertex_oport_oport|336|0|524|0|{4|error|}184|189|}
{2010212001|XXGvertex_oport_oport|337|0|526|0|{5|log|}184|190|}
{2010211001|XXGvertex_iport_iport|338|0|528|0|{0|in|}184|191|}
{2010214001|XXGiport_src_flow|339|0|530|0|{0|}191|173|}
{2010212001|XXGvertex_oport_oport|340|0|531|0|{0|out0|}171|192|}
{2010216002|XXGoport_binding_oport|341|0|533|0|{.5|.5|{0|}3965|}192|185|}
{2010211001|XXGvertex_iport_iport|342|0|534|0|{0|in0|}171|193|}
{2010215002|XXGiport_binding_iport|343|0|536|0|{.5|.5|{0|}3964|}193|177|}
{2010214001|XXGiport_src_flow|344|0|537|0|{0|}193|145|}
{2010007001|XXGobject_proto_object|345|0|538|0|{}171|194|}
{2010604001|XXGgraph_flow_flow|346|0|540|0|{Flow_1|}194|195|}
{2010604001|XXGgraph_flow_flow|347|0|542|0|{Flow_8|}194|196|}
{2010601001|XXGgraph_vertex_vertex|348|0|544|0|{Find_Files_and_Read_Blocks|}194|197|}
{2010212001|XXGvertex_oport_oport|349|0|546|0|{0|out0|}197|198|}
{2010213001|XXGoport_dst_flow|350|0|548|0|{0|}198|195|}
{2010212001|XXGvertex_oport_oport|351|0|549|0|{1|log|}197|199|}
{2010211001|XXGvertex_iport_iport|352|0|551|0|{0|in0|}197|200|}
{2010007001|XXGobject_proto_object|353|0|553|0|{}197|201|}
{2010212001|XXGvertex_oport_oport|354|0|555|0|{0|out0|}201|202|}
{2010006001|XXGobject_psameas_object|355|0|557|0|{metadata|out0_metadata|1|0|}202|201|}
{2010212001|XXGvertex_oport_oport|356|0|558|0|{1|log|}201|203|}
{2010006001|XXGobject_psameas_object|357|0|560|0|{metadata|log_metadata|1|0|}203|201|}
{2010211001|XXGvertex_iport_iport|358|0|561|0|{0|in0|}201|204|}
{2010006001|XXGobject_psameas_object|359|0|563|0|{metadata|in0_metadata|1|0|}204|201|}
{2010601001|XXGgraph_vertex_vertex|360|0|564|0|{Partition_Blocks|}194|205|}
{2010212001|XXGvertex_oport_oport|361|0|566|0|{0|out|}205|206|}
{2010213001|XXGoport_dst_flow|362|0|568|0|{0|}206|196|}
{2010212001|XXGvertex_oport_oport|363|0|569|0|{1|reject|}205|207|}
{2010212001|XXGvertex_oport_oport|364|0|571|0|{2|error|}205|208|}
{2010212001|XXGvertex_oport_oport|365|0|573|0|{3|log|}205|209|}
{2010211001|XXGvertex_iport_iport|366|0|575|0|{0|in|}205|210|}
{2010214001|XXGiport_src_flow|367|0|577|0|{0|}210|195|}
{2010007001|XXGobject_proto_object|368|0|578|0|{}205|211|}
{2010212001|XXGvertex_oport_oport|369|0|580|0|{0|out|}211|212|}
{2010006001|XXGobject_psameas_object|370|0|582|0|{metadata|out_metadata|1|0|}212|211|}
{2010212001|XXGvertex_oport_oport|371|0|583|0|{1|reject|}211|213|}
{2010006001|XXGobject_psameas_object|372|0|585|0|{metadata|reject_metadata|1|0|}213|211|}
{2010212001|XXGvertex_oport_oport|373|0|586|0|{2|error|}211|214|}
{2010006001|XXGobject_psameas_object|374|0|588|0|{metadata|error_metadata|1|0|}214|211|}
{2010212001|XXGvertex_oport_oport|375|0|589|0|{3|log|}211|215|}
{2010006001|XXGobject_psameas_object|376|0|591|0|{metadata|log_metadata|1|0|}215|211|}
{2010211001|XXGvertex_iport_iport|377|0|592|0|{0|in|}211|216|}
{2010006001|XXGobject_psameas_object|378|0|594|0|{metadata|in_metadata|1|0|}216|211|}
{2010006001|XXGobject_psameas_object|379|0|595|0|{error_group|ERROR_GROUP|1|0|}205|194|}
{2010006001|XXGobject_psameas_object|380|0|596|0|{log_group|LOG_GROUP|1|0|}205|194|}
{2010006001|XXGobject_psameas_object|381|0|597|0|{logging|LOGGING|1|0|}205|194|}
{2010006001|XXGobject_psameas_object|382|0|598|0|{package|BLOCK_PARTITION_XFR|1|0|}205|194|}
{2010006001|XXGobject_psameas_object|383|0|599|0|{reject_threshold|REJECT_THRESHOLD|1|0|}205|194|}
{2010601001|XXGgraph_vertex_vertex|384|0|600|0|{Read_Blocks|}194|217|}
{2010212001|XXGvertex_oport_oport|385|0|602|0|{0|out|}217|218|}
{2010212001|XXGvertex_oport_oport|386|0|604|0|{1|filereject|}217|219|}
{2010212001|XXGvertex_oport_oport|387|0|606|0|{2|fileerror|}217|220|}
{2010212001|XXGvertex_oport_oport|388|0|608|0|{3|reject|}217|221|}
{2010212001|XXGvertex_oport_oport|389|0|610|0|{4|error|}217|222|}
{2010212001|XXGvertex_oport_oport|390|0|612|0|{5|log|}217|223|}
{2010211001|XXGvertex_iport_iport|391|0|614|0|{0|in|}217|224|}
{2010214001|XXGiport_src_flow|392|0|616|0|{0|}224|196|}
{2010007001|XXGobject_proto_object|393|0|617|0|{}217|225|}
{2010212001|XXGvertex_oport_oport|394|0|619|0|{0|out|}225|226|}
{2010006001|XXGobject_psameas_object|395|0|621|0|{metadata|out_metadata|1|0|}226|225|}
{2010212001|XXGvertex_oport_oport|396|0|622|0|{1|filereject|}225|227|}
{2010006001|XXGobject_psameas_object|397|0|624|0|{metadata|filereject_metadata|1|0|}227|225|}
{2010212001|XXGvertex_oport_oport|398|0|625|0|{2|fileerror|}225|228|}
{2010006001|XXGobject_psameas_object|399|0|627|0|{metadata|fileerror_metadata|1|0|}228|225|}
{2010212001|XXGvertex_oport_oport|400|0|628|0|{3|reject|}225|229|}
{2010006001|XXGobject_psameas_object|401|0|630|0|{metadata|reject_metadata|1|0|}229|225|}
{2010212001|XXGvertex_oport_oport|402|0|631|0|{4|error|}225|230|}
{2010006001|XXGobject_psameas_object|403|0|633|0|{metadata|error_metadata|1|0|}230|225|}
{2010212001|XXGvertex_oport_oport|404|0|634|0|{5|log|}225|231|}
{2010006001|XXGobject_psameas_object|405|0|636|0|{metadata|log_metadata|1|0|}231|225|}
{2010211001|XXGvertex_iport_iport|406|0|637|0|{0|in|}225|232|}
{2010006001|XXGobject_psameas_object|407|0|639|0|{metadata|in_metadata|1|0|}232|225|}
{2010006001|XXGobject_psameas_object|408|0|640|0|{error_group|ERROR_GROUP|1|0|}217|194|}
{2010006001|XXGobject_psameas_object|409|0|641|0|{log_group|LOG_GROUP|1|0|}217|194|}
{2010006001|XXGobject_psameas_object|410|0|642|0|{logging|LOGGING|1|0|}217|194|}
{2010006001|XXGobject_psameas_object|411|0|643|0|{out_metadata|OUTPUT_DML|1|0|}217|194|}
{2010006001|XXGobject_psameas_object|412|0|644|0|{reject_threshold|REJECT_THRESHOLD|1|0|}217|194|}
{2010006001|XXGobject_psameas_object|413|0|645|0|{schema_file|SCHEMA_FILE|1|0|}217|194|}
{2010006001|XXGobject_psameas_object|414|0|646|0|{select_columns|READ_COLUMNS|1|0|}217|194|}
{2010006001|XXGobject_psameas_object|415|0|647|0|{transform|RMF_XFR|1|0|}217|194|}
{2010212001|XXGvertex_oport_oport|416|0|648|0|{0|out0|}194|233|}
{2010216002|XXGoport_binding_oport|417|0|650|0|{.5|.5|{0|}3965|}233|218|}
{2010211001|XXGvertex_iport_iport|418|0|651|0|{0|in0|}194|234|}
{2010215002|XXGiport_binding_iport|419|0|653|0|{.5|.5|{0|}3964|}234|200|}
{2010006001|XXGobject_psameas_object|420|0|654|0|{READ_SPECIFICATION|in0_metadata|0|0|}194|197|}
{2010006001|XXGobject_psameas_object|421|0|655|0|{BLOCK_PARTITION_XFR|BLOCK_PARTITION_XFR|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|422|0|656|0|{ERROR_GROUP|ERROR_GROUP|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|423|0|657|0|{FILE_FORMAT|FILE_FORMAT|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|424|0|658|0|{HDFS_FILE_SUFFIX|HDFS_FILE_SUFFIX|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|425|0|659|0|{HOST_DEPTH|HOST_DEPTH|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|426|0|660|0|{HOST_LIST|HOST_LIST|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|427|0|661|0|{LOGGING|LOGGING|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|428|0|662|0|{LOG_GROUP|LOG_GROUP|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|429|0|663|0|{OUTPUT_DML|OUTPUT_DML|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|430|0|664|0|{PATH_GLOB_PATTERN|PATH_GLOB_PATTERN|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|431|0|665|0|{READ_COLUMNS|READ_COLUMNS|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|432|0|666|0|{READ_LAYOUT|READ_LAYOUT|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|433|0|667|0|{REFORMAT_XFR|REFORMAT_XFR|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|434|0|668|0|{REJECT_THRESHOLD|REJECT_THRESHOLD|1|0|}171|143|}
{2010006001|XXGobject_psameas_object|435|0|669|0|{SCHEMA_FILE|SCHEMA_FILE|1|0|}171|143|}
{2010601001|XXGgraph_vertex_vertex|436|0|670|0|{Validate_HIVE_LAYOUT|}143|235|}
{2010604001|XXGgraph_flow_flow|437|0|672|0|{Flow_4|}235|236|}
{2010601001|XXGgraph_vertex_vertex|438|0|674|0|{Perform_Validation|}235|237|}
{2010212001|XXGvertex_oport_oport|439|0|676|0|{0|out|}237|238|}
{2010213001|XXGoport_dst_flow|440|0|678|0|{0|}238|236|}
{2010212001|XXGvertex_oport_oport|441|0|679|0|{1|error|}237|239|}
{2010212001|XXGvertex_oport_oport|442|0|681|0|{2|log|}237|240|}
{2010007001|XXGobject_proto_object|443|0|683|0|{}237|241|}
{2010212001|XXGvertex_oport_oport|444|0|685|0|{0|out|}241|242|}
{2010006001|XXGobject_psameas_object|445|0|687|0|{metadata|out_metadata|1|0|}242|241|}
{2010212001|XXGvertex_oport_oport|446|0|688|0|{1|error|}241|243|}
{2010006001|XXGobject_psameas_object|447|0|690|0|{metadata|error_metadata|1|0|}243|241|}
{2010212001|XXGvertex_oport_oport|448|0|691|0|{2|log|}241|244|}
{2010006001|XXGobject_psameas_object|449|0|693|0|{metadata|log_metadata|1|0|}244|241|}
{2010006001|XXGobject_psameas_object|450|0|694|0|{Layout|Layout|0|0|}237|161|}
{2010601001|XXGgraph_vertex_vertex|451|0|695|0|{Trash|}235|245|}
{2010211001|XXGvertex_iport_iport|452|0|697|0|{0|in|}245|246|}
{2010214001|XXGiport_src_flow|453|0|699|0|{0|}246|236|}
{2010007001|XXGobject_proto_object|454|0|700|0|{}245|247|}
{2010211001|XXGvertex_iport_iport|455|0|702|0|{0|in|}247|248|}
{2010006001|XXGobject_psameas_object|456|0|704|0|{metadata|in_metadata|1|0|}248|247|}
{2010212001|XXGvertex_oport_oport|457|0|705|0|{0|out0|}143|249|}
{2010216002|XXGoport_binding_oport|458|0|707|0|{.5|.5|{0|}4034|}249|192|}
{2010601001|XXGgraph_vertex_vertex|459|0|708|0|{Replicate|}1|250|}
{2010212001|XXGvertex_oport_oport|460|0|710|0|{0|out|}250|251|}
{2010213001|XXGoport_dst_flow|461|0|712|0|{0|}251|21|}
{2010213001|XXGoport_dst_flow|462|0|713|0|{1|}251|23|}
{2010211001|XXGvertex_iport_iport|463|0|714|0|{0|in|}250|252|}
{2010214001|XXGiport_src_flow|464|0|716|0|{0|}252|22|}
{2010007001|XXGobject_proto_object|465|0|717|0|{}250|253|}
{2010212001|XXGvertex_oport_oport|466|0|719|0|{0|out|}253|254|}
{2010006001|XXGobject_psameas_object|467|0|721|0|{metadata|out_metadata|1|0|}254|253|}
{2010211001|XXGvertex_iport_iport|468|0|722|0|{0|in|}253|255|}
{2010006001|XXGobject_psameas_object|469|0|724|0|{metadata|in_metadata|1|0|}255|253|}
{2010006001|XXGobject_psameas_object|470|0|725|0|{Layout|Layout|0|0|}250|43|}
{2010006001|XXGobject_psameas_object|471|0|726|0|{in_metadata|out_metadata|0|0|}250|47|}
{2010006001|XXGobject_psameas_object|472|0|727|0|{out_metadata|out_metadata|0|0|}250|47|}
{2010601001|XXGgraph_vertex_vertex|473|0|728|0|{Risk_scores_Rejected|}1|256|}
{2010604001|XXGgraph_flow_flow|474|0|730|0|{Flow_16|}256|257|}
{2010604001|XXGgraph_flow_flow|475|0|732|0|{Flow_17|}256|258|}
{2010601001|XXGgraph_vertex_vertex|476|0|734|0|{Merge_3|}256|259|}
{2010212001|XXGvertex_oport_oport|477|0|736|0|{0|out|}259|260|}
{2010213001|XXGoport_dst_flow|478|0|738|0|{0|}260|257|}
{2010211001|XXGvertex_iport_iport|479|0|739|0|{0|in|}259|261|}
{2010007001|XXGobject_proto_object|480|0|741|0|{}259|262|}
{2010212001|XXGvertex_oport_oport|481|0|743|0|{0|out|}262|263|}
{2010006001|XXGobject_psameas_object|482|0|745|0|{metadata|out_metadata|1|0|}263|262|}
{2010211001|XXGvertex_iport_iport|483|0|746|0|{0|in|}262|264|}
{2010006001|XXGobject_psameas_object|484|0|748|0|{metadata|in_metadata|1|0|}264|262|}
{2010006001|XXGobject_psameas_object|485|0|749|0|{Layout|Layout|0|0|}259|265|}
{2010211001|XXGvertex_iport_iport|486|0|751|0|{0|write|}265|266|}
{2010214001|XXGiport_src_flow|487|0|753|0|{0|}266|257|}
{2010007001|XXGobject_proto_object|488|0|754|0|{}265|267|}
{2010211001|XXGvertex_iport_iport|489|0|756|0|{0|write|}267|268|}
{2010006001|XXGobject_psameas_object|490|0|758|0|{metadata|write_metadata|1|0|}268|267|}
{2010006001|XXGobject_psameas_object|491|0|759|0|{write_metadata|out0_metadata|0|0|}265|269|}
{2010212001|XXGvertex_oport_oport|492|0|761|0|{0|out0|}269|270|}
{2010213001|XXGoport_dst_flow|493|0|763|0|{0|}270|14|}
{2010212001|XXGvertex_oport_oport|494|0|764|0|{1|reject0|}269|271|}
{2010213001|XXGoport_dst_flow|495|0|766|0|{0|}271|12|}
{2010212001|XXGvertex_oport_oport|496|0|767|0|{2|error0|}269|272|}
{2010212001|XXGvertex_oport_oport|497|0|769|0|{3|log|}269|273|}
{2010211001|XXGvertex_iport_iport|498|0|771|0|{0|in|}269|274|}
{2010214001|XXGiport_src_flow|499|0|773|0|{0|}274|19|}
{2010007001|XXGobject_proto_object|500|0|774|0|{}269|275|}
{2010212001|XXGvertex_oport_oport|501|0|776|0|{0|out0|}275|276|}
{2010006001|XXGobject_psameas_object|502|0|778|0|{metadata|out0_metadata|1|0|}276|275|}
{2010006001|XXGobject_psameas_object|503|0|779|0|{transform0|transform0|1|0|}276|275|}
{2010212001|XXGvertex_oport_oport|504|0|780|0|{1|reject0|}275|277|}
{2010006001|XXGobject_psameas_object|505|0|782|0|{metadata|reject0_metadata|1|0|}277|275|}
{2010212001|XXGvertex_oport_oport|506|0|783|0|{2|error0|}275|278|}
{2010006001|XXGobject_psameas_object|507|0|785|0|{metadata|error0_metadata|1|0|}278|275|}
{2010212001|XXGvertex_oport_oport|508|0|786|0|{3|log|}275|279|}
{2010006001|XXGobject_psameas_object|509|0|788|0|{metadata|log_metadata|1|0|}279|275|}
{2010211001|XXGvertex_iport_iport|510|0|789|0|{0|in|}275|280|}
{2010006001|XXGobject_psameas_object|511|0|791|0|{metadata|in_metadata|1|0|}280|275|}
{2010006001|XXGobject_psameas_object|512|0|792|0|{Layout|Layout|0|0|}269|90|}
{2010006001|XXGobject_psameas_object|513|0|793|0|{in_metadata|read_metadata|0|0|}269|90|}
{2010006001|XXGobject_psameas_object|514|0|794|0|{reject0_metadata|read_metadata|0|0|}269|90|}
{2010006001|XXGobject_psameas_object|515|0|795|0|{in_metadata|out0_metadata|0|0|}259|269|}
{2010006001|XXGobject_psameas_object|516|0|796|0|{out_metadata|out0_metadata|0|0|}259|269|}
{2010601001|XXGgraph_vertex_vertex|517|0|797|0|{Merge_4|}256|281|}
{2010212001|XXGvertex_oport_oport|518|0|799|0|{0|out|}281|282|}
{2010213001|XXGoport_dst_flow|519|0|801|0|{0|}282|258|}
{2010211001|XXGvertex_iport_iport|520|0|802|0|{0|in|}281|283|}
{2010007001|XXGobject_proto_object|521|0|804|0|{}281|284|}
{2010212001|XXGvertex_oport_oport|522|0|806|0|{0|out|}284|285|}
{2010006001|XXGobject_psameas_object|523|0|808|0|{metadata|out_metadata|1|0|}285|284|}
{2010211001|XXGvertex_iport_iport|524|0|809|0|{0|in|}284|286|}
{2010006001|XXGobject_psameas_object|525|0|811|0|{metadata|in_metadata|1|0|}286|284|}
{2010006001|XXGobject_psameas_object|526|0|812|0|{Layout|Layout|0|0|}281|287|}
{2010211001|XXGvertex_iport_iport|527|0|814|0|{0|write|}287|288|}
{2010214001|XXGiport_src_flow|528|0|816|0|{0|}288|258|}
{2010007001|XXGobject_proto_object|529|0|817|0|{}287|289|}
{2010211001|XXGvertex_iport_iport|530|0|819|0|{0|write|}289|290|}
{2010006001|XXGobject_psameas_object|531|0|821|0|{metadata|write_metadata|1|0|}290|289|}
{2010006001|XXGobject_psameas_object|532|0|822|0|{write_metadata|out0_metadata|0|0|}287|269|}
{2010006001|XXGobject_psameas_object|533|0|823|0|{in_metadata|out0_metadata|0|0|}281|269|}
{2010006001|XXGobject_psameas_object|534|0|824|0|{out_metadata|out0_metadata|0|0|}281|269|}
{2010601001|XXGgraph_vertex_vertex|535|0|825|0|{bcs_risk_rej|}256|265|}
{2010601001|XXGgraph_vertex_vertex|536|0|826|0|{neuro_rej|}256|287|}
{2010211001|XXGvertex_iport_iport|537|0|827|0|{0|in0|}256|291|}
{2010215002|XXGiport_binding_iport|538|0|829|0|{.5|.5|{0|}4504|}291|261|}
{2010214001|XXGiport_src_flow|539|0|830|0|{0|}291|13|}
{2010211001|XXGvertex_iport_iport|540|0|831|0|{1|in1|}256|292|}
{2010215002|XXGiport_binding_iport|541|0|833|0|{.5|.5|{0|}4506|}292|283|}
{2010214001|XXGiport_src_flow|542|0|834|0|{0|}292|16|}
{2010601001|XXGgraph_vertex_vertex|543|0|835|0|{Run_Program|}1|293|}
{2010212001|XXGvertex_oport_oport|544|0|837|0|{0|out|}293|294|}
{2010211001|XXGvertex_iport_iport|545|0|839|0|{0|in|}293|295|}
{2010007001|XXGobject_proto_object|546|0|841|0|{}293|296|}
{2010212001|XXGvertex_oport_oport|547|0|843|0|{0|out|}296|297|}
{2010006001|XXGobject_psameas_object|548|0|845|0|{metadata|out_metadata|1|0|}297|296|}
{2010211001|XXGvertex_iport_iport|549|0|846|0|{0|in|}296|298|}
{2010006001|XXGobject_psameas_object|550|0|848|0|{metadata|in_metadata|1|0|}298|296|}
{2010601001|XXGgraph_vertex_vertex|551|0|849|0|{Sort|}1|299|}
{2010212001|XXGvertex_oport_oport|552|0|851|0|{0|out|}299|300|}
{2010213001|XXGoport_dst_flow|553|0|853|0|{0|}300|17|}
{2010211001|XXGvertex_iport_iport|554|0|854|0|{0|in|}299|301|}
{2010214001|XXGiport_src_flow|555|0|856|0|{0|}301|9|}
{2010007001|XXGobject_proto_object|556|0|857|0|{}299|302|}
{2010212001|XXGvertex_oport_oport|557|0|859|0|{0|out|}302|303|}
{2010006001|XXGobject_psameas_object|558|0|861|0|{metadata|out_metadata|1|0|}303|302|}
{2010211001|XXGvertex_iport_iport|559|0|862|0|{0|in|}302|304|}
{2010006001|XXGobject_psameas_object|560|0|864|0|{metadata|in_metadata|1|0|}304|302|}
{2010006001|XXGobject_psameas_object|561|0|865|0|{Layout|Layout|0|0|}299|43|}
{2010006001|XXGobject_psameas_object|562|0|866|0|{in_metadata|out_metadata|0|0|}299|47|}
{2010006001|XXGobject_psameas_object|563|0|867|0|{out_metadata|out_metadata|0|0|}299|47|}
{2010601001|XXGgraph_vertex_vertex|564|0|868|0|{Sort_within_Groups|}1|305|}
{2010212001|XXGvertex_oport_oport|565|0|870|0|{0|out|}305|306|}
{2010213001|XXGoport_dst_flow|566|0|872|0|{0|}306|22|}
{2010211001|XXGvertex_iport_iport|567|0|873|0|{0|in|}305|307|}
{2010214001|XXGiport_src_flow|568|0|875|0|{0|}307|17|}
{2010007001|XXGobject_proto_object|569|0|876|0|{}305|308|}
{2010212001|XXGvertex_oport_oport|570|0|878|0|{0|out|}308|309|}
{2010006001|XXGobject_psameas_object|571|0|880|0|{metadata|out_metadata|1|0|}309|308|}
{2010211001|XXGvertex_iport_iport|572|0|881|0|{0|in|}308|310|}
{2010006001|XXGobject_psameas_object|573|0|883|0|{metadata|in_metadata|1|0|}310|308|}
{2010006001|XXGobject_psameas_object|574|0|884|0|{Layout|Layout|0|0|}305|43|}
{2010006001|XXGobject_psameas_object|575|0|885|0|{in_metadata|out_metadata|0|0|}305|47|}
{2010006001|XXGobject_psameas_object|576|0|886|0|{out_metadata|out_metadata|0|0|}305|47|}
{2010601001|XXGgraph_vertex_vertex|577|0|887|0|{Summary_extraction|}1|311|}
{2010212001|XXGvertex_oport_oport|578|0|889|0|{0|out|}311|312|}
{2010211001|XXGvertex_iport_iport|579|0|891|0|{0|in|}311|313|}
{2010007001|XXGobject_proto_object|580|0|893|0|{}311|314|}
{2010212001|XXGvertex_oport_oport|581|0|895|0|{0|out|}314|315|}
{2010006001|XXGobject_psameas_object|582|0|897|0|{metadata|out_metadata|1|0|}315|314|}
{2010211001|XXGvertex_iport_iport|583|0|898|0|{0|in|}314|316|}
{2010006001|XXGobject_psameas_object|584|0|900|0|{metadata|in_metadata|1|0|}316|314|}
{2010601001|XXGgraph_vertex_vertex|585|0|901|0|{cust_seg_func|}1|269|}
{2010601001|XXGgraph_vertex_vertex|586|0|902|0|{cust_seg_rejected|}1|317|}
{2010604001|XXGgraph_flow_flow|587|0|904|0|{Flow_15|}317|318|}
{2010601001|XXGgraph_vertex_vertex|588|0|906|0|{Merge_2|}317|319|}
{2010212001|XXGvertex_oport_oport|589|0|908|0|{0|out|}319|320|}
{2010213001|XXGoport_dst_flow|590|0|910|0|{0|}320|318|}
{2010211001|XXGvertex_iport_iport|591|0|911|0|{0|in|}319|321|}
{2010007001|XXGobject_proto_object|592|0|913|0|{}319|322|}
{2010212001|XXGvertex_oport_oport|593|0|915|0|{0|out|}322|323|}
{2010006001|XXGobject_psameas_object|594|0|917|0|{metadata|out_metadata|1|0|}323|322|}
{2010211001|XXGvertex_iport_iport|595|0|918|0|{0|in|}322|324|}
{2010006001|XXGobject_psameas_object|596|0|920|0|{metadata|in_metadata|1|0|}324|322|}
{2010006001|XXGobject_psameas_object|597|0|921|0|{Layout|Layout|0|0|}319|325|}
{2010211001|XXGvertex_iport_iport|598|0|923|0|{0|write|}325|326|}
{2010214001|XXGiport_src_flow|599|0|925|0|{0|}326|318|}
{2010007001|XXGobject_proto_object|600|0|926|0|{}325|327|}
{2010211001|XXGvertex_iport_iport|601|0|928|0|{0|write|}327|328|}
{2010006001|XXGobject_psameas_object|602|0|930|0|{metadata|write_metadata|1|0|}328|327|}
{2010006001|XXGobject_psameas_object|603|0|931|0|{write_metadata|read_metadata|0|0|}325|90|}
{2010006001|XXGobject_psameas_object|604|0|932|0|{in_metadata|read_metadata|0|0|}319|90|}
{2010006001|XXGobject_psameas_object|605|0|933|0|{out_metadata|read_metadata|0|0|}319|90|}
{2010601001|XXGgraph_vertex_vertex|606|0|934|0|{models_rejected|}317|325|}
{2010211001|XXGvertex_iport_iport|607|0|935|0|{0|in0|}317|329|}
{2010215002|XXGiport_binding_iport|608|0|937|0|{.5|.5|{0|}4507|}329|321|}
{2010214001|XXGiport_src_flow|609|0|938|0|{0|}329|12|}
{2010601001|XXGgraph_vertex_vertex|610|0|939|0|{risk_scores_func|}1|330|}
{2010212001|XXGvertex_oport_oport|611|0|941|0|{0|out0|}330|331|}
{2010213001|XXGoport_dst_flow|612|0|943|0|{0|}331|10|}
{2010212001|XXGvertex_oport_oport|613|0|944|0|{1|out1|}330|332|}
{2010213001|XXGoport_dst_flow|614|0|946|0|{0|}332|11|}
{2010212001|XXGvertex_oport_oport|615|0|947|0|{2|reject0|}330|333|}
{2010213001|XXGoport_dst_flow|616|0|949|0|{0|}333|13|}
{2010212001|XXGvertex_oport_oport|617|0|950|0|{3|reject1|}330|334|}
{2010213001|XXGoport_dst_flow|618|0|952|0|{0|}334|16|}
{2010212001|XXGvertex_oport_oport|619|0|953|0|{4|error0|}330|335|}
{2010212001|XXGvertex_oport_oport|620|0|955|0|{5|error1|}330|336|}
{2010212001|XXGvertex_oport_oport|621|0|957|0|{6|log|}330|337|}
{2010211001|XXGvertex_iport_iport|622|0|959|0|{0|in|}330|338|}
{2010214001|XXGiport_src_flow|623|0|961|0|{0|}338|14|}
{2010007001|XXGobject_proto_object|624|0|962|0|{}330|339|}
{2010212001|XXGvertex_oport_oport|625|0|964|0|{0|out0|}339|340|}
{2010006001|XXGobject_psameas_object|626|0|966|0|{metadata|out0_metadata|1|0|}340|339|}
{2010006001|XXGobject_psameas_object|627|0|967|0|{transform0|transform0|1|0|}340|339|}
{2010212001|XXGvertex_oport_oport|628|0|968|0|{1|out1|}339|341|}
{2010006001|XXGobject_psameas_object|629|0|970|0|{metadata|out1_metadata|1|0|}341|339|}
{2010006001|XXGobject_psameas_object|630|0|971|0|{transform1|transform1|1|0|}341|339|}
{2010212001|XXGvertex_oport_oport|631|0|972|0|{2|reject0|}339|342|}
{2010006001|XXGobject_psameas_object|632|0|974|0|{metadata|reject0_metadata|1|0|}342|339|}
{2010212001|XXGvertex_oport_oport|633|0|975|0|{3|reject1|}339|343|}
{2010006001|XXGobject_psameas_object|634|0|977|0|{metadata|reject1_metadata|1|0|}343|339|}
{2010212001|XXGvertex_oport_oport|635|0|978|0|{4|error0|}339|344|}
{2010006001|XXGobject_psameas_object|636|0|980|0|{metadata|error0_metadata|1|0|}344|339|}
{2010212001|XXGvertex_oport_oport|637|0|981|0|{5|error1|}339|345|}
{2010006001|XXGobject_psameas_object|638|0|983|0|{metadata|error1_metadata|1|0|}345|339|}
{2010212001|XXGvertex_oport_oport|639|0|984|0|{6|log|}339|346|}
{2010006001|XXGobject_psameas_object|640|0|986|0|{metadata|log_metadata|1|0|}346|339|}
{2010211001|XXGvertex_iport_iport|641|0|987|0|{0|in|}339|347|}
{2010006001|XXGobject_psameas_object|642|0|989|0|{metadata|in_metadata|1|0|}347|339|}
{2010006001|XXGobject_psameas_object|643|0|990|0|{Layout|Layout|0|0|}330|90|}
{2010006001|XXGobject_psameas_object|644|0|991|0|{in_metadata|out0_metadata|0|0|}330|269|}
{2010006001|XXGobject_psameas_object|645|0|992|0|{out0_metadata|write_metadata|0|0|}330|25|}
{2010006001|XXGobject_psameas_object|646|0|993|0|{out1_metadata|write_metadata|0|0|}330|106|}
{2010006001|XXGobject_psameas_object|647|0|994|0|{reject0_metadata|out0_metadata|0|0|}330|269|}
{2010006001|XXGobject_psameas_object|648|0|995|0|{reject1_metadata|out0_metadata|0|0|}330|269|}
{2010109001|XXGobject_property_value|649|0|996|0|{0|TrackingThumbprint|72|}1|348|}
