@
{18|Type|XXGrepository|Primary_Name|XXGgraph|_ab_object_schema|0|_ab_semantic_schema|9|eme_flatten_format|1|schema_version|34|root_id|0|ent_count|176|rel_count|291|}
{2010001002|XXGdirectory|0|1|1|0|{@{}@}}
{2010600005|XXGgraph|1|0|1|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|_ab_semantic_schema|9|1|1|Hnl|@{0|}}
{30001002|XXparameter|_ab_has_render_fixups|2|1|1|Hl||{0|}}
{30001002|XXparameter|_UseNewErrorLogDML|True|13|1|Hl||{0|}}
{30001002|XXparameter|!ab_compatibility|4.0.2.2|3|9|P|@{0|}}
}}@0|@0|0|0|0|0|0|0|file_test|mg16734|@1|100|-1|@9|@34817|{0|}0|0|{0|}{0|}{0|}{0|}1.0|1299000|541000|7|}}
{2010703001|XXGgraphinfo|2|0|3|0|{@{}@1|4.0.2.4|{2|1|1|}Job 'Graph2' Execution Status Report


Job "Graph2" Execution started at Thursday, January 13, 2022 10:40:13
***** Job execution failed at Thursday, January 13, 2022 10:40:15 *****
(Application Output may contain additional information describing the failure)

------------------------------
Job Statistics:

Job status at termination: Failed
Run time (wall clock): 0:00:02
Run performed by user mg16734
||||@@33207807|}}
{2010705002|XXGrunsettings|3|0|5|0|{@{}@EDW_DEV||||1|60|0|1|1|0|0|0|0|1|1|0|0|1|2|1|1|0|0|0|@16|}}
{2010242002|XXGface|4|0|7|0|{@{}@Arial|0|100|0|}}
{2010210004|XXGflow|5|0|9|0|{@{}@0|.5|.5|{0|}103|17|}}
{2010210004|XXGflow|6|0|11|0|{@{}@384|.5|.5|{12|136000|269000|156000|269000|163000|269000|163000|279000|171000|279000|192000|279000|}107|17|}}
{2010210004|XXGflow|7|0|13|0|{@{}@0|.5|.5|{0|}105|17|}}
{2010210004|XXGflow|8|0|15|0|{@{}@0|.5|.5|{0|}104|17|}}
{2010210004|XXGflow|9|0|17|0|{@{}@384|.5|.5|{8|1113000|239000|1113000|239000|1130000|239000|1137000|239000|}82|531|}}
{2010501005|XXGpvertex|10|0|19|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Gather.mpc|3|2|Pf$|@{0|}}
}}@1|@1188000|257500|1148000|217000|50000|41000|6|Gather|Ab Initio Software|Built-in|1|100|0||6||32833|1|{1|0|}}}
{2010203004|XXGoport|11|0|21|0|{@{}@1197000|234000|11000|11000|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|12|0|23|0|{@{}@1138000|234000|11000|11000|in|0.0|@@@1810|0|}}
{2010501005|XXGpvertex|13|0|26|0|{Combines data records from multiple flow partitions arbitrarily.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|gather|3|1|Hl||{0|}}
{30001002|XXparameter|image__|~ab_home/bin/unitool|3|2|H$||{0|}}
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
{30001002|XXparameter|mpcmodtime|1383376018|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|14|0|28|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|15|0|31|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1810|0|}}
{2010503005|XXGfvertex|16|0|34|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|condition|$[GENERATE_HEADER]|3|9||@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/$\{INPUT_MAIN_FILE_FULL_NAME\}_header_for_check.dat|3|2|$|@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/$\{INPUT_MAIN_FILE_FULL_NAME\}_header_for_check.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|write_metadata|record
      decimal(1) tipo_registro;
      string(4) sitema;
      string(8) fecha_book;
      string(6) hrgenarc;
      string(8) fhininfo;
      string(8) fecha_2;
      string(2) nucsvoar;
      string(3) cvecsi;
      string(4) cvsisfue;
      //pg83302 - se agrega filler
      string(726) filler;
      string(1) new_line_hdr;
end;|3|1|l|@{0|}}
}}@0|@516667|146333|999000|96000|56000|50000|98|Header|A||1|100|-1||6||33025|-1|-1|}}
{2010202004|XXGiport|17|0|36|0|{@{}@989000|114000|11000|11000|write|0.0|@@@1776|0|}}
{2010503005|XXGfvertex|18|0|39|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url|@28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|param block_compressed True mode lookup version 2.15.5.r34:|3|15|P?|@{0|}}
{30001002|XXparameter|Layout|@28|2|RF$||{0|}}
{30001002|XXparameter|write_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|mpcmodtime|1276748815|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|19|0|41|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1776|0|}}
{2010503005|XXGfvertex|20|0|44|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("read", "pdl") map_dataset 1 mapping [record dataset_path _interp_("$AI_SERIAL/CITSGRAL_WS054692_TI2021_T1020_TXNMON01.txt", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|read_metadata|type da_file_with_trl_t = record
                             string("\|")  tip_reg;
                             string("\\n") filler;
                          end;
                          
type da_file_with_trl_t_2 = record
                             string(",")  tip_reg;
                             string("\\n") filler;
                          end;
                          
type da_file_with_trl_t_3 = record
                             decimal(2)   tip_reg;
                             string("\\n") filler;
                          end;   

type da_file_with_trl_t_4 = record
                             decimal(1)   tipo_registro;
                             string("\\n") filler;
                          end;
                          
metadata type = da_file_with_trl_t_4;|3|3|c|@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|Layout|file:$AI_SERIAL/CITSGRAL_WS054692_TI2021_T1020_TXNMON01.txt|3|2|$|@{0|}}
}}@0|@97839|275086|70000|245000|56000|50000|108|Input File|Ab Initio Software||1|200|0||6||33025|-1|-1|}}
{2010203004|XXGoport|21|0|46|0|{@{}@125000|264000|11000|11000|read|0.0|@@@2160|0|}}
{2010503005|XXGfvertex|22|0|49|0|{Represents one file, many files, or a multifile as an input to your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0001|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url|@28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if the block compressed lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|param block_compressed True mode lookup version 2.15.5.r34:|3|15|P?|@{0|}}
{30001002|XXparameter|Layout|$[[record kind 85 subkind 0 parts [vector]]]|28|9|RF||{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
{30001002|XXparameter|read_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|mpcmodtime|1349474929|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|-1|-1|}}
{2010203004|XXGoport|23|0|51|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|read|0.0|@@@2160|0|}}
{2010501005|XXGpvertex|24|0|54|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Redefine_Format.mpc|3|2|Pf$|@{0|}}
}}@1|@1093000|260000|1053000|219000|50000|41000|83|Redefine Format|Ab Initio Software|Built-in|1|100|-1||6||32833|1|{1|0|}}}
{2010203004|XXGoport|25|0|56|0|{@{}@1102000|234000|11000|11000|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|26|0|59|0|{@{}@1043000|234000|11000|11000|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|27|0|61|0|{Copies data records from its input to its output without changing the values.  Use Redefine Format to change a record format or rename fields.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|copy|3|1|Hl||{0|}}
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
{30001002|XXparameter|mpcmodtime|1383376013|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|28|0|63|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|29|0|66|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010600005|XXGgraph|30|0|69|0|{Subgraph created from graph "rc_data_acq"|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|condition||3|2|F$||{0|}}
}}@0|@209666|220262|203000|227000|744000|352000|106|Sb: Input File and trailer validation|A|Created 1/12/2010 2:33:35 PM|1|10|0||6||32769|{0|}0|0|{0|}{0|}{0|}{0|}.301075279712677|744000|352000|3|}}
{2010600005|XXGgraph|31|0|71|0|{Subgraph created from graph "source_to_stage_data_acq"|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|conditionInputPort|in0|3|1|Fl||{0|}}
{30001002|XXparameter|conditionOutputPort|out0|3|1|Fl||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
}}@0|@83874|123796|103000|142000|990000|494000|26674|Sb Header, Detail & Trailer Validation|A||1|10|0||6||32769|{0|}0|0|{0|}{0|}{0|}{0|}.21616162359714508|990000|493000|7|}}
{2010210004|XXGflow|32|0|73|0|{@{}@384|.5|.5|{12|140000|354000|160000|354000|160000|376000|106000|376000|106000|399000|137000|399000|}760|17|}}
{2010210004|XXGflow|33|0|75|0|{@{}@384|.5|.31182795763015747|{12|298000|244000|318000|244000|453000|244000|453000|109000|754000|109000|775000|109000|}837|17|}}
{2010210004|XXGflow|34|0|77|0|{@{}@384|.5|.30454546213150024|{12|298000|264000|318000|264000|452000|264000|452000|409000|758000|409000|779000|409000|}838|17|}}
{2010210004|XXGflow|35|0|79|0|{@{}@384|.5|.5|{8|298000|254000|328000|254000|752000|254000|773000|254000|}841|17|}}
{2010243001|XXGwatcher|36|0|81|0|{@{}@1|100|0||0|}}
{2010210004|XXGflow|37|0|83|0|{@{}@384|.5|.5|{0|}840|18|}}
{2010243001|XXGwatcher|38|0|85|0|{@{}@1|100|-1||0|}}
{2010210004|XXGflow|39|0|87|0|{@{}@384|.5|.5|{12|109000|434000|109000|434000|119000|434000|119000|429000|130000|429000|137000|429000|}759|529|}}
{2010501005|XXGpvertex|40|0|89|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|function|if(tipo_registro == 1 ) 0
else if(tipo_registro == 9) 2
     else 1;|3|9||@{0|}}
{30001002|XXparameter|package||3|2|f$|@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Partition_by_Expression.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|!validation_exclusions|1\|\@\{52\|1\|\{53\|error_suppression\|2\|\{56\|\|\}\{53\|status_info\|4\|\{56\|DAV_pbe_fanout\|\}\{56\|CTL10113\|\}\{51\|0\|\}\{\}\}\}\}|3|9|P|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|@136083|191422|156000|201000|132000|107000|839|Partition by Expression|Ab Initio Software|Built-in|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|41|0|91|0|{@{}@287000|239000|11000|31000|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|42|0|96|0|{@{}@179000|307000|11000|11000|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|43|0|98|0|{@{}@219000|307000|11000|11000|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|44|0|100|0|{@{}@259000|307000|11000|11000|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|45|0|102|0|{@{}@146000|249000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|46|0|104|0|{Distributes data records to its output flow partitions according to the specified DML expression.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|function-partition|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
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
{30001002|XXparameter|operation1|optional integer(8) index_out::partition_index(in)|3|2|H$|Use this instead of the function parameter when use_package is true.|{0|}}
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
{30001002|XXparameter|type1|error_info_t error_info "record utf8 string(big endian integer(4)) component; big endian integer(4) port_index; utf8 string(big endian integer(4)) parameter; utf8 string(big endian integer(4)) message; record utf8 string(big endian integer(4)) code; big endian integer(4) parent_index; record utf8 string(big endian integer(4)) name; utf8 string(big endian integer(4)) value; end [big endian integer(4)] attributes; end [big endian integer(4)] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('') event_type; string('') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation2|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation3|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|3|1|2|H$|Number of callbacks in package|{0|}}
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
{30001002|XXparameter|mpcmodtime|1276748904|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|47|0|106|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2323|0|}}
{2010203004|XXGoport|48|0|109|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|49|0|112|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|50|0|115|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|51|0|118|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|52|0|125|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Redefine_Format.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|doc_transform|out :: document(in) =
begin
  out :: in;
end;|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
    decimal(1)   tipo_registro;
    string(19)   cuenta;
    string(6)    autorizacion;
    decimal(9)   distintivo_timestamp;
    decimal(10)  negocio;
    string(10)   fecha;
    decimal(6)   hora;
    string(8)    term;
    decimal(4)   sucursal;
    decimal(4)   cajero;
    string(8)    operador;
    string(4)    ret_cat;
    string(2)    resp_cde;
    decimal(4)   resp_time;
    string(3)    curr_cde;
    string(14)   importe;
    string(7)    tipo_de_cambio;
    string(14)   importe_mn;
    string(14)   cred_disp;
    string(4)    adquirente;
    string(4)    emisor;
    decimal(1)   responder;
    string(4)    tran_typ;
    string(3)    cod_pais;
    string(9)    cod_post;
    string(3)    access_mode;
    string(2)    access_med;
    string(1)    est_cuenta;
    string(1)    est_plastico;
    string(1)    est_negocio;
    decimal(4)   fopera;
    string(6)    proc_code;
    decimal(4)   ica;
    decimal(1)   adq_neg;
    string(1)    modo_falcon;
    string(6)    marc_resp;
    string(6)    fvalida;
    decimal(4)   resp_int;
    decimal(9)   lin_cred;
    decimal(4)   score_flcn;
    decimal(9)   ulfd_num_modulo;
    decimal(4)   ulfd_num_consec;
    string(14)   ulfd_importe_entregado;
    string(1)    ulfd_status_conciliaci;
    string(1)    ulfd_ind_comer_elect;
    string(14)   ulfd_importe_cash_back;
    string(2)    ulfd_tipo_plan;
    string(2)    ulfd_diferimiento;
    string(2)    ulfd_num_plazo;
    string(25)   ulfd_nom_negocio;
    string(25)   ulfd_tracki;
    string(13)   ulfd_location_city;
    string(3)    ulfd_location_state;
    decimal(3)   ulfd_score_mastercard;
    decimal(2)   ulfd_score_visa;
    string(1)    id_tipo_tabla;
    //gj08685- se agrega campos emv
    string(3)   service_code;
    string(1)   trans_categ_code;
    decimal(1)  term_input_capind;
    string(1)   crdhldr_id_method;
    string(2)   crypto_inf_data;
    string(10)  tvr;
    string(16)  arqc;
    string(12)  amt_auth;
    string(12)  amt_other;
    string(4)   aip;
    string(4)   atc;
    string(3) term_cntry_code;
    string(3) tran_crncy_code;
    string(6) tran_date;
    string(2) crypto_info_data;
    string(8) unpredict_num;
    string(64) iss_appl_data;
    string(8) term_serl_num;
    string(8) emv_term_cap;
    string(2) emv_term_type;
    string(4) appl_ver_num;
    string(6) cvm_rslts;
    string(32) df_name;
    decimal(2) inp_entry_mode;
    decimal(1) inp_entry_pin;
    string(1) term_entry_cap;
    string(1) last_emv_stat;
    string(1) data_suspect;
    string(2) appl_pan_seq_num;
    string(6) dev_info;
    string(4) rsn_onl_cde;
    string(1) arqc_vrfy;
    string(1) iso_rc_ind;
    string(4) iss_auth_data_lgth;     
    string(32) emv_iss_auth_data;
    string(1) send_crd_blk;
    string(1) send_put_data;
    //md11572 - se agregan campos
    string(1) tipo_de_pan;
    decimal(16) numero_de_cuenta;
    decimal(4) vigencia;
    decimal(11) id_asociado;
    decimal (2) onbehalf_serv;
    string (1) onbehalf_res;
    decimal(2) nivel_de_assurance;
    string(2) tipo_de_almacenamiento;
    decimal (2) srv_preval;
    string (1) tipo_validacion;
    //ab38354-fd97628 - se agregan campos proyecto CVV2
    decimal(1) pre_cvv2;
    decimal(1) res_cvv2;
    decimal(2) pre_dfa;
    decimal(1) res_dfa;
    decimal(2) id_autentica;
    string (3) UL_B0_DSRP_INDICADOR;
    string(3) UL_B0_ID_WALLET_WID;
    //pp95943 - se agregan campos proyecto Arcot 3D secure
    string(1) numero_version;
    string(1) tipo_autenticacion;
    string(36) directorio;
    string(1) criptograma_presente;
    string(1) criptograma_resultado;
    string(15) ip_address;
    string(17) mac_address;   
   // string(99)  filler;
    string(27)  filler;
    string(1)    new_line;
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|@771019|229627|784000|234000|44000|41000|827|Redefine Format Detail|Ab Initio Software|Built-in|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|53|0|127|0|{@{}@827000|249000|11000|11000|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|54|0|129|0|{@{}@774000|249000|11000|11000|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|55|0|132|0|{Copies data records from its input to its output without changing the values.  Use Redefine Format to change a record format or rename fields.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|copy|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=byte_copy(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1276748893|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|56|0|134|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|57|0|137|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010503005|XXGfvertex|58|0|140|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("/abinitio/data1/CitiTech/mfs/mfs4way/MEX/GCG/DTTK/S054-692/main/./CITSGRAL_WS054692_TINOT _TSET_TXNMON_detail_stage.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|Layout|mfile:/abinitio/data1/CitiTech/mfs/mfs4way/MEX/GCG/DTTK/S054-692/main/./CITSGRAL_WS054692_TINOT _TSET_TXNMON_detail_stage.dat|3|2|$|@{0|}}
{30001002|XXparameter|write_metadata|record
    decimal(1)   tipo_registro;
    string(19)   cuenta;
    string(6)    autorizacion;
    decimal(9)   distintivo_timestamp;
    decimal(10)  negocio;
    string(10)   fecha;
    decimal(6)   hora;
    string(8)    term;
    decimal(4)   sucursal;
    decimal(4)   cajero;
    string(8)    operador;
    string(4)    ret_cat;
    string(2)    resp_cde;
    decimal(4)   resp_time;
    string(3)    curr_cde;
    string(14)   importe;
    string(7)    tipo_de_cambio;
    string(14)   importe_mn;
    string(14)   cred_disp;
    string(4)    adquirente;
    string(4)    emisor;
    decimal(1)   responder;
    string(4)    tran_typ;
    string(3)    cod_pais;
    string(9)    cod_post;
    string(3)    access_mode;
    string(2)    access_med;
    string(1)    est_cuenta;
    string(1)    est_plastico;
    string(1)    est_negocio;
    decimal(4)   fopera;
    string(6)    proc_code;
    decimal(4)   ica;
    decimal(1)   adq_neg;
    string(1)    modo_falcon;
    string(6)    marc_resp;
    string(6)    fvalida;
    decimal(4)   resp_int;
    decimal(9)   lin_cred;
    decimal(4)   score_flcn;
    decimal(9)   ulfd_num_modulo;
    decimal(4)   ulfd_num_consec;
    string(14)   ulfd_importe_entregado;
    string(1)    ulfd_status_conciliaci;
    string(1)    ulfd_ind_comer_elect;
    string(14)   ulfd_importe_cash_back;
    string(2)    ulfd_tipo_plan;
    string(2)    ulfd_diferimiento;
    string(2)    ulfd_num_plazo;
    string(25)   ulfd_nom_negocio;
    string(25)   ulfd_tracki;
    string(13)   ulfd_location_city;
    string(3)    ulfd_location_state;
    decimal(3)   ulfd_score_mastercard;
    decimal(2)   ulfd_score_visa;
    string(1)    id_tipo_tabla;
    //gj08685- se agrega campos emv
    string(3)   service_code;
    string(1)   trans_categ_code;
    decimal(1)  term_input_capind;
    string(1)   crdhldr_id_method;
    string(2)   crypto_inf_data;
    string(10)  tvr;
    string(16)  arqc;
    string(12)  amt_auth;
    string(12)  amt_other;
    string(4)   aip;
    string(4)   atc;
    string(3) term_cntry_code;
    string(3) tran_crncy_code;
    string(6) tran_date;
    string(2) crypto_info_data;
    string(8) unpredict_num;
    string(64) iss_appl_data;
    string(8) term_serl_num;
    string(8) emv_term_cap;
    string(2) emv_term_type;
    string(4) appl_ver_num;
    string(6) cvm_rslts;
    string(32) df_name;
    decimal(2) inp_entry_mode;
    decimal(1) inp_entry_pin;
    string(1) term_entry_cap;
    string(1) last_emv_stat;
    string(1) data_suspect;
    string(2) appl_pan_seq_num;
    string(6) dev_info;
    string(4) rsn_onl_cde;
    string(1) arqc_vrfy;
    string(1) iso_rc_ind;
    string(4) iss_auth_data_lgth;     
    string(32) emv_iss_auth_data;
    string(1) send_crd_blk;
    string(1) send_put_data;
    //md11572 - se agregan campos
    string(1) tipo_de_pan;
    decimal(16) numero_de_cuenta;
    decimal(4) vigencia;
    decimal(11) id_asociado;
    decimal (2) onbehalf_serv;
    string (1) onbehalf_res;
    decimal(2) nivel_de_assurance;
    string(2) tipo_de_almacenamiento;
    decimal (2) srv_preval;
    string (1) tipo_validacion;
    //ab38354-fd97628 - se agregan campos proyecto CVV2
    decimal(1) pre_cvv2;
    decimal(1) res_cvv2;
    decimal(2) pre_dfa;
    decimal(1) res_dfa;
    decimal(2) id_autentica;
    string (3) UL_B0_DSRP_INDICADOR;
    string(3) UL_B0_ID_WALLET_WID;
    //pp95943 - se agregan campos proyecto Arcot 3D secure
    string(1) numero_version;
    string(1) tipo_autenticacion;
    string(36) directorio;
    string(1) criptograma_presente;
    string(1) criptograma_resultado;
    string(15) ip_address;
    string(17) mac_address;   
   // string(99)  filler;
    string(27)  filler;
    string(1)    new_line;
end;|3|1|l|@{0|}}
}}@0|@545876|260323|793000|245000|56000|50000|102|Stage Detail|A||1|10|-1||6||33025|-1|-1|}}
{2010202004|XXGiport|59|0|142|0|{@{}@783000|264000|11000|11000|write|0.0|@@@1776|0|}}
{2010503005|XXGfvertex|60|0|145|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url|@28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|param block_compressed True mode lookup version 2.15.5.r34:|3|15|P?|@{0|}}
{30001002|XXparameter|Layout|@28|2|RF$||{0|}}
{30001002|XXparameter|write_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|mpcmodtime|1276748815|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|61|0|147|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1776|0|}}
{2010501005|XXGpvertex|62|0|151|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Redefine_Format.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|doc_transform|out :: document(in) =
begin
  out :: in;
end;|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
      decimal(1) tipo_registro;
      string(4) sitema;
      string(8) fecha_book;
      string(6) hrgenarc;
      string(8) fhininfo;
      string(8) fecha_2;
      string(2) nucsvoar;
      string(3) cvecsi;
      string(4) cvsisfue;
      //pg83302 - se agrega filler
      string(726) filler;
      string(1) new_line_hdr;
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|=|@{0|}}
}}@0|@772713|77403|786000|88000|44000|41000|836|Redefine Format Header|Ab Initio Software|Built-in|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|63|0|153|0|{@{}@829000|104000|11000|11000|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|64|0|155|0|{@{}@776000|104000|11000|11000|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|65|0|158|0|{Copies data records from its input to its output without changing the values.  Use Redefine Format to change a record format or rename fields.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|copy|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=byte_copy(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1276748893|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|66|0|160|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|67|0|163|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|68|0|168|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Redefine_Format.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|doc_transform|out :: document(in) =
begin
  out :: in;
end;|3|2|$|@{0|}}
{30001002|XXparameter|out_metadata|record
      decimal(1) tipo_registro;
      string(31) trailer;
      //pg83302 - se agrega filler
      //string(468) filler;
      //string(9) filler;
      string(1)  new_line_trl;
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|@777009|380078|790000|389000|44000|41000|829|Redefine Format Trailer|Ab Initio Software|Built-in|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|69|0|170|0|{@{}@833000|404000|11000|11000|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|70|0|172|0|{@{}@780000|404000|11000|11000|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|71|0|175|0|{Copies data records from its input to its output without changing the values.  Use Redefine Format to change a record format or rename fields.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|copy|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=byte_copy(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1276748893|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|72|0|177|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|73|0|180|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010503005|XXGfvertex|74|0|183|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|condition|$[GENERATE_HEADER]|3|9||@{0|}}
{30001002|XXparameter|eme_dataset_mapping|$[[record map_component 1 datasets [vector [record variable _interp_("write", "pdl") map_dataset 1 mapping [record dataset_path _interp_("/abinitio/data1/CitiTech/serial/MEX/GCG/DTTK/S054-692/main/./CITSGRAL_WS054692_TINOT _TSET_TXNMON_trailer_for_check.dat", "pdl") create_update 1 is_db 0 dml_info NULL]]]]]|3|9||@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Datasets/Output_File.mdc|3|2|Pf$|@{0|}}
{30001002|XXparameter|write_metadata|record
      decimal(1) tipo_registro;
      string(31) trailer;
      //pg83302 - se agrega filler
      //string(468) filler;
      //string(9) filler;
      string(1)  new_line_trl;
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout|file:/abinitio/data1/CitiTech/serial/MEX/GCG/DTTK/S054-692/main/./CITSGRAL_WS054692_TINOT _TSET_TXNMON_trailer_for_check.dat|3|2|$|@{0|}}
}}@0|@536667|376333|999000|391000|56000|50000|100|Trailer|A||1|100|-1||6||33025|-1|-1|}}
{2010202004|XXGiport|75|0|185|0|{@{}@989000|409000|11000|11000|write|0.0|@@@1776|0|}}
{2010503005|XXGfvertex|76|0|188|0|{Represents one file, many files, or a multifile as an output from your graph.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|protection|0666|12|2|RF$||{0|}}
{30001002|XXparameter|mode|0x0062|1|2|FH$|modes of access|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort||3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort||3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Remove completely|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|key||19|2|RF$|Key specifier For Lookup File|{0|}}
{30001002|XXparameter|key.condition|param direct_addressed False mode lookup|3|15|P?|@{0|}}
{30001002|XXparameter|m_catalog_add_option_names|block_compressed keep_on_disk direct_addressed|3|2|H$||{0|}}
{30001002|XXparameter|eme_index_location||3|2|F$|Place in the EME to create a dataset corresponding to this index.|{0|}}
{30001002|XXparameter|eme_index_location.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|index_url|@28|2|F$|The URL of the index for this lookup file (optional)|{0|}}
{30001002|XXparameter|index_url.condition|param direct_addressed False mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|keep_on_disk|False|13|1|Fl|Keep on Disk|{0|}}
{30001002|XXparameter|keep_on_disk.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|block_compressed|False|13|1|Fl|Block Compressed|{0|}}
{30001002|XXparameter|block_compressed.condition|mode lookup version 2.15.2.r23:|3|15|P?|@{0|}}
{30001002|XXparameter|direct_addressed|False|13|1|Fl|Set to true if lookup is direct addressed|{0|}}
{30001002|XXparameter|direct_addressed.condition|param block_compressed True mode lookup version 2.15.5.r34:|3|15|P?|@{0|}}
{30001002|XXparameter|Layout|@28|2|RF$||{0|}}
{30001002|XXparameter|write_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|mpcmodtime|1276748815|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|eme_dataset_mapping||40|9|F|Place in the EME to create the dataset(s) corresponding to this component.|{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|-1|-1|}}
{2010202004|XXGiport|77|0|190|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|write|0.0|@@@1776|0|}}
{2010501005|XXGpvertex|78|0|194|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|l|@{0|}}
{30001002|XXparameter|out0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|transform0|/*Reformat operation*/
out::reformat(in)=
begin
  out.tipo_registro :: in.tipo_registro;
  out.filler:: string_replace(in.filler, "\\x01", " ");
end;|3|1|l|@{0|}}
{30001002|XXparameter|Layout||3|8|s=|@{0|}}
}}@0|@511000|190000|0|0|0|0|842|Reformat - Remove Inv Char|Ab Initio Software|Built-in|1|100|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|79|0|196|0|{@{}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|80|0|199|0|{@{}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|81|0|201|0|{@{}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|82|0|203|0|{@{}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|83|0|205|0|{@{}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|84|0|208|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
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
{30001002|XXparameter|output_indexes_signature|int[int] output_indices_out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
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
{30001002|XXparameter|num_operations|5|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
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
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1383376019|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@||1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|85|0|210|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|86|0|214|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|87|0|217|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|88|0|220|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|89|0|223|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|90|0|230|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Replicate.mpc|3|2|Pf$|@{0|}}
}}@0|@39469|403422|49000|412000|50000|41000|758|Replicate|Ab Initio Software|Built-in|1|10|0||6||32833|1|{1|0|}}}
{2010203004|XXGoport|91|0|232|0|{@{}@98000|429000|11000|11000|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|92|0|235|0|{@{}@39000|429000|11000|11000|in|0.0|@@@1812|0|}}
{2010501005|XXGpvertex|93|0|237|0|{Arbitrarily combines all the data records it receives into a single flow and writes a copy of that flow to each of its output flows.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
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
{30001002|XXparameter|mpcmodtime|1276748893|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|94|0|239|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|95|0|242|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1812|0|}}
{2010501005|XXGpvertex|96|0|245|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Replicate.mpc|3|2|Pf$|@{0|}}
}}@0|@70365|324474|80000|333000|50000|41000|744|Replicate-1|Ab Initio Software|Built-in|1|10|0||6||32833|1|{1|0|}}}
{2010203004|XXGoport|97|0|247|0|{@{}@129000|349000|11000|11000|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|98|0|250|0|{@{}@70000|349000|11000|11000|in|0.0|@@@1812|0|}}
{2010501005|XXGpvertex|99|0|252|0|{Arbitrarily combines all the data records it receives into a single flow and writes a copy of that flow to each of its output flows.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
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
{30001002|XXparameter|mpcmodtime|1276748893|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|100|0|254|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2068|0|}}
{2010202004|XXGiport|101|0|257|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1812|0|}}
{2010600005|XXGgraph|102|0|260|0|{Subgraph created from graph "Sb Header, Detail & Trailer Validation"|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|condition|$[TRAILER]|3|9|F||{0|}}
}}@0|@127614|346020|148000|366000|1050000|452000|761|Validate Qty Records|A||1|10|0||6||32833|{0|}0|0|{0|}{0|}{0|}{0|}.19411766529083252|1050909|451000|7|}}
{2010210004|XXGflow|103|0|262|0|{@{}@384|.5|.5|{12|173000|154000|193000|154000|218000|154000|218000|124000|243000|124000|264000|124000|}26858|17|}}
{2010210004|XXGflow|104|0|264|0|{@{}@384|.5|.8474576473236084|{12|408000|124000|428000|124000|550000|124000|550000|194000|572000|194000|593000|194000|}26854|17|}}
{2010210004|XXGflow|105|0|266|0|{@{}@384|.5|.9481865167617798|{12|236000|314000|256000|314000|555000|314000|555000|224000|572000|224000|593000|224000|}26855|17|}}
{2010210004|XXGflow|106|0|268|0|{@{}@384|.5|.5|{12|819000|209000|839000|209000|862000|209000|862000|224000|885000|224000|906000|224000|}26856|17|}}
{2010501005|XXGpvertex|107|0|270|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Partitioning/Concatenate.mpc|3|2|Pf$|@{0|}}
}}@0|@833181|361682|843000|371000|50000|41000|26838|Concatenate|Ab Initio Software|Built-in|1|10|0||6||32833|1|{1|0|}}}
{2010203004|XXGoport|108|0|272|0|{@{}@892000|384000|11000|11000|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|109|0|274|0|{@{}@833000|384000|11000|11000|in|0.0|@@@18195|0|}}
{2010501005|XXGpvertex|110|0|276|0|{Appends multiple flow partitions of data records one after another.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|concat|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
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
{30001002|XXparameter|mpcmodtime|1276748904|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagate_through|metadata type: out = in
metadata type: in = out|3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|111|0|278|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|112|0|281|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@18195|0|}}
{2010501005|XXGpvertex|113|0|284|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|transform|include "~$ERROR_DML_URL/da_error_info_type.dml";

da_error_info_t out::handler_error(error_info)=
begin       
   let da_error_info_t error_rec = allocate();
   
   error_rec.file_name     = "$\{BASE_FILE_NAME\}$\{FILE_EXTENSION:+.$FILE_EXTENSION\}";
   error_rec.batch_id      = $\{FILE_RECEIPT_SID\};
   error_rec.record_number = '0';
   error_rec.error_code    = error_info.details[0].code;
   error_rec.component     = error_info.component;
   error_rec.message       = error_info.message;
   
   out :: error_rec;
end;

da_error_info_t error::make_error(error_info,in0,in1)=
begin
   error :: handler_error(error_info);
end;

/*Function combining one record from each input to produce one record on the output.*/
out::fuse(in0,in1)=
begin
  if(!is_defined(in0.qty_records))
    force_error("TRAILER NOT FOUND IN FILE");
    
  if(in0.qty_records != in1.qty_records)
    force_error(string_concat("TRAILER records doesn't much count of records (",(string("\\n"))decimal_strip(in0.qty_records)," <> ",(string("\\n"))decimal_strip(in1.qty_records),")"));

  out.* :: in0.*;
end;|3|3|c|@{0|}}
{30001002|XXparameter|error_group|STG_ERROR|3|2|$|@{0|}}
{30001002|XXparameter|reject_threshold|Never abort|3|1|l|@{0|}}
{30001002|XXparameter|error0_metadata|include "~$ERROR_DML_URL/da_error_info_type.dml";
metadata type = da_error_info_t;|3|1|l|@{0|}}
{30001002|XXparameter|error1_metadata|include "~$ERROR_DML_URL/da_error_info_type.dml";
metadata type = da_error_info_t;|3|1|l|@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Fuse.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|_propagate_through|metadata type: in = out
metadata type: out = in|3|9||@{0|}}
{30001002|XXparameter|in0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|in1_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|out_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject1_metadata||3|8|s=|@{0|}}
}}@0|@584000|155590|604000|176000|205000|69000|26857|Fuse|Ab Initio Software|Built-in 2.10:|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|114|0|286|0|{@{}@808000|204000|11000|11000|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|115|0|289|0|{@{}@619000|244000|11000|11000|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|116|0|291|0|{@{}@659000|244000|11000|11000|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|117|0|293|0|{@{}@699000|244000|11000|14000|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|118|0|295|0|{@{}@739000|244000|11000|14000|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|119|0|297|0|{@{}@779000|244000|11000|11000|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|120|0|299|0|{@{}@594000|189000|11000|11000|in0|0.0|count|in|0|1936|0|}}
{2010202004|XXGiport|121|0|302|0|{@{}@594000|219000|11000|11000|in1|0.0|count|in|1|1936|0|}}
{2010501005|XXGpvertex|122|0|305|0|{Applies a transform to the corresponding records from each input flow. The transform is first applied to the first record on each flow, then to the second, and so on. The result of the transform is sent out of the out port.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|fuse-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
{30001002|XXparameter|count|2|1|1|Fl|Number of inputs to fuse function|{0|}}
{30001002|XXparameter|count.is_index|true|3|9|P|@{0|}}
{30001002|XXparameter|transform||8|1|RFOl|Required and optional DML functions|{0|}}
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
{30001002|XXparameter|operation1|optional integer(4) out::select(in[*])|3|2|H$|If this returns 0, the input records are discarded.|{0|}}
{30001002|XXparameter|operation1_analysis|integer(4) select_out::select(in[*])|3|2|H$||{0|}}
{30001002|XXparameter|operation2|out::fuse(in[*])|3|2|H$|Function combining one record from each input to produce one record on the output.|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|deadlock_prone|True|13|1|l|Necessary record on one input stops read on all inputs|{0|}}
{30001002|XXparameter|deadlock_prone.display_name|deadlock-prone|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject*=in*|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record utf8 string(big endian integer(4)) component; big endian integer(4) port_index; utf8 string(big endian integer(4)) parameter; utf8 string(big endian integer(4)) message; record utf8 string(big endian integer(4)) code; big endian integer(4) parent_index; record utf8 string(big endian integer(4)) name; utf8 string(big endian integer(4)) value; end [big endian integer(4)] attributes; end [big endian integer(4)] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('') event_type; string('') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation3|optional out::output_for_error(error_info, in[*])|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation4|optional error::make_error(error_info, in[*])|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::log_error(error_info, in[*])|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation6|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|False|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count in|3|1|l||{0|}}
{30001002|XXparameter|in0_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|in1_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|reject1_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|error1_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|record string("\|") node, timestamp, component, subcomponent, event_type; string("\|\\n") event_text; end|7|1|Fl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,reject[*],error[*],log::document(in[*])|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1276748906|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = "record string(\\"\|\\") node, timestamp, component, subcomponent, event_type; string(\\"\|\\\\n\\") event_text; end"|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|123|0|307|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|124|0|310|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|125|0|313|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject1|0.0|count|reject|1|1168|0|}}
{2010203004|XXGoport|126|0|316|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|127|0|319|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error1|0.0|count|error|1|1176|0|}}
{2010203004|XXGoport|128|0|322|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|129|0|325|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in0|0.0|count|in|0|1936|0|}}
{2010202004|XXGiport|130|0|328|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in1|0.0|count|in|1|1936|0|}}
{2010501005|XXGpvertex|131|0|331|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|sorted_input|False|3|1|l|@{0|}}
{30001002|XXparameter|key|\{\}|3|2|$|@{0|}}
{30001002|XXparameter|transform|out :: rollup(in) =
begin
  out.qty_records :: count(in) - $\{TRAILER_DELTA\};
end;|3|3|c|@{0|}}
{30001002|XXparameter|max_core|$AI_GRAPH_MAX_CORE|3|2|$|@{0|}}
{30001002|XXparameter|check_sort|False|3|1|l|@{0|}}
{30001002|XXparameter|out_metadata|record
  decimal("\\n") qty_records;
end;|3|1|l|@{0|}}
{30001002|XXparameter|error_metadata|string('\\n')|3|1|l|@{0|}}
{30001002|XXparameter|log_metadata|record string("\|") node, timestamp, component, subcomponent, event_type; string("\|\\n") event_text; end|3|1|l|@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Rollup.mpc|3|2|Pf$|@{0|}}
}}@0|@82787|261605|103000|282000|123000|69000|26853|Rollup|Ab Initio Software|Built-in 2.0:|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|132|0|333|0|{@{}@225000|309000|11000|11000|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|133|0|336|0|{@{}@119000|350000|11000|11000|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|134|0|338|0|{@{}@159000|350000|11000|11000|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|135|0|340|0|{@{}@199000|350000|11000|11000|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|136|0|342|0|{@{}@93000|309000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|137|0|344|0|{Generates data records that summarize groups of data records.  Rollup in memory maximizes performance by keeping intermediate results in main memory.  Rollup sorted requires grouped input.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|?rollup|3|1|Hl||{0|}}
{30001002|XXparameter|image__|/~ab_home/bin/transform|3|2|H$||{0|}}
{30001002|XXparameter|sorted_input|True|13|1|Fl|Ordering of input data|{0|}}
{30001002|XXparameter|sorted_input.display_name|sorted-input|3|9|P|@{0|}}
{30001002|XXparameter|sorted_input.update_clauses|retain_old_default|3|9|P|@{0|}}
{30001002|XXparameter|sorted_input_display_values|In-memory:Inputneednotbesorted Inputmustbesortedorgrouped|3|2|H$||{0|}}
{30001002|XXparameter|sorted_input_display_values.display_name|sorted-input-display-values|3|9|P|@{0|}}
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
{30001002|XXparameter|major_key.condition|param grouped-input True|3|15|P?|@{0|}}
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
{30001002|XXparameter|num_operations|10|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|num_variables|1|1|2|H$|Number of public variables in rollup|{0|}}
{30001002|XXparameter|variable1|optional temporary_type temp|3|2|H$|Temporary variable|{0|}}
{30001002|XXparameter|operation1|optional int out::input_select(in)|3|2|H$|Select input record|{0|}}
{30001002|XXparameter|operation2|optional temp ? temp::initialize(in) : NULL|3|2|H$|Initialize temporary|{0|}}
{30001002|XXparameter|operation3|temp ? temp::rollup(temp, in) : out::rollup(in)|3|2|H$|Do computation|{0|}}
{30001002|XXparameter|operation4|optional temp ? out::finalize(temp, in) : NULL|3|2|H$|Create output record|{0|}}
{30001002|XXparameter|operation5|optional int out::output_select(out)|3|2|H$|Select output record|{0|}}
{30001002|XXparameter|operation6|optional integer(8) out::key_change(in in1, in in2)|3|2|H$|Determine if key changed|{0|}}
{30001002|XXparameter|operation1_analysis|int input_select_out::input_select(in)|3|2|H$|Select input record|{0|}}
{30001002|XXparameter|operation5_analysis|int output_select_out::output_select(out)|3|2|H$|Select output record|{0|}}
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
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record utf8 string(big endian integer(4)) component; big endian integer(4) port_index; utf8 string(big endian integer(4)) parameter; utf8 string(big endian integer(4)) message; record utf8 string(big endian integer(4)) code; big endian integer(4) parent_index; record utf8 string(big endian integer(4)) name; utf8 string(big endian integer(4)) value; end [big endian integer(4)] attributes; end [big endian integer(4)] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('') event_type; string('') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation7|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation8|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation9|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation10|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|reject_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out,reject,error,log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1276748906|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|_propagation|metadata type: reject = in
metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|138|0|346|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010203004|XXGoport|139|0|349|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject|0.0|@@@1168|0|}}
{2010203004|XXGoport|140|0|352|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error|0.0|@@@1176|0|}}
{2010203004|XXGoport|141|0|355|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|142|0|358|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|143|0|365|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|condition|$[REDEF_INPUT_FILE_DML]|3|9||@{0|}}
{30001002|XXparameter|out_metadata|$[REDEF_INPUT_FILE_DML_T]|3|9||@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Redefine_Format.mpc|3|2|Pf$|@{0|}}
}}@0|@105511|123157|119000|132000|44000|41000|26859|Redefine - trailer (if needed)-1|Ab Initio Software|Built-in|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|144|0|367|0|{@{}@162000|149000|11000|11000|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|145|0|370|0|{@{}@109000|149000|11000|11000|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|146|0|372|0|{Copies data records from its input to its output without changing the values.  Use Redefine Format to change a record format or rename fields.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|copy|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|out=byte_copy(in)|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1276748893|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|147|0|374|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|out|0.0|@@@2448|0|}}
{2010202004|XXGiport|148|0|377|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1936|0|}}
{2010501005|XXGpvertex|149|0|380|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|transform0|/*Reformat operation*/
out::reformat(in)=
begin

  out.qty_records :: in.cant_reg;

end;|3|1|l|@{0|}}
{30001002|XXparameter|error0_metadata|string('\\n')|3|1|l|@{0|}}
{30001002|XXparameter|log_metadata|record string("\|") node, timestamp, component, subcomponent, event_type; string("\|\\n") event_text; end|3|1|l|@{0|}}
{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Transform/Reformat.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|out0_metadata||3|8|=|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
{30001002|XXparameter|reject0_metadata||3|8|s=|@{0|}}
}}@0|@254783|52306|275000|72000|123000|107000|26840|Rf: Trailer Validation|Ab Initio Software|Built-in|1|10|0||6||32769|1|{1|0|}}}
{2010203004|XXGoport|150|0|382|0|{@{}@397000|119000|11000|11000|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|151|0|385|0|{@{}@289000|178000|11000|11000|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|152|0|387|0|{@{}@329000|178000|11000|11000|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|153|0|389|0|{@{}@369000|178000|11000|11000|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|154|0|391|0|{@{}@265000|119000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|155|0|394|0|{Changes the record format of your data by dropping fields or by using DML expressions to add fields, combine fields, or modify the data.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|reformat-transform|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
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
{30001002|XXparameter|output_index_signature|int out::output_index(in)|3|2|H$|Function returning index of output port|{0|}}
{30001002|XXparameter|output_index_signature.display_name|output-index_signature|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes||8|1|FKl|Output index vector computation|{0|}}
{30001002|XXparameter|output_indexes.display_name|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes.keyword|output-indexes|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port|discriminator|3|2|FHK$|Output index port for debugger|{0|}}
{30001002|XXparameter|output_indexes_port.display_name|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_port.keyword|output-indexes_port|3|9|P|@{0|}}
{30001002|XXparameter|output_indexes_signature|int[int] out::output_indexes(in)|3|2|H$|Function returning vector of indexes of output ports|{0|}}
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
{30001002|XXparameter|num_operations|5|1|2|H$|Number of operations in package|{0|}}
{30001002|XXparameter|operation1|out::reformat(in)|3|2|H$|Reformat operation|{0|}}
{30001002|XXparameter|condition||3|2|F$||{0|}}
{30001002|XXparameter|conditionInputPort|in|3|2|F$||{0|}}
{30001002|XXparameter|conditionOutputPort|out*|3|2|F$||{0|}}
{30001002|XXparameter|condition_interpretation|Replace with flow|15|1|Fl||{2|Replace with flow|Remove completely|}}
{30001002|XXparameter|condition_interpretation.display_name|condition-interpretation|3|9|P|@{0|}}
{30001002|XXparameter|port_analysis|reject*=in;out*=in|3|2|H$||{0|}}
{30001002|XXparameter|continuous_analysis||3|2|H$||{0|}}
{30001002|XXparameter|filter_aggregate_analysis|out=filter(select)|3|2|H$||{0|}}
{30001002|XXparameter|num_types|2|1|2|H$|Number of private data types in package|{0|}}
{30001002|XXparameter|type1|error_info_t error_info "record utf8 string(big endian integer(4)) component; big endian integer(4) port_index; utf8 string(big endian integer(4)) parameter; utf8 string(big endian integer(4)) message; record utf8 string(big endian integer(4)) code; big endian integer(4) parent_index; record utf8 string(big endian integer(4)) name; utf8 string(big endian integer(4)) value; end [big endian integer(4)] attributes; end [big endian integer(4)] details; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|type2|log_event_t log_event "record string('') event_type; string('') event_text; end"|3|2|H$|Type of error_info|{0|}}
{30001002|XXparameter|operation2|optional out::output_for_error(error_info, in)|3|2|H$|Function to create output in case of error.|{0|}}
{30001002|XXparameter|operation3|optional error::make_error(error_info, in)|3|2|H$|Function to create error record in case of error.|{0|}}
{30001002|XXparameter|operation4|optional log_event::log_error(error_info, in)|3|2|H$|Function to create log record in case of error.|{0|}}
{30001002|XXparameter|operation5|optional log_event::final_log_output()|3|2|H$|Function to create final log record.|{0|}}
{30001002|XXparameter|num_callbacks|4|1|2|H$|Number of callbacks in package|{0|}}
{30001002|XXparameter|_use_rich_error_format|True|13|1|Hl|False means use legacy string newline format|{0|}}
{30001002|XXparameter|_use_rich_log_format|True|13|1|Hl|False means use legacy native charset format|{0|}}
{30001002|XXparameter|Layout|@9|2|RFs$||{0|}}
{30001002|XXparameter|main_mp_port|count out|3|1|l||{0|}}
{30001002|XXparameter|in_metadata||7|1|RFsl||{0|}}
{30001002|XXparameter|out0_metadata||7|1|RFl||{0|}}
{30001002|XXparameter|reject0_metadata||7|1|Fsl||{0|}}
{30001002|XXparameter|error0_metadata|$AB_HOME/include/error-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|log_metadata|$AB_HOME/include/log-info.dml|7|2|Ff$||{0|}}
{30001002|XXparameter|doc_transform||8|2|FHs$|Document your transformation for dependency analysis|{0|}}
{30001002|XXparameter|doc_operation1|out[*],reject[*],error[*],log::document(in)|3|2|RH$||{0|}}
{30001002|XXparameter|mpcmodtime|1276748906|1|1|Hl|The last modification time of this component's template|{0|}}
{30001002|XXparameter|_propagation|metadata type: error = remote("$AB_HOME/include/error-info.dml")
metadata type: reject = in
metadata type: log = remote("$AB_HOME/include/log-info.dml")|3|1|HKl|@{0|}}
{30001002|XXparameter|_propagate_through||3|1|FHKl|@{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010203004|XXGoport|156|0|396|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
{30001002|XXparameter|transform0||8|8|FO=|Reformat transform|{0|}}
{30001002|XXparameter|transform0.index|count|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_value|0|3|9|P|@{0|}}
{30001002|XXparameter|transform0.index_name|transform|3|9|P|@{0|}}
}}@0|0|0|0|out0|0.0|count|out|0|2448|0|}}
{2010203004|XXGoport|157|0|400|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|reject0|0.0|count|reject|0|1168|0|}}
{2010203004|XXGoport|158|0|403|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|error0|0.0|count|error|0|1176|0|}}
{2010203004|XXGoport|159|0|406|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|F=||{0|}}
}}@0|0|0|0|log|0.0|@@@1176|0|}}
{2010202004|XXGiport|160|0|409|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|161|0|416|0|{|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|!prototype_path|$AB_COMPONENTS/Miscellaneous/Trash.mpc|3|2|Pf$|@{0|}}
{30001002|XXparameter|in_metadata||3|8|s=|@{0|}}
}}@0|@880333|161276|917000|189000|56000|72000|26847|Trash|Ab Initio Software|Built-in|1|10|0||6||32769|1|{1|0|}}}
{2010202004|XXGiport|162|0|418|0|{@{}@907000|219000|11000|11000|in|0.0|@@@1808|0|}}
{2010501005|XXGpvertex|163|0|421|0|{Ends a flow by discarding all input data records.|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|mpname|broadcast|3|1|Hl||{0|}}
{30001002|XXparameter|image__|unitool|3|2|H$||{0|}}
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
{30001002|XXparameter|mpcmodtime|1276748894|1|1|Hl|The last modification time of this component's template|{0|}}
}}@0|@0|0|0|0|0|0|0|@@@1|100|-1|@6|@1|1|{1|0|}}}
{2010202004|XXGiport|164|0|423|0|{@{30100001|XXparameter_set|@@@@{{30001002|XXparameter|metadata||7|8|RF=||{0|}}
}}@0|0|0|0|in|0.0|@@@1808|0|}}
{2010202004|XXGiport|165|0|427|0|{@{}@138000|424000|11000|11000|in1|.7230392156862745|@@@14096|0|}}
{2010202004|XXGiport|166|0|431|0|{@{}@138000|394000|11000|11000|in0|.36519607843137253|@@@14224|0|}}
{2010203004|XXGoport|167|0|435|0|{@{}@316000|189000|11000|11000|out0|.5253549695740365|@@@14736|0|}}
{2010203004|XXGoport|168|0|438|0|{@{}@316000|154000|11000|11000|out1|.16666666666666666|@@@14736|0|}}
{2010203004|XXGoport|169|0|441|0|{@{}@316000|224000|11000|11000|out2|.8333333333333333|@@@14736|0|}}
{2010202004|XXGiport|170|0|444|0|{@{}@93000|189000|11000|11000|in0|.5|@@@14096|0|}}
{2010203004|XXGoport|171|0|447|0|{@{}@426000|239000|11000|11000|out1|.16666666666666666|@@@14736|0|}}
{2010203004|XXGoport|172|0|451|0|{@{}@426000|309000|11000|11000|out2|.8333333333333333|@@@14736|0|}}
{2010203004|XXGoport|173|0|455|0|{@{}@426000|274000|11000|11000|out0|.5|@@@14736|0|}}
{2010202004|XXGiport|174|0|459|0|{@{}@193000|274000|11000|11000|in0|.5|@@@14096|0|}}
{2010110002|XXGconstant|175|0|465|0|{@{}@{1|9200090|}}}
{2010002001|XXGdirectory_object_object|0|1|2|0|{XXGgraph|}0|1|}
{2010704001|XXGgraph_graphinfo_graphinfo|1|0|2|0|{}1|2|}
{2010706001|XXGgraphinfo_runsettings_runsettings|2|0|4|0|{}2|3|}
{2010109001|XXGobject_property_value|3|0|6|0|{0|legend_face|92|}2|4|}
{2010604001|XXGgraph_flow_flow|4|0|8|0|{Flow_1|}1|5|}
{2010604001|XXGgraph_flow_flow|5|0|10|0|{Flow_2|}1|6|}
{2010604001|XXGgraph_flow_flow|6|0|12|0|{Flow_3|}1|7|}
{2010604001|XXGgraph_flow_flow|7|0|14|0|{Flow_4|}1|8|}
{2010604001|XXGgraph_flow_flow|8|0|16|0|{Flow_7|}1|9|}
{2010601001|XXGgraph_vertex_vertex|9|0|18|0|{Gather|}1|10|}
{2010212001|XXGvertex_oport_oport|10|0|20|0|{0|out|}10|11|}
{2010211001|XXGvertex_iport_iport|11|0|22|0|{0|in|}10|12|}
{2010214001|XXGiport_src_flow|12|0|24|0|{0|}12|9|}
{2010007001|XXGobject_proto_object|13|0|25|0|{}10|13|}
{2010212001|XXGvertex_oport_oport|14|0|27|0|{0|out|}13|14|}
{2010006001|XXGobject_psameas_object|15|0|29|0|{metadata|out_metadata|1|0|}14|13|}
{2010211001|XXGvertex_iport_iport|16|0|30|0|{0|in|}13|15|}
{2010006001|XXGobject_psameas_object|17|0|32|0|{metadata|in_metadata|1|0|}15|13|}
{2010601001|XXGgraph_vertex_vertex|18|0|33|0|{Header|}1|16|}
{2010211001|XXGvertex_iport_iport|19|0|35|0|{0|write|}16|17|}
{2010214001|XXGiport_src_flow|20|0|37|0|{0|}17|5|}
{2010007001|XXGobject_proto_object|21|0|38|0|{}16|18|}
{2010211001|XXGvertex_iport_iport|22|0|40|0|{0|write|}18|19|}
{2010006001|XXGobject_psameas_object|23|0|42|0|{metadata|write_metadata|1|0|}19|18|}
{2010601001|XXGgraph_vertex_vertex|24|0|43|0|{Input_File|}1|20|}
{2010212001|XXGvertex_oport_oport|25|0|45|0|{0|read|}20|21|}
{2010213001|XXGoport_dst_flow|26|0|47|0|{0|}21|6|}
{2010007001|XXGobject_proto_object|27|0|48|0|{}20|22|}
{2010212001|XXGvertex_oport_oport|28|0|50|0|{0|read|}22|23|}
{2010006001|XXGobject_psameas_object|29|0|52|0|{metadata|read_metadata|1|0|}23|22|}
{2010601001|XXGgraph_vertex_vertex|30|0|53|0|{Redefine_Format|}1|24|}
{2010212001|XXGvertex_oport_oport|31|0|55|0|{0|out|}24|25|}
{2010213001|XXGoport_dst_flow|32|0|57|0|{0|}25|9|}
{2010211001|XXGvertex_iport_iport|33|0|58|0|{0|in|}24|26|}
{2010007001|XXGobject_proto_object|34|0|60|0|{}24|27|}
{2010212001|XXGvertex_oport_oport|35|0|62|0|{0|out|}27|28|}
{2010006001|XXGobject_psameas_object|36|0|64|0|{metadata|out_metadata|1|0|}28|27|}
{2010211001|XXGvertex_iport_iport|37|0|65|0|{0|in|}27|29|}
{2010006001|XXGobject_psameas_object|38|0|67|0|{metadata|in_metadata|1|0|}29|27|}
{2010601001|XXGgraph_vertex_vertex|39|0|68|0|{Sb_Input_File_and_trailer_validation|}1|30|}
{2010601001|XXGgraph_vertex_vertex|40|0|70|0|{Sb_Header_Detail_Trailer_Validation|}30|31|}
{2010604001|XXGgraph_flow_flow|41|0|72|0|{Flow_1|}31|32|}
{2010604001|XXGgraph_flow_flow|42|0|74|0|{Flow_2|}31|33|}
{2010604001|XXGgraph_flow_flow|43|0|76|0|{Flow_3|}31|34|}
{2010604001|XXGgraph_flow_flow|44|0|78|0|{Flow_4|}31|35|}
{2010244001|XXGflow_watcher_watcher|45|0|80|0|{}35|36|}
{2010604001|XXGgraph_flow_flow|46|0|82|0|{Flow_5|}31|37|}
{2010244001|XXGflow_watcher_watcher|47|0|84|0|{}37|38|}
{2010604001|XXGgraph_flow_flow|48|0|86|0|{Flow_6|}31|39|}
{2010601001|XXGgraph_vertex_vertex|49|0|88|0|{Partition_by_Expression|}31|40|}
{2010212001|XXGvertex_oport_oport|50|0|90|0|{0|out|}40|41|}
{2010213001|XXGoport_dst_flow|51|0|92|0|{0|}41|33|}
{2010213001|XXGoport_dst_flow|52|0|93|0|{1|}41|37|}
{2010213001|XXGoport_dst_flow|53|0|94|0|{2|}41|34|}
{2010212001|XXGvertex_oport_oport|54|0|95|0|{1|reject|}40|42|}
{2010212001|XXGvertex_oport_oport|55|0|97|0|{2|error|}40|43|}
{2010212001|XXGvertex_oport_oport|56|0|99|0|{3|log|}40|44|}
{2010211001|XXGvertex_iport_iport|57|0|101|0|{0|in|}40|45|}
{2010007001|XXGobject_proto_object|58|0|103|0|{}40|46|}
{2010212001|XXGvertex_oport_oport|59|0|105|0|{0|out|}46|47|}
{2010006001|XXGobject_psameas_object|60|0|107|0|{metadata|out_metadata|1|0|}47|46|}
{2010212001|XXGvertex_oport_oport|61|0|108|0|{1|reject|}46|48|}
{2010006001|XXGobject_psameas_object|62|0|110|0|{metadata|reject_metadata|1|0|}48|46|}
{2010212001|XXGvertex_oport_oport|63|0|111|0|{2|error|}46|49|}
{2010006001|XXGobject_psameas_object|64|0|113|0|{metadata|error_metadata|1|0|}49|46|}
{2010212001|XXGvertex_oport_oport|65|0|114|0|{3|log|}46|50|}
{2010006001|XXGobject_psameas_object|66|0|116|0|{metadata|log_metadata|1|0|}50|46|}
{2010211001|XXGvertex_iport_iport|67|0|117|0|{0|in|}46|51|}
{2010006001|XXGobject_psameas_object|68|0|119|0|{metadata|in_metadata|1|0|}51|46|}
{2010006001|XXGobject_psameas_object|69|0|120|0|{Layout|Layout|0|0|}40|20|}
{2010006001|XXGobject_psameas_object|70|0|121|0|{in_metadata|read_metadata|0|0|}40|20|}
{2010006001|XXGobject_psameas_object|71|0|122|0|{out_metadata|read_metadata|0|0|}40|20|}
{2010006001|XXGobject_psameas_object|72|0|123|0|{reject_metadata|read_metadata|0|0|}40|20|}
{2010601001|XXGgraph_vertex_vertex|73|0|124|0|{Redefine_Format_Detail|}31|52|}
{2010212001|XXGvertex_oport_oport|74|0|126|0|{0|out|}52|53|}
{2010211001|XXGvertex_iport_iport|75|0|128|0|{0|in|}52|54|}
{2010214001|XXGiport_src_flow|76|0|130|0|{0|}54|35|}
{2010007001|XXGobject_proto_object|77|0|131|0|{}52|55|}
{2010212001|XXGvertex_oport_oport|78|0|133|0|{0|out|}55|56|}
{2010006001|XXGobject_psameas_object|79|0|135|0|{metadata|out_metadata|1|0|}56|55|}
{2010211001|XXGvertex_iport_iport|80|0|136|0|{0|in|}55|57|}
{2010006001|XXGobject_psameas_object|81|0|138|0|{metadata|in_metadata|1|0|}57|55|}
{2010006001|XXGobject_psameas_object|82|0|139|0|{Layout|Layout|0|0|}52|58|}
{2010211001|XXGvertex_iport_iport|83|0|141|0|{0|write|}58|59|}
{2010214001|XXGiport_src_flow|84|0|143|0|{0|}59|7|}
{2010007001|XXGobject_proto_object|85|0|144|0|{}58|60|}
{2010211001|XXGvertex_iport_iport|86|0|146|0|{0|write|}60|61|}
{2010006001|XXGobject_psameas_object|87|0|148|0|{metadata|write_metadata|1|0|}61|60|}
{2010006001|XXGobject_psameas_object|88|0|149|0|{in_metadata|read_metadata|0|0|}52|20|}
{2010601001|XXGgraph_vertex_vertex|89|0|150|0|{Redefine_Format_Header|}31|62|}
{2010212001|XXGvertex_oport_oport|90|0|152|0|{0|out|}62|63|}
{2010211001|XXGvertex_iport_iport|91|0|154|0|{0|in|}62|64|}
{2010214001|XXGiport_src_flow|92|0|156|0|{0|}64|33|}
{2010007001|XXGobject_proto_object|93|0|157|0|{}62|65|}
{2010212001|XXGvertex_oport_oport|94|0|159|0|{0|out|}65|66|}
{2010006001|XXGobject_psameas_object|95|0|161|0|{metadata|out_metadata|1|0|}66|65|}
{2010211001|XXGvertex_iport_iport|96|0|162|0|{0|in|}65|67|}
{2010006001|XXGobject_psameas_object|97|0|164|0|{metadata|in_metadata|1|0|}67|65|}
{2010006001|XXGobject_psameas_object|98|0|165|0|{Layout|Layout|0|0|}62|20|}
{2010006001|XXGobject_psameas_object|99|0|166|0|{in_metadata|read_metadata|0|0|}62|20|}
{2010601001|XXGgraph_vertex_vertex|100|0|167|0|{Redefine_Format_Trailer|}31|68|}
{2010212001|XXGvertex_oport_oport|101|0|169|0|{0|out|}68|69|}
{2010211001|XXGvertex_iport_iport|102|0|171|0|{0|in|}68|70|}
{2010214001|XXGiport_src_flow|103|0|173|0|{0|}70|34|}
{2010007001|XXGobject_proto_object|104|0|174|0|{}68|71|}
{2010212001|XXGvertex_oport_oport|105|0|176|0|{0|out|}71|72|}
{2010006001|XXGobject_psameas_object|106|0|178|0|{metadata|out_metadata|1|0|}72|71|}
{2010211001|XXGvertex_iport_iport|107|0|179|0|{0|in|}71|73|}
{2010006001|XXGobject_psameas_object|108|0|181|0|{metadata|in_metadata|1|0|}73|71|}
{2010006001|XXGobject_psameas_object|109|0|182|0|{Layout|Layout|0|0|}68|74|}
{2010211001|XXGvertex_iport_iport|110|0|184|0|{0|write|}74|75|}
{2010214001|XXGiport_src_flow|111|0|186|0|{0|}75|8|}
{2010007001|XXGobject_proto_object|112|0|187|0|{}74|76|}
{2010211001|XXGvertex_iport_iport|113|0|189|0|{0|write|}76|77|}
{2010006001|XXGobject_psameas_object|114|0|191|0|{metadata|write_metadata|1|0|}77|76|}
{2010006001|XXGobject_psameas_object|115|0|192|0|{in_metadata|read_metadata|0|0|}68|20|}
{2010601001|XXGgraph_vertex_vertex|116|0|193|0|{Reformat_Remove_Inv_Char|}31|78|}
{2010212001|XXGvertex_oport_oport|117|0|195|0|{0|out0|}78|79|}
{2010213001|XXGoport_dst_flow|118|0|197|0|{0|}79|35|}
{2010212001|XXGvertex_oport_oport|119|0|198|0|{1|reject0|}78|80|}
{2010212001|XXGvertex_oport_oport|120|0|200|0|{2|error0|}78|81|}
{2010212001|XXGvertex_oport_oport|121|0|202|0|{3|log|}78|82|}
{2010211001|XXGvertex_iport_iport|122|0|204|0|{0|in|}78|83|}
{2010214001|XXGiport_src_flow|123|0|206|0|{0|}83|37|}
{2010007001|XXGobject_proto_object|124|0|207|0|{}78|84|}
{2010212001|XXGvertex_oport_oport|125|0|209|0|{0|out0|}84|85|}
{2010006001|XXGobject_psameas_object|126|0|211|0|{metadata|out0_metadata|1|0|}85|84|}
{2010006001|XXGobject_psameas_object|127|0|212|0|{transform0|transform0|1|0|}85|84|}
{2010212001|XXGvertex_oport_oport|128|0|213|0|{1|reject0|}84|86|}
{2010006001|XXGobject_psameas_object|129|0|215|0|{metadata|reject0_metadata|1|0|}86|84|}
{2010212001|XXGvertex_oport_oport|130|0|216|0|{2|error0|}84|87|}
{2010006001|XXGobject_psameas_object|131|0|218|0|{metadata|error0_metadata|1|0|}87|84|}
{2010212001|XXGvertex_oport_oport|132|0|219|0|{3|log|}84|88|}
{2010006001|XXGobject_psameas_object|133|0|221|0|{metadata|log_metadata|1|0|}88|84|}
{2010211001|XXGvertex_iport_iport|134|0|222|0|{0|in|}84|89|}
{2010006001|XXGobject_psameas_object|135|0|224|0|{metadata|in_metadata|1|0|}89|84|}
{2010006001|XXGobject_psameas_object|136|0|225|0|{Layout|Layout|0|0|}78|58|}
{2010006001|XXGobject_psameas_object|137|0|226|0|{in_metadata|read_metadata|0|0|}78|20|}
{2010006001|XXGobject_psameas_object|138|0|227|0|{out0_metadata|read_metadata|0|0|}78|20|}
{2010006001|XXGobject_psameas_object|139|0|228|0|{reject0_metadata|read_metadata|0|0|}78|20|}
{2010601001|XXGgraph_vertex_vertex|140|0|229|0|{Replicate|}31|90|}
{2010212001|XXGvertex_oport_oport|141|0|231|0|{0|out|}90|91|}
{2010213001|XXGoport_dst_flow|142|0|233|0|{0|}91|39|}
{2010211001|XXGvertex_iport_iport|143|0|234|0|{0|in|}90|92|}
{2010007001|XXGobject_proto_object|144|0|236|0|{}90|93|}
{2010212001|XXGvertex_oport_oport|145|0|238|0|{0|out|}93|94|}
{2010006001|XXGobject_psameas_object|146|0|240|0|{metadata|out_metadata|1|0|}94|93|}
{2010211001|XXGvertex_iport_iport|147|0|241|0|{0|in|}93|95|}
{2010006001|XXGobject_psameas_object|148|0|243|0|{metadata|in_metadata|1|0|}95|93|}
{2010601001|XXGgraph_vertex_vertex|149|0|244|0|{Replicate_1|}31|96|}
{2010212001|XXGvertex_oport_oport|150|0|246|0|{0|out|}96|97|}
{2010213001|XXGoport_dst_flow|151|0|248|0|{0|}97|32|}
{2010211001|XXGvertex_iport_iport|152|0|249|0|{0|in|}96|98|}
{2010007001|XXGobject_proto_object|153|0|251|0|{}96|99|}
{2010212001|XXGvertex_oport_oport|154|0|253|0|{0|out|}99|100|}
{2010006001|XXGobject_psameas_object|155|0|255|0|{metadata|out_metadata|1|0|}100|99|}
{2010211001|XXGvertex_iport_iport|156|0|256|0|{0|in|}99|101|}
{2010006001|XXGobject_psameas_object|157|0|258|0|{metadata|in_metadata|1|0|}101|99|}
{2010601001|XXGgraph_vertex_vertex|158|0|259|0|{Validate_Qty_Records|}31|102|}
{2010604001|XXGgraph_flow_flow|159|0|261|0|{Flow_1|}102|103|}
{2010604001|XXGgraph_flow_flow|160|0|263|0|{Flow_2|}102|104|}
{2010604001|XXGgraph_flow_flow|161|0|265|0|{Flow_3|}102|105|}
{2010604001|XXGgraph_flow_flow|162|0|267|0|{Flow_4|}102|106|}
{2010601001|XXGgraph_vertex_vertex|163|0|269|0|{Concatenate|}102|107|}
{2010212001|XXGvertex_oport_oport|164|0|271|0|{0|out|}107|108|}
{2010211001|XXGvertex_iport_iport|165|0|273|0|{0|in|}107|109|}
{2010007001|XXGobject_proto_object|166|0|275|0|{}107|110|}
{2010212001|XXGvertex_oport_oport|167|0|277|0|{0|out|}110|111|}
{2010006001|XXGobject_psameas_object|168|0|279|0|{metadata|out_metadata|1|0|}111|110|}
{2010211001|XXGvertex_iport_iport|169|0|280|0|{0|in|}110|112|}
{2010006001|XXGobject_psameas_object|170|0|282|0|{metadata|in_metadata|1|0|}112|110|}
{2010601001|XXGgraph_vertex_vertex|171|0|283|0|{Fuse|}102|113|}
{2010212001|XXGvertex_oport_oport|172|0|285|0|{0|out|}113|114|}
{2010213001|XXGoport_dst_flow|173|0|287|0|{0|}114|106|}
{2010212001|XXGvertex_oport_oport|174|0|288|0|{1|reject0|}113|115|}
{2010212001|XXGvertex_oport_oport|175|0|290|0|{2|reject1|}113|116|}
{2010212001|XXGvertex_oport_oport|176|0|292|0|{3|error0|}113|117|}
{2010212001|XXGvertex_oport_oport|177|0|294|0|{4|error1|}113|118|}
{2010212001|XXGvertex_oport_oport|178|0|296|0|{5|log|}113|119|}
{2010211001|XXGvertex_iport_iport|179|0|298|0|{0|in0|}113|120|}
{2010214001|XXGiport_src_flow|180|0|300|0|{0|}120|104|}
{2010211001|XXGvertex_iport_iport|181|0|301|0|{1|in1|}113|121|}
{2010214001|XXGiport_src_flow|182|0|303|0|{0|}121|105|}
{2010007001|XXGobject_proto_object|183|0|304|0|{}113|122|}
{2010212001|XXGvertex_oport_oport|184|0|306|0|{0|out|}122|123|}
{2010006001|XXGobject_psameas_object|185|0|308|0|{metadata|out_metadata|1|0|}123|122|}
{2010212001|XXGvertex_oport_oport|186|0|309|0|{1|reject0|}122|124|}
{2010006001|XXGobject_psameas_object|187|0|311|0|{metadata|reject0_metadata|1|0|}124|122|}
{2010212001|XXGvertex_oport_oport|188|0|312|0|{2|reject1|}122|125|}
{2010006001|XXGobject_psameas_object|189|0|314|0|{metadata|reject1_metadata|1|0|}125|122|}
{2010212001|XXGvertex_oport_oport|190|0|315|0|{3|error0|}122|126|}
{2010006001|XXGobject_psameas_object|191|0|317|0|{metadata|error0_metadata|1|0|}126|122|}
{2010212001|XXGvertex_oport_oport|192|0|318|0|{4|error1|}122|127|}
{2010006001|XXGobject_psameas_object|193|0|320|0|{metadata|error1_metadata|1|0|}127|122|}
{2010212001|XXGvertex_oport_oport|194|0|321|0|{5|log|}122|128|}
{2010006001|XXGobject_psameas_object|195|0|323|0|{metadata|log_metadata|1|0|}128|122|}
{2010211001|XXGvertex_iport_iport|196|0|324|0|{0|in0|}122|129|}
{2010006001|XXGobject_psameas_object|197|0|326|0|{metadata|in0_metadata|1|0|}129|122|}
{2010211001|XXGvertex_iport_iport|198|0|327|0|{1|in1|}122|130|}
{2010006001|XXGobject_psameas_object|199|0|329|0|{metadata|in1_metadata|1|0|}130|122|}
{2010006001|XXGobject_psameas_object|200|0|330|0|{in0_metadata|out_metadata|0|0|}113|131|}
{2010212001|XXGvertex_oport_oport|201|0|332|0|{0|out|}131|132|}
{2010213001|XXGoport_dst_flow|202|0|334|0|{0|}132|105|}
{2010212001|XXGvertex_oport_oport|203|0|335|0|{1|reject|}131|133|}
{2010212001|XXGvertex_oport_oport|204|0|337|0|{2|error|}131|134|}
{2010212001|XXGvertex_oport_oport|205|0|339|0|{3|log|}131|135|}
{2010211001|XXGvertex_iport_iport|206|0|341|0|{0|in|}131|136|}
{2010007001|XXGobject_proto_object|207|0|343|0|{}131|137|}
{2010212001|XXGvertex_oport_oport|208|0|345|0|{0|out|}137|138|}
{2010006001|XXGobject_psameas_object|209|0|347|0|{metadata|out_metadata|1|0|}138|137|}
{2010212001|XXGvertex_oport_oport|210|0|348|0|{1|reject|}137|139|}
{2010006001|XXGobject_psameas_object|211|0|350|0|{metadata|reject_metadata|1|0|}139|137|}
{2010212001|XXGvertex_oport_oport|212|0|351|0|{2|error|}137|140|}
{2010006001|XXGobject_psameas_object|213|0|353|0|{metadata|error_metadata|1|0|}140|137|}
{2010212001|XXGvertex_oport_oport|214|0|354|0|{3|log|}137|141|}
{2010006001|XXGobject_psameas_object|215|0|356|0|{metadata|log_metadata|1|0|}141|137|}
{2010211001|XXGvertex_iport_iport|216|0|357|0|{0|in|}137|142|}
{2010006001|XXGobject_psameas_object|217|0|359|0|{metadata|in_metadata|1|0|}142|137|}
{2010006001|XXGobject_psameas_object|218|0|360|0|{in1_metadata|out_metadata|0|0|}113|131|}
{2010006001|XXGobject_psameas_object|219|0|361|0|{out_metadata|out_metadata|0|0|}113|131|}
{2010006001|XXGobject_psameas_object|220|0|362|0|{reject0_metadata|out_metadata|0|0|}113|131|}
{2010006001|XXGobject_psameas_object|221|0|363|0|{reject1_metadata|out_metadata|0|0|}113|131|}
{2010601001|XXGgraph_vertex_vertex|222|0|364|0|{Redefine_trailer_if_needed_1|}102|143|}
{2010212001|XXGvertex_oport_oport|223|0|366|0|{0|out|}143|144|}
{2010213001|XXGoport_dst_flow|224|0|368|0|{0|}144|103|}
{2010211001|XXGvertex_iport_iport|225|0|369|0|{0|in|}143|145|}
{2010007001|XXGobject_proto_object|226|0|371|0|{}143|146|}
{2010212001|XXGvertex_oport_oport|227|0|373|0|{0|out|}146|147|}
{2010006001|XXGobject_psameas_object|228|0|375|0|{metadata|out_metadata|1|0|}147|146|}
{2010211001|XXGvertex_iport_iport|229|0|376|0|{0|in|}146|148|}
{2010006001|XXGobject_psameas_object|230|0|378|0|{metadata|in_metadata|1|0|}148|146|}
{2010601001|XXGgraph_vertex_vertex|231|0|379|0|{Rf_Trailer_Validation|}102|149|}
{2010212001|XXGvertex_oport_oport|232|0|381|0|{0|out0|}149|150|}
{2010213001|XXGoport_dst_flow|233|0|383|0|{0|}150|104|}
{2010212001|XXGvertex_oport_oport|234|0|384|0|{1|reject0|}149|151|}
{2010212001|XXGvertex_oport_oport|235|0|386|0|{2|error0|}149|152|}
{2010212001|XXGvertex_oport_oport|236|0|388|0|{3|log|}149|153|}
{2010211001|XXGvertex_iport_iport|237|0|390|0|{0|in|}149|154|}
{2010214001|XXGiport_src_flow|238|0|392|0|{0|}154|103|}
{2010007001|XXGobject_proto_object|239|0|393|0|{}149|155|}
{2010212001|XXGvertex_oport_oport|240|0|395|0|{0|out0|}155|156|}
{2010006001|XXGobject_psameas_object|241|0|397|0|{metadata|out0_metadata|1|0|}156|155|}
{2010006001|XXGobject_psameas_object|242|0|398|0|{transform0|transform0|1|0|}156|155|}
{2010212001|XXGvertex_oport_oport|243|0|399|0|{1|reject0|}155|157|}
{2010006001|XXGobject_psameas_object|244|0|401|0|{metadata|reject0_metadata|1|0|}157|155|}
{2010212001|XXGvertex_oport_oport|245|0|402|0|{2|error0|}155|158|}
{2010006001|XXGobject_psameas_object|246|0|404|0|{metadata|error0_metadata|1|0|}158|155|}
{2010212001|XXGvertex_oport_oport|247|0|405|0|{3|log|}155|159|}
{2010006001|XXGobject_psameas_object|248|0|407|0|{metadata|log_metadata|1|0|}159|155|}
{2010211001|XXGvertex_iport_iport|249|0|408|0|{0|in|}155|160|}
{2010006001|XXGobject_psameas_object|250|0|410|0|{metadata|in_metadata|1|0|}160|155|}
{2010006001|XXGobject_psameas_object|251|0|411|0|{in_metadata|out_metadata|0|0|}149|143|}
{2010006001|XXGobject_psameas_object|252|0|412|0|{out0_metadata|out_metadata|0|0|}149|131|}
{2010006001|XXGobject_psameas_object|253|0|413|0|{reject0_metadata|out_metadata|0|0|}149|143|}
{2010601001|XXGgraph_vertex_vertex|254|0|414|0|{Rollup|}102|131|}
{2010601001|XXGgraph_vertex_vertex|255|0|415|0|{Trash|}102|161|}
{2010211001|XXGvertex_iport_iport|256|0|417|0|{0|in|}161|162|}
{2010214001|XXGiport_src_flow|257|0|419|0|{0|}162|106|}
{2010007001|XXGobject_proto_object|258|0|420|0|{}161|163|}
{2010211001|XXGvertex_iport_iport|259|0|422|0|{0|in|}163|164|}
{2010006001|XXGobject_psameas_object|260|0|424|0|{metadata|in_metadata|1|0|}164|163|}
{2010006001|XXGobject_psameas_object|261|0|425|0|{in_metadata|out_metadata|0|0|}161|131|}
{2010211001|XXGvertex_iport_iport|262|0|426|0|{0|in1|}102|165|}
{2010215002|XXGiport_binding_iport|263|0|428|0|{.5|.5|{12|93000|314000|73000|314000|57000|314000|57000|344000|40000|344000|20000|344000|}26860|}165|136|}
{2010214001|XXGiport_src_flow|264|0|429|0|{0|}165|39|}
{2010211001|XXGvertex_iport_iport|265|0|430|0|{1|in0|}102|166|}
{2010215002|XXGiport_binding_iport|266|0|432|0|{.5|.5|{12|109000|154000|89000|154000|65000|154000|65000|184000|40000|184000|20000|184000|}26861|}166|145|}
{2010214001|XXGiport_src_flow|267|0|433|0|{0|}166|32|}
{2010212001|XXGvertex_oport_oport|268|0|434|0|{0|out0|}31|167|}
{2010216002|XXGoport_binding_oport|269|0|436|0|{.5|.572519063949585|{12|837000|254000|857000|254000|923000|254000|923000|264000|989000|264000|1009000|264000|}806|}167|53|}
{2010212001|XXGvertex_oport_oport|270|0|437|0|{1|out1|}31|168|}
{2010216002|XXGoport_binding_oport|271|0|439|0|{.5|.4883720874786377|{12|839000|109000|859000|109000|924000|109000|924000|99000|989000|99000|1009000|99000|}807|}168|63|}
{2010212001|XXGvertex_oport_oport|272|0|440|0|{2|out2|}31|169|}
{2010216002|XXGoport_binding_oport|273|0|442|0|{.5|.5|{12|843000|409000|863000|409000|926000|409000|926000|429000|989000|429000|1009000|429000|}808|}169|69|}
{2010211001|XXGvertex_iport_iport|274|0|443|0|{0|in0|}31|170|}
{2010215002|XXGiport_binding_iport|275|0|445|0|{.5|.5|{12|146000|254000|126000|254000|83000|254000|83000|264000|40000|264000|20000|264000|}805|}170|45|}
{2010212001|XXGvertex_oport_oport|276|0|446|0|{0|out1|}30|171|}
{2010216002|XXGoport_binding_oport|277|0|448|0|{.5|.237726092338562|{12|326000|159000|346000|159000|439000|159000|439000|79000|741000|79000|761000|79000|}2|}171|168|}
{2010213001|XXGoport_dst_flow|278|0|449|0|{0|}171|5|}
{2010212001|XXGvertex_oport_oport|279|0|450|0|{1|out2|}30|172|}
{2010216002|XXGoport_binding_oport|280|0|452|0|{.5|.24031007289886475|{12|326000|229000|346000|229000|440000|229000|440000|314000|741000|314000|761000|314000|}3|}172|169|}
{2010213001|XXGoport_dst_flow|281|0|453|0|{0|}172|8|}
{2010212001|XXGvertex_oport_oport|282|0|454|0|{2|out0|}30|173|}
{2010216002|XXGoport_binding_oport|283|0|456|0|{.5|.5|{8|326000|194000|346000|194000|741000|194000|761000|194000|}4|}173|167|}
{2010213001|XXGoport_dst_flow|284|0|457|0|{0|}173|7|}
{2010211001|XXGvertex_iport_iport|285|0|458|0|{0|in0|}30|174|}
{2010215002|XXGiport_binding_iport|286|0|460|0|{.5|.5|{8|93000|194000|73000|194000|38000|194000|18000|194000|}1|}174|170|}
{2010214001|XXGiport_src_flow|287|0|461|0|{0|}174|6|}
{2010601001|XXGgraph_vertex_vertex|288|0|462|0|{Stage_Detail|}1|58|}
{2010601001|XXGgraph_vertex_vertex|289|0|463|0|{Trailer|}1|74|}
{2010109001|XXGobject_property_value|290|0|464|0|{0|TrackingThumbprint|72|}1|175|}
