@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|9|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|128|rel_count|228|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_semantic_schema|9|1|1|Hnl|@{0|}}
{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
{30001002|XXparameter|!ab_compatibility|4.1.6.2|3|9|P|@{0|}}
{30001002|XXparameter|_UseNewErrorLogDML|True|13|1|Hl||{0|}}
}}@0|@0|0|0|0|0|0|0|ECS_S500_FV|jd77584|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|1010000|526000|7|}}
{2010703001|XXGgraphinfo|2|0|3|0|{@{}@1|4.0.2.4|{3|1|1|1|}Job 'ECS_S500_FV' Execution Status Report

Job completed successfully at Thursday, July 07, 2022 09:18:02
Run performed by user jd77584
||||@@33207807|}}
{2010705002|XXGrunsettings|3|0|5|0|{@{}@EDW||||1|60|0|1|1|0|0|0|0|1|1|0|0|1|2|1|1|0|0|0|@16|}}
{2010242002|XXGface|4|0|7|0|{@{}@Arial|0|100|0|}}
{2010210004|XXGflow|5|0|9|0|{@{}@0|.5|.5|{0|}480|17|}}
{2010210004|XXGflow|6|0|11|0|{@{}@0|.5|.5|{0|}477|17|}}
{2010210004|XXGflow|7|0|13|0|{@{}@0|.5|.5|{0|}447|17|}}
{2010210004|XXGflow|8|0|15|0|{@{}@0|.5|.5|{0|}416|17|}}
{2010210004|XXGflow|9|0|17|0|{@{}@0|.5|.5|{0|}403|17|}}
{2010210004|XXGflow|10|0|19|0|{@{}@0|.5|.5|{0|}418|17|}}
{2010210004|XXGflow|11|0|21|0|{@{}@0|.5|.5|{0|}414|17|}}
{2010210004|XXGflow|12|0|23|0|{@{}@0|.5|.5|{0|}476|17|}}
{2010210004|XXGflow|13|0|25|0|{@{}@0|.5|.5|{0|}479|17|}}
{2010210004|XXGflow|14|0|27|0|{@{}@0|.5|.5|{0|}458|17|}}
{2010210004|XXGflow|15|0|29|0|{@{}@0|.5|.5|{0|}469|17|}}
{2010210004|XXGflow|16|0|31|0|{@{}@0|.5|.5|{0|}466|17|}}
{2010210004|XXGflow|17|0|33|0|{@{}@0|.5|.9620253443717957|{0|}474|17|}}
{2010210004|XXGflow|18|0|35|0|{@{}@0|.5|.5|{0|}472|17|}}
{2010501005|XXGpvertex|19|0|37|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Concatenate.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Concatenate|572000|330000|0|0|0|0|468|Concatenate|Ab Initio Software|Built-in 1.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|20|0|39|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|21|0|42|0|{@{}@0|0|0|0|in|0.0|@@@18195|0|}}
{2010501005|XXGpvertex|22|0|46|0|{Appends multiple flow partitions of data records one after another.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|concat|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=exact(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1639787120|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Concatenate|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|23|0|48|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|24|0|51|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@18195|0|}}
{2010503005|XXGfvertex|25|0|54|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/COUNT_FILTER_S500.TXT", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|$AI_SERIAL/COUNT_FILTER_S500.TXT|3|2|$|@{0|}}
{30001002|XXparameter|write_metadata||3|8|s=|@{0|}}
}}@0|Output File|919000|320000|0|0|0|0|473|Output File|Ab Initio Software|@1|1000|-1||6||257|-1|-1|}}
{2010202004|XXGiport|26|0|56|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|27|0|59|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Output File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|28|0|61|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|29|0|64|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Rollup.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|l|@{0|}}
{30001002|XXparameter|out_metadata|record
 string(1) key;
 string(4) system;
 decimal("x00") count_S500;
end;|3|1|l|@{0|}}
{30001002|XXparameter|in_metadata|include "~$AI_DML/S500_INCOMING.dml";
metadata type = ws._cfzo500s_r_ab_type;|3|1|l|@{0|}}
{30001002|XXparameter|key|\{sat_fec_transaccion\}|3|2|$|@{0|}}
{30001002|XXparameter|transform|out :: rollup(in) =
begin
  out.key::"T";
  out.system::'S500';
  out.count_S500 :: count(in.sat_fec_transaccion);
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Rollup|384000|294000|0|0|0|0|456|Filter Count|Ab Initio Software|Built-in 2.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|30|0|66|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|31|0|69|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|32|0|71|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|33|0|73|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|34|0|75|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|35|0|78|0|{ROLLUP processes groups of input records that have the same key, generating one output record for each group. The input to ROLLUP can be ordered or unordered; for more information, see the sorted-input parameter. ROLLUP itself does not sort the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|?rollup|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/transform|3|2|H$||{0|}}
{30001002|XXparameter|sorted_input|True|13|1|Fl|Set this parameter to False if the input is not sorted or grouped.|{0|}}
{30001002|XXparameter|sorted_input.display_name|sorted-input|3|9|P|@{0|}}
{30001002|XXparameter|sorted_input.update_clauses|retain_old_default|3|9|P|@{0|}}
{30001002|XXparameter|key_method|value sorted-input False True default constant True|13|13|Fv|How groups are specified|{0|}}
{30001002|XXparameter|key_method.display_name|key-method|3|9|P|@{0|}}
{30001002|XXparameter|key_method.condition|param sorted-input True|3|15|P?|@{0|}}
{30001002|XXparameter|key_method_display_values|Usekey_changefunction Usekeyspecifier|3|2|H$||{0|}}
{30001002|XXparameter|key_method_display_values.display_name|key-method-display-values|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key to define rollup groups|{0|}}
{30001002|XXparameter|key.condition|param key-method True|3|15|P?|@{0|}}
{30001002|XXparameter|positional_key|value key-method False "" sameas key|19|13|Ov|Key to define rollup groups|{0|}}
{30001002|XXparameter|transform||8|1|RFOl|Required and optional DML functions|{0|}}
{30001002|XXparameter|max_core|67108864|1|2|FK$|Maximum memory usage (before spilling to disk) in bytes|{0|}}
{30001002|XXparameter|max_core.display_name|max-core|3|9|P|@{0|}}
{30001002|XXparameter|max_core.keyword|max-core|3|9|P|@{0|}}
{30001002|XXparameter|max_core.condition|param sorted-input False|3|15|P?|@{0|}}
{30001002|XXparameter|max_core.update_clauses|retain_old_default|3|9|P|@{0|}}
{30001002|XXparameter|output_without_input|Never|15|1|FKl|When to invoke the output_without_input transform function to produce an output record not corresponding to an input record.|{4|Never|At each computepoint|At each checkpoint|At component shutdown|}}
{30001002|XXparameter|output_without_input.condition|version 3.2.2.r15:|3|15|P?|@{0|}}
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
{30001002|XXparameter|check_sort.condition|param key-method True param sorted-input True version 2.11.1:|3|15|P?|@{0|}}
{30001002|XXparameter|check_sort.update_clauses|update_value False|3|9|P|@{0|}}
{30001002|XXparameter|grouped_input|False|13|1|Fl|Input data should be processed in groups|{0|}}
{30001002|XXparameter|grouped_input.display_name|grouped-input|3|9|P|@{0|}}
{30001002|XXparameter|grouped_input.condition|param sorted-input False version 2.14.102:|3|15|P?|@{0|}}
{30001002|XXparameter|grouped_input_display_values|Dataisnotgroupedbyamajorkey Dataisgroupedbyamajorkey|3|2|H$||{0|}}
{30001002|XXparameter|grouped_input_display_values.display_name|grouped-input-display-values|3|9|P|@{0|}}
{30001002|XXparameter|major_key||19|2|FK$|Major key into which data is grouped|{0|}}
{30001002|XXparameter|major_key.display_name|major-key|3|9|P|@{0|}}
{30001002|XXparameter|major_key.keyword|major-key|3|9|P|@{0|}}
{30001002|XXparameter|major_key.condition|param grouped-input True param sorted-input False version 2.14.102:|3|15|P?|@{0|}}
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
{30001002|XXparameter|num_operations|13|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|num_variables|1|1|2|H$|Number of public variables in rollup|{0|}}
{30001002|XXparameter|variable1|optional temporary_type temp|3|2|H$|Temporary variable|{0|}}
{30001002|XXparameter|operation1|optional integer(8) out::input_select(in)|3|2|H$|Select input record|{0|}}
{30001002|XXparameter|operation2|optional temp ? temp::initialize(in) : NULL|3|2|H$|Initialize temporary|{0|}}
{30001002|XXparameter|operation3|temp ? temp::rollup(temp, in) : out::rollup(in)|3|2|H$|Do computation|{0|}}
{30001002|XXparameter|operation4|optional temp ? out::finalize(temp, in) : NULL|3|2|H$|Create output record|{0|}}
{30001002|XXparameter|operation5|optional integer(8) out::output_select(out)|3|2|H$|Select output record|{0|}}
{30001002|XXparameter|operation6|optional integer(8) out::key_change(in in1, in in2)|3|2|H$|Determine if key changed|{0|}}
{30001002|XXparameter|operation7|optional out::output_without_input()|3|2|H$|Output when there are no input records|{0|}}
{30001002|XXparameter|operation7.condition|version 3.2.2.r15:|3|15|P?|@{0|}}
{30001002|XXparameter|operation1_analysis|integer(8) input_select_out::input_select(in)|3|2|H$|Select input record|{0|}}
{30001002|XXparameter|operation5_analysis|integer(8) output_select_out::output_select(out)|3|2|H$|Select output record|{0|}}
{30001002|XXparameter|operation6_analysis|integer(8) key_change_out::key_change(in in, in in)|3|2|H$|Determine if key changed|{0|}}
{30001002|XXparameter|_simple_transform_operation|rollup|3|2|H$|What operation should transform editor open with|{0|}}
{30001002|XXparameter|_simple_transform_operation.condition|version 2.11.7.m1:|3|15|P?|@{0|}}
{30001002|XXparameter|sorted_mpname|rollup|3|2|H$||{0|}}
{30001002|XXparameter|sorted_mpname.display_name|sorted-mpname|3|9|P|@{0|}}
{30001002|XXparameter|memory_mpname|hash-rollup|3|2|H$||{0|}}
{30001002|XXparameter|memory_mpname.display_name|memory-mpname|3|9|P|@{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter_xfr(transform.input_select); out=filter_xfr(transform.output_select); out=aggregate(key)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|3|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type3|event_info_t event_info "record int event_type; end"|3|2|H$|Information about the kind of event that happened|{0|}}
{30001002|XXparameter|operation8|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation9|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation10|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation11|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation12|optional out::output_at_event(event_info)|3|2|H$|Function to allow the output of an additional record at event|{0|}}
{30001002|XXparameter|operation13|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|6|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Rollup|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|36|0|80|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|37|0|83|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|38|0|86|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|39|0|89|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|40|0|92|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|41|0|99|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Concatenate.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Concatenate|244000|185500|0|0|0|0|219|Concatenate-1-4|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|42|0|101|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|43|0|104|0|{@{}@0|0|0|0|in|0.0|@@@18195|0|}}
{2010501005|XXGpvertex|44|0|110|0|{Appends multiple flow partitions of data records one after another.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|concat|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=exact(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis|fan_in_ok|3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|Concatenate|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|45|0|112|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|46|0|115|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@18195|0|}}
{2010503005|XXGfvertex|47|0|118|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/MWMX.BBD.UPLOAD.TRANLIST.NMIG.SE500", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|write_metadata|record
string (3000) data;

end|3|1|l|@{0|}}
{30001002|XXparameter|Layout|$AI_SERIAL/MWMX.BBD.UPLOAD.TRANLIST.NMIG.SE500|3|2|$|@{0|}}
}}@2|Output File|912000|175000|0|0|0|0|448|Output File-3|Ab Initio Software|@1|1000|-1||6||33025|-1|-1|}}
{2010202004|XXGiport|48|0|120|0|{@{}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010503005|XXGfvertex|49|0|123|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
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
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Output File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|50|0|125|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1780|0|}}
{2010501005|XXGpvertex|51|0|128|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|transform0|/*Reformat operation*/
out::reformat(in)=
begin
//HDR

//DTL
out.LAYINC_SISTEMA::'S500';
out.BDODTRNL_CARD_NBR::string_lrepad(string_substring((string(20))(decimal(20))in.cta_ordenante,2,19),19,'0'); 
out.BDODTRNL_EXTERNAL_ACCT::'   ';
out.BDODTRNL_TRANS_DATE::in.sat_fec_procesamntotxn;
out.signo::"+";
out.BDODTRNL_TRANS_AMT::string_substring((string(17))(decimal(17.2))in.sat_imp_transaccion,0,17); 
out.BDODTRNL_DISP_AMT::'0000000000';
out.BDODTRNL_TRANS_CD::string_lrepad(string_substring(in.sat_cve_txnsistema,1,4),6,'0');
out.BDODTRNL_DEST_TRANS::'000';
out.BDODTRNL_ORIG_CURR_CD::string_lrepad((string(3))(decimal(3))in.sat_cve_monedaoriginal, 3, '0'); //cambio 6
out.BDODTRNL_DEST_CURR_CD::'   ';
out.BDODTRNL_ORG::'   ';//
out.BDODTRNL_MERCH_NBR::string_lrepad(in.sat_num_nominamaker,16,'0');
out.BDODTRNL_MERCH_NAME::'                          ';
out.BDODTRNL_MERCH_CITY::'               ';
out.BDODTRNL_MERCH_CNTRY::'   ';
out.BDODTRNL_MCC::string_lrepad((string(4))(decimal(4))in.sat_num_sector,4,'0');
out.BDODTRNL_MERCH_POSTAL_CODE::'          ';
out.BDODTRNL_MERCH_STATE::'   ';
out.BDODTRNL_MERCH_RATE_CODE::'  ';//
out.BDODTRNL_ACQ_REF_NBR::in.sat_bitnf_ref23pos;
out.BDODTRNL_TRAN_UTILI_CODE::'0000';
out.BDODTRNL_AUTH_CODE::string_lrepad(string_substring((string(19))(decimal(19))in.sat_num_autransaccion,14,6),6,'0');
out.BDODTRNL_TERM_ID::string_lrepad(string_concat((string(4))(decimal(4))in.sat_num_suctransmisora,(string(2))(decimal(2))in.sat_num_cajatransmsora),8,'0'); //solo se llena de ceros el de la derecha, concatenar dos ceros? 12340028
out.BDODTRNL_POS_ENTRY_MODE::'  ';
out.BDODTRNL_ECOMERCE_INDEX::' ';
out.BDODTRNL_CAPTURE_TYPE::' ';
out.BDODTRNL_PROCESS_DATE::in.sat_fec_transaccion;
out.BDODTRNL_TRANS_DESC::in.sat_cve_leyenda;
out.BDODTRNL_PROMO_BRANCH::string_lrepad((string(5))(decimal(5))in.sat_num_sucpromtoracta,5,'0');
out.BDODTRNL_BRANCH_CASHIER::string_lrepad((string(3))(decimal(3))in.sat_num_caja, 2,'0');//cambio 3 
out.BDODTRNL_AUTORIZATION::string_lrepad((string(18))(decimal(18))in.sat_num_autransaccion,18,'0');
out.BDODTRNL_CHECK_NUMBER::in.sat_bit500_micr_s500.sat_bit500_refch_s500;//cambio 7
out.BDODTRNL_APPLICATION_ID::string_lrepad((string(4))(decimal(4))in.sat_num_sistemaorigtxn, 4, '0');//cambio 4
out.BDODTRNL_TRANSACTION_NUM::'0000';
out.BDODTRNL_TRANS_TIME::in.sat_hor_fintxn; 
out.BDODTRNL_CASE_PROC_TYPE::' ';
out.BDODTRNL_PLAN_NBR::'00000';
out.BDODTRNL_TCR_E::' ';
out.BDODTRNL_PROCESS_CODE::'      ';
out.BDODTRNL_MEANS_CONTANCT::string_lrepad((string(3))(decimal(3))in.sat_cve_mediocontacto,3,'0'); 
out.BDODTRNL_SERVICE_CODE::string_lrepad((string(3))(decimal(3))in.sat_num_serviciocd,3,'0');
out.BDODTRNL_TRANS_CTGY_CODE::'    ';
out.BDODTRNL_TERM_CAP::'      ';
out.BDODTRNL_CARDHLDR_IDN_MTHD::' ';
out.BDODTRNL_CRYPTO_INFO_DATA::'  ';
out.BDODTRNL_TVR_TER_VER_RES::'          ';
out.BDODTRNL_ARQC::'                ';
out.BDODTRNL_AUTH_AMT::'  ';
out.BDODTRNL_SECONDARY_AMT::'  ';
out.BDODTRNL_AIP::'    ';
out.BDODTRNL_ATC::'    ';
out.BDODTRNL_TERM_CNTRY_CD::'   ';
out.BDODTRNL_TRANS_CURR_CD::'   ';
out.BDODTRNL_EMV_TRANS_DT::'          ';
out.BDODTRNL_EMV_TRANS_TYPE::'  ';
out.BDODTRNL_UNPREDICTA_NUM::'        ';
out.BDODTRNL_IAD::'                                                                ';
out.BDODTRNL_IFD::'        ';
out.BDODTRNL_EMV_TERM_CAP::'        ';
out.BDODTRNL_EMV_TERM_TYPE::'  ';
out.BDODTRNL_APPL_VER_NUM::'    ';
out.BDODTRNL_CVMR::'      ';
out.BDODTRNL_DEDIC_FILE_NAME::'                                ';
out.BDODTRNL_POS_ENTRY_MOD_INP::'  ';
out.BDODTRNL_ENTRY_PIN::' ';
out.BDODTRNL_TERM_ENTRY_CPBLTY::' ';
out.BDODTRNL_LAST_EMV_STATUS::' ';
out.BDODTRNL_DATA_SUSPECT::' ';
out.BDODTRNL_PAN_SEQ_NUM::'  ';
out.BDODTRNL_DEVICE_INFO::'      ';
out.BDODTRNL_REASON_ON_LINE_CO::'    ';
out.BDODTRNL_ARQC_VERIFY::' ';
out.BDODTRNL_ISO_RESP_CODE::' ';
out.BDODTRNL_ISS_AUTH_DATA_LEN::'   ';
out.BDODTRNL_ISS_AUTH_DATA::'                                ';
out.BDODTRNL_SEND_CARD_BLOCK::' ';
out.BDODTRNL_SEND_PUT_DATA::' ';
out.BDODTRNL_OPR_CVETIPO::'    ';
out.BDODTRNL_OPR_PRESENICA_CVV::'          ';
out.BDODTRNL_OPR_VAL_CVV2::'          ';
out.BDODTRNL_OPR_PRES2AUTH::'          ';
out.BDODTRNL_OPR_VAL2AUTH::'          ';
out.BDODTRNL_ATM_RES_IND::' ';
out.BDODTRNL_CHIP_PIN_IND::' ';
out.BDODTRNL_3DS_OPT_RES_IND::' ';
out.BDODTRNL_WALLET_IND::' ';
out.BDODTRNL_DCVV2_RES_IND::' ';
out.BDODTRNL_2FA_RES_IND::' ';
out.BDODTRNL_TIPOAUTH7_NONE::' ';
out.BDODTRNL_PROTO_PGM_3DS2::' ';
out.BDODTRNL_AUTH_TYPE_3DS2::'                              ';
out.BDODTRNL_DS_TXN_ID_3DS2::'                                    ';
out.BDODTRNL_IAV_PRS_IND_3DS2::' ';
out.BDODTRNL_IAV_VL_TLT_3DS2::' ';
out.BDODTRNL_IP_ADDR_3DS2::'                                                  ';
out.BDODTRNL_MAC_ADDR_3DS2::'                    ';
out.BDODTRNL_CVE_MODACCESO::'   ';
out.BDODTRNL_WLL_CRYPTOGRAM::' ';
out.BDODTRNL_DEBIT_WALLET_ID::' ';
out.BDODTRNL_DPAN_ACCT_NBR::'                ';
out.BDODTRNL_MDES_TOKEN_REQID::'           ';
///.ecundarios S111
out.DET_HIS_PROCESO_AMD::'          ';
out.DET_HIS_MES_Y_CICLO_CORTE::'0000';
out.DET_HIS_DOLARES::'+00000000000000.00';
//S.cundarios 500
out.A00_BIT500_FUNCION::string_lrepad((string(2))(decimal(2))in.sat_funcion,2,'0');    
out.A00_BIT500_SISTEMA:: string_lrepad((string(4))(decimal(4))in.sat_num_sistemaorigtxn, 4, '0'); //Cambio 5
out.A00_BIT500_PRODUCTO::string_lrepad((string(4))(decimal(4))in.sat_num_producto,4,'0');   
out.A00_BIT500_INSTRUMENTO::string_lrepad((string(2))(decimal(2))in.sat_num_instrumento,2,'0');
out.A00_BIT500_CONTRATO::string_lrepad((string(16))(decimal(16))in.sat_num_cuenta,16,'0');//cambio 9 
out.A00_BIT500_CVEIMP:: ' '; //No encontrado    
out.A00_BIT500_FECVAL::in.sat_fec_fecval;   
out.A00_BIT500_AUT3ER:: string_substring(in.sat_num_empleadoautxn3, 1,10);//cambio 8, consultar longitud
out.A00_BIT500_REFNUM::string_lrepad(in.sat_cve_referenciatxn,20,'0'); 
out.A00_BIT500_MDA_SUC::string_lrepad((string(4))(decimal(4))in.sat_num_sucenvaincitva,4,'0');//cambio 10
out.A00_BIT500_CVEMDE:: string_lrepad((string(2))(decimal(2))in.sat_num_cajatransmsora, 2, '0'); //cambio 11       
out.A00_BIT500_SUCOPER::string_lrepad((string(4))(decimal(4))in.sat_num_sucoperadora,4,'0'); // cambio 12        
out.A00_BIT500_CAJAOPER:: string_lrepad((string(4))(decimal(4))in.sat_num_caja,4,'0');  //Cambio 13   
out.A00_BIT500_SUCTRAN::string_lrepad((string(4))(decimal(4))in.sat_num_suctransmisora,4,'0');        
out.A00_BIT500_CAJATRAN::string_lrepad((string(4))(decimal(4))in.sat_num_cajatransmsora,4,'0');     
out.A00_BIT500_ORIGEN:: '00';      
out.A00_BIT500_AUT_S151:: string_lrepad((string(8))(decimal(8))in.sat_num_autransaccion,8,'0');  //cambio 14     
out.A00_BIT500_AUTELI_S151::string_lrepad((string(8))(decimal(8))in.sat_auteli_s151,8,'0');    
out.A00_BIT500_AUTELI_ANT_S151::string_lrepad((string(8))(decimal(8))in.sat_auteli_ant_s151,8,'0');//solo tiene 4
out.A00_BIT500_TIPO_PROC:: '00';      
out.A00_BIT500_SOBREGIRO::string_lrepad((string(2))(decimal(2))in.sat_sobregiro,2,'0');      
out.A00_BIT500_CVEAVISO::string_lrepad((string(4))(decimal(4))in.sat_cveaviso,4,'0');  //solo es de 2     
out.A00_BIT500_IND_EDOCTA::string_lrepad((string(2))(decimal(2))in.sat_num_edocta,2,'0');     
out.A00_BIT500_IND_DATOS_ADIC::string_lrepad((string(2))(decimal(2))in.sat_num_datosadic,2,'0'); 
out.A00_BIT500_FECUM_NDIAS::in.sat_fec_ultmov; // Cambio 15    
out.A00_BIT500_BANCA::string_lrepad((string(2))(decimal(2))in.sat_num_banca,2,'0'); 
out.A00_BIT500_DATAGRUP1_PROD_TPR::string_lrepad((string(4))(decimal(4))in.sat_num_prodtprod,4,'0');
out.A00_BIT500_DATAGRUP2_INST_TCR::string_lrepad((string(4))(decimal(4))in.sat_num_insttcred,4,'0');
out.A00_BIT500_SIRH_DEPTO::string_lrepad((string(4))(decimal(4))in.sat_num_sirh,4,'0');        
out.A00_BIT500_LIBRO_CONTABLE::string_lrepad((string(2))(decimal(2))in.sat_num_librocontable,2,'0');    
out.A00_BIT500_CVE_DESVIO1::string_lrepad((string(4))(decimal(4))in.sat_cve_desvio,4,'0');
out.A00_BIT500_GUIA_DESVIO1::string_lrepad((string(4))(decimal(4))in.sat_guia_desvio,4,'0');
out.A00_BIT500_CVE_DESVIO2:: string_lrepad((string(4))(decimal(4))in.sat_cve_desvio, 4, '0'); //'0000' cambio 16
out.A00_BIT500_GUIA_DESVIO2:: string_lrepad((string(4))(decimal(4))in.sat_guia_desvio,4,'0');//'0000' cambio 17
out.A00_BIT500_CVE_DESVIO3:: string_lrepad((string(4))(decimal(4))in.sat_cve_desvio, 4, '0'); //'0000' cambio 18
out.A00_BIT500_GUIA_DESVIO3:: string_lrepad((string(4))(decimal(4))in.sat_guia_desvio,4,'0');//'0000' cambio 19
out.A00_BIT500_CVE_DESVIO4:: string_lrepad((string(4))(decimal(4))in.sat_cve_desvio, 4, '0'); //'0000' cambio 20
out.A00_BIT500_GUIA_DESVIO4:: string_lrepad((string(4))(decimal(4))in.sat_guia_desvio,4,'0');//'0000' cambio 21
out.A00_BIT500_CVE_DESVIO5:: string_lrepad((string(4))(decimal(4))in.sat_cve_desvio, 4, '0'); //'0000' cambio 22
out.A00_BIT500_GUIA_DESVIO5:: string_lrepad((string(4))(decimal(4))in.sat_guia_desvio,4,'0');//'0000' cambio 23
out.A00_BIT500_CLIENTE::string_lrepad(in.sat_num_cliente,14,'0'); //se mantiene seg�n pedido de cliente cambio 24 
out.A00_BIT500_NODO_ORIG:: '00';     
out.A00_BIT500_STATUS::string_lrepad((string(2))(decimal(2))in.sat_cve_estatustxn,2,'0');//verificar        
out.A00_BIT500_NOMINA_FUN1:: string_lrepad((string(10))(decimal(10))in.sat_num_empleadoautxn1, 10, '0'); //'00000000000000' Cambio 25   
out.A00_BIT500_NOMINA_FUN2:: string_lrepad((string(10))(decimal(10))in.sat_num_empleadoautxn2, 10, '0'); //'00000000000000' Cambio 26   
out.A00_BIT500_SIST_ORIG::string_lrepad((string(4))(decimal(4))in.sat_num_sistemaorigtxn,4,'0');     
out.A00_BIT500_PROD_ORIG::string_lrepad((string(4))(decimal(4))in.sat_num_prodorigentxn,4,'0');     
out.A00_BIT500_INST_ORIG::string_lrepad((string(2))(decimal(2))in.sat_num_instrumentorig,2,'0');     
out.A00_BIT500_CVETR_ORIG:: '000000';
out.A00_BIT500_CONT_ORIG:: in.cta_ordenante; //'                    '; cambio 27
out.A00_BIT500_REF_ALFA:: string_lrepad((string(24))(decimal(24)) in.cta_ordenante, 24, '0');//' ';cambio 28
out.A00_BIT500_CVECAUSA::string_lrepad((string(4))(decimal(4))in.sat_cve_causadevdocto,4,'0');
out.A00_BIT500_FECDEV::string_lrepad(in.sat_fec_devdocumento,10,'0');  
out.A00_BIT500_BANCO:: string_lrepad((string(4))(decimal(4))in.sat_num_bcoemisororden,4,'0'); //'0000'; cambio 29  
out.A00_BIT500_NOMORD:: ' ';  
out.A00_BIT500_CAUSAORD::string_lrepad(in.sat_cve_causaord,50,'0');
out.A00_BIT500_SUCORD::string_lrepad((string(4))(decimal(4))in.sat_num_sucord,4,'0');  
out.A00_BIT500_CTACON::string_lrepad((string(2))(decimal(2))in.sat_num_ctacon,2,'0');
out.signo_saldo::"+";
out.A00_BIT500_SALDO::string_lrepad((string(17))(decimal(17.2))in.sat_mto_saldo,17,'0');
out.A00_BIT500_0_REFNUM_CBII::in.sat_cve_refnumcbii; 
out.A00_BIT500_0_REFALFA_CBII::string_lrepad(in.sat_cve_refalfacbii,15,'0');
out.A00_BIT500_INTERCOMPANY:: '000000';
out.A00_BIT500_IMPBASE_ESQFINAN:: '+00000000000000.00';//No se encuentra
out.A00_BIT500_SIN_USO:: ' ';         
out.A00_BIT500_ESTATUS_REG:: '00';     
out.A00_BIT500_TIPO_OPER::in.sat_cve_tipopercd; // ' '; cambio 30     
out.A00_BIT500_TIPO_MOV:: string_lrepad((string(2))(decimal(2))in.sat_cve_tipomovcd,2,'0');//'00'; cambio 31        
out.A00_BIT500_AGRUP_DESVIO:: '0000';    
out.A00_BIT500_AGRUP_INST::string_lrepad((string(4))(decimal(4))in.sat_ind_agrupdesinstcd,4,'0');      
out.A00_BIT500_AGRUP_SIRH::string_lrepad((string(4))(decimal(4))in.sat_ind_agrupdessirhcd,4,'0');      
out.A00_BIT500_IND_ENVIO_CITI::string_lrepad(in.sat_bitnf_ind_envio_citi,2,'0');  //ebcdic
out.A00_BIT500_CVE_FILIAL::in.sat_cve_filialcd;      
out.A00_BIT500_AUT_NIO_S500:: string_lrepad((string(16))(decimal(16))in.sat_ind_autnio,1,'0');//' ';  cambio 32  
out.A00_BIT500_NOMINA_MAKER::string_lrepad((string(14))(decimal(14))in.sat_num_nominamaker,14,'0');    
out.A00_BIT500_NOMINA_CHECKER::string_lrepad((string(14))(decimal(14))in.sat_num_nominachecker,14,'0');  
out.A00_BIT500_REF_CLIENTE::in.sat_cve_refclientecd;     
out.A00_BIT500_REFERENCIA1_CTE::in.sat_cve_ref1clientecd; 
out.A00_BIT500_REFERENCIA2_CTE::in.sat_cve_ref2clientecd; 
out.A00_BIT500_REFERENCIA3_CTE::in.sat_cve_ref3clientecd; 
out.A00_BIT500_REFERENCIA4_CTE::' '; //no encontrado
out.A00_BIT500_LEYENDA2::in.sat_nom_leyenda2cd;        
out.A00_BIT500_LEYENDA3::in.sat_nom_leyenda3cd;        
out.A00_BIT500_LEYENDA4::in.sat_nom_leyenda4cd;        
out.A00_BIT500_LEYENDA5::in.sat_nom_leyenda5cd;        
out.A00_BIT500_MOTIVO_DEV::in.sat_nom_motivodevcd;      
out.A00_BIT500_NOM_BCO_EMISOR::in.sat_nom_bcoemisorcd;  
out.A00_BIT500_REF_CECOBAN::in.sat_cve_refcecobancd;     
out.A00_BIT500_NUM_ORD_PAGO::string_lrepad((string(18))(decimal(18))in.sat_num_ordpagocd,18,'0');    
out.A00_BIT500_NOM_BENEFICIARIO::string_substring(in.sat_nom_beneficiariocd,70,50); //el que necesitamos esta comentado arriba
out.A00_BIT500_CVE_RASTREO::in.sat_cve_rastreocd;     
out.A00_BIT500_FEC_PAGO::in.sat_fec_pagocd;        
out.A00_BIT500_NOM_CLIENTE::in.sat_nom_clientecd;     
out.A00_BIT500_VER_FIRMA::string_lrepad((string(3))(decimal(3))in.sat_num_verfirmacd,3,'0');       
out.A00_BIT500_TIPO_CHEQUE::string_lrepad((string(3))(decimal(3))in.sat_cve_tipochequecd,3,'0');     
out.A00_BIT500_CLIENTE_S500:: string_lrepad((string(12))(decimal(12))in.sat_num_cliente,12,'0');//'000000000000';  cambio 33  
out.A00_BIT500_SERVICIO_ALERTA:: in.sat_bit500_servicio_alerta;//'0000'; cambio 34
out.A00_BIT500_GRUPO_SOC:: '0000';       
out.A00_BIT500_BIN_TAR:: string_lrepad((string(4))(decimal(4))in.sat_num_prefijomedacc,6,'0');//'000000'; cambio 34       
out.A00_BIT500_SDO_FIN_S500::string_lrepad((string(15))(decimal(15,2))in.sat_mto_saldo,17,'0'); //'+00000000000000.00'; cambio 35
out.A00_BIT500_CSIREC_S500::in.sat_bit500_trui_s500.sat_bit500_csirec_s500; //'0000000'; cambio 36
out.A00_BIT500_CSIOR_S500::in.sat_bit500_trui_s500.sat_bit500_csior_s500; //'0000000';  cambio 37
out.A00_BIT500_NUMOP_S500::in.sat_bit500_trui_s500.sat_bit500_numop_s500; //'0000000'; cambio 38
out.A00_BIT500_NUMTR_S500::in.sat_bit500_trui_s500.sat_bit500_numtr_s500; //'0000000';  cambio 39
out.A00_BIT500_INSMN_S500::in.sat_bit500_trui_s500.sat_bit500_insmn_s500; //'00'; cambio 40
out.A00_BIT500_CODSEG_S500::in.sat_bit500_micr_s500.sat_bit500_codseg_s500; //'000'; cambio 41
out.A00_BIT500_VERPRE_S500::in.sat_bit500_micr_s500.sat_bit500_verpre_s500;//'0'; cambio 42
out.A00_BIT500_CTRMON_S500::in.sat_bit500_micr_s500.sat_bit500_ctrmon_s500;//'00'; cambio 43
out.A00_BIT500_PLCEC_S500::in.sat_bit500_micr_s500.sat_bit500_plcec_s500;//'000'; cambio 44
out.A00_BIT500_BNCEM_S500::in.sat_bit500_micr_s500.sat_bit500_bncem_s500;//'000'; cambio 45
out.A00_BIT500_DVEIN_S500::in.sat_bit500_micr_s500.sat_bit500_dvein_s500; //'0'; cambio 46
out.A00_BIT500_CTACH_S500::in.sat_bit500_micr_s500.sat_bit500_ctach_s500; //'00000000000';  cambio 47
out.A00_BIT500_CTABEN_S500::in.sat_bit500_ctaben_s500; // cambio 48
out.A00_BIT500_BCREC_S500::in.sat_bit500_bcrec_s500;  //cambio 49
out.A00_BIT500_NOMBEN_S500::in.sat_bit500_nomben_s500;//' '; Cambio 50 
out.A00_BIT500_RFCBCO_S500::in.sat_bit500_rfcbco_s500;//' '; Cambio  51 
out.A00_BIT500_NOMPAN_S500::' '; 
out.A00_BIT500_OPCPAN_S500::' '; 
out.A00_BIT500_NUMCTO1_S500::'0000000000000000';
out.A00_BIT500_NUMCTO2_S500::'0000000000000000';
out.A00_BIT500_NUMCTO3_S500::'0000000000000000';
out.A00_BIT500_IND_SUBC::string_lrepad(in.sat_bit500_ind_subc,1,'0');      
out.A00_BIT500_PRO_SUBC::string_lrepad(in.sat_bit500_pro_subc,4,'0');      
out.A00_BIT500_INST_SUBC::string_lrepad(in.sat_bit500_ins_subc,4,'0');     
out.A00_BIT500_MON_SUBC::string_lrepad(in.sat_bit500_mon_subc,3,'0');      
out.A00_BIT500_CONT_SUBC::string_lrepad(in.sat_bit500_cto_subc,16,'0');     
out.A00_BIT500_CTAMDA_SUBC::string_lrepad(in.sat_bit500_ctamda_subc,16,'0');   
out.A00_BIT500_STA_SUBC::string_lrepad(in.sat_bit500_sta_subc,4,'0');      
out.A00_BIT500_INDALER_SUBC::string_lrepad(in.sat_bit500_indaler_subc,4,'0');  
out.A00_BIT500_INDCTACON_SUBC::string_lrepad(in.sat_bit500_indctacon_subc,2,'0');
out.A00_BIT500_LEYENDA_SUBC::in.sat_bit500_leyenda_subc;
//T.ANSFER SECUNDARIOS
out.NUM_CONTRATO:: '000000000000';
out.HOR_FIN_TRANSACCION:: ' ';
out.CVE_BCO_ORIGEN:: '000';
out.CVE_BCO_DESTINO:: '000';
out.NUM_DESTINO_TRNX:: '000000000000000000';
out.NUM_SIRH:: '000000000';
out.CVE_EJECUTIVO:: ' ';
out.CVE_STS_TRANSACCION:: '00';
out.SDO_CUENTA_ORIGEN:: '+00000000000000.00';
out.SDO_CUENTA_DESTINO:: '+00000000000000.00';
out.COMISION:: '+00000000000000.00';
out.IVA:: '+00000000000000.00';
out.TASA_IVA:: '00';
out.DES_MENSAJE_ERR:: ' ';
out.ID_TRANSACCION_REVERSO:: ' ';
out.AUDIT_NUMBER:: '000000000000000';
out.MSISDN_RECEPCION:: '0000000000';
out.CARRIER:: ' ';
out.TIPO_ASOCIACION_BMX:: '00';
out.CLAVE_RASTREO:: ' ';
out.NUMERO_REFERENCIA:: '0000000';
out.EXTERNAL_P2P:: '0';
out.VALIDACION_H_INE_TX:: '0';
out.PERCENTAGE_INE_TX:: '00000';
out.FOLIO_TXN_INE:: ' ';
out.AUTH_SUPERV_TX:: ' ';
out.NOMBRE_COMPLETO_SPEI:: ' ';
out.FOLIO_RENAPO:: ' ';
out.filler2::' ' ; 
out.new_line::("\\n"); 


end;|3|1|l|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out0_metadata|record
       //HDR
       
       
        string (4) LAYINC_SISTEMA;
        string (19) BDODTRNL_CARD_NBR; // Enter your record definition here
        string (3) BDODTRNL_EXTERNAL_ACCT;     
        string (10) BDODTRNL_TRANS_DATE;  
        string(1) signo; 
        string (17) BDODTRNL_TRANS_AMT;         
        string (10) BDODTRNL_DISP_AMT;          
        string (6) BDODTRNL_TRANS_CD;          
        string (3) BDODTRNL_DEST_TRANS;        
        string (4) BDODTRNL_ORIG_CURR_CD; //     
        string (3) BDODTRNL_DEST_CURR_CD;     
        string (3) BDODTRNL_ORG;
        string (16) BDODTRNL_MERCH_NBR;         
        string (26) BDODTRNL_MERCH_NAME;        
        string (15) BDODTRNL_MERCH_CITY;        
        string (3) BDODTRNL_MERCH_CNTRY;       
        decimal (4) BDODTRNL_MCC;               
        string (10) BDODTRNL_MERCH_POSTAL_CODE; 
        string (3) BDODTRNL_MERCH_STATE;    
        string (2) BDODTRNL_MERCH_RATE_CODE;
        string (23) BDODTRNL_ACQ_REF_NBR;    
        string (4) BDODTRNL_TRAN_UTILI_CODE;
        string (6) BDODTRNL_AUTH_CODE;      
        string (8) BDODTRNL_TERM_ID;        
        string (2) BDODTRNL_POS_ENTRY_MODE; 
        string (1) BDODTRNL_ECOMERCE_INDEX; 
        string (1) BDODTRNL_CAPTURE_TYPE;   
        string (10) BDODTRNL_PROCESS_DATE; 
        string (40) BDODTRNL_TRANS_DESC;          
        string (5)BDODTRNL_PROMO_BRANCH; 
        string (2)BDODTRNL_BRANCH_CASHIER ;
        string (18)BDODTRNL_AUTORIZATION ;
        string (12)BDODTRNL_CHECK_NUMBER ;
        string (4)BDODTRNL_APPLICATION_ID ;
        string (4)BDODTRNL_TRANSACTION_NUM ;
        string (8)BDODTRNL_TRANS_TIME ;
        string (1)BDODTRNL_CASE_PROC_TYPE ;
        string (5)BDODTRNL_PLAN_NBR;
        string (1)BDODTRNL_TCR_E ;
        string (6)BDODTRNL_PROCESS_CODE ;
        string (3)BDODTRNL_MEANS_CONTANCT ;
        string (3)BDODTRNL_SERVICE_CODE ;
        string (4)BDODTRNL_TRANS_CTGY_CODE ;
        string (6)BDODTRNL_TERM_CAP ;
        string (1)BDODTRNL_CARDHLDR_IDN_MTHD ;
        string (2)BDODTRNL_CRYPTO_INFO_DATA ;
        string (10)BDODTRNL_TVR_TER_VER_RES ;
        string (16)BDODTRNL_ARQC ;
        string (12)BDODTRNL_AUTH_AMT ;
        string (12)BDODTRNL_SECONDARY_AMT ;
        string (4)BDODTRNL_AIP ;
        string (4)BDODTRNL_ATC ;
        string (3)BDODTRNL_TERM_CNTRY_CD ;
        string (3)BDODTRNL_TRANS_CURR_CD ;
        string (10)BDODTRNL_EMV_TRANS_DT ;
        string (2)BDODTRNL_EMV_TRANS_TYPE ;
        string (8)BDODTRNL_UNPREDICTA_NUM ;
        string (64)BDODTRNL_IAD ;
        string (8)BDODTRNL_IFD ;
        string (8)BDODTRNL_EMV_TERM_CAP ;
        string (2)BDODTRNL_EMV_TERM_TYPE ;
        string (4)BDODTRNL_APPL_VER_NUM ;
        string (6)BDODTRNL_CVMR ;
        string (32)BDODTRNL_DEDIC_FILE_NAME ;
        string (2)BDODTRNL_POS_ENTRY_MOD_INP ;
        string (1)BDODTRNL_ENTRY_PIN ;
        string (1)BDODTRNL_TERM_ENTRY_CPBLTY ;
        string (1)BDODTRNL_LAST_EMV_STATUS ;
        string (1)BDODTRNL_DATA_SUSPECT ;
        string (2)BDODTRNL_PAN_SEQ_NUM ;
        string (6)BDODTRNL_DEVICE_INFO ;
        string (4)BDODTRNL_REASON_ON_LINE_CO ;
        string (1)BDODTRNL_ARQC_VERIFY ;
        string (1)BDODTRNL_ISO_RESP_CODE ;
        string (4)BDODTRNL_ISS_AUTH_DATA_LEN ;
        string (32)BDODTRNL_ISS_AUTH_DATA ;
        string (1)BDODTRNL_SEND_CARD_BLOCK ;
        string (1)BDODTRNL_SEND_PUT_DATA ;
        string (4)BDODTRNL_OPR_CVETIPO ;
        string (10)BDODTRNL_OPR_PRESENICA_CVV ;
        string (10)BDODTRNL_OPR_VAL_CVV2 ;
        string (10)BDODTRNL_OPR_PRES2AUTH ;
        string (10)BDODTRNL_OPR_VAL2AUTH ;
        string (1)BDODTRNL_ATM_RES_IND ;
        string (1)BDODTRNL_CHIP_PIN_IND ;
        string (1)BDODTRNL_3DS_OPT_RES_IND ;
        string (1)BDODTRNL_WALLET_IND ;
        string (1)BDODTRNL_DCVV2_RES_IND ;
        string (1)BDODTRNL_2FA_RES_IND ;
        string (1)BDODTRNL_TIPOAUTH7_NONE ;
        string (1)BDODTRNL_PROTO_PGM_3DS2 ;
        string (30)BDODTRNL_AUTH_TYPE_3DS2 ;
        string (36)BDODTRNL_DS_TXN_ID_3DS2 ;
        string (1)BDODTRNL_IAV_PRS_IND_3DS2 ;
        string (1)BDODTRNL_IAV_VL_TLT_3DS2 ;
        string (50)BDODTRNL_IP_ADDR_3DS2 ;
        string (20)BDODTRNL_MAC_ADDR_3DS2 ;
        string (3)BDODTRNL_CVE_MODACCESO ;
        string (1)BDODTRNL_WLL_CRYPTOGRAM;
        string (1)BDODTRNL_DEBIT_WALLET_ID;
        string (16)BDODTRNL_DPAN_ACCT_NBR;
        string (11)BDODTRNL_MDES_TOKEN_REQID;
        string (10)DET_HIS_PROCESO_AMD;
        string (4)DET_HIS_MES_Y_CICLO_CORTE;
        string (18)DET_HIS_DOLARES;
//Fin s111
//Inicio s500
 //S500 SECUNDARIOS
        string	(2)	A00_BIT500_FUNCION;    
        string	(4)	A00_BIT500_SISTEMA;
        string	(4)	A00_BIT500_PRODUCTO;   
        string	(2)	A00_BIT500_INSTRUMENTO;
        string	(16)    A00_BIT500_CONTRATO;   
        string  (140)   A00_BIT500_CVEIMP;     
        string  (10)    A00_BIT500_FECVAL;   
        string	(10)    A00_BIT500_AUT3ER;   
        string  (20)    A00_BIT500_REFNUM;
        string	(4)	A00_BIT500_MDA_SUC;
        string	(2)	A00_BIT500_CVEMDE;         
        string	(4)	A00_BIT500_SUCOPER;        
        string	(4)	A00_BIT500_CAJAOPER;       
        string	(4)	A00_BIT500_SUCTRAN;        
        string	(4)	A00_BIT500_CAJATRAN;       
        string	(2)	A00_BIT500_ORIGEN;         
        string	(8)	A00_BIT500_AUT_S151;       
        string	(8)	A00_BIT500_AUTELI_S151;    
        string	(8)	A00_BIT500_AUTELI_ANT_S151;
        string	(2)	A00_BIT500_TIPO_PROC;      
        string	(2)	A00_BIT500_SOBREGIRO;      
        string	(4)	A00_BIT500_CVEAVISO;       
        string	(2)	A00_BIT500_IND_EDOCTA;     
        string	(2)	A00_BIT500_IND_DATOS_ADIC; 
        string	(10)    A00_BIT500_FECUM_NDIAS;    
        string	(2)     A00_BIT500_BANCA; 
        string	(4)	A00_BIT500_DATAGRUP1_PROD_TPR;
        string	(4)	A00_BIT500_DATAGRUP2_INST_TCR;
        string	(4)	A00_BIT500_SIRH_DEPTO;        
        string	(2)	A00_BIT500_LIBRO_CONTABLE;    
        string	(4)	A00_BIT500_CVE_DESVIO1;
        string	(4)	A00_BIT500_GUIA_DESVIO1;
        string	(4)	A00_BIT500_CVE_DESVIO2;
        string	(4)	A00_BIT500_GUIA_DESVIO2;
        string	(4)	A00_BIT500_CVE_DESVIO3;
        string	(4)	A00_BIT500_GUIA_DESVIO3;
        string	(4)	A00_BIT500_CVE_DESVIO4;
        string	(4)	A00_BIT500_GUIA_DESVIO4;
        string	(4)	A00_BIT500_CVE_DESVIO5;
        string	(4)	A00_BIT500_GUIA_DESVIO5;
        string	(14)    A00_BIT500_CLIENTE;
        string	(2)	A00_BIT500_NODO_ORIG;     
        string	(2)	A00_BIT500_STATUS;        
        string	(14)    A00_BIT500_NOMINA_FUN1;   
        string	(14)    A00_BIT500_NOMINA_FUN2;   
        string	(4)	A00_BIT500_SIST_ORIG;     
        string	(4)	A00_BIT500_PROD_ORIG;     
        string	(2)	A00_BIT500_INST_ORIG;     
        string	(6)	A00_BIT500_CVETR_ORIG;
        string  (20)    A00_BIT500_CONT_ORIG; 
        string  (24)    A00_BIT500_REF_ALFA;
        string	(4)	A00_BIT500_CVECAUSA;
        string  (10)    A00_BIT500_FECDEV;  
        string	(4)	A00_BIT500_BANCO;   
        string  (30)    A00_BIT500_NOMORD;  
        string  (50)    A00_BIT500_CAUSAORD;
        string	(4)	A00_BIT500_SUCORD;  
        string	(2)	A00_BIT500_CTACON;
        string (1) signo_saldo;
        string  (17)    A00_BIT500_SALDO;      
        string  (10)    A00_BIT500_0_REFNUM_CBII; 
        string  (15)    A00_BIT500_0_REFALFA_CBII;
        string	(6)	A00_BIT500_INTERCOMPANY;
        string	(18)    A00_BIT500_IMPBASE_ESQFINAN;
        string  (15)    A00_BIT500_SIN_USO;         
        string	(2)	A00_BIT500_ESTATUS_REG;     
        string  (1)	A00_BIT500_TIPO_OPER;       
        string	(2)	A00_BIT500_TIPO_MOV;        
        string	(4)	A00_BIT500_AGRUP_DESVIO;    
        string	(4)	A00_BIT500_AGRUP_INST;      
        string	(4)	A00_BIT500_AGRUP_SIRH;      
        string	(2)	A00_BIT500_IND_ENVIO_CITI;  
        string  (5)	A00_BIT500_CVE_FILIAL;      
        string  (16)    A00_BIT500_AUT_NIO_S500;    
        string	(14)    A00_BIT500_NOMINA_MAKER;    
        string	(14)    A00_BIT500_NOMINA_CHECKER;  
        string  (16)    A00_BIT500_REF_CLIENTE;     
        string  (35)    A00_BIT500_REFERENCIA1_CTE; 
        string  (35)    A00_BIT500_REFERENCIA2_CTE; 
        string  (35)    A00_BIT500_REFERENCIA3_CTE; 
        string  (35)    A00_BIT500_REFERENCIA4_CTE; 
        string  (40)    A00_BIT500_LEYENDA2;        
        string  (40)    A00_BIT500_LEYENDA3;        
        string  (40)    A00_BIT500_LEYENDA4;        
        string  (40)    A00_BIT500_LEYENDA5;        
        string  (30)    A00_BIT500_MOTIVO_DEV;      
        string  (20)    A00_BIT500_NOM_BCO_EMISOR;  
        string  (7)	A00_BIT500_REF_CECOBAN;     
        string	(18)    A00_BIT500_NUM_ORD_PAGO;    
        string  (50)    A00_BIT500_NOM_BENEFICIARIO;
        string  (30)    A00_BIT500_CVE_RASTREO;     
        string  (10)    A00_BIT500_FEC_PAGO;        
        string  (36)    A00_BIT500_NOM_CLIENTE;     
        string	(3)	A00_BIT500_VER_FIRMA;       
        string	(3)	A00_BIT500_TIPO_CHEQUE;     
        string	(12)    A00_BIT500_CLIENTE_S500;    
        string	(4)	A00_BIT500_SERVICIO_ALERTA; 
        string	(4)	A00_BIT500_GRUPO_SOC;       
        string	(6)	A00_BIT500_BIN_TAR;         
        string	(18)    A00_BIT500_SDO_FIN_S500;
        string	(7)	A00_BIT500_CSIREC_S500;
        string	(7)	A00_BIT500_CSIOR_S500; 
        string	(7)	A00_BIT500_NUMOP_S500; 
        string	(7)	A00_BIT500_NUMTR_S500; 
        string	(2)	A00_BIT500_INSMN_S500;
        string	(3)	A00_BIT500_CODSEG_S500;
        string	(1)	A00_BIT500_VERPRE_S500;
        string	(2)	A00_BIT500_CTRMON_S500;
        string	(3)	A00_BIT500_PLCEC_S500; 
        string	(3)	A00_BIT500_BNCEM_S500; 
        string	(1)	A00_BIT500_DVEIN_S500; 
        string	(11)    A00_BIT500_CTACH_S500; 
        string  (20)    A00_BIT500_CTABEN_S500; 
        string	(3)	A00_BIT500_BCREC_S500;  
        string  (40)    A00_BIT500_NOMBEN_S500; 
        string  (13)    A00_BIT500_RFCBCO_S500; 
        string  (5)	A00_BIT500_NOMPAN_S500; 
        string  (1)	A00_BIT500_OPCPAN_S500; 
        string	(16)    A00_BIT500_NUMCTO1_S500;
        string	(16)    A00_BIT500_NUMCTO2_S500;
        string	(16)    A00_BIT500_NUMCTO3_S500;
        string	(1)	A00_BIT500_IND_SUBC;      
        string	(4)	A00_BIT500_PRO_SUBC;      
        string	(4)	A00_BIT500_INST_SUBC;     
        string	(3)	A00_BIT500_MON_SUBC;      
        string	(16)    A00_BIT500_CONT_SUBC;     
        string	(16)    A00_BIT500_CTAMDA_SUBC;   
        string	(4)	A00_BIT500_STA_SUBC;      
        string	(4)	A00_BIT500_INDALER_SUBC;  
        string	(2)	A00_BIT500_INDCTACON_SUBC;
        string  (40)    A00_BIT500_LEYENDA_SUBC;
                        //TRANSFER SECUNDARIOS
        string	(12)    NUM_CONTRATO;
        string  (8)      HOR_FIN_TRANSACCION;
        string  (3)	CVE_BCO_ORIGEN;
        string	(3)	CVE_BCO_DESTINO;
        string	(18)    NUM_DESTINO_TRNX;
        string	(9)	NUM_SIRH;
        string  (15)     CVE_EJECUTIVO;
        string  (2)	CVE_STS_TRANSACCION;
        
        string  (18)    SDO_CUENTA_ORIGEN;
        string  (18)    SDO_CUENTA_DESTINO;
        string  (18)    COMISION;
        string  (18)    IVA;
        string  (2)     TASA_IVA;
        string  (20)     DES_MENSAJE_ERR;
        string  (20)     ID_TRANSACCION_REVERSO;
        string  (15)    AUDIT_NUMBER;
        string  (10)    MSISDN_RECEPCION;
        string  (4)      CARRIER;
        string  (2)	TIPO_ASOCIACION_BMX;
        string  (30)     CLAVE_RASTREO;
        string  (7)	NUMERO_REFERENCIA;
        string  (1)	EXTERNAL_P2P;
        string  (1)     VALIDACION_H_INE_TX;
        string  (5)     PERCENTAGE_INE_TX;
        string  (25)     FOLIO_TXN_INE;
        string  (16)     AUTH_SUPERV_TX;
        string  (60)     NOMBRE_COMPLETO_SPEI;
        string  (25)     FOLIO_RENAPO;
       
        string (213) filler2; 
         string (1) new_line;
         
      
        
end ;|3|1|l|@{0|}}
{30001002|XXparameter|in_metadata|include "~$AI_DML/S500_INCOMING.dml";
metadata type = ws._cfzo500s_r_ab_type;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@1|Reformat|567000|155000|0|0|0|0|481|Mapping Trans-7|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|52|0|130|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|53|0|133|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|54|0|135|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|55|0|137|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|56|0|139|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|57|0|142|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
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
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Reformat|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|58|0|144|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|59|0|148|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|60|0|151|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|61|0|154|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|62|0|157|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|63|0|163|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Validate/Create_Data.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|num_records|1|3|2|$|@{0|}}
{30001002|XXparameter|transform|out::create(index) = begin
  out.key::'T';
  out.system::'S500';
  out.count_S500::0;
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Create Data|410000|446000|0|0|0|0|475|Create Data|Ab Initio Software|Built-in 2.15.2:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|64|0|165|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|65|0|168|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|66|0|170|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|67|0|172|0|{Creates records according to a transform.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|Create_Data|3|1|Hl||{0|}}
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
{30001002|XXparameter|mpcmodtime|1639787121|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
}}@0|Create Data|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|68|0|174|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|69|0|177|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|70|0|180|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010501005|XXGpvertex|71|0|185|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Dedup_Sorted.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|dup_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|key|\{key\}|3|2|$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Dedup Sorted|675000|301000|0|0|0|0|471|Dedup Sorted|Ab Initio Software|Built-in 2.0:|1|100|0||6||4097|1|{1|0|}}}
{2010203004|XXGoport|72|0|187|0|{@{}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|73|0|190|0|{@{}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|74|0|192|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|75|0|194|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|76|0|196|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|77|0|198|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|78|0|201|0|{Separates one specified data record in each group of data records from the rest of the records in the group.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|dedup|3|1|Hl||{0|}}
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
{2010203004|XXGoport|79|0|203|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2196|0|}}
{2010203004|XXGoport|80|0|206|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|dup|0.0|@@@2192|0|}}
{2010203004|XXGoport|81|0|209|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|82|0|212|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|83|0|215|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|84|0|218|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|85|0|227|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Filter_by_Expression.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|deselect_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|select_expr|(decimal(10))sat_cve_txnsistema >= 1000 or
(decimal(10))sat_cve_txnsistema == 938|3|2|$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|Filter by Expression|350000|175000|0|0|0|0|478|Filter S500|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|86|0|229|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|87|0|232|0|{@{}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|88|0|235|0|{@{}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|89|0|237|0|{@{}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|90|0|239|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|91|0|241|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|92|0|244|0|{Filters data records according to the specified DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|select-transform|3|1|Hl||{0|}}
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
{30001002|XXparameter|num_operations|6|1|2|H$|Number of operations in package|{0|}}
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
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select_expr); deselect=filter(select_expr); out=filter_xfr(package.select); deselect=filter_xfr(package.select);|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record string('', charset='x-ab-internal') component; int port_index; string('', charset='x-ab-internal') parameter; string('', charset='x-ab-internal') message; record string('', charset='x-ab-internal') code; int parent_index; record string('', charset='x-ab-internal') name; string('', charset='x-ab-internal') value; end[int] attributes; end[int] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('', charset='x-ab-internal') event_type; string('', charset='x-ab-internal') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|operation6|optional ::on_startup(long in_recovery)|3|2|H$|Function executed at graph startup|{0|}}
{30001002|XXparameter|num_callbacks|5|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|deselect_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,deselect,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
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
{2010203004|XXGoport|93|0|246|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|94|0|249|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|deselect|0.0|@@@2192|0|}}
{2010203004|XXGoport|95|0|252|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|96|0|255|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|97|0|258|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|98|0|261|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010503005|XXGfvertex|99|0|269|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C1002", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C1002|3|2|$|@{0|}}
{30001002|XXparameter|read_metadata||3|8|s=|@{0|}}
}}@0|Input File|24000|335500|0|0|0|0|404|Input File-10|Ab Initio Software|@1|3000|0||6||33025|-1|-1|}}
{2010203004|XXGoport|100|0|271|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|101|0|274|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
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
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|102|0|276|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|103|0|280|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C0401", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C0401|3|2|$|@{0|}}
{30001002|XXparameter|read_metadata||3|8|s=|@{0|}}
}}@0|Input File|24000|65500|0|0|0|0|415|Input File-12|Ab Initio Software|@1|1000|0||6||33025|-1|-1|}}
{2010203004|XXGoport|104|0|282|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|105|0|285|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
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
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|106|0|287|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|107|0|291|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C1001", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C1001|3|2|$|@{0|}}
{30001002|XXparameter|read_metadata||3|8|s=|@{0|}}
}}@0|Input File|24000|140500|0|0|0|0|419|Input File-3|Ab Initio Software|@1|11000|0||6||33025|-1|-1|}}
{2010203004|XXGoport|108|0|293|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|109|0|296|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
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
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|110|0|298|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|111|0|302|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C0402", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/CITSGRAL.WS654690.FZZPWDFI.SAYYYY.UMMDD.C0402|3|2|$|@{0|}}
{30001002|XXparameter|read_metadata||3|8|s=|@{0|}}
}}@0|Input File|24000|235500|0|0|0|0|417|Input File-7|Ab Initio Software|@1|1000|0||6||33025|-1|-1|}}
{2010203004|XXGoport|112|0|304|0|{@{}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010503005|XXGfvertex|113|0|307|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
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
{30001002|XXparameter|read_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|mpcmodtime|1603964908|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|Input File|0|0|0|0|0|0|0|@|@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|114|0|309|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2164|0|}}
{2010501005|XXGpvertex|115|0|316|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Redefine_Format.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@2|Redefine Format|770000|185000|0|0|0|0|446|Redefine Format-8|Ab Initio Software|Built-in 1.0:|1|100|0||6||36865|1|{1|0|}}}
{2010203004|XXGoport|116|0|318|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|117|0|321|0|{@{}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|118|0|324|0|{Copies data records from its input to its output without changing the values.  Use Redefine Format to change a record format or rename fields.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|copy|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=byte_copy(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1603964909|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|Redefine Format|0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|119|0|326|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|120|0|329|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|121|0|335|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Sort/Sort.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|key|\{sat_fec_transaccion\}|3|2|$|@{0|}}
}}@0|Sort|223000|305000|0|0|0|0|459|Sort|Ab Initio Software|Built-in 1.0:|1|100|0||6||1|1|{1|0|}}}
{2010203004|XXGoport|122|0|337|0|{@{}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|123|0|340|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|124|0|343|0|{Orders your data according to a key specifier.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|local-sort|3|1|Hl||{0|}}
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
{2010203004|XXGoport|125|0|345|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|126|0|348|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010110002|XXGconstant|127|0|354|0|{@{}@{1|5518936|}}}
{2010002001|XXGdirectory_object_object|0|1|2|0|{XXGgraph|}0|1|}
{2010704001|XXGgraph_graphinfo_graphinfo|1|0|2|0|{}1|2|}
{2010706001|XXGgraphinfo_runsettings_runsettings|2|0|4|0|{}2|3|}
{2010109001|XXGobject_property_value|3|0|6|0|{0|legend_face|92|}2|4|}
{2010604001|XXGgraph_flow_flow|4|0|8|0|{Flow_1|}1|5|}
{2010604001|XXGgraph_flow_flow|5|0|10|0|{Flow_10|}1|6|}
{2010604001|XXGgraph_flow_flow|6|0|12|0|{Flow_2|}1|7|}
{2010604001|XXGgraph_flow_flow|7|0|14|0|{Flow_20|}1|8|}
{2010604001|XXGgraph_flow_flow|8|0|16|0|{Flow_22|}1|9|}
{2010604001|XXGgraph_flow_flow|9|0|18|0|{Flow_23|}1|10|}
{2010604001|XXGgraph_flow_flow|10|0|20|0|{Flow_24|}1|11|}
{2010604001|XXGgraph_flow_flow|11|0|22|0|{Flow_3|}1|12|}
{2010604001|XXGgraph_flow_flow|12|0|24|0|{Flow_4|}1|13|}
{2010604001|XXGgraph_flow_flow|13|0|26|0|{Flow_5|}1|14|}
{2010604001|XXGgraph_flow_flow|14|0|28|0|{Flow_6|}1|15|}
{2010604001|XXGgraph_flow_flow|15|0|30|0|{Flow_7|}1|16|}
{2010604001|XXGgraph_flow_flow|16|0|32|0|{Flow_8|}1|17|}
{2010604001|XXGgraph_flow_flow|17|0|34|0|{Flow_9|}1|18|}
{2010601001|XXGgraph_vertex_vertex|18|0|36|0|{Concatenate|}1|19|}
{2010212001|XXGvertex_oport_oport|19|0|38|0|{0|out|}19|20|}
{2010213001|XXGoport_dst_flow|20|0|40|0|{0|}20|15|}
{2010211001|XXGvertex_iport_iport|21|0|41|0|{0|in|}19|21|}
{2010214001|XXGiport_src_flow|22|0|43|0|{0|}21|16|}
{2010214001|XXGiport_src_flow|23|0|44|0|{1|}21|17|}
{2010007001|XXGobject_proto_object|24|0|45|0|{}19|22|}
{2010212001|XXGvertex_oport_oport|25|0|47|0|{0|out|}22|23|}
{2010006001|XXGobject_psameas_object|26|0|49|0|{metadata|out_metadata|1|0|}23|22|}
{2010211001|XXGvertex_iport_iport|27|0|50|0|{0|in|}22|24|}
{2010006001|XXGobject_psameas_object|28|0|52|0|{metadata|in_metadata|1|0|}24|22|}
{2010006001|XXGobject_psameas_object|29|0|53|0|{Layout|Layout|0|0|}19|25|}
{2010211001|XXGvertex_iport_iport|30|0|55|0|{0|write|}25|26|}
{2010214001|XXGiport_src_flow|31|0|57|0|{0|}26|18|}
{2010007001|XXGobject_proto_object|32|0|58|0|{}25|27|}
{2010211001|XXGvertex_iport_iport|33|0|60|0|{0|write|}27|28|}
{2010006001|XXGobject_psameas_object|34|0|62|0|{metadata|write_metadata|1|0|}28|27|}
{2010006001|XXGobject_psameas_object|35|0|63|0|{write_metadata|out_metadata|0|0|}25|29|}
{2010212001|XXGvertex_oport_oport|36|0|65|0|{0|out|}29|30|}
{2010213001|XXGoport_dst_flow|37|0|67|0|{0|}30|16|}
{2010212001|XXGvertex_oport_oport|38|0|68|0|{1|reject|}29|31|}
{2010212001|XXGvertex_oport_oport|39|0|70|0|{2|error|}29|32|}
{2010212001|XXGvertex_oport_oport|40|0|72|0|{3|log|}29|33|}
{2010211001|XXGvertex_iport_iport|41|0|74|0|{0|in|}29|34|}
{2010214001|XXGiport_src_flow|42|0|76|0|{0|}34|14|}
{2010007001|XXGobject_proto_object|43|0|77|0|{}29|35|}
{2010212001|XXGvertex_oport_oport|44|0|79|0|{0|out|}35|36|}
{2010006001|XXGobject_psameas_object|45|0|81|0|{metadata|out_metadata|1|0|}36|35|}
{2010212001|XXGvertex_oport_oport|46|0|82|0|{1|reject|}35|37|}
{2010006001|XXGobject_psameas_object|47|0|84|0|{metadata|reject_metadata|1|0|}37|35|}
{2010212001|XXGvertex_oport_oport|48|0|85|0|{2|error|}35|38|}
{2010006001|XXGobject_psameas_object|49|0|87|0|{metadata|error_metadata|1|0|}38|35|}
{2010212001|XXGvertex_oport_oport|50|0|88|0|{3|log|}35|39|}
{2010006001|XXGobject_psameas_object|51|0|90|0|{metadata|log_metadata|1|0|}39|35|}
{2010211001|XXGvertex_iport_iport|52|0|91|0|{0|in|}35|40|}
{2010006001|XXGobject_psameas_object|53|0|93|0|{metadata|in_metadata|1|0|}40|35|}
{2010006001|XXGobject_psameas_object|54|0|94|0|{Layout|Layout|0|0|}29|25|}
{2010006001|XXGobject_psameas_object|55|0|95|0|{reject_metadata|in_metadata|0|0|}29|29|}
{2010006001|XXGobject_psameas_object|56|0|96|0|{in_metadata|out_metadata|0|0|}19|29|}
{2010006001|XXGobject_psameas_object|57|0|97|0|{out_metadata|out_metadata|0|0|}19|29|}
{2010601001|XXGgraph_vertex_vertex|58|0|98|0|{Concatenate_14|}1|41|}
{2010212001|XXGvertex_oport_oport|59|0|100|0|{0|out|}41|42|}
{2010213001|XXGoport_dst_flow|60|0|102|0|{0|}42|12|}
{2010211001|XXGvertex_iport_iport|61|0|103|0|{0|in|}41|43|}
{2010214001|XXGiport_src_flow|62|0|105|0|{0|}43|11|}
{2010214001|XXGiport_src_flow|63|0|106|0|{1|}43|10|}
{2010214001|XXGiport_src_flow|64|0|107|0|{2|}43|8|}
{2010214001|XXGiport_src_flow|65|0|108|0|{3|}43|9|}
{2010007001|XXGobject_proto_object|66|0|109|0|{}41|44|}
{2010212001|XXGvertex_oport_oport|67|0|111|0|{0|out|}44|45|}
{2010006001|XXGobject_psameas_object|68|0|113|0|{metadata|out_metadata|1|0|}45|44|}
{2010211001|XXGvertex_iport_iport|69|0|114|0|{0|in|}44|46|}
{2010006001|XXGobject_psameas_object|70|0|116|0|{metadata|in_metadata|1|0|}46|44|}
{2010006001|XXGobject_psameas_object|71|0|117|0|{Layout|Layout|0|0|}41|47|}
{2010211001|XXGvertex_iport_iport|72|0|119|0|{0|write|}47|48|}
{2010214001|XXGiport_src_flow|73|0|121|0|{0|}48|7|}
{2010007001|XXGobject_proto_object|74|0|122|0|{}47|49|}
{2010211001|XXGvertex_iport_iport|75|0|124|0|{0|write|}49|50|}
{2010006001|XXGobject_psameas_object|76|0|126|0|{metadata|write_metadata|1|0|}50|49|}
{2010006001|XXGobject_psameas_object|77|0|127|0|{in_metadata|in_metadata|0|0|}41|51|}
{2010212001|XXGvertex_oport_oport|78|0|129|0|{0|out0|}51|52|}
{2010213001|XXGoport_dst_flow|79|0|131|0|{0|}52|5|}
{2010212001|XXGvertex_oport_oport|80|0|132|0|{1|reject0|}51|53|}
{2010212001|XXGvertex_oport_oport|81|0|134|0|{2|error0|}51|54|}
{2010212001|XXGvertex_oport_oport|82|0|136|0|{3|log|}51|55|}
{2010211001|XXGvertex_iport_iport|83|0|138|0|{0|in|}51|56|}
{2010214001|XXGiport_src_flow|84|0|140|0|{0|}56|13|}
{2010007001|XXGobject_proto_object|85|0|141|0|{}51|57|}
{2010212001|XXGvertex_oport_oport|86|0|143|0|{0|out0|}57|58|}
{2010006001|XXGobject_psameas_object|87|0|145|0|{metadata|out0_metadata|1|0|}58|57|}
{2010006001|XXGobject_psameas_object|88|0|146|0|{transform0|transform0|1|0|}58|57|}
{2010212001|XXGvertex_oport_oport|89|0|147|0|{1|reject0|}57|59|}
{2010006001|XXGobject_psameas_object|90|0|149|0|{metadata|reject0_metadata|1|0|}59|57|}
{2010212001|XXGvertex_oport_oport|91|0|150|0|{2|error0|}57|60|}
{2010006001|XXGobject_psameas_object|92|0|152|0|{metadata|error0_metadata|1|0|}60|57|}
{2010212001|XXGvertex_oport_oport|93|0|153|0|{3|log|}57|61|}
{2010006001|XXGobject_psameas_object|94|0|155|0|{metadata|log_metadata|1|0|}61|57|}
{2010211001|XXGvertex_iport_iport|95|0|156|0|{0|in|}57|62|}
{2010006001|XXGobject_psameas_object|96|0|158|0|{metadata|in_metadata|1|0|}62|57|}
{2010006001|XXGobject_psameas_object|97|0|159|0|{Layout|Layout|0|0|}51|47|}
{2010006001|XXGobject_psameas_object|98|0|160|0|{reject0_metadata|in_metadata|0|0|}51|51|}
{2010006001|XXGobject_psameas_object|99|0|161|0|{out_metadata|in_metadata|0|0|}41|51|}
{2010601001|XXGgraph_vertex_vertex|100|0|162|0|{Create_Data|}1|63|}
{2010212001|XXGvertex_oport_oport|101|0|164|0|{0|out|}63|64|}
{2010213001|XXGoport_dst_flow|102|0|166|0|{0|}64|17|}
{2010212001|XXGvertex_oport_oport|103|0|167|0|{1|error|}63|65|}
{2010212001|XXGvertex_oport_oport|104|0|169|0|{2|log|}63|66|}
{2010007001|XXGobject_proto_object|105|0|171|0|{}63|67|}
{2010212001|XXGvertex_oport_oport|106|0|173|0|{0|out|}67|68|}
{2010006001|XXGobject_psameas_object|107|0|175|0|{metadata|out_metadata|1|0|}68|67|}
{2010212001|XXGvertex_oport_oport|108|0|176|0|{1|error|}67|69|}
{2010006001|XXGobject_psameas_object|109|0|178|0|{metadata|error_metadata|1|0|}69|67|}
{2010212001|XXGvertex_oport_oport|110|0|179|0|{2|log|}67|70|}
{2010006001|XXGobject_psameas_object|111|0|181|0|{metadata|log_metadata|1|0|}70|67|}
{2010006001|XXGobject_psameas_object|112|0|182|0|{Layout|Layout|0|0|}63|25|}
{2010006001|XXGobject_psameas_object|113|0|183|0|{out_metadata|out_metadata|0|0|}63|29|}
{2010601001|XXGgraph_vertex_vertex|114|0|184|0|{Dedup_Sorted|}1|71|}
{2010212001|XXGvertex_oport_oport|115|0|186|0|{0|out|}71|72|}
{2010213001|XXGoport_dst_flow|116|0|188|0|{0|}72|18|}
{2010212001|XXGvertex_oport_oport|117|0|189|0|{1|dup|}71|73|}
{2010212001|XXGvertex_oport_oport|118|0|191|0|{2|reject|}71|74|}
{2010212001|XXGvertex_oport_oport|119|0|193|0|{3|error|}71|75|}
{2010212001|XXGvertex_oport_oport|120|0|195|0|{4|log|}71|76|}
{2010211001|XXGvertex_iport_iport|121|0|197|0|{0|in|}71|77|}
{2010214001|XXGiport_src_flow|122|0|199|0|{0|}77|15|}
{2010007001|XXGobject_proto_object|123|0|200|0|{}71|78|}
{2010212001|XXGvertex_oport_oport|124|0|202|0|{0|out|}78|79|}
{2010006001|XXGobject_psameas_object|125|0|204|0|{metadata|out_metadata|1|0|}79|78|}
{2010212001|XXGvertex_oport_oport|126|0|205|0|{1|dup|}78|80|}
{2010006001|XXGobject_psameas_object|127|0|207|0|{metadata|dup_metadata|1|0|}80|78|}
{2010212001|XXGvertex_oport_oport|128|0|208|0|{2|reject|}78|81|}
{2010006001|XXGobject_psameas_object|129|0|210|0|{metadata|reject_metadata|1|0|}81|78|}
{2010212001|XXGvertex_oport_oport|130|0|211|0|{3|error|}78|82|}
{2010006001|XXGobject_psameas_object|131|0|213|0|{metadata|error_metadata|1|0|}82|78|}
{2010212001|XXGvertex_oport_oport|132|0|214|0|{4|log|}78|83|}
{2010006001|XXGobject_psameas_object|133|0|216|0|{metadata|log_metadata|1|0|}83|78|}
{2010211001|XXGvertex_iport_iport|134|0|217|0|{0|in|}78|84|}
{2010006001|XXGobject_psameas_object|135|0|219|0|{metadata|in_metadata|1|0|}84|78|}
{2010006001|XXGobject_psameas_object|136|0|220|0|{Layout|Layout|0|0|}71|25|}
{2010006001|XXGobject_psameas_object|137|0|221|0|{dup_metadata|out_metadata|0|0|}71|29|}
{2010006001|XXGobject_psameas_object|138|0|222|0|{in_metadata|out_metadata|0|0|}71|29|}
{2010006001|XXGobject_psameas_object|139|0|223|0|{out_metadata|out_metadata|0|0|}71|29|}
{2010006001|XXGobject_psameas_object|140|0|224|0|{reject_metadata|out_metadata|0|0|}71|29|}
{2010601001|XXGgraph_vertex_vertex|141|0|225|0|{Filter_Count|}1|29|}
{2010601001|XXGgraph_vertex_vertex|142|0|226|0|{Filter_S500|}1|85|}
{2010212001|XXGvertex_oport_oport|143|0|228|0|{0|out|}85|86|}
{2010213001|XXGoport_dst_flow|144|0|230|0|{0|}86|13|}
{2010212001|XXGvertex_oport_oport|145|0|231|0|{1|deselect|}85|87|}
{2010213001|XXGoport_dst_flow|146|0|233|0|{0|}87|6|}
{2010212001|XXGvertex_oport_oport|147|0|234|0|{2|reject|}85|88|}
{2010212001|XXGvertex_oport_oport|148|0|236|0|{3|error|}85|89|}
{2010212001|XXGvertex_oport_oport|149|0|238|0|{4|log|}85|90|}
{2010211001|XXGvertex_iport_iport|150|0|240|0|{0|in|}85|91|}
{2010214001|XXGiport_src_flow|151|0|242|0|{0|}91|12|}
{2010007001|XXGobject_proto_object|152|0|243|0|{}85|92|}
{2010212001|XXGvertex_oport_oport|153|0|245|0|{0|out|}92|93|}
{2010006001|XXGobject_psameas_object|154|0|247|0|{metadata|out_metadata|1|0|}93|92|}
{2010212001|XXGvertex_oport_oport|155|0|248|0|{1|deselect|}92|94|}
{2010006001|XXGobject_psameas_object|156|0|250|0|{metadata|deselect_metadata|1|0|}94|92|}
{2010212001|XXGvertex_oport_oport|157|0|251|0|{2|reject|}92|95|}
{2010006001|XXGobject_psameas_object|158|0|253|0|{metadata|reject_metadata|1|0|}95|92|}
{2010212001|XXGvertex_oport_oport|159|0|254|0|{3|error|}92|96|}
{2010006001|XXGobject_psameas_object|160|0|256|0|{metadata|error_metadata|1|0|}96|92|}
{2010212001|XXGvertex_oport_oport|161|0|257|0|{4|log|}92|97|}
{2010006001|XXGobject_psameas_object|162|0|259|0|{metadata|log_metadata|1|0|}97|92|}
{2010211001|XXGvertex_iport_iport|163|0|260|0|{0|in|}92|98|}
{2010006001|XXGobject_psameas_object|164|0|262|0|{metadata|in_metadata|1|0|}98|92|}
{2010006001|XXGobject_psameas_object|165|0|263|0|{Layout|Layout|0|0|}85|47|}
{2010006001|XXGobject_psameas_object|166|0|264|0|{deselect_metadata|in_metadata|0|0|}85|51|}
{2010006001|XXGobject_psameas_object|167|0|265|0|{in_metadata|in_metadata|0|0|}85|51|}
{2010006001|XXGobject_psameas_object|168|0|266|0|{out_metadata|in_metadata|0|0|}85|51|}
{2010006001|XXGobject_psameas_object|169|0|267|0|{reject_metadata|in_metadata|0|0|}85|51|}
{2010601001|XXGgraph_vertex_vertex|170|0|268|0|{Input_File_10|}1|99|}
{2010212001|XXGvertex_oport_oport|171|0|270|0|{0|read|}99|100|}
{2010213001|XXGoport_dst_flow|172|0|272|0|{0|}100|9|}
{2010007001|XXGobject_proto_object|173|0|273|0|{}99|101|}
{2010212001|XXGvertex_oport_oport|174|0|275|0|{0|read|}101|102|}
{2010006001|XXGobject_psameas_object|175|0|277|0|{metadata|read_metadata|1|0|}102|101|}
{2010006001|XXGobject_psameas_object|176|0|278|0|{read_metadata|in_metadata|0|0|}99|51|}
{2010601001|XXGgraph_vertex_vertex|177|0|279|0|{Input_File_12|}1|103|}
{2010212001|XXGvertex_oport_oport|178|0|281|0|{0|read|}103|104|}
{2010213001|XXGoport_dst_flow|179|0|283|0|{0|}104|11|}
{2010007001|XXGobject_proto_object|180|0|284|0|{}103|105|}
{2010212001|XXGvertex_oport_oport|181|0|286|0|{0|read|}105|106|}
{2010006001|XXGobject_psameas_object|182|0|288|0|{metadata|read_metadata|1|0|}106|105|}
{2010006001|XXGobject_psameas_object|183|0|289|0|{read_metadata|in_metadata|0|0|}103|51|}
{2010601001|XXGgraph_vertex_vertex|184|0|290|0|{Input_File_3|}1|107|}
{2010212001|XXGvertex_oport_oport|185|0|292|0|{0|read|}107|108|}
{2010213001|XXGoport_dst_flow|186|0|294|0|{0|}108|10|}
{2010007001|XXGobject_proto_object|187|0|295|0|{}107|109|}
{2010212001|XXGvertex_oport_oport|188|0|297|0|{0|read|}109|110|}
{2010006001|XXGobject_psameas_object|189|0|299|0|{metadata|read_metadata|1|0|}110|109|}
{2010006001|XXGobject_psameas_object|190|0|300|0|{read_metadata|in_metadata|0|0|}107|51|}
{2010601001|XXGgraph_vertex_vertex|191|0|301|0|{Input_File_7|}1|111|}
{2010212001|XXGvertex_oport_oport|192|0|303|0|{0|read|}111|112|}
{2010213001|XXGoport_dst_flow|193|0|305|0|{0|}112|8|}
{2010007001|XXGobject_proto_object|194|0|306|0|{}111|113|}
{2010212001|XXGvertex_oport_oport|195|0|308|0|{0|read|}113|114|}
{2010006001|XXGobject_psameas_object|196|0|310|0|{metadata|read_metadata|1|0|}114|113|}
{2010006001|XXGobject_psameas_object|197|0|311|0|{read_metadata|in_metadata|0|0|}111|51|}
{2010601001|XXGgraph_vertex_vertex|198|0|312|0|{Mapping_Trans_7|}1|51|}
{2010601001|XXGgraph_vertex_vertex|199|0|313|0|{Output_File|}1|25|}
{2010601001|XXGgraph_vertex_vertex|200|0|314|0|{Output_File_3|}1|47|}
{2010601001|XXGgraph_vertex_vertex|201|0|315|0|{Redefine_Format_8|}1|115|}
{2010212001|XXGvertex_oport_oport|202|0|317|0|{0|out|}115|116|}
{2010213001|XXGoport_dst_flow|203|0|319|0|{0|}116|7|}
{2010211001|XXGvertex_iport_iport|204|0|320|0|{0|in|}115|117|}
{2010214001|XXGiport_src_flow|205|0|322|0|{0|}117|5|}
{2010007001|XXGobject_proto_object|206|0|323|0|{}115|118|}
{2010212001|XXGvertex_oport_oport|207|0|325|0|{0|out|}118|119|}
{2010006001|XXGobject_psameas_object|208|0|327|0|{metadata|out_metadata|1|0|}119|118|}
{2010211001|XXGvertex_iport_iport|209|0|328|0|{0|in|}118|120|}
{2010006001|XXGobject_psameas_object|210|0|330|0|{metadata|in_metadata|1|0|}120|118|}
{2010006001|XXGobject_psameas_object|211|0|331|0|{Layout|Layout|0|0|}115|47|}
{2010006001|XXGobject_psameas_object|212|0|332|0|{in_metadata|out0_metadata|0|0|}115|51|}
{2010006001|XXGobject_psameas_object|213|0|333|0|{out_metadata|write_metadata|0|0|}115|47|}
{2010601001|XXGgraph_vertex_vertex|214|0|334|0|{Sort|}1|121|}
{2010212001|XXGvertex_oport_oport|215|0|336|0|{0|out|}121|122|}
{2010213001|XXGoport_dst_flow|216|0|338|0|{0|}122|14|}
{2010211001|XXGvertex_iport_iport|217|0|339|0|{0|in|}121|123|}
{2010214001|XXGiport_src_flow|218|0|341|0|{0|}123|6|}
{2010007001|XXGobject_proto_object|219|0|342|0|{}121|124|}
{2010212001|XXGvertex_oport_oport|220|0|344|0|{0|out|}124|125|}
{2010006001|XXGobject_psameas_object|221|0|346|0|{metadata|out_metadata|1|0|}125|124|}
{2010211001|XXGvertex_iport_iport|222|0|347|0|{0|in|}124|126|}
{2010006001|XXGobject_psameas_object|223|0|349|0|{metadata|in_metadata|1|0|}126|124|}
{2010006001|XXGobject_psameas_object|224|0|350|0|{Layout|Layout|0|0|}121|25|}
{2010006001|XXGobject_psameas_object|225|0|351|0|{in_metadata|in_metadata|0|0|}121|51|}
{2010006001|XXGobject_psameas_object|226|0|352|0|{out_metadata|in_metadata|0|0|}121|51|}
{2010109001|XXGobject_property_value|227|0|353|0|{0|TrackingThumbprint|72|}1|127|}
